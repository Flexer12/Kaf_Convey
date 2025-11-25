import paho.mqtt.client as mqtt
import json
import logging
from config.config import load_config


class MQTTClient:
    def __init__(self):
        self.config = load_config()
        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        self.connected = False

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            logging.info("Успешное подключение к MQTT брокеру")
            # Подписываемся на топик команд
            self.client.subscribe(self.config['mqtt']['topics']['commands'])
        else:
            logging.error(f"Ошибка подключения к MQTT: {rc}")

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            topic = msg.topic
            logging.info(f"Получено сообщение из топика {topic}: {payload}")

            # Обработка команд
            if topic == self.config['mqtt']['topics']['commands']:
                self._handle_command(payload)

        except Exception as e:
            logging.error(f"Ошибка обработки MQTT сообщения: {e}")

    def _on_disconnect(self, client, userdata, rc):
        self.connected = False
        logging.info("Отключение от MQTT брокера")

    def _handle_command(self, command):
        """Обработка входящих команд"""
        command_type = command.get('type')

        if command_type == 'SET_SPEED':
            new_speed = command.get('speed')
            logging.info(f"Команда установки скорости: {new_speed}")
            # Здесь будет код для отправки команды на PLC

        elif command_type == 'EMERGENCY_STOP':
            logging.info("Команда аварийной остановки")
            # Код для аварийной остановки

        elif command_type == 'MAINTENANCE_MODE':
            logging.info("Переход в режим обслуживания")

    def connect(self):
        mqtt_config = self.config['mqtt']
        try:
            self.client.username_pw_set(
                mqtt_config['username'],
                mqtt_config['password']
            )
            self.client.connect(
                mqtt_config['broker'],
                mqtt_config['port'],
                60
            )
            self.client.loop_start()
        except Exception as e:
            logging.error(f"Ошибка подключения MQTT: {e}")

    def publish_sensor_data(self, sensor_data):
        if self.connected:
            topic = self.config['mqtt']['topics']['sensors']
            self.client.publish(topic, json.dumps(sensor_data))

    def publish_alert(self, alert_data):
        if self.connected:
            topic = self.config['mqtt']['topics']['alerts']
            self.client.publish(topic, json.dumps(alert_data))

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()