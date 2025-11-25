import logging
import time
import signal
import sys
from datetime import datetime

from config import load_config
from hardware.modbus_client import ModbusClient
from hardware.sensors import SensorManager
from iot.mqtt_client import MQTTClient
from digital_twin.twin_core import DigitalTwin
from digital_twin.analytics import AnalyticsEngine
from data.database import DatabaseManager


class ConveyorDigitalTwin:
    def __init__(self):
        # Настройка логирования
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('conveyor_twin.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )

        self.logger = logging.getLogger(__name__)
        self.config = load_config()
        self.running = False

        # Инициализация компонентов
        self.logger.info("Инициализация компонентов системы...")

        # Подключение к оборудованию
        self.modbus_client = ModbusClient(
            self.config['modbus']['host'],
            self.config['modbus']['port']
        )

        self.sensor_manager = SensorManager(self.modbus_client)
        self.mqtt_client = MQTTClient()
        self.database = DatabaseManager()

        # Цифровой двойник и аналитика
        self.digital_twin = DigitalTwin()
        self.analytics_engine = AnalyticsEngine(self.digital_twin)

        self.logger.info("Все компоненты инициализированы")

    def start(self):
        """Запуск системы цифрового двойника"""
        self.logger.info("Запуск системы цифрового двойника конвейера")
        self.running = True

        # Подключение к MQTT брокеру
        self.mqtt_client.connect()

        # Основной цикл работы
        try:
            while self.running:
                self._main_loop()
                time.sleep(2)  # Цикл обновления каждые 2 секунды

        except KeyboardInterrupt:
            self.logger.info("Получен сигнал прерывания")
        except Exception as e:
            self.logger.error(f"Критическая ошибка: {e}")
        finally:
            self.stop()

    def _main_loop(self):
        """Основной цикл обработки данных"""
        try:
            # 1. Чтение данных с датчиков
            sensor_data = self.sensor_manager.get_sensor_data()

            if sensor_data:
                # 2. Обновление цифрового двойника
                self.digital_twin.update_state(sensor_data)

                # 3. Сохранение в базу данных
                self.database.save_sensor_data(sensor_data)

                # 4. Отправка данных через MQTT
                self.mqtt_client.publish_sensor_data({
                    'sensor_data': sensor_data,
                    'digital_twin_state': self.digital_twin.operational_parameters,
                    'timestamp': datetime.now().isoformat()
                })

                # 5. Отправка алертов при необходимости
                for alert in self.digital_twin.alerts:
                    self.mqtt_client.publish_alert(alert)
                    self.database.save_alert(alert)
                    self.logger.warning(f"ALERT: {alert['message']}")

                # 6. Логирование состояния
                if len(self.digital_twin.alerts) == 0:
                    self.logger.info(
                        f"Скорость: {self.digital_twin.operational_parameters['current_speed']:.1f} м/с, "
                        f"Эффективность: {self.digital_twin.operational_parameters['efficiency']:.1f}%"
                    )

        except Exception as e:
            self.logger.error(f"Ошибка в основном цикле: {e}")

    def stop(self):
        """Корректная остановка системы"""
        self.logger.info("Остановка системы...")
        self.running = False

        if hasattr(self, 'modbus_client'):
            self.modbus_client.disconnect()

        if hasattr(self, 'mqtt_client'):
            self.mqtt_client.disconnect()

        self.logger.info("Система остановлена")


def signal_handler(signum, frame):
    """Обработчик сигналов для корректного завершения"""
    print("\nПолучен сигнал завершения...")
    sys.exit(0)


if __name__ == "__main__":
    # Регистрация обработчиков сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Создание и запуск системы
    conveyor_system = ConveyorDigitalTwin()
    conveyor_system.start()