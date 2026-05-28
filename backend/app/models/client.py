from sqlalchemy import Column, Integer, String
from backend.app.database.database import Base

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, nullable=False)
    nome = Column(String, nullable=False)
    frequencia_dias = Column(Integer)