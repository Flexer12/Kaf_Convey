# config/__init__.py

import os
import yaml
from typing import Dict, Any

# Импорт основных классов конфигурации
from .modbus_config import MODBUS_REGISTERS, SENSOR_THRESHOLDS

# Версия пакета конфигурации
__version__ = "1.0.0"
__author__ = "Engineering Team"


def load_config() -> Dict[str, Any]:
    """
    Загрузка конфигурации из YAML файла
    """
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')

    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
            return config or {}
    except FileNotFoundError:
        print(f"Warning: Config file not found at {config_path}")
        return {}
    except yaml.YAMLError as e:
        print(f"Error parsing YAML config: {e}")
        return {}


def get_database_url() -> str:
    """
    Формирование URL для подключения к базе данных
    """
    config = load_config()
    db_config = config.get('database', {})

    return (f"postgresql://{db_config.get('user', 'postgres')}:"
            f"{db_config.get('password', 'password')}@"
            f"{db_config.get('host', 'localhost')}:"
            f"{db_config.get('port', 5432)}/"
            f"{db_config.get('name', 'conveyor_db')}")


def get_mqtt_config() -> Dict[str, Any]:
    """
    Получение конфигурации MQTT
    """
    config = load_config()
    return config.get('mqtt', {})


def validate_config() -> bool:
    """
    Валидация конфигурационных параметров
    """
    config = load_config()

    # Проверка обязательных параметров
    required_sections = ['modbus', 'mqtt', 'database']
    for section in required_sections:
        if section not in config:
            print(f"Missing required config section: {section}")
            return False

    # Проверка Modbus конфигурации
    modbus_config = config['modbus']
    if not modbus_config.get('host') or not modbus_config.get('port'):
        print("Invalid Modbus configuration")
        return False

    return True


# Автоматическая загрузка конфигурации при импорте пакета
CONFIG = load_config()

# Экспорт основных переменных для удобного доступа
__all__ = [
    'load_config',
    'get_database_url',
    'get_mqtt_config',
    'validate_config',
    'MODBUS_REGISTERS',
    'SENSOR_THRESHOLDS',
    'CONFIG'
]