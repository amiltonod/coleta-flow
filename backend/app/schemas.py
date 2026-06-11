"""
Schemas Pydantic para validação de entrada nos endpoints.

Cada schema valida:
- Tipo de dado (str, int, date)
- Tamanho (min/max)
- Valores obrigatórios vs opcionais
- Formato (datas, etc)
"""

from pydantic import BaseModel, Field, validator
from datetime import date
from typing import Optional


class ClienteCreate(BaseModel):
    """Schema para criar novo cliente via POST"""
    
    codigo: str = Field(
        ..., 
        min_length=1, 
        max_length=20,
        description="Código único do cliente (ex: L001, 15, ABC)"
    )
    nome: str = Field(
        ..., 
        min_length=1, 
        max_length=200,
        description="Nome do cliente"
    )
    cidade: Optional[str] = Field(
        None, 
        max_length=100,
        description="Cidade"
    )
    unidade: Optional[str] = Field(
        None, 
        max_length=100,
        description="Unidade/Filial"
    )
    observacao: Optional[str] = Field(
        None, 
        max_length=500,
        description="Observações (ex: 'Por solicitação', 'Segunda,Quinta')"
    )
    frequencia_dias: Optional[int] = Field(
        None, 
        ge=1, 
        le=365,
        description="Dias entre coletas (1-365)"
    )
    fixo: Optional[bool] = Field(
        False,
        description="Se coleta em dias fixos"
    )
    dia_fixo: Optional[str] = Field(
        None,
        max_length=100,
        description="Dias da semana (Segunda,Quinta)"
    )
    
    @validator("codigo")
    def codigo_nao_vazio(cls, v):
        """Valida que código não é só espaços"""
        if not v.strip():
            raise ValueError("Código não pode ser vazio ou só espaços")
        return v.strip()
    
    @validator("nome")
    def nome_nao_vazio(cls, v):
        """Valida que nome não é só espaços"""
        if not v.strip():
            raise ValueError("Nome não pode ser vazio ou só espaços")
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "codigo": "L001",
                "nome": "Supermercado ABC",
                "cidade": "Araquari",
                "unidade": "Matriz",
                "frequencia_dias": 3,
                "fixo": False
            }
        }


class ClienteUpdate(BaseModel):
    """Schema para atualizar cliente via PUT"""
    
    nome: Optional[str] = Field(
        None, 
        min_length=1,
        max_length=200
    )
    cidade: Optional[str] = Field(
        None, 
        max_length=100
    )
    unidade: Optional[str] = Field(
        None, 
        max_length=100
    )
    observacao: Optional[str] = Field(
        None, 
        max_length=500
    )
    frequencia_dias: Optional[int] = Field(
        None, 
        ge=1, 
        le=365
    )
    ultima_coleta: Optional[date] = Field(
        None,
        description="Última data de coleta realizada"
    )
    proxima_coleta: Optional[date] = Field(
        None,
        description="Próxima data de coleta calculada"
    )
    fixo: Optional[bool] = None
    dia_fixo: Optional[str] = Field(
        None,
        max_length=100
    )
    
    @validator("nome")
    def nome_nao_vazio(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Nome não pode ser só espaços")
        return v.strip() if v else None
    
    class Config:
        json_schema_extra = {
            "example": {
                "frequencia_dias": 5,
                "observacao": "Aumentou frequência"
            }
        }


class ConfirmarColeta(BaseModel):
    """Schema para confirmar coleta realizada via POST"""
    
    data_realizada: date = Field(
        ...,
        description="Data em que a coleta foi realizada (YYYY-MM-DD)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "data_realizada": "2026-06-15"
            }
        }


class ClienteResponse(BaseModel):
    """Schema de resposta ao retornar cliente"""
    
    id: int
    codigo: str
    nome: str
    cidade: Optional[str] = None
    unidade: Optional[str] = None
    observacao: Optional[str] = None
    frequencia_dias: Optional[int] = None
    ultima_coleta: Optional[date] = None
    proxima_coleta: Optional[date] = None
    fixo: bool
    dia_fixo: Optional[str] = None
    
    class Config:
        from_attributes = True  # SQLAlchemy compatibility


class BuscaResponse(BaseModel):
    """Schema para resposta de busca"""
    
    id: int
    codigo: str
    nome: str
    cidade: Optional[str] = None
    unidade: Optional[str] = None


class MensagemResponse(BaseModel):
    """Schema genérico para respostas de sucesso"""
    
    mensagem: str


class ErroResponse(BaseModel):
    """Schema genérico para respostas de erro"""
    
    erro: str
    status_code: int


class ProgramacaoResponse(BaseModel):
    """Schema para resposta de programação semanal"""
    
    dias: list
    programacao: dict
    offset: int
    semana_atual: bool