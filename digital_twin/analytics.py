import numpy as np
from datetime import datetime, timedelta


class AnalyticsEngine:
    def __init__(self, digital_twin):
        self.digital_twin = digital_twin
        self.performance_metrics = {}

    def calculate_oee(self):
        """Расчет Overall Equipment Effectiveness"""
        availability = self._calculate_availability()
        performance = self._calculate_performance()
        quality = self._calculate_quality()

        oee = availability * performance * quality
        return {
            'oee': oee * 100,
            'availability': availability * 100,
            'performance': performance * 100,
            'quality': quality * 100
        }

    def _calculate_availability(self):
        """Расчет доступности оборудования"""
        # Упрощенный расчет
        planned_production_time = 24 * 60  # минуты
        downtime = len(self.digital_twin.alerts) * 5  # предполагаем 5 мин на каждый алерт
        return max(0, (planned_production_time - downtime) / planned_production_time)

    def _calculate_performance(self):
        """Расчет производительности"""
        ideal_cycle_time = 1.0  # идеальное время цикла
        actual_cycle_time = max(0.1, 1.0 / self.digital_twin.operational_parameters['current_speed'])
        return ideal_cycle_time / actual_cycle_time

    def _calculate_quality(self):
        """Расчет качества"""
        total_items = self.digital_twin.operational_parameters['items_processed']
        defects = self.digital_twin.operational_parameters['defects_count']

        if total_items == 0:
            return 1.0

        return (total_items - defects) / total_items

    def trend_analysis(self, data_points, window=10):
        """Анализ трендов показателей"""
        if len(data_points) < window:
            return "INSUFFICIENT_DATA"

        recent_data = data_points[-window:]
        x = np.arange(len(recent_data))
        y = np.array(recent_data)

        # Линейная регрессия для определения тренда
        slope = np.polyfit(x, y, 1)[0]

        if slope > 0.1:
            return "INCREASING"
        elif slope < -0.1:
            return "DECREASING"
        else:
            return "STABLE"

    def generate_report(self, period_hours=24):
        """Генерация отчета за период"""
        oee_metrics = self.calculate_oee()

        return {
            'period': f"Последние {period_hours} часов",
            'timestamp': datetime.now().isoformat(),
            'oee_metrics': oee_metrics,
            'operational_parameters': self.digital_twin.operational_parameters,
            'alerts_count': len(self.digital_twin.alerts),
            'maintenance_prediction': self.digital_twin.predict_maintenance(),
            'recommendations': self._generate_recommendations()
        }

    def _generate_recommendations(self):
        """Генерация рекомендаций по оптимизации"""
        recommendations = []
        params = self.digital_twin.operational_parameters

        if params['efficiency'] < 85:
            recommendations.append("Проверить настройки двигателя и балансировку")

        if params['motor_temperature'] > 80:
            recommendations.append("Обеспечить лучшее охлаждение двигателя")

        if len(self.digital_twin.alerts) > 5:
            recommendations.append("Требуется диагностика системы")

        return recommendations