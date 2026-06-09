import os
import shutil
from datetime import date, timedelta
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, File, UploadFile, Request, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.app.database import get_db
from backend.app.models.client import Client
from backend.app.models.schedule import Schedule
from backend.app.services.import_service import importar_clientes
from backend.app.services.generate_schedule import gerar_programacao

from backend.app.services.fechar_semana import fechar_semana as processar_fechamento
from backend.app.models.controle import Controle

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

router = APIRouter()
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

DIAS_SEMANA = {
    0: "Segunda", 1: "Terça", 2: "Quarta", 
    3: "Quinta", 4: "Sexta", 5: "Sábado", 6: "Domingo"
}

# ── SCHEMAS DE VALIDAÇÃO (PYDANTIC) ──────────────────
class ClienteCreate(BaseModel):
    codigo: str
    nome: str
    cidade: Optional[str] = None
    frequencia_dias: Optional[int] = None

class ClienteFixar(BaseModel):
    fixo: bool
    dia_fixo: Optional[str] = None

class ScheduleAdd(BaseModel):
    codigo_cliente: str
    data_coleta: str

class ScheduleUpdate(BaseModel):
    data_coleta: str


# ── FUNÇÃO DE FECHAMENTO AUTOMÁTICO ──────────────────
def realizar_fechamento_automatico(db: Session):
    """
    Verifica se há coletas das semanas anteriores que ainda estão como 'Programado'.
    Se houver, atualiza a ultima_coleta do cliente, recalcula a próxima e muda o status.
    """
    hoje = date.today()
    # Descobre o dia da segunda-feira desta semana
    dias_para_segunda = hoje.weekday()
    segunda_atual = hoje - timedelta(days=dias_para_segunda)
    
    # Pega tudo que ficou para trás (antes desta segunda) e que ainda não foi fechado
    coletas_pendentes = db.query(Schedule).filter(
        Schedule.data_coleta < segunda_atual,
        Schedule.status == "Programado"
    ).all()

    if not coletas_pendentes:
        return # Se não tem nada atrasado, encerra a função rapidamente
        
    clientes_atualizados = {}
    
    for coleta in coletas_pendentes:
        codigo = coleta.codigo_cliente
        # Muda o status para não processar novamente numa próxima abertura
        coleta.status = "Realizado" 
        
        # Guarda a maior data de coleta daquele cliente no passado
        if codigo not in clientes_atualizados or coleta.data_coleta > clientes_atualizados[codigo]:
            clientes_atualizados[codigo] = coleta.data_coleta
            
    # Atualiza os clientes
    for codigo, ultima_data in clientes_atualizados.items():
        cliente = db.query(Client).filter(Client.codigo == codigo).first()
        if cliente:
            cliente.ultima_coleta = ultima_data
            if cliente.frequencia_dias:
                cliente.proxima_coleta = ultima_data + timedelta(days=cliente.frequencia_dias)
                
    db.commit()


# ── ROTAS DE PÁGINA E UPLOAD ─────────────────────────
@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    # Executa a rotina de fechamento automático silenciosamente
    realizar_fechamento_automatico(db)
    
    clientes = db.query(Client).all()
    schedules = db.query(Schedule).all()
    fixos = db.query(Client).filter(Client.fixo == True).all()
    return templates.TemplateResponse(
        name="index.html",
        request=request,
        context={"clientes": clientes, "schedules": schedules, "fixos": fixos}
    )

@router.post("/upload")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    importar_clientes(file_path, db)
    return {"status": "sucesso"}


