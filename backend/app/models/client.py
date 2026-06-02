from sqlalchemy import Column, Integer, String, Date, Boolean
from backend.app.database import Base


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, nullable=False)
    nome = Column(String, nullable=False)
    cidade = Column(String, nullable=True)
    unidade = Column(String, nullable=True)
    observacao = Column(String, nullable=True)
    frequencia_dias = Column(Integer, nullable=True)
    ultima_coleta = Column(Date, nullable=True)
    proxima_coleta = Column(Date, nullable=True)
    fixo = Column(Boolean, default=False)
    dia_fixo = Column(String, nullable=True)