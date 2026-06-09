from sqlalchemy import Column, Integer, Date
from backend.app.database import Base


class Controle(Base):
    __tablename__ = "controle"

    id = Column(Integer, primary_key=True)
    ultima_semana_fechada = Column(Date, nullable=True)