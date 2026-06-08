from datetime import date, timedelta
from sqlalchemy.orm import Session
from backend.app.models.client import Client
from backend.app.models.schedule import Schedule

DIAS_SEMANA = {
    0: "Segunda", 1: "Terça", 2: "Quarta", 
    3: "Quinta", 4: "Sexta", 5: "Sábado", 6: "Domingo"
}
DIAS_SEMANA_REVERSO = {v: k for k, v in DIAS_SEMANA.items()}

def ajustar_para_dia_util(data: date) -> date:
    while data.weekday() >= 5:
        data += timedelta(days=1)
    return data

def proxima_data_para_dia(dia_nome: str, segunda: date) -> date:
    offset = DIAS_SEMANA_REVERSO.get(dia_nome, 0)
    return segunda + timedelta(days=offset)

def gerar_programacao(db: Session) -> dict:
    clientes = db.query(Client).all()
    if not clientes:
        return {"gerados": 0, "mensagem": "Nenhum cliente encontrado no banco."}

    hoje = date.today()
    dias_ate_segunda = (7 - hoje.weekday()) % 7 or 7
    segunda = hoje + timedelta(days=dias_ate_segunda)
    
    inicio_semana = segunda
    fim_semana = segunda + timedelta(days=6)

    gerados = 0
    ignorados = 0

    for cliente in clientes:
        # 1. FILTRO: "Por solicitação"
        # .lower() converte tudo para minúsculo, garantindo que não pule por erro de digitação
        if cliente.observacao and "por solicitação" in cliente.observacao.lower():
            ignorados += 1
            continue

        # 2. CLIENTE FIXO — Pode ter múltiplos dias ("Segunda,Quinta")
        if cliente.fixo and cliente.dia_fixo:
            # Transforma a string "Segunda, Quinta" numa lista ["Segunda", "Quinta"]
            dias_fixos = [dia.strip() for dia in cliente.dia_fixo.split(",")]
            
            for dia in dias_fixos:
                data_coleta = proxima_data_para_dia(dia, segunda)
                
                # Trava para clientes FIXOS: Verifica se já existe aquele "dia" específico na semana
                existe = db.query(Schedule).filter(
                    Schedule.codigo_cliente == cliente.codigo,
                    Schedule.data_coleta >= inicio_semana,
                    Schedule.data_coleta <= fim_semana,
                    Schedule.dia_semana == dia # Importante para não bloquear a Quinta se já achou a Segunda!
                ).first()

                if not existe:
                    schedule = Schedule(
                        cliente=cliente.nome,
                        codigo_cliente=cliente.codigo,
                        unidade=cliente.unidade,
                        data_coleta=data_coleta,
                        dia_semana=dia,
                        status="Programado",
                        fixo=True,
                    )
                    db.add(schedule)
                    gerados += 1
                else:
                    ignorados += 1

        # 3. CLIENTE NORMAL — Calcula pela frequência
        elif cliente.ultima_coleta and cliente.frequencia_dias:
            data_coleta = cliente.ultima_coleta + timedelta(days=cliente.frequencia_dias)
            data_coleta = ajustar_para_dia_util(data_coleta)
            dia_semana = DIAS_SEMANA.get(data_coleta.weekday(), "Segunda")

            dias_semana_proxima = [segunda + timedelta(days=i) for i in range(5)]
            if data_coleta not in dias_semana_proxima:
                ignorados += 1
                continue

            # Trava para clientes NORMAIS: Verifica a semana toda
            existe = db.query(Schedule).filter(
                Schedule.codigo_cliente == cliente.codigo,
                Schedule.data_coleta >= inicio_semana,
                Schedule.data_coleta <= fim_semana
            ).first()

            if not existe:
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
        else:
            ignorados += 1

    db.commit()
    return {
        "gerados": gerados,
        "ignorados": ignorados,
        "mensagem": "Programação processada com sucesso!"
    }