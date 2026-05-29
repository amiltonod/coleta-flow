from sqlalchemy import Column, Integer, String, Date

from backend.database.database import Base


class Client(Base):

    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)

    codigo = Column(String)

    nome = Column(String)

    cidade = Column(String)

    unidade = Column(String)

    observacao = Column(String)

    frequencia_dias = Column(Integer)

    penultima_coleta = Column(Date)

    ultima_coleta = Column(Date)

    proxima_coleta = Column(Date)

    dia_preferencial = Column(String)