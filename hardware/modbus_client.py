from pymodbus.client import ModbusTcpClient
import logging
from config.modbus_config import MODBUS_REGISTERS


class ModbusClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.client = None
        self.connect()

    def connect(self):
        try:
            self.client = ModbusTcpClient(self.host, port=self.port)
            if self.client.connect():
                logging.info(f"Успешное подключение к Modbus серверу {self.host}:{self.port}")
            else:
                logging.error("Не удалось подключиться к Modbus серверу")
        except Exception as e:
            logging.error(f"Ошибка подключения Modbus: {e}")

    def read_register(self, register_name):
        if register_name not in MODBUS_REGISTERS:
            logging.error(f"Неизвестный регистр: {register_name}")
            return None

        reg_config = MODBUS_REGISTERS[register_name]
        try:
            result = self.client.read_holding_registers(
                address=reg_config['address'],
                count=1,
                slave=1
            )

            if not result.isError():
                raw_value = result.registers[0]
                scaled_value = raw_value * reg_config['scale']
                return scaled_value
            else:
                logging.error(f"Ошибка чтения регистра {register_name}")
                return None

        except Exception as e:
            logging.error(f"Исключение при чтении {register_name}: {e}")
            return None

    def read_all_sensors(self):
        sensor_data = {}
        for sensor_name in MODBUS_REGISTERS.keys():
            value = self.read_register(sensor_name)
            if value is not None:
                sensor_data[sensor_name] = value

        return sensor_data

    def disconnect(self):
        if self.client:
            self.client.close()
            logging.info("Отключение от Modbus сервера")