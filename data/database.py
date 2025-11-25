import psycopg2
import logging
from datetime import datetime
from config import load_config


class DatabaseManager:
    def __init__(self):
        self.config = load_config()
        self.connection = None
        self.connect()

    def connect(self):
        try:
            self.connection = psycopg2.connect(
                host=self.config['database']['host'],
                port=self.config['database']['port'],
                database=self.config['database']['name'],
                user=self.config['database']['user'],
                password=self.config['database']['password']
            )
            logging.info("Успешное подключение к базе данных")
        except Exception as e:
            logging.error(f"Ошибка подключения к БД: {e}")

    def save_sensor_data(self, sensor_data):
        query = """
        INSERT INTO sensor_data 
        (timestamp, speed, temperature, vibration, current, efficiency) 
        VALUES (%s, %s, %s, %s, %s, %s)
        """

        try:
            cursor = self.connection.cursor()
            cursor.execute(query, (
                datetime.now(),
                sensor_data.get('conveyor_speed', 0),
                sensor_data.get('motor_temperature', 0),
                sensor_data.get('vibration_level', 0),
                sensor_data.get('motor_current', 0),
                sensor_data.get('efficiency', 100)
            ))
            self.connection.commit()
            cursor.close()
        except Exception as e:
            logging.error(f"Ошибка сохранения данных: {e}")
            self.connection.rollback()

    def save_alert(self, alert_data):
        query = """
        INSERT INTO alerts 
        (timestamp, alert_type, severity, message, resolved) 
        VALUES (%s, %s, %s, %s, %s)
        """

        try:
            cursor = self.connection.cursor()
            cursor.execute(query, (
                datetime.now(),
                alert_data['type'],
                alert_data['severity'],
                alert_data['message'],
                False
            ))
            self.connection.commit()
            cursor.close()
        except Exception as e:
            logging.error(f"Ошибка сохранения алерта: {e}")

    def get_historical_data(self, hours=24):
        query = """
        SELECT timestamp, speed, temperature, vibration, efficiency 
        FROM sensor_data 
        WHERE timestamp >= NOW() - INTERVAL '%s hours' 
        ORDER BY timestamp
        """

        try:
            cursor = self.connection.cursor()
            cursor.execute(query, (hours,))
            data = cursor.fetchall()
            cursor.close()
            return data
        except Exception as e:
            logging.error(f"Ошибка получения исторических данных: {e}")
            return []