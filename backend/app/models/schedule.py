from sqlalchemy import Column, Integer, String, Date
from backend.app.database import Base


class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    cliente = Column(String, nullable=False)
    codigo_cliente = Column(String, nullable=True)
    unidade = Column(String, nullable=True)
    data_coleta = Column(Date, nullable=True)
    dia_semana = Column(String, nullable=True)
    status = Column(String, default="Programado")