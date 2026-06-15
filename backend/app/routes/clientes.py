"""
ROTAS REFATORADAS — Sprint 1

Este arquivo mostra TODAS as mudanças nas rotas para usar Pydantic + padronizar erros.

IMPORTANTE: Substitua seu backend/app/routes/clientes.py com este arquivo,
ou aplique as mudanças manualmente seguindo o padrão.

Mudanças principales:
1. Importar schemas (ClienteCreate, ClienteUpdate, ConfirmarColeta)
2. Mudar `dados: dict` para `dados: ClienteCreate` (validação automática)
3. Mudar `return {"erro": ...}` para `raise HTTPException(...)`
4. Adicionar imports necessários
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request, Query
from pydantic import BaseModel, Field 
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import date, timedelta
import os
import io
import pandas as pd
import logging

logger = logging.getLogger("coleta_flow")

# ✅ NOVO: Importar schemas
from backend.app.schemas import (
    ClienteCreate,
    ClienteUpdate, 
    ConfirmarColeta,
    ClienteResponse,
    BuscaResponse,
    MensagemResponse
)
from backend.app.database import get_db
from backend.app.models.client import Client
from backend.app.models.schedule import Schedule
from backend.app.models.controle import Controle
from backend.app.services.generate_schedule import (
    gerar_programacao as gerar_prog_service,
    ja_agendado_na_data
)
from backend.app.services.fechar_semana import fechar_semana
from backend.app.services.import_service import importar_clientes

# Configuração
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

router = APIRouter()

DIAS_SEMANA = {
    0: "Segunda", 1: "Terça", 2: "Quarta", 
    3: "Quinta", 4: "Sexta", 5: "Sábado", 6: "Domingo"
}

# ═══════════════════════════════════════════════════════════════════════════════
# PÁGINA INICIAL
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    """
    Página inicial do sistema.
    
    Executa fechamento automático em segundo plano (silenciosamente).
    """
    # Processa fechamento automático (silencioso)
    fechar_semana(db)
    
    clientes = db.query(Client).all()
    schedules = db.query(Schedule).all()
    fixos = db.query(Client).filter(Client.fixo == True).all()
    
    return templates.TemplateResponse(
        name="index.html",
        request=request,
        context={"clientes": clientes, "schedules": schedules, "fixos": fixos}
    )

# ═══════════════════════════════════════════════════════════════════════════════
# CLIENTES - LISTAR
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/clientes")
async def listar_clientes(db: Session = Depends(get_db)):
    """Retorna todos os clientes cadastrados"""
    clientes = db.query(Client).all()
    return {"clientes": clientes}

# ═══════════════════════════════════════════════════════════════════════════════
# CLIENTES - BUSCAR
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/clientes/buscar")
async def buscar_clientes(q: str, db: Session = Depends(get_db)):
    """
    Busca clientes por nome, código ou cidade.
    
    Parâmetro:
        q: String de busca (mínimo 2 caracteres)
    """
    if len(q) < 2:
        raise HTTPException(
            status_code=400,
            detail="Busca deve ter pelo menos 2 caracteres"
        )
    
    termo = f"%{q}%"
    clientes = db.query(Client).filter(
        or_(
            Client.codigo.ilike(termo),
            Client.nome.ilike(termo),
            Client.cidade.ilike(termo)
        )
    ).all()
    
    return {"resultados": [
        {
            "id": c.id,
            "codigo": c.codigo,
            "nome": c.nome,
            "cidade": c.cidade,
            "unidade": c.unidade
        }
        for c in clientes
    ]}

# ═══════════════════════════════════════════════════════════════════════════════
# CLIENTES - LISTAR FIXOS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/clientes/fixos")
async def listar_fixos(db: Session = Depends(get_db)):
    """Retorna apenas clientes com coletas fixas"""
    fixos = db.query(Client).filter(Client.fixo == True).all()
    return {"fixos": fixos}


# ═══════════════════════════════════════════════════════════════════════════════
# CLIENTES — ADICIONAR
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/clientes/adicionar", status_code=201)
async def adicionar_cliente(
    dados: ClienteCreate,
    db: Session = Depends(get_db)
):
    logger.info(f"Adicionando novo cliente: codigo={dados.codigo}, nome={dados.nome}")
    
    existe = db.query(Client).filter_by(codigo=dados.codigo).first()
    if existe:
        logger.warning(f"Tentativa de adicionar cliente duplicado: codigo={dados.codigo}")
        raise HTTPException(
            status_code=400,
            detail=f"Cliente com código {dados.codigo} já existe"
        )
    
    try:
        logger.debug(f"Criando objeto Client: nome={dados.nome}, cidade={dados.cidade}")
        
        novo_cliente = Client(
            codigo=dados.codigo,
            nome=dados.nome,
            cidade=dados.cidade,
            unidade=dados.unidade,
            observacao=dados.observacao,
            frequencia_dias=dados.frequencia_dias,
            fixo=dados.fixo,
            dia_fixo=dados.dia_fixo
        )
        
        db.add(novo_cliente)
        db.commit()
        db.refresh(novo_cliente)
        
        logger.info(f"Cliente criado com sucesso: id={novo_cliente.id}, codigo={novo_cliente.codigo}")
        
        return {
            "mensagem": "Cliente adicionado com sucesso",
            "cliente_id": novo_cliente.id,
            "codigo": novo_cliente.codigo
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao adicionar cliente {dados.codigo}: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="Erro ao adicionar cliente")

# ═══════════════════════════════════════════════════════════════════════════════
# PROGRAMAÇÃO — ADICIONAR CLIENTE
# ═══════════════════════════════════════════════════════════════════════════════

class AdicionarColetaSchema(BaseModel):
    """Schema para adicionar coleta manualmente"""
    codigo_cliente: str = Field(..., min_length=1, max_length=20)
    data_coleta: date = Field(..., description="Data em formato YYYY-MM-DD")


@router.post("/programacao/adicionar", status_code=201)
async def adicionar_coleta_manual(
    dados: AdicionarColetaSchema,  # ✅ Recebe JSON (POST data)
    db: Session = Depends(get_db)
):
    """
    Adiciona coleta manualmente para um cliente.
    """
    logger.info(f"Adicionando coleta manual: codigo={dados.codigo_cliente}, data={dados.data_coleta}")
    
    try:
        # Verificar se cliente existe
        cliente = db.query(Client).filter(Client.codigo == dados.codigo_cliente).first()
        if not cliente:
            logger.warning(f"Cliente não encontrado: {dados.codigo_cliente}")
            raise HTTPException(
                status_code=404,
                detail=f"Cliente {dados.codigo_cliente} não encontrado"
            )
        
        # Verificar se já não existe agendamento na data
        ja_existe = db.query(Schedule).filter(
            Schedule.codigo_cliente == dados.codigo_cliente,
            Schedule.data_coleta == dados.data_coleta
        ).first()
        
        if ja_existe:
            logger.warning(f"Coleta já existe: {dados.codigo_cliente} em {dados.data_coleta}")
            raise HTTPException(
                status_code=400,
                detail=f"Já existe coleta agendada para {dados.codigo_cliente} em {dados.data_coleta}"
            )
        
        logger.debug(f"Criando schedule para {cliente.nome}")
        
        # Criar novo agendamento
        novo_schedule = Schedule(
            codigo_cliente=cliente.codigo,
            cliente=cliente.nome,
            unidade=cliente.unidade,
            data_coleta=dados.data_coleta,
            dia_semana=DIAS_SEMANA.get(dados.data_coleta.weekday(), "Desconhecido"),
            status="Programado",
            fixo=False
        )
        
        db.add(novo_schedule)
        db.commit()
        db.refresh(novo_schedule)
        
        logger.info(f"Coleta adicionada com sucesso: id={novo_schedule.id}, cliente={cliente.nome}, data={dados.data_coleta}")
        
        return {
            "mensagem": "Coleta adicionada com sucesso",
            "schedule_id": novo_schedule.id,
            "codigo_cliente": novo_schedule.codigo_cliente,
            "cliente": novo_schedule.cliente,
            "data_coleta": novo_schedule.data_coleta.isoformat(),
            "status": novo_schedule.status
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao adicionar coleta manual: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="Erro ao adicionar coleta")

# ═══════════════════════════════════════════════════════════════════════════════
# CLIENTES - ATUALIZAR
# ═══════════════════════════════════════════════════════════════════════════════

# ❌ ANTES (INCONSISTENTE):
# @router.put("/clientes/{cliente_id}")
# async def atualizar_cliente(cliente_id: int, dados: dict, db: Session = Depends(get_db)):
#     cliente = db.query(Client).filter(Client.id == cliente_id).first()
#     if not cliente:
#         return {"erro": "Cliente não encontrado"}  # ← Status 200 errado!

# ✅ DEPOIS (CONSISTENTE):
@router.put("/clientes/{cliente_id}")
async def atualizar_cliente(
    cliente_id: int,
    dados: ClienteUpdate,  # ← Validado automaticamente
    db: Session = Depends(get_db)
):
    """
    Atualiza cliente existente.
    
    Apenas campos fornecidos serão atualizados (PUT parcial).
    """
    cliente = db.query(Client).filter(Client.id == cliente_id).first()
    if not cliente:
        raise HTTPException(
            status_code=404,
            detail=f"Cliente {cliente_id} não encontrado"
        )
    
    # Atualizar apenas campos fornecidos
    dados_dict = dados.model_dump(exclude_unset=True)
    for campo, valor in dados_dict.items():
        setattr(cliente, campo, valor)
    
    db.commit()
    db.refresh(cliente)
    
    return {
        "mensagem": "Cliente atualizado com sucesso",
        "cliente_id": cliente.id
    }

# ═══════════════════════════════════════════════════════════════════════════════
# CLIENTES - DELETAR
# ═══════════════════════════════════════════════════════════════════════════════

@router.delete("/clientes/{cliente_id}")
async def deletar_cliente(cliente_id: int, db: Session = Depends(get_db)):
    """
    Deleta cliente e seus agendamentos associados.
    """
    cliente = db.query(Client).filter(Client.id == cliente_id).first()
    if not cliente:
        raise HTTPException(
            status_code=404,
            detail=f"Cliente {cliente_id} não encontrado"
        )
    
    # Contar e deletar agendamentos associados
    agendamentos = db.query(Schedule).filter(
        Schedule.codigo_cliente == cliente.codigo
    ).all()
    agendamentos_removidos = len(agendamentos)
    
    for ag in agendamentos:
        db.delete(ag)
    
    db.delete(cliente)
    db.commit()
    
    return {
        "mensagem": "Cliente deletado com sucesso",
        "agendamentos_removidos": agendamentos_removidos
    }

# ═══════════════════════════════════════════════════════════════════════════════
# PROGRAMAÇÃO - SEMANA
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/programacao-semana")
async def programacao_semana(offset: int = 0, db: Session = Depends(get_db)):
    """
    Retorna programação de coletas da semana.
    
    ✅ OTIMIZADO: Filtra no banco SQL, não em Python
    
    Parâmetros:
        offset: 0=próxima semana, -1=semana atual, -2=semana anterior
    """
    
    # Calcular datas da semana
    hoje = date.today()
    dias_ate_segunda = (7 - hoje.weekday()) % 7 or 7
    segunda_base = hoje + timedelta(days=dias_ate_segunda)
    segunda = segunda_base + timedelta(weeks=offset)
    
    # Gerar lista de 5 dias (segunda a sexta)
    dias_semana = [segunda + timedelta(days=i) for i in range(5)]
    
    # Inicializar resultado
    resultado = {}
    for dia in dias_semana:
        resultado[dia.isoformat()] = []
    
    # ✅ OTIMIZADO: Filtrar NO BANCO (não em Python)
    schedules = db.query(Schedule).filter(
        Schedule.data_coleta.in_(dias_semana)  # ← SQL WHERE IN (...)
    ).all()
    
    # Preencher resultado
    for s in schedules:
        resultado[s.data_coleta.isoformat()].append({
            "id": s.id,
            "codigo": s.codigo_cliente,
            "cliente": s.cliente,
            "unidade": s.unidade or "",
            "status": s.status,
            "fixo": s.fixo or False,
        })
    
    # Ordenar por fixo (fixos primeiro) depois por cliente
    for dia in resultado:
        resultado[dia].sort(key=lambda x: (not x["fixo"], x["cliente"]))
    
    return {
        "dias": [d.isoformat() for d in dias_semana],
        "programacao": resultado,
        "offset": offset,
        "semana_atual": offset == -1,
    }

@router.post("/fechar-semana")
async def fechar_semana_endpoint(db: Session = Depends(get_db)):
    """Endpoint para fechar semana manualmente"""
    resultado = fechar_semana(db)
    return {
        "mensagem": "Semana fechada com sucesso",
        "resultado": resultado
    }

# ═══════════════════════════════════════════════════════════════════════════════
# PROGRAMAÇÃO - GERAR
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/gerar-programacao")
async def processar_geracao_automatica(db: Session = Depends(get_db)):
    """
    Gera automaticamente a programação da semana.
    
    Considera:
    - Clientes fixos (Segunda, Quinta, etc)
    - Clientes por frequência (a cada 7 dias, 3 dias, etc)
    - Validação anti-duplicidade
    """
    resultado = gerar_prog_service(db)
    
    return {
        "mensagem": "Programação gerada com sucesso",
        "gerados": resultado.get("gerados", 0),
        "ignorados": resultado.get("ignorados", 0),
        "duplicados": resultado.get("duplicados", 0),
        "por_solicitacao": resultado.get("por_solicitacao", 0)
    }

# ═══════════════════════════════════════════════════════════════════════════════
# PROGRAMAÇÃO - CONFIRMAR COLETA
# ═══════════════════════════════════════════════════════════════════════════════

# ❌ ANTES:
# @router.post("/confirmar-coleta/{schedule_id}")
# async def confirmar_coleta(schedule_id: int, dados: dict, db: Session = Depends(get_db)):
#     schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
#     if not schedule:
#         return {"erro": "Agendamento não encontrado"}  # ← Status 200 errado!

# ✅ DEPOIS:
@router.post("/confirmar-coleta/{schedule_id}")
async def confirmar_coleta(
    schedule_id: int,
    dados: ConfirmarColeta,  # ← Validado e com data segura
    db: Session = Depends(get_db)
):
    """
    Marca coleta como realizada.
    
    Atualiza:
    - Schedule.status = "Concluído"
    - Client.ultima_coleta = data_realizada
    - Client.proxima_coleta = calculada automaticamente
    """
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(
            status_code=404,
            detail=f"Agendamento {schedule_id} não encontrado"
        )
    
    # Atualizar schedule
    schedule.status = "Concluído"
    schedule.data_coleta = dados.data_realizada
    
    # Atualizar cliente
    cliente = db.query(Client).filter(
        Client.codigo == schedule.codigo_cliente
    ).first()
    
    if cliente:
        cliente.ultima_coleta = dados.data_realizada
        
        # Calcular próxima coleta
        if cliente.frequencia_dias:
            proxima = dados.data_realizada + timedelta(days=cliente.frequencia_dias)
            cliente.proxima_coleta = proxima
    
    db.commit()
    
    return {
    "mensagem": "Coleta confirmada com sucesso",
    "schedule_id": schedule_id,
    "status": schedule.status,
    "proxima_coleta_calculada": cliente.proxima_coleta.isoformat() if (cliente and cliente.proxima_coleta) else None
}

# ═══════════════════════════════════════════════════════════════════════════════
# PROGRAMAÇÃO - DELETAR
# ═══════════════════════════════════════════════════════════════════════════════

@router.delete("/programacao/{schedule_id}")
async def deletar_agendamento(schedule_id: int, db: Session = Depends(get_db)):
    """Deleta um agendamento específico"""
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(
            status_code=404,
            detail=f"Agendamento {schedule_id} não encontrado"
        )
    
    db.delete(schedule)
    db.commit()
    
    return {
        "mensagem": "Agendamento removido com sucesso",
        "schedule_id": schedule_id
    }


# ═══════════════════════════════════════════════════════════════════════════════
# PROGRAMAÇÃO - ATUALIZAR (DRAG & DROP)
# ═══════════════════════════════════════════════════════════════════════════════

@router.put("/programacao/{schedule_id}")
async def atualizar_agendamento(
    schedule_id: int,
    dados: dict,
    db: Session = Depends(get_db)
):
    """
    Atualiza um agendamento (ex: mover para outro dia via drag & drop).
    
    Aceita:
        data_coleta: Nova data (formato YYYY-MM-DD)
        status: Novo status (opcional)
    """
    logger.info(f"Atualizando agendamento: id={schedule_id}")
    
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        logger.warning(f"Agendamento não encontrado: id={schedule_id}")
        raise HTTPException(
            status_code=404,
            detail=f"Agendamento {schedule_id} não encontrado"
        )
    
    try:
        # Atualizar data se fornecida
        if "data_coleta" in dados:
            nova_data = dados["data_coleta"]
            if isinstance(nova_data, str):
                from datetime import datetime
                nova_data = datetime.strptime(nova_data, "%Y-%m-%d").date()
            
            logger.debug(f"Mudando data: {schedule.data_coleta} → {nova_data}")
            
            # Verificar duplicação
            ja_existe = db.query(Schedule).filter(
                Schedule.codigo_cliente == schedule.codigo_cliente,
                Schedule.data_coleta == nova_data,
                Schedule.id != schedule_id
            ).first()
            
            if ja_existe:
                logger.warning(f"Conflito: cliente {schedule.codigo_cliente} já tem coleta em {nova_data}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Já existe coleta agendada para este cliente em {nova_data}"
                )
            
            schedule.data_coleta = nova_data
            schedule.dia_semana = DIAS_SEMANA.get(nova_data.weekday(), "Desconhecido")
        
        # Atualizar status se fornecido
        if "status" in dados:
            schedule.status = dados["status"]
        
        db.commit()
        db.refresh(schedule)
        
        logger.info(f"Agendamento atualizado: id={schedule_id}, nova_data={schedule.data_coleta}")
        
        return {
            "mensagem": "Agendamento atualizado com sucesso",
            "schedule_id": schedule.id,
            "cliente": schedule.cliente,
            "data_coleta": schedule.data_coleta.isoformat(),
            "status": schedule.status
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar agendamento {schedule_id}: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="Erro ao atualizar agendamento")


# ═══════════════════════════════════════════════════════════════════════════════
# UPLOAD - IMPORTAR EXCEL
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/upload")
async def upload_arquivo(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Importa clientes de arquivo Excel.
    
    Formato esperado:
    - Coluna A: Código
    - Coluna B: Nome
    - Coluna C: Cidade
    - Coluna D: Observação
    """
    if not file:
        raise HTTPException(
            status_code=400,
            detail="Nenhum arquivo enviado"
        )
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400,
            detail="Arquivo deve ser Excel (.xlsx ou .xls)"
        )
    
    try:
        conteudo = await file.read()
        arquivo_io = io.BytesIO(conteudo)
        
        # Salvar temporariamente
        caminho_temp = os.path.join(BASE_DIR, "uploads", file.filename)
        os.makedirs(os.path.dirname(caminho_temp), exist_ok=True)
        
        with open(caminho_temp, "wb") as f:
            f.write(conteudo)
        
        # Importar
        resultado = importar_clientes(caminho_temp, db)
        
        # Cleanup
        if os.path.exists(caminho_temp):
            os.remove(caminho_temp)
        
        return {
            "mensagem": "Importação concluída",
            "importados": resultado.get("importados", 0),
            "atualizados": resultado.get("atualizados", 0),
            "erros": resultado.get("erros", []),
            "total_linhas": resultado.get("total_linhas", 0)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar arquivo: {str(e)}"
        )

