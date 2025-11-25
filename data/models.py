from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()


class SensorData(Base):
    __tablename__ = 'sensor_data'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now)
    conveyor_speed = Column(Float)
    motor_temperature = Column(Float)
    vibration_level = Column(Float)
    motor_current = Column(Float)
    efficiency = Column(Float)

    def __repr__(self):
        return f"<SensorData(speed={self.conveyor_speed}, temp={self.motor_temperature})>"


class Alert(Base):
    __tablename__ = 'alerts'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now)
    alert_type = Column(String(50))
    severity = Column(String(20))  # LOW, MEDIUM, HIGH, CRITICAL
    message = Column(String(500))
    resolved = Column(Boolean, default=False)

    def __repr__(self):
        return f"<Alert({self.alert_type}, {self.severity})>"


class MaintenanceLog(Base):
    __tablename__ = 'maintenance_log'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now)
    maintenance_type = Column(String(100))
    description = Column(String(500))
    technician = Column(String(100))
    duration_minutes = Column(Integer)

    def __repr__(self):
        return f"<Maintenance({self.maintenance_type}, {self.timestamp})>"