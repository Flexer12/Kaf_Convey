MODBUS_REGISTERS = {
    'encoder_position': {'address': 0, 'type': 'uint16', 'scale': 0.1},
    'motor_temperature': {'address': 1, 'type': 'uint16', 'scale': 0.1},
    'vibration_level': {'address': 2, 'type': 'uint16', 'scale': 0.01},
    'motor_current': {'address': 3, 'type': 'uint16', 'scale': 0.01},
    'conveyor_speed': {'address': 4, 'type': 'uint16', 'scale': 0.01},
    'emergency_stop': {'address': 5, 'type': 'bool', 'scale': 1},
}

SENSOR_THRESHOLDS = {
    'temperature_warning': 80.0,
    'temperature_critical': 90.0,
    'vibration_warning': 5.0,
    'vibration_critical': 7.0,
    'current_warning': 15.0,
}