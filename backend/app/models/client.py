from sqlalchemy import Column, Integer, String

from backend.app.database.database import Base


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)

    codigo = Column(String, nullable=False)
    nome = Column(String, nullable=False)

    cidade = Column(String)
    unidade = Column(String)

    frequencia_dias = Column(Integer)

    observacao = Column(String)

    dia_preferencial = Column(String)