# ═══════════════════════════════════════════════════════════════════════════════
# ℹ️ RESUMO DAS MUDANÇAS
# ═══════════════════════════════════════════════════════════════════════════════
"""
✅ MUDANÇAS IMPLEMENTADAS:

1. IMPORTES NOVOS
   - from backend.app.schemas import (ClienteCreate, ClienteUpdate, ConfirmarColeta)
   
2. ENDPOINTS COM VALIDAÇÃO PYDANTIC
   - POST /clientes/adicionar: Usa ClienteCreate
   - PUT /clientes/{id}: Usa ClienteUpdate
   - POST /confirmar-coleta/{id}: Usa ConfirmarColeta
   
3. PADRONIZAÇÃO DE ERROS
   - Antes: return {"erro": "..."}  # Status 200
   - Depois: raise HTTPException(status_code=404, detail="...")
   
4. VALIDAÇÕES AUTOMÁTICAS
   - Tipo de dado (str, int, date)
   - Tamanho (min/max)
   - Valores obrigatórios
   
5. REMOVIDO CÓDIGO DUPLICADO DE FECHAMENTO
   - Antes: realizar_fechamento_automatico() [função duplicada]
   - Depois: processar_fechamento(db) [de services]
   
6. OTIMIZAÇÃO DE QUERY
   - Antes: db.query(Schedule).all() [carrega tudo]
   - Depois: db.query(Schedule).filter(Schedule.data_coleta.in_(...)) [filtra no banco]
"""

from fastapi import Response

@router.get("/favicon.ico")
async def favicon():
    """Ignora requisição de favicon"""
    return Response(status_code=204)