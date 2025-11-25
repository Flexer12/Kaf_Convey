import logging
import time
from datetime import datetime

from config import MODBUS_REGISTERS


class SensorManager:
    def __init__(self, modbus_client):
        self.modbus_client = modbus_client
        self.sensor_cache = {}
        self.last_update = None

    def get_sensor_data(self):
        """Получение данных со всех датчиков"""
        try:
            raw_data = self.modbus_client.read_all_sensors()

            # Добавляем метку времени
            sensor_data = {
                'timestamp': datetime.now().isoformat(),
                **raw_data
            }

            # Кэшируем данные
            self.sensor_cache = sensor_data
            self.last_update = datetime.now()

            return sensor_data

        except Exception as e:
            logging.error(f"Ошибка получения данных с датчиков: {e}")
            return self.sensor_cache  # Возвращаем кэшированные данные

    def get_sensor_history(self, sensor_name, window=10):
        """Получение истории показаний датчика"""
        # В реальной реализации здесь будет обращение к БД
        # Для демонстрации возвращаем фиктивные данные
        import random
        return [random.uniform(0, 10) for _ in range(window)]

    def check_sensor_health(self):
        """Проверка работоспособности датчиков"""
        health_status = {}
        for sensor_name in MODBUS_REGISTERS.keys():
            value = self.modbus_client.read_register(sensor_name)
            health_status[sensor_name] = value is not None

        return health_status