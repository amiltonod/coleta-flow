import io
import pandas as pd
from datetime import date, datetime
from sqlalchemy.orm import Session
from backend.app.models.veiculo import Veiculo


def _clean(val, default: str = "") -> str:
    """Remove espaços normais e \xa0 (espaço invisível do sistema exportador)."""
    if val is None:
        return default
    s = str(val).strip().replace("\xa0", "").strip()
    return s if s and s.lower() != "nan" else default


def _parse_date(val) -> date | None:
    if val is None:
        return None
    if isinstance(val, (datetime, pd.Timestamp)):
        return val.date()
    if isinstance(val, date):
        return val
    s = _clean(val)
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None


def _parse_hora(val) -> str | None:
    """Retorna 'HH:MM' ou None. Aceita HH:MM:SS ou HH:MM."""
    s = _clean(val)
    if not s:
        return None
    partes = s.split(":")
    if len(partes) >= 2:
        try:
            return f"{int(partes[0]):02d}:{int(partes[1]):02d}"
        except ValueError:
            pass
    return None


class LinhaColeta:
    """Representa uma linha lida da planilha — usada para gerar o WhatsApp."""
    def __init__(self, data, hora, cliente, obs, placa, motorista):
        self.data      = data
        self.hora      = hora
        self.cliente   = cliente
        self.obs       = obs
        self.placa     = placa
        self.motorista = motorista


def importar_programacao(conteudo: bytes, db: Session) -> dict:
   
    try:
        df = pd.read_excel(io.BytesIO(conteudo), dtype=str)
    except Exception:
        try:
            df = pd.read_csv(io.BytesIO(conteudo), dtype=str)
        except Exception as e:
            return {
                "veiculos_novos": 0, "veiculos_atualizados": 0,
                "linhas_lidas": [],
                "erros": [{"linha": -1, "erro": f"Formato inválido: {e}"}],
            }

    veiculos_novos = 0
    veiculos_atualizados = 0
    linhas_lidas: list[LinhaColeta] = []
    erros = []

    data_primeira_linha = df.iloc[0, 0]
    data_obj = _parse_date(data_primeira_linha) # Usa sua função existente


    for idx, row in df.iterrows():
        try:
            data_coleta  = _parse_date(row.iloc[0] if len(row) > 0 else None)
            hora_str     = _parse_hora(row.iloc[3] if len(row) > 3 else None)
            cliente_nome = _clean(row.iloc[4] if len(row) > 4 else None)
            obs          = _clean(row.iloc[5] if len(row) > 5 else None)
            placa        = _clean(row.iloc[7] if len(row) > 7 else None)
            motorista    = _clean(row.iloc[8] if len(row) > 8 else None)

            if not placa:
                continue  # linha sem placa — pula

            # ── ÚNICO efeito no banco: cadastrar/atualizar Veiculo ──────────
            veiculo = db.query(Veiculo).filter(Veiculo.placa == placa).first()
            if not veiculo:
                db.add(Veiculo(placa=placa, motorista=motorista or None))
                veiculos_novos += 1
            elif motorista and veiculo.motorista != motorista:
                veiculo.motorista = motorista
                veiculos_atualizados += 1

            # ── guardar para gerar WhatsApp ─────────────────────────────────
            linhas_lidas.append(LinhaColeta(
                data=data_coleta,
                hora=hora_str,
                cliente=cliente_nome,
                obs=obs,
                placa=placa,
                motorista=motorista,
            ))

        except Exception as e:
            erros.append({"linha": int(idx) + 2, "erro": str(e)})

    db.commit()
    
    return {
        "veiculos_novos": veiculos_novos,
        "veiculos_atualizados": veiculos_atualizados,
        "linhas_lidas": linhas_lidas,
        "erros": erros,
    }