# ── ROTAS DOS CLIENTES (CRUD & BUSCA COLETAS) ────────
@router.get("/programacao-semana")
async def obter_programacao_semana(db: Session = Depends(get_db)):
    hoje = date.today()
    dias_para_segunda = (0 - hoje.weekday() + 7) % 7
    if dias_para_segunda == 0:
        dias_para_segunda = 7
    segunda = hoje + timedelta(days=dias_para_segunda)
    dias_semana = [segunda + timedelta(days=i) for i in range(5)]
    
    dias_iso = [d.isoformat() for d in dias_semana]
    resultado_programacao = {d: [] for d in dias_iso}
    
    schedules = db.query(Schedule).filter(Schedule.data_coleta.in_(dias_semana)).all()
    for s in schedules:
        cod_s = str(s.codigo_cliente).strip()
        
        # BLINDAGEM: Garante correspondência mesmo se houver variação de string/int ou zeros à esquerda
        condicoes = [Client.codigo == cod_s]
        if cod_s.isdigit():
            condicoes.append(Client.codigo == str(int(cod_s)))
            condicoes.append(Client.codigo == int(cod_s))
            
        cliente = db.query(Client).filter(or_(*condicoes)).first()
        if cliente:
            resultado_programacao[s.data_coleta.isoformat()].append({
                "id": s.id,
                "codigo": cliente.codigo,  # Retorna sempre o código oficial e higienizado do cadastro
                "cliente": cliente.nome,
                "fixo": cliente.fixo
            })
            
    return {"dias": dias_iso, "programacao": resultado_programacao}

@router.get("/clientes/buscar")
async def buscar_clientes(q: str, db: Session = Depends(get_db)):
    clientes = db.query(Client).filter(
        or_(Client.nome.ilike(f"%{q}%"), Client.codigo.ilike(f"%{q}%"))
    ).limit(10).all()
    return [{"codigo": c.codigo, "nome": c.nome} for c in clientes]

@router.post("/clientes/adicionar")
async def adicionar_cliente(cliente_in: ClienteCreate, db: Session = Depends(get_db)):
    codigo_limpo = cliente_in.codigo.strip()
    
    if codigo_limpo.isdigit():
        codigo_busca = str(int(codigo_limpo))
    else:
        codigo_busca = codigo_limpo

    cliente_existe = db.query(Client).filter(
        (Client.codigo == str(codigo_busca)) | (Client.codigo == codigo_busca)
    ).first()
    
    if cliente_existe:
        raise HTTPException(
            status_code=400, 
            detail=f"O código '{codigo_busca}' já está em uso pelo cliente: {cliente_existe.nome}."
        )
    
    novo_cliente = Client(
        codigo=str(codigo_busca),
        nome=cliente_in.nome.strip(),
        cidade=cliente_in.cidade.strip() if cliente_in.cidade else None,
        frequencia_dias=cliente_in.frequencia_dias,
        fixo=False
    )
    
    try:
        db.add(novo_cliente)
        db.commit()
        db.refresh(novo_cliente)
        return {"status": "sucesso", "id": novo_cliente.id}
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Erro de integridade. Código duplicado no banco.")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.put("/clientes/{cliente_id}")
async def atualizar_cliente(
    cliente_id: int,
    dados: dict,
    db: Session = Depends(get_db)
):
    cliente = db.query(Client).filter(Client.id == cliente_id).first()
    if not cliente:
        return {"erro": "Cliente não encontrado"}

    if "nome" in dados:
        cliente.nome = dados["nome"]
    if "cidade" in dados:
        cliente.cidade = dados["cidade"]
    if "unidade" in dados:
        cliente.unidade = dados["unidade"]
    if "observacao" in dados:
        cliente.observacao = dados["observacao"]

    if "frequencia_dias" in dados:
        valor = dados["frequencia_dias"]
        cliente.frequencia_dias = int(valor) if valor else None

    if "ultima_coleta" in dados:
        if dados["ultima_coleta"]:
            cliente.ultima_coleta = date.fromisoformat(dados["ultima_coleta"])
        else:
            cliente.ultima_coleta = None

    # Recalcula próxima coleta sempre que ultima_coleta ou frequencia mudar
    if cliente.ultima_coleta and cliente.frequencia_dias:
        cliente.proxima_coleta = cliente.ultima_coleta + timedelta(
            days=cliente.frequencia_dias
        )
    else:
        cliente.proxima_coleta = None

    db.commit()
    return {
        "mensagem": "Cliente atualizado com sucesso",
        "proxima_coleta": cliente.proxima_coleta.isoformat() if cliente.proxima_coleta else None
    }

