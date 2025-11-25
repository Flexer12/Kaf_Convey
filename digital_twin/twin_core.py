import logging
from datetime import datetime, timedelta
from config import load_config
from config.modbus_config import SENSOR_THRESHOLDS


class DigitalTwin:
    def __init__(self):
        self.config = load_config()
        self.sensor_data = {}
        self.operational_parameters = {
            'current_speed': 0.0,
            'motor_temperature': 0.0,
            'vibration_level': 0.0,
            'motor_current': 0.0,
            'efficiency': 100.0,
            'uptime_hours': 0,
            'items_processed': 0,
            'defects_count': 0
        }
        self.alerts = []
        self.maintenance_schedule = []
        self.operating_mode = "NORMAL"  # NORMAL, MAINTENANCE, EMERGENCY

    def update_state(self, sensor_data):
        """Обновление состояния цифрового двойника на основе данных с датчиков"""
        self.sensor_data = sensor_data

        # Обновление операционных параметров
        self.operational_parameters.update({
            'current_speed': sensor_data.get('conveyor_speed', 0),
            'motor_temperature': sensor_data.get('motor_temperature', 0),
            'vibration_level': sensor_data.get('vibration_level', 0),
            'motor_current': sensor_data.get('motor_current', 0),
        })

        # Расчет эффективности
        self._calculate_efficiency()

        # Проверка аномалий
        self._check_anomalies()

        # Обновление статистики
        self._update_statistics()

    def _calculate_efficiency(self):
        """Расчет эффективности работы конвейера"""
        base_efficiency = 100.0
        params = self.operational_parameters

        # Штраф за высокую температуру
        if params['motor_temperature'] > SENSOR_THRESHOLDS['temperature_warning']:
            temp_penalty = (params['motor_temperature'] - SENSOR_THRESHOLDS['temperature_warning']) * 0.5
            base_efficiency -= temp_penalty

        # Штраф за вибрацию
        if params['vibration_level'] > SENSOR_THRESHOLDS['vibration_warning']:
            vibration_penalty = (params['vibration_level'] - SENSOR_THRESHOLDS['vibration_warning']) * 2.0
            base_efficiency -= vibration_penalty

        # Штраф за перегрузку по току
        if params['motor_current'] > SENSOR_THRESHOLDS['current_warning']:
            current_penalty = (params['motor_current'] - SENSOR_THRESHOLDS['current_warning']) * 1.5
            base_efficiency -= current_penalty

        self.operational_parameters['efficiency'] = max(60.0, base_efficiency)

    def _check_anomalies(self):
        """Обнаружение аномалий и генерация предупреждений"""
        params = self.operational_parameters
        new_alerts = []

        # Проверка критической температуры
        if params['motor_temperature'] > SENSOR_THRESHOLDS['temperature_critical']:
            new_alerts.append({
                'type': 'CRITICAL_TEMPERATURE',
                'message': f'Критическая температура двигателя: {params["motor_temperature"]:.1f}°C',
                'severity': 'HIGH',
                'timestamp': datetime.now().isoformat()
            })

        # Проверка вибрации
        if params['vibration_level'] > SENSOR_THRESHOLDS['vibration_critical']:
            new_alerts.append({
                'type': 'HIGH_VIBRATION',
                'message': f'Высокий уровень вибрации: {params["vibration_level"]:.2f} mm/s',
                'severity': 'HIGH',
                'timestamp': datetime.now().isoformat()
            })

        # Проверка низкой эффективности
        if params['efficiency'] < 75.0:
            new_alerts.append({
                'type': 'LOW_EFFICIENCY',
                'message': f'Низкая эффективность: {params["efficiency"]:.1f}%',
                'severity': 'MEDIUM',
                'timestamp': datetime.now().isoformat()
            })

        self.alerts = new_alerts

    def _update_statistics(self):
        """Обновление статистики работы"""
        # В реальной реализации здесь будет сложная логика подсчета
        self.operational_parameters['uptime_hours'] += 0.0002778  # ~1 секунда в часах
        self.operational_parameters['items_processed'] += int(self.operational_parameters['current_speed'] * 0.1)

    def predict_maintenance(self):
        """Прогнозирование необходимости обслуживания"""
        prediction = {
            'maintenance_needed': False,
            'predicted_failure': None,
            'recommended_actions': [],
            'urgency': 'LOW'
        }

        params = self.operational_parameters

        # Простая логика предсказания (можно заменить ML-моделью)
        if (params['vibration_level'] > 6.0 and
                params['motor_temperature'] > 85 and
                params['efficiency'] < 80):
            prediction.update({
                'maintenance_needed': True,
                'predicted_failure': 'Подшипник двигателя',
                'recommended_actions': ['Проверить балансировку', 'Заменить подшипники'],
                'urgency': 'HIGH'
            })

        elif params['uptime_hours'] > self.config['conveyor']['maintenance_interval']:
            prediction.update({
                'maintenance_needed': True,
                'predicted_failure': 'Плановое обслуживание',
                'recommended_actions': ['Полное техническое обслуживание'],
                'urgency': 'MEDIUM'
            })

        return prediction

    def simulate_scenario(self, scenario_type, parameters=None):
        """Симуляция различных сценариев работы"""
        if scenario_type == "increase_speed":
            new_speed = parameters.get('speed', self.operational_parameters['current_speed'] * 1.2)

            return {
                'scenario': 'increase_speed',
                'current_speed': new_speed,
                'predicted_vibration': self.operational_parameters['vibration_level'] * 1.3,
                'predicted_temperature': self.operational_parameters['motor_temperature'] * 1.15,
                'warning': new_speed > self.config['conveyor']['max_speed']
            }

        elif scenario_type == "component_failure":
            return {
                'scenario': 'component_failure',
                'affected_component': parameters.get('component', 'motor_bearing'),
                'estimated_downtime_hours': 4.0,
                'required_parts': ['Подшипник XYZ-123', 'Смазка'],
                'urgency': 'HIGH'
            }