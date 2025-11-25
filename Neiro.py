import cv2
import serial
import threading
import time
from ultralytics import YOLO


class BoltDetectionSystem:
    def __init__(self, model_path, com_port_1="COM3", com_port_2="COM5", baudrate=115200):
        self.com_port_1 = com_port_1
        self.com_port_2 = com_port_2
        self.baudrate = baudrate
        self.running = True

        print("Загрузка модели YOLO...")
        self.model = YOLO(model_path)
        print("Модель загружена")

        # Подключаемся к двум Arduino
        self.ser_1 = self.connect_to_arduino(self.com_port_1, "Arduino 1")
        self.ser_2 = self.connect_to_arduino(self.com_port_2, "Arduino 2")

        # Начальный статус - NO BOLT
        self.current_detection = 0  # 0 - NO BOLT, 1 - LONG BOLT, 2 - SHORT BOLT
        self.last_detection = 0
        self.frame_count = 0

    def connect_to_arduino(self, port, arduino_name):
        """Подключение к Arduino - ВЫЗЫВАЕТСЯ в __init__"""
        try:
            ser = serial.Serial(port, self.baudrate)
            time.sleep(2)
            print(f"✅ Подключение к {arduino_name} ({port}) установлено")
            return ser
        except Exception as e:
            print(f"❌ Ошибка подключения к {arduino_name} ({port}): {e}")
            return None

    def read_from_arduino(self, ser, arduino_name):
        """Чтение данных от Arduino - ВЫЗЫВАЕТСЯ в потоке"""
        print(f"📡 Запуск потока чтения из {arduino_name}...")
        while self.running:
            try:
                if ser and ser.in_waiting > 0:
                    data = ser.readline().decode('ascii', errors='ignore').strip()
                    if data:
                        print(f"📨 {arduino_name}: {data}")
            except Exception as e:
                print(f'Ошибка считывания от {arduino_name}:', e)
            time.sleep(0.01)

    def user_input_handler(self):
        """Ввод команд пользователем - ВЫЗЫВАЕТСЯ в основном потоке"""
        print("💬 Запуск потока ввода пользователя...")
        while self.running:
            try:
                cmd = input().strip()
                if not cmd:
                    continue

                if cmd.lower() == 'exit':
                    print("🛑 Завершение работы...")
                    self.running = False
                    break
                elif cmd.lower() == 'status':
                    self.show_system_status()
                elif cmd.lower() == 'help':
                    self.show_help()
                elif cmd.lower() == 'save_frame':
                    self.save_current_frame = True
                    print("💾 Следующий кадр будет сохранен")
                elif cmd.lower() == 'reset':
                    self.current_detection = 0
                    self.last_detection = 0
                    self.write_to_arduino_2(0)  # Отправляем сброс на вторую Arduino
                    print("🔄 Статус сброшен на NO BOLT")
                elif cmd.startswith('arduino1 '):
                    # Команда для первой Arduino
                    command = cmd[9:]  # Убираем 'arduino1 '
                    self.send_user_command(self.ser_1, command, "Arduino 1")
                elif cmd.startswith('arduino2 '):
                    # Команда для второй Arduino
                    command = cmd[9:]  # Убираем 'arduino2 '
                    self.send_user_command(self.ser_2, command, "Arduino 2")
                else:
                    # Отправляем команду на обе Arduino
                    self.send_user_command(self.ser_1, cmd, "Arduino 1")


            except Exception as e:
                print(f"Ошибка ввода: {e}")
                break

    def send_user_command(self, ser, cmd, arduino_name):
        """Отправка пользовательской команды в Arduino - ВЫЗЫВАЕТСЯ из user_input_handler"""
        if ser and ser.is_open:
            try:
                ser.write(cmd.encode())
                print(f"👤 [USER] Отправлено в {arduino_name}: {cmd}")
            except Exception as e:
                print(f"❌ Ошибка отправки команды в {arduino_name}: {e}")
        else:
            print(f"❌ {arduino_name} не подключен")

    def write_to_arduino_2(self, detection):
        """Отправка данных детекции во вторую Arduino - ВЫЗЫВАЕТСЯ из process_video_stream"""
        if self.ser_2 and self.ser_2.is_open:
            try:
                if detection == 1:  # long_bolt
                    self.ser_2.write('1'.encode())
                    print("🔩 [AUTO] Отправлено в Arduino 2: 1 (LONG_BOLT)")
                elif detection == 2:  # short_bolt
                    self.ser_2.write('2'.encode())
                    print("🔩 [AUTO] Отправлено в Arduino 2: 2 (SHORT_BOLT)")
                elif detection == 0:  # no_bolt
                    self.ser_2.write('0'.encode())
                    print("🔩 [AUTO] Отправлено в Arduino 2: 0 (NO_BOLT)")
            except Exception as e:
                print(f'❌ Ошибка отправки детекции в Arduino 2: {e}')

    def detect_bolts(self, frame):
        """Детекция болтов на кадре - ВЫЗЫВАЕТСЯ из process_video_stream"""
        results = self.model(frame, verbose=False)
        detected_class = 0

        for result in results:
            if result.boxes is not None and len(result.boxes) > 0:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])

                    if confidence > 0.5:
                        if class_id == 0:  # long_bolt
                            detected_class = 1
                            break
                        elif class_id == 1:  # short_bolt
                            detected_class = 2
                            break
        return detected_class

    def process_video_stream(self, source=0):
        """Обработка видеопотока - ВЫЗЫВАЕТСЯ в потоке"""
        print("🎥 Запуск видеопотока ")
        cap = self.initialize_camera(source)
        if not cap:
            return

        self.save_current_frame = False
        last_status = None

        while self.running:
            ret, frame = cap.read()
            if not ret:
                print("❌ Ошибка чтения кадра")
                time.sleep(1)
                continue

            # ВЫЗОВ ФУНКЦИИ детекции
            detected_class = self.detect_bolts(frame)

            # НОВАЯ ЛОГИКА: обновляем статус только при обнаружении нового типа болта
            if detected_class != 0:  # Если обнаружен какой-то болт
                if detected_class != self.current_detection:  # И это новый тип
                    self.current_detection = detected_class
                    # Отправляем команду на вторую Arduino
                    self.write_to_arduino_2(self.current_detection)
                    print(f"🔄 Переключение статуса: {self.get_detection_status()[0]}")
            # Если болт исчез (detected_class == 0), НЕ меняем текущий статус

            # ВЫЗОВ ФУНКЦИИ обработки кадра (без отображения)
            self.process_frame(frame)

            # Вывод статуса только при изменении
            current_status = self.get_detection_status()[0]
            if current_status != last_status:
                print(f"🔍 Статус детекции: {current_status}")
                last_status = current_status

            # Сохранение кадра только по команде пользователя
            if self.save_current_frame:
                self.save_frame_with_detection(frame)
                self.save_current_frame = False

            self.frame_count += 1
            time.sleep(0.03)  # ~30 FPS

        self.cleanup_camera(cap)

    def initialize_camera(self, source):
        """Инициализация камеры - ВЫЗЫВАЕТСЯ из process_video_stream"""
        cap = cv2.VideoCapture(source, cv2.CAP_DSHOW)
        # Настройки камеры
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        cap.set(cv2.CAP_PROP_FPS, 30)
        cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
        cap.set(cv2.CAP_PROP_FOCUS, 20)
        cap.set(cv2.CAP_PROP_AUTO_WB, 0)
        cap.set(cv2.CAP_PROP_WB_TEMPERATURE, 4500)
        cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0)
        cap.set(cv2.CAP_PROP_EXPOSURE, -7)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        if not cap.isOpened():
            print("❌ Ошибка открытия видеопотока")
            return None

        print("✅ Камера инициализирована")
        return cap

    def process_frame(self, frame):
        """Обработка кадра без отображения - ВЫЗЫВАЕТСЯ из process_video_stream"""
        # Здесь можно добавить дополнительную обработку кадра
        # Например, логирование, анализ и т.д.
        pass

    def save_frame_with_detection(self, frame):
        """Сохранение кадра с детекцией - ВЫЗЫВАЕТСЯ по команде пользователя"""
        try:
            # Аннотирование кадра
            results = self.model(frame, verbose=False)
            annotated_frame = results[0].plot()

            # Добавление текста статуса
            status_text, color = self.get_detection_status()
            cv2.putText(annotated_frame, f"Status: {status_text}",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            cv2.putText(annotated_frame, f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}",
                        (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            # Сохранение файла
            timestamp = int(time.time())
            filename = f"detection_{timestamp}_{status_text.replace(' ', '_')}.jpg"
            cv2.imwrite(filename, annotated_frame)
            print(f"💾 Кадр сохранен: {filename}")

        except Exception as e:
            print(f"❌ Ошибка сохранения кадра: {e}")

    def get_detection_status(self):
        """Получение статуса детекции - ВЫЗЫВАЕТСЯ из различных методов"""
        if self.current_detection == 1:
            return "LONG BOLT", (0, 255, 0)
        elif self.current_detection == 2:
            return "SHORT BOLT", (0, 255, 255)
        else:
            return "NO BOLT", (0, 0, 255)

    def cleanup_camera(self, cap):
        """Очистка ресурсов камеры - ВЫЗЫВАЕТСЯ из process_video_stream"""
        cap.release()
        print("✅ Ресурсы камеры освобождены")

    def show_system_status(self):
        """Показать статус системы - ВЫЗЫВАЕТСЯ из user_input_handler"""
        status = "✅ Активен" if self.running else "❌ Остановлен"
        arduino1_status = "✅ Подключен" if self.ser_1 and self.ser_1.is_open else "❌ Отключен"
        arduino2_status = "✅ Подключен" if self.ser_2 and self.ser_2.is_open else "❌ Отключен"

        print("\n=== СТАТУС СИСТЕМЫ ===")
        print(f"Система: {status}")
        print(f"Arduino 1: {arduino1_status}")
        print(f"Arduino 2: {arduino2_status}")
        print(f"Текущая детекция: {self.get_detection_status()[0]}")
        print(f"Обработано кадров: {self.frame_count}")
        print("=====================\n")

    def show_help(self):
        """Показать справку - ВЫЗЫВАЕТСЯ из user_input_handler"""
        print("\n=== СПРАВКА ПО КОМАНДАМ ===")
        print("help              - показать эту справку")
        print("status            - показать статус системы")
        print("save_frame        - сохранить следующий кадр")
        print("reset             - сбросить статус на NO BOLT")
        print("exit              - завершить работу программы")
        print("arduino1 <команда> - отправить команду только в Arduino 1")
        print("arduino2 <команда> - отправить команду только в Arduino 2")
        print("<любой текст>     - отправить команду в обе Arduino")
        print("===========================\n")

    def start_system(self):
        """Запуск системы - ВЫЗЫВАЕТСЯ из main"""
        print("\n🚀 ЗАПУСК СИСТЕМЫ ДЕТЕКЦИИ BOLTS С ДВУМЯ ARDUINO")
        print("=" * 50)

        # Запуск всех потоков
        threads = []

        # Поток чтения из Arduino 1
        if self.ser_1:
            reader_thread_1 = threading.Thread(target=self.read_from_arduino,
                                               args=(self.ser_1, "Arduino 1"), daemon=True)
            reader_thread_1.start()
            threads.append(reader_thread_1)

        # Поток чтения из Arduino 2
        if self.ser_2:
            reader_thread_2 = threading.Thread(target=self.read_from_arduino,
                                               args=(self.ser_2, "Arduino 2"), daemon=True)
            reader_thread_2.start()
            threads.append(reader_thread_2)

        # Поток видеопотока
        video_thread = threading.Thread(target=self.process_video_stream, args=(0,), daemon=True)
        video_thread.start()
        threads.append(video_thread)

        print("✅ Все потоки запущены")
        print("💬 Вводите команды ниже...")
        self.show_help()

        # Основной поток - ввод пользователя
        self.user_input_handler()

    def stop_system(self):
        """Остановка системы - ВЫЗЫВАЕТСЯ из main"""
        print("\n🛑 Остановка системы...")
        self.running = False

        if self.ser_1 and self.ser_1.is_open:
            self.ser_1.close()
            print("✅ Соединение с Arduino 1 закрыто")

        if self.ser_2 and self.ser_2.is_open:
            self.ser_2.close()
            print("✅ Соединение с Arduino 2 закрыто")

        print("✅ Система полностью остановлена")


def main():
    """Основная функция - ТОЧКА ВХОДА"""
    MODEL_PATH = "best.pt"
    COM_PORT_1 = "COM3"  # Первая Arduino
    COM_PORT_2 = "COM5"  # Вторая Arduino
    BAUD_RATE = 115200

    system = BoltDetectionSystem(MODEL_PATH, COM_PORT_1, COM_PORT_2, BAUD_RATE)

    try:
        system.start_system()
    except KeyboardInterrupt:
        print("\n⚠️ Программа прервана пользователем (Ctrl+C)")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
    finally:
        system.stop_system()
if __name__ == "__main__":
    main()