@router.put("/clientes/{id}/fixar")
async def fixar_cliente(id: int, dados: ClienteFixar, db: Session = Depends(get_db)):
    cliente = db.query(Client).filter(Client.id == id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    cliente.fixo = dados.fixo
    cliente.dia_fixo = dados.dia_fixo
    db.commit()
    return {"status": "sucesso"}

@router.delete("/clientes/{id}")
async def excluir_cliente(id: int, db: Session = Depends(get_db)):
    cliente = db.query(Client).filter(Client.id == id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    coletas_ativas = db.query(Schedule).filter(Schedule.codigo_cliente == cliente.codigo).first()
    if coletas_ativas:
        raise HTTPException(status_code=400, detail="Cliente possui coletas ativas registradas.")
        
    db.delete(cliente)
    db.commit()
    return {"status": "sucesso"}


# ── ROTAS DE PROGRAMAÇÃO (AGENDAMENTOS) ──────────────
@router.post("/programacao/adicionar")
async def adicionar_programacao(dados: ScheduleAdd, db: Session = Depends(get_db)):
    try:
        data_dt = date.fromisoformat(dados.data_coleta)
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de data inválido.")
    
    # 1. Higieniza o código recebido para a busca
    cod_limpo = str(dados.codigo_cliente).strip()
    if cod_limpo.isdigit():
        cod_final = str(int(cod_limpo))
    else:
        cod_final = cod_limpo
        
    # 2. BUSCA O CLIENTE NO CADASTRO PARA PEGAR O NOME (Evita o erro NOT NULL)
    cliente_db = db.query(Client).filter(Client.codigo == cod_final).first()
    if not cliente_db and cod_limpo != cod_final:
        cliente_db = db.query(Client).filter(Client.codigo == cod_limpo).first()
        
    if not cliente_db:
        raise HTTPException(
            status_code=404, 
            detail=f"Não foi possível replicar: Cliente com código '{cod_limpo}' não encontrado no banco de dados."
        )
        
    # 3. Descobre o dia da semana por extenso (ex: "Quinta")
    dia_extenso = DIAS_SEMANA.get(data_dt.weekday())
        
    # 4. CRIA A COLETA COM TODOS OS CAMPOS OBRIGATÓRIOS EXIGIDOS PELO SEU BANCO
    nova_coleta = Schedule(
        codigo_cliente=cliente_db.codigo,
        cliente=cliente_db.nome,        # <--- Correção crítica aqui!
        data_coleta=data_dt,
        dia_semana=dia_extenso,
        status="Programado",
        fixo=cliente_db.fixo
    )
    
    try:
        db.add(nova_coleta)
        db.commit()
        return {"status": "sucesso"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao gravar no banco: {str(e)}")

@router.put("/programacao/{id}")
async def atualizar_programacao(id: int, dados: ScheduleUpdate, db: Session = Depends(get_db)):
    coleta = db.query(Schedule).filter(Schedule.id == id).first()
    if not coleta:
        raise HTTPException(status_code=404, detail="Coleta não encontrada")
    try:
        coleta.data_coleta = date.fromisoformat(dados.data_coleta)
    except ValueError:
        raise HTTPException(status_code=400, detail="Data inválida.")
    db.commit()
    return {"status": "sucesso"}

@router.delete("/programacao/{id}")
async def excluir_programacao(id: int, db: Session = Depends(get_db)):
    coleta = db.query(Schedule).filter(Schedule.id == id).first()
    if not coleta:
        raise HTTPException(status_code=404, detail="Coleta não encontrada")
    db.delete(coleta)
    db.commit()
    return {"status": "sucesso"}

@router.post("/gerar-programacao")
async def processar_geracao_automatica(db: Session = Depends(get_db)):
    try:
        gerar_programacao(db)
        return {"status": "sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.post("/fechar-semana")
async def fechar_semana_route(db: Session = Depends(get_db)):
    """
    Verifica e fecha semanas passadas não processadas.
    Chamado automaticamente pelo frontend ao carregar.
    """
    resultado = processar_fechamento(db)
    return resultado