"""
Модуль симуляции для цифрового двойника конвейера.

Обеспечивает:
- Симуляцию различных сценариев работы
- Моделирование отказов оборудования
- Тестирование алгоритмов управления
- Прогнозирование поведения системы
"""

import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

from config import load_config
from config.modbus_config import SENSOR_THRESHOLDS

logger = logging.getLogger(__name__)


class SimulationMode(Enum):
    """Режимы симуляции"""
    NORMAL_OPERATION = "normal"
    STRESS_TEST = "stress"
    FAILURE_SIMULATION = "failure"
    WHAT_IF_ANALYSIS = "what_if"
    MAINTENANCE_SCENARIO = "maintenance"


@dataclass
class SimulationResult:
    """Результат выполнения симуляции"""
    scenario_name: str
    timestamp: datetime
    parameters: Dict[str, Any]
    warnings: List[str]
    recommendations: List[str]
    success: bool
    duration_seconds: float


class ConveyorSimulator:
    """
    Класс для симуляции работы конвейера и тестирования сценариев
    """

    def __init__(self, digital_twin):
        self.digital_twin = digital_twin
        self.config = load_config()
        self.simulation_history = []
        self.active_simulations = {}

    def simulate_speed_increase(self, target_speed: float, duration_minutes: int = 60) -> SimulationResult:
        """
        Симуляция увеличения скорости конвейера

        Args:
            target_speed: Целевая скорость (м/с)
            duration_minutes: Длительность симуляции в минутах

        Returns:
            SimulationResult: Результаты симуляции
        """
        logger.info(f"Симуляция увеличения скорости до {target_speed} м/с")

        start_time = datetime.now()
        warnings = []
        recommendations = []

        # Текущие параметры
        current_params = self.digital_twin.operational_parameters.copy()

        # Прогнозируемые параметры при новой скорости
        predicted_params = self._predict_parameters_for_speed(target_speed)

        # Проверка ограничений
        max_speed = self.config['conveyor']['max_speed']
        if target_speed > max_speed:
            warnings.append(f"Целевая скорость {target_speed} м/с превышает максимальную {max_speed} м/с")
            success = False
        else:
            success = True

        # Проверка температурного режима
        if predicted_params['motor_temperature'] > SENSOR_THRESHOLDS['temperature_critical']:
            warnings.append(
                f"Прогнозируемая температура двигателя: {predicted_params['motor_temperature']:.1f}°C (критическая)")
            recommendations.append("Увеличить охлаждение двигателя перед увеличением скорости")
            success = False
        elif predicted_params['motor_temperature'] > SENSOR_THRESHOLDS['temperature_warning']:
            warnings.append(
                f"Прогнозируемая температура двигателя: {predicted_params['motor_temperature']:.1f}°C (высокая)")

        # Проверка вибрации
        if predicted_params['vibration_level'] > SENSOR_THRESHOLDS['vibration_critical']:
            warnings.append(
                f"Прогнозируемый уровень вибрации: {predicted_params['vibration_level']:.2f} mm/s (критический)")
            recommendations.append("Требуется балансировка оборудования перед увеличением скорости")
            success = False

        # Расчет эффективности
        efficiency_impact = self._calculate_efficiency_impact(current_params, predicted_params)
        predicted_params['efficiency'] = max(60, current_params['efficiency'] + efficiency_impact)

        if success:
            recommendations.append(f"Скорость может быть увеличена до {target_speed} м/с")
            recommendations.append(f"Прогнозируемая эффективность: {predicted_params['efficiency']:.1f}%")

        duration = (datetime.now() - start_time).total_seconds()

        result = SimulationResult(
            scenario_name="speed_increase",
            timestamp=start_time,
            parameters=predicted_params,
            warnings=warnings,
            recommendations=recommendations,
            success=success,
            duration_seconds=duration
        )

        self.simulation_history.append(result)
        return result

    def simulate_component_failure(self, component: str, severity: float = 0.5) -> SimulationResult:
        """
        Симуляция отказа компонента

        Args:
            component: Компонент для симуляции отказа ('motor', 'bearing', 'sensor', 'controller')
            severity: Степень тяжести отказа (0.1 - легкая, 1.0 - полный отказ)

        Returns:
            SimulationResult: Результаты симуляции
        """
        logger.info(f"Симуляция отказа компонента: {component} (тяжесть: {severity})")

        start_time = datetime.now()
        warnings = []
        recommendations = []

        # Базовые параметры для симуляции
        simulated_params = self.digital_twin.operational_parameters.copy()

        # Моделирование эффектов в зависимости от компонента
        if component == 'motor':
            simulated_params['motor_temperature'] += 20 * severity
            simulated_params['motor_current'] += 5 * severity
            simulated_params['efficiency'] -= 25 * severity
            warnings.append(f"Симуляция отказа двигателя (тяжесть: {severity})")
            recommendations.append("Немедленно остановить конвейер")
            recommendations.append("Вызвать сервисного инженера")

        elif component == 'bearing':
            simulated_params['vibration_level'] += 3 * severity
            simulated_params['motor_temperature'] += 10 * severity
            simulated_params['efficiency'] -= 15 * severity
            warnings.append(f"Симуляция отказа подшипника (тяжесть: {severity})")
            recommendations.append("Плановое обслуживание в течение 24 часов")

        elif component == 'sensor':
            # Симуляция некорректных показаний датчика
            simulated_params['efficiency'] -= 10 * severity
            warnings.append(f"Симуляция отказа датчика (тяжесть: {severity})")
            recommendations.append("Калибровка системы датчиков")

        elif component == 'controller':
            simulated_params['conveyor_speed'] *= (1 - 0.3 * severity)
            simulated_params['efficiency'] -= 20 * severity
            warnings.append(f"Симуляция отказа контроллера (тяжесть: {severity})")
            recommendations.append("Перезагрузка системы управления")

        # Ограничение значений
        simulated_params['efficiency'] = max(0, simulated_params['efficiency'])
        simulated_params['vibration_level'] = max(0, simulated_params['vibration_level'])

        duration = (datetime.now() - start_time).total_seconds()

        result = SimulationResult(
            scenario_name=f"failure_{component}",
            timestamp=start_time,
            parameters=simulated_params,
            warnings=warnings,
            recommendations=recommendations,
            success=False,  # Отказ всегда считается неуспешным сценарием
            duration_seconds=duration
        )

        self.simulation_history.append(result)
        return result

    def simulate_what_if_scenario(self, scenario_config: Dict[str, Any]) -> SimulationResult:
        """
        Симуляция сценария 'Что если...'

        Args:
            scenario_config: Конфигурация сценария

        Returns:
            SimulationResult: Результаты симуляции
        """
        logger.info(f"Симуляция сценария: {scenario_config.get('name', 'unknown')}")

        start_time = datetime.now()
        warnings = []
        recommendations = []

        # Начальные параметры
        simulated_params = self.digital_twin.operational_parameters.copy()

        # Применение изменений из конфигурации
        changes = scenario_config.get('changes', {})
        for param, value in changes.items():
            if param in simulated_params:
                simulated_params[param] = value

        # Симуляция долгосрочных эффектов
        duration_hours = scenario_config.get('duration_hours', 1)
        long_term_effects = self._simulate_long_term_effects(simulated_params, duration_hours)
        simulated_params.update(long_term_effects)

        # Анализ результатов
        success = self._analyze_scenario_results(simulated_params)

        if not success:
            warnings.append("Сценарий привел к критическим параметрам")

        # Генерация рекомендаций
        recommendations.extend(self._generate_scenario_recommendations(scenario_config, simulated_params))

        duration = (datetime.now() - start_time).total_seconds()

        result = SimulationResult(
            scenario_name=scenario_config.get('name', 'what_if_scenario'),
            timestamp=start_time,
            parameters=simulated_params,
            warnings=warnings,
            recommendations=recommendations,
            success=success,
            duration_seconds=duration
        )

        self.simulation_history.append(result)
        return result

    def simulate_maintenance_impact(self, maintenance_type: str, duration_hours: int = 8) -> SimulationResult:
        """
        Симуляция воздействия технического обслуживания

        Args:
            maintenance_type: Тип обслуживания ('preventive', 'corrective', 'predictive')
            duration_hours: Продолжительность обслуживания

        Returns:
            SimulationResult: Результаты симуляции
        """
        logger.info(f"Симуляция воздействия ТО: {maintenance_type}")

        start_time = datetime.now()
        warnings = []
        recommendations = []

        # Параметры после обслуживания
        improved_params = self.digital_twin.operational_parameters.copy()

        # Улучшения в зависимости от типа обслуживания
        if maintenance_type == 'preventive':
            improved_params['vibration_level'] *= 0.7  # Уменьшение вибрации на 30%
            improved_params['efficiency'] = min(100, improved_params['efficiency'] + 10)
            recommendations.append("Плановое ТО улучшит производительность")

        elif maintenance_type == 'corrective':
            improved_params['vibration_level'] *= 0.5  # Уменьшение вибрации на 50%
            improved_params['motor_temperature'] -= 5
            improved_params['efficiency'] = min(100, improved_params['efficiency'] + 15)
            recommendations.append("Корректирующее ТО устранит текущие проблемы")

        elif maintenance_type == 'predictive':
            improved_params['vibration_level'] *= 0.6
            improved_params['motor_temperature'] -= 3
            improved_params['efficiency'] = min(100, improved_params['efficiency'] + 12)
            recommendations.append("Прогнозное ТО предотвратит будущие отказы")

        # Расчет ROI обслуживания
        roi_analysis = self._calculate_maintenance_roi(maintenance_type, duration_hours, improved_params)
        recommendations.append(f"Прогнозируемый ROI: {roi_analysis['roi_percentage']:.1f}%")

        duration = (datetime.now() - start_time).total_seconds()

        result = SimulationResult(
            scenario_name=f"maintenance_{maintenance_type}",
            timestamp=start_time,
            parameters=improved_params,
            warnings=warnings,
            recommendations=recommendations,
            success=True,
            duration_seconds=duration
        )

        self.simulation_history.append(result)
        return result

    def run_stress_test(self, duration_minutes: int = 30) -> SimulationResult:
        """
        Проведение стресс-теста системы

        Args:
            duration_minutes: Длительность теста

        Returns:
            SimulationResult: Результаты стресс-теста
        """
        logger.info(f"Запуск стресс-теста на {duration_minutes} минут")

        start_time = datetime.now()
        warnings = []
        recommendations = []

        # Постепенное увеличение нагрузки
        stress_results = []
        time_points = np.linspace(0, duration_minutes, 10)

        for time_point in time_points:
            load_factor = min(1.0, time_point / duration_minutes * 1.5)  # До 150% нагрузки
            stress_params = self._simulate_stress_load(load_factor)
            stress_results.append(stress_params)

            # Проверка на критические условия
            if (stress_params['motor_temperature'] > SENSOR_THRESHOLDS['temperature_critical'] or
                    stress_params['vibration_level'] > SENSOR_THRESHOLDS['vibration_critical']):
                warnings.append(f"Критические параметры достигнуты на {time_point:.1f} минуте")
                break

        # Анализ результатов стресс-теста
        max_params = self._find_max_parameters(stress_results)
        success = not warnings  # Успешен, если не было критических предупреждений

        if success:
            recommendations.append(f"Система стабильна при нагрузке до {max_params['load_factor'] * 100:.1f}%")
        else:
            recommendations.append("Рекомендуется снизить максимальную рабочую нагрузку")

        duration = (datetime.now() - start_time).total_seconds()

        result = SimulationResult(
            scenario_name="stress_test",
            timestamp=start_time,
            parameters=max_params,
            warnings=warnings,
            recommendations=recommendations,
            success=success,
            duration_seconds=duration
        )

        self.simulation_history.append(result)
        return result

    def _predict_parameters_for_speed(self, target_speed: float) -> Dict[str, float]:
        """Прогнозирование параметров при заданной скорости"""
        current_speed = self.digital_twin.operational_parameters['current_speed']
        speed_ratio = target_speed / max(current_speed, 0.1)  # Избегаем деления на 0

        return {
            'conveyor_speed': target_speed,
            'motor_temperature': self.digital_twin.operational_parameters['motor_temperature'] * speed_ratio ** 0.8,
            'vibration_level': self.digital_twin.operational_parameters['vibration_level'] * speed_ratio ** 1.2,
            'motor_current': self.digital_twin.operational_parameters['motor_current'] * speed_ratio,
            'efficiency': self.digital_twin.operational_parameters['efficiency']
        }

    def _calculate_efficiency_impact(self, current: Dict, predicted: Dict) -> float:
        """Расчет влияния на эффективность"""
        # Простая модель влияния параметров на эффективность
        temp_impact = max(0, predicted['motor_temperature'] - current['motor_temperature']) * -0.5
        vibration_impact = max(0, predicted['vibration_level'] - current['vibration_level']) * -2.0
        speed_impact = (predicted['conveyor_speed'] - current['conveyor_speed']) * 0.1

        return temp_impact + vibration_impact + speed_impact

    def _simulate_long_term_effects(self, params: Dict, duration_hours: int) -> Dict[str, float]:
        """Симуляция долгосрочных эффектов"""
        # Модель деградации со временем
        degradation_rate = 0.01  # % деградации в час

        return {
            'efficiency': params.get('efficiency', 100) * (1 - degradation_rate * duration_hours),
            'vibration_level': params.get('vibration_level', 0) * (1 + degradation_rate * duration_hours * 0.5),
            'motor_temperature': params.get('motor_temperature', 0) * (1 + degradation_rate * duration_hours * 0.1)
        }

    def _analyze_scenario_results(self, params: Dict) -> bool:
        """Анализ результатов сценария на предмет критических условий"""
        return (params['motor_temperature'] <= SENSOR_THRESHOLDS['temperature_critical'] and
                params['vibration_level'] <= SENSOR_THRESHOLDS['vibration_critical'] and
                params['efficiency'] >= 60)

    def _generate_scenario_recommendations(self, scenario: Dict, params: Dict) -> List[str]:
        """Генерация рекомендаций на основе сценария"""
        recommendations = []

        if params['efficiency'] < 80:
            recommendations.append("Рассмотреть оптимизацию рабочих параметров")

        if params['motor_temperature'] > 80:
            recommendations.append("Увеличить охлаждение двигателя")

        return recommendations

    def _calculate_maintenance_roi(self, maintenance_type: str, duration: int, improved_params: Dict) -> Dict[
        str, float]:
        """Расчет возврата инвестиций в обслуживание"""
        # Упрощенная модель ROI
        cost_factors = {
            'preventive': 1.0,
            'corrective': 1.5,
            'predictive': 1.2
        }

        base_cost = 1000  # Базовая стоимость
        cost = base_cost * cost_factors.get(maintenance_type, 1.0)

        # Расчет выгоды от улучшения эффективности
        efficiency_gain = improved_params['efficiency'] - self.digital_twin.operational_parameters['efficiency']
        benefit = efficiency_gain * 100  # Упрощенная модель

        roi = (benefit - cost) / cost * 100 if cost > 0 else 0

        return {
            'cost': cost,
            'benefit': benefit,
            'roi_percentage': roi,
            'payback_period_days': cost / max(benefit, 1) * 30
        }

    def _simulate_stress_load(self, load_factor: float) -> Dict[str, float]:
        """Симуляция стрессовой нагрузки"""
        base_params = self.digital_twin.operational_parameters.copy()

        return {
            'load_factor': load_factor,
            'conveyor_speed': base_params['conveyor_speed'] * load_factor,
            'motor_temperature': base_params['motor_temperature'] * (1 + 0.5 * load_factor),
            'vibration_level': base_params['vibration_level'] * (1 + 0.8 * load_factor),
            'motor_current': base_params['motor_current'] * load_factor,
            'efficiency': base_params['efficiency'] * (1 - 0.2 * max(0, load_factor - 1))
        }

    def _find_max_parameters(self, results: List[Dict]) -> Dict[str, float]:
        """Нахождение максимальных параметров из списка результатов"""
        if not results:
            return {}

        max_params = results[0].copy()
        for result in results[1:]:
            for key, value in result.items():
                if isinstance(value, (int, float)):
                    if key in ['conveyor_speed', 'motor_temperature', 'vibration_level', 'motor_current',
                               'load_factor']:
                        max_params[key] = max(max_params.get(key, 0), value)
                    elif key == 'efficiency':
                        max_params[key] = min(max_params.get(key, 100), value)

        return max_params

    def get_simulation_history(self, limit: int = 10) -> List[SimulationResult]:
        """Получение истории симуляций"""
        return self.simulation_history[-limit:] if self.simulation_history else []

    def clear_history(self):
        """Очистка истории симуляций"""
        self.simulation_history.clear()


# Утилиты для работы с симуляциями
def create_scenario_template() -> Dict[str, Any]:
    """Создание шаблона для сценария 'Что если'"""
    return {
        "name": "Новый сценарий",
        "description": "",
        "changes": {
            "conveyor_speed": 0,
            "motor_temperature": 0,
            "vibration_level": 0
        },
        "duration_hours": 1,
        "expected_impact": "neutral"
    }


def validate_scenario_config(config: Dict) -> bool:
    """Валидация конфигурации сценария"""
    required_fields = ['name', 'changes']
    return all(field in config for field in required_fields)


# Экспорт основных классов и функций
__all__ = [
    'ConveyorSimulator',
    'SimulationResult',
    'SimulationMode',
    'create_scenario_template',
    'validate_scenario_config'
]