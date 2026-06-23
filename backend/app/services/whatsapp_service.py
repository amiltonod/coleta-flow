from datetime import date
from sqlalchemy.orm import Session

from backend.app.models.schedule import Schedule
from backend.app.models.veiculo import Veiculo


def _hora_sort_key(hora_str: str | None) -> str:
    """Retorna a hora como string sortável; coletas sem hora vão para o final."""
    return hora_str if hora_str else "99:99"


def gerar_mensagem_whatsapp(data_ref: date, db: Session) -> str:
 
    # buscar todas as coletas do dia, com join no veículo
    schedules = (
        db.query(Schedule)
        .filter(Schedule.data_coleta == data_ref)
        .order_by(Schedule.veiculo_id, Schedule.hora_coleta)
        .all()
    )

    if not schedules:
        return f"PROGRAMAÇÃO – {data_ref.strftime('%d/%m/%Y')}\n\n(Nenhuma coleta encontrada para este dia)"

    # agrupar por veiculo_id
    grupos: dict[int | None, list[Schedule]] = {}
    for s in schedules:
        grupos.setdefault(s.veiculo_id, []).append(s)

    # montar texto
    linhas = [f"PROGRAMAÇÃO – {data_ref.strftime('%d/%m/%Y')}", ""]

    # ordenar grupos: veículos com id primeiro (por placa), sem veículo por último
    veiculos_cache: dict[int, Veiculo] = {}
    ids_ordenados: list[int | None] = sorted(
        [k for k in grupos if k is not None],
        key=lambda vid: _get_placa(vid, db, veiculos_cache),
    )
    if None in grupos:
        ids_ordenados.append(None)

    for vid in ids_ordenados:
        coletas = sorted(grupos[vid], key=lambda s: _hora_sort_key(s.hora_coleta))

        if vid is not None:
            v = _get_veiculo(vid, db, veiculos_cache)
            motorista = (v.motorista or "NÃO INFORMADO").upper()
            placa = v.placa
        else:
            placa = "SEM PLACA"
            motorista = "NÃO INFORMADO"

        linhas.append(f"*{placa} – {motorista}*")
        linhas.append("")

        for c in coletas:
            hora = c.hora_coleta or "--:--"
            linhas.append(f"{hora} – {c.cliente}")
            if c.observacao:
                linhas.append(c.observacao)
            linhas.append("")

        linhas.append("────────────────────")
        linhas.append("")

    return "\n".join(linhas)


# ── helpers ─────────────────────────────────────────────────────────────────

def _get_veiculo(vid: int, db: Session, cache: dict) -> Veiculo:
    if vid not in cache:
        cache[vid] = db.query(Veiculo).filter(Veiculo.id == vid).first()
    return cache[vid]


def _get_placa(vid: int, db: Session, cache: dict) -> str:
    v = _get_veiculo(vid, db, cache)
    return v.placa if v else "ZZZ"
