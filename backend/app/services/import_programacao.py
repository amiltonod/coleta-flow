import io
import pandas as pd
from datetime import date, datetime
from sqlalchemy.orm import Session
from backend.app.models.veiculo import Veiculo


# ── helpers ──────────────────────────────────────────────────────────────────

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
    """Representa uma linha lida — usada para gerar o WhatsApp."""
    def __init__(self, data, hora, cliente, obs, placa, motorista):
        self.data      = data
        self.hora      = hora
        self.cliente   = cliente
        self.obs       = obs
        self.placa     = placa
        self.motorista = motorista


# ── mapeamento de colunas por nome ───────────────────────────────────────────
# Variações aceitas para cada campo — protege contra diferenças entre máquinas
COLUNAS = {
    "data":      ["DATA"],
    "hora":      ["HORA"],
    "cliente":   ["NOME RAZÃO SOCIAL", "NOME RAZAO SOCIAL", "CLIENTE", "RAZÃO SOCIAL"],
    "obs":       ["OBS 01", "OBS", "OBSERVAÇÃO", "OBSERVACAO"],
    "placa":     ["PLACA"],
    "motorista": ["MOTORISTA"],
}


def _mapear_colunas(df: pd.DataFrame) -> dict:
    """
    Normaliza os cabeçalhos para maiúsculo e localiza cada campo.
    Retorna {campo: nome_real_no_df} — valor None se não encontrado.
    """
    colunas_df = {c.strip().upper(): c for c in df.columns}
    mapeamento = {}
    for campo, variacoes in COLUNAS.items():
        encontrado = None
        for v in variacoes:
            if v in colunas_df:
                encontrado = colunas_df[v]
                break
        mapeamento[campo] = encontrado
    return mapeamento


def _col(row, mapa: dict, campo: str):
    """Lê o valor de uma linha pelo nome mapeado. Retorna None se não mapeado."""
    nome = mapa.get(campo)
    if nome is None or nome not in row.index:
        return None
    return row[nome]


# ── núcleo compartilhado ─────────────────────────────────────────────────────

def _processar_df(df: pd.DataFrame, db: Session) -> dict:
    """
    Recebe um DataFrame já pronto (de arquivo ou de texto colado) e processa.
    Único efeito no banco: criar/atualizar Veiculo (placa + motorista).
    """
    mapa = _mapear_colunas(df)

    erros_cabecalho = [
        f"Coluna '{c}' não encontrada — verifique o cabeçalho da planilha"
        for c in ("placa", "motorista", "data", "hora", "cliente")
        if mapa[c] is None
    ]
    if erros_cabecalho:
        return {
            "veiculos_novos": 0, "veiculos_atualizados": 0,
            "linhas_lidas": [],
            "erros": [{"linha": 1, "erro": e} for e in erros_cabecalho],
        }

    veiculos_novos = 0
    veiculos_atualizados = 0
    linhas_lidas: list[LinhaColeta] = []
    erros = []

    for idx, row in df.iterrows():
        try:
            data_coleta  = _parse_date(_col(row, mapa, "data"))
            hora_str     = _parse_hora(_col(row, mapa, "hora"))
            cliente_nome = _clean(_col(row, mapa, "cliente"))
            obs          = _clean(_col(row, mapa, "obs"))
            placa        = _clean(_col(row, mapa, "placa"))
            motorista    = _clean(_col(row, mapa, "motorista"))

            if not placa:
                continue

            # único efeito no banco
            veiculo = db.query(Veiculo).filter(Veiculo.placa == placa).first()
            if not veiculo:
                db.add(Veiculo(placa=placa, motorista=motorista or None))
                db.flush()
                veiculos_novos += 1
            elif motorista and veiculo.motorista != motorista:
                veiculo.motorista = motorista
                veiculos_atualizados += 1

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


# ── entradas públicas ─────────────────────────────────────────────────────────

def importar_texto(texto: str, db: Session) -> dict:
    """
    Entrada via cola direta (Ctrl+C no Sagy → Ctrl+V no ColetaFlow).
    O Sagy copia como TSV (colunas separadas por tab), igual ao Excel.
    A primeira linha deve ser o cabeçalho.
    """
    if not texto or not texto.strip():
        return {
            "veiculos_novos": 0, "veiculos_atualizados": 0,
            "linhas_lidas": [],
            "erros": [{"linha": -1, "erro": "Nenhum dado colado"}],
        }
    try:
        df = pd.read_csv(io.StringIO(texto), sep="\t", dtype=str)
    except Exception as e:
        return {
            "veiculos_novos": 0, "veiculos_atualizados": 0,
            "linhas_lidas": [],
            "erros": [{"linha": -1, "erro": f"Erro ao ler dados colados: {e}"}],
        }
    return _processar_df(df, db)


def importar_programacao(conteudo: bytes, db: Session) -> dict:
    """Entrada via arquivo Excel ou CSV (mantida para compatibilidade)."""
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
    return _processar_df(df, db)