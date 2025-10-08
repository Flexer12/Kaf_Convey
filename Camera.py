import cv2
import os
from datetime import datetime
import time


class CameraCapture:
    def __init__(self, camera_index=1, output_dir="train"):
        self.camera_index = camera_index
        self.output_dir = output_dir
        self.cap = None

    def initialize_camera(self):
        """Инициализация камеры"""
        self.cap = cv2.VideoCapture(self.camera_index)

        # Настройка параметров камеры (опционально)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_FPS, 30)

        # Проверяем подключение камеры
        if not self.cap.isOpened():
            print(f"Ошибка: Не удалось подключиться к камере с индексом {self.camera_index}")
            return False

        print("Камера успешно подключена!")
        return True

    def capture_single_photo(self, filename=None):
        """Сделать одно фото и сохранить"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"photo_{timestamp}.jpg"

        full_path = os.path.join(self.output_dir, filename)

        # Захватываем кадр
        ret, frame = self.cap.read()

        if ret:
            # Сохраняем изображение
            cv2.imwrite(full_path, frame)
            print(f"Фото сохранено: {full_path}")
            return True, full_path
        else:
            print("Ошибка: Не удалось захватить кадр")
            return False, None

    def capture_multiple_photos(self, count=10, delay=2):
        """Сделать несколько фото с интервалом"""
        print(f"Начинаем захват {count} фото с интервалом {delay} секунд...")

        for i in range(count):
            filename = f"batch_photo_{i + 1:03d}.jpg"
            success, path = self.capture_single_photo(filename)

            if success:
                print(f"Сделано фото {i + 1}/{count}")
            else:
                print(f"Ошибка при создании фото {i + 1}")

            if i < count - 1:  # Не ждем после последнего фото
                time.sleep(delay)

    def preview_mode(self):
        """Режим предпросмотра с возможностью сделать фото по нажатию"""
        print("Режим предпросмотра запущен")
        print("Нажмите:")
        print("  SPACE - сделать фото")
        print("  'q' - выйти")

        photo_count = 0

        while True:
            ret, frame = self.cap.read()

            if not ret:
                print("Ошибка чтения кадра")
                break

            # Добавляем текст на изображение
            cv2.putText(frame, "Press SPACE to capture, 'q' to quit",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f"Photos taken: {photo_count}",
                        (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            cv2.imshow('Camera Preview - Capture Photos', frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord(' '):  # SPACE для фото
                photo_count += 1
                filename = f"preview_photo_{photo_count:03d}.jpg"
                success, path = self.capture_single_photo(filename)

                if success:
                    # Показываем подтверждение
                    confirmation = frame.copy()
                    cv2.putText(confirmation, "PHOTO CAPTURED!",
                                (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
                    cv2.imshow('Camera Preview - Capture Photos', confirmation)
                    cv2.waitKey(500)  # Показываем сообщение 0.5 секунды

            elif key == ord('q'):  # 'q' для выхода
                break

        cv2.destroyAllWindows()

    def release_camera(self):
        """Освобождаем камеру"""
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        print("Камера отключена")


# Использование
def main():
    # Создаем экземпляр камеры
    # camera_index = 0 - обычно это встроенная камера
    # camera_in dex = 1 - USB камера
    camera = CameraCapture(camera_index=1, output_dir="train")
    camera.initialize_camera()

    if camera.initialize_camera():

        try:
            # Тестируем одно фото
            print("Делаем тестовое фото...")
            camera.capture_single_photo("test_photo.jpg")

            # Запускаем режим предпросмотра
            camera.preview_mode()

            # Или делаем серию фото автоматически
            # camera.capture_multiple_photos(count=20, delay=3)

        finally:
            camera.release_camera()


main()
