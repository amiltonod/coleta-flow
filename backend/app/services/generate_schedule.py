from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from backend.app.models.client import Client
from backend.app.models.schedule import Schedule

DIAS_SEMANA = {
    0: "Segunda",
    1: "Terça",
    2: "Quarta",
    3: "Quinta",
    4: "Sexta",
    5: "Sábado",
    6: "Domingo",
}

DIAS_SEMANA_REVERSO = {v.lower(): k for k, v in DIAS_SEMANA.items()}


def ajustar_para_dia_util(data: date) -> date:
    while data.weekday() >= 5:
        data += timedelta(days=1)
    return data


def proxima_data_para_dia(dia_nome: str, segunda: date) -> date:
    nome_limpo = dia_nome.strip().lower()
    offset = DIAS_SEMANA_REVERSO.get(nome_limpo)
    
    if offset is None:
        return None
        
    return segunda + timedelta(days=offset)


def ja_agendado_na_data(db: Session, codigo: str, data: date) -> bool:
    """TRAVA PARA FIXOS: Garante que o mesmo cliente não tenha duas coletas no MESMO DIA."""
    cod_limpo = str(codigo).strip()
    cod_alternativo = str(int(cod_limpo)) if cod_limpo.isdigit() else cod_limpo

    # 1. Checa na memória local (fila do commit atual)
    for obj in db.new:
        if isinstance(obj, Schedule):
            obj_cod = str(obj.codigo_cliente).strip()
            if obj_cod in (cod_limpo, cod_alternativo) and obj.data_coleta == data:
                return True

    # 2. Checa no Banco de Dados
    existente = db.query(Schedule).filter(
        or_(
            Schedule.codigo_cliente == cod_limpo,
            Schedule.codigo_cliente == cod_alternativo
        ),
        func.date(Schedule.data_coleta) == data
    ).first()
    
    return existente is not None


def ja_agendado_na_semana(db: Session, codigo: str, data_inicio: date, data_fim: date) -> bool:
    """TRAVA PARA NORMAIS: Garante que o cliente só tenha UMA coleta AUTOMÁTICA na semana inteira."""
    cod_limpo = str(codigo).strip()
    cod_alternativo = str(int(cod_limpo)) if cod_limpo.isdigit() else cod_limpo

    # 1. Checa na memória local (previne duplicar se clicar no botão duas vezes seguidas)
    for obj in db.new:
        if isinstance(obj, Schedule):
            obj_cod = str(obj.codigo_cliente).strip()
            if obj_cod in (cod_limpo, cod_alternativo):
                if data_inicio <= obj.data_coleta <= data_fim:
                    return True

    # 2. Checa no Banco de Dados (bloqueia se já foi gerado antes ou inserido manualmente)
    existente = db.query(Schedule).filter(
        or_(
            Schedule.codigo_cliente == cod_limpo,
            Schedule.codigo_cliente == cod_alternativo
        ),
        func.date(Schedule.data_coleta) >= data_inicio,
        func.date(Schedule.data_coleta) <= data_fim
    ).first()
    
    return existente is not None


def gerar_programacao(db: Session) -> dict:
    """
    Gera a programação da próxima semana sem duplicar clientes normais na mesma semana.
    """
    clientes = db.query(Client).all()

    if not clientes:
        return {"gerados": 0, "mensagem": "Nenhum cliente encontrado."}

    hoje = date.today()
    dias_ate_segunda = (7 - hoje.weekday()) % 7 or 7
    segunda = hoje + timedelta(days=dias_ate_segunda)
    domingo = segunda + timedelta(days=6)  # Define o limite do final da semana alvo
    
    dias_semana = [segunda + timedelta(days=i) for i in range(5)]

    gerados = 0
    ignorados = 0
    duplicados = 0
    solicitacao = 0

    for cliente in clientes:
        # ── BLINDAGEM 1: Checagem de "Por Solicitação" (Alvo curto para evitar erros de digitação)
        obs_texto = (cliente.observacao or "").lower()
        dia_fixo_texto = (cliente.dia_fixo or "").lower()
        
        if "solicit" in obs_texto or "solicit" in dia_fixo_texto:
            solicitacao += 1
            continue

        # ── CLIENTE FIXO: Pode ter mais de uma na semana, mas não no mesmo dia
        if cliente.fixo and cliente.dia_fixo:
            dias_fixos = [d.strip() for d in cliente.dia_fixo.split(",")]

            for dia_nome in dias_fixos:
                data_coleta = proxima_data_para_dia(dia_nome, segunda)

                if data_coleta is None:
                    continue

                if ja_agendado_na_data(db, cliente.codigo, data_coleta):
                    duplicados += 1
                    continue

                schedule = Schedule(
                    cliente=cliente.nome,
                    codigo_cliente=cliente.codigo,
                    unidade=cliente.unidade,
                    data_coleta=data_coleta,
                    dia_semana=dia_nome.strip().capitalize(),
                    status="Programado",
                    fixo=True,
                )
                db.add(schedule)
                gerados += 1

        # ── CLIENTE NORMAL: Máximo de UMA coleta automática por semana
        elif cliente.ultima_coleta and cliente.frequencia_dias:
            data_coleta = cliente.ultima_coleta + timedelta(days=cliente.frequencia_dias)
            data_coleta = ajustar_para_dia_util(data_coleta)
            dia_semana = DIAS_SEMANA.get(data_coleta.weekday(), "Segunda")

            if data_coleta not in dias_semana:
                ignorados += 1
                continue

            # 🚨 AQUI ESTÁ A MUDANÇA: Verifica se o cliente já tem QUALQUER coleta entre segunda e domingo
            if ja_agendado_na_semana(db, cliente.codigo, segunda, domingo):
                duplicados += 1
                continue

            schedule = Schedule(
                cliente=cliente.nome,
                codigo_cliente=cliente.codigo,
                unidade=cliente.unidade,
                data_coleta=data_coleta,
                dia_semana=dia_semana,
                status="Programado",
                fixo=False,
            )
            db.add(schedule)
            gerados += 1

        else:
            ignorados += 1

    db.commit()

    return {
        "gerados": gerados,
        "ignorados": ignorados,
        "duplicados": duplicados,
        "por_solicitacao": solicitacao,  
        "mensagem": "Programação criada com sucesso!"
    }