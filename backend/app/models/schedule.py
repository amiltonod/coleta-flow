from sqlalchemy import Column, Integer, String, Date

from backend.app.database.database import Base


class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)

    cliente = Column(String, nullable=False)

    codigo_cliente = Column(String)

    data_coleta = Column(Date)

    dia_semana = Column(String)

    status = Column(String, default="Programado")