import datetime
import json
import os
import time
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).parent
ACTIONS_PATH = ROOT / "actions.json"
DAMAGE_CSV = ROOT / "base_pronta.csv"
MISSING_CSV = ROOT / "base_falta_pronta.csv"

ACTION_COLUMNS = ["id", "filial", "action", "start_date", "end_date", "status"]
DEFAULT_DURATION_DAYS = 14
STATUS_VALUES = ("Planejada", "Em andamento", "Concluída")
MAX_FILIAL_CHARS = 150
MAX_ACTION_CHARS = 2000

def source_mtime() -> float:
    """Mtime mais recente dos CSVs — chave de cache do Streamlit (evita reler os ~21 MB)."""
    return max((path.stat().st_mtime for path in (DAMAGE_CSV, MISSING_CSV) if path.exists()), default=0.0)

def actions_mtime() -> float:
    """Mtime do actions.json — invalida o cache quando o site/dashboard grava."""
    return ACTIONS_PATH.stat().st_mtime if ACTIONS_PATH.exists() else 0.0


def default_end_date(start_date: str, days: int = DEFAULT_DURATION_DAYS) -> str:
    """Calcula a data final padrão (início + 14 dias) quando o término não é informado."""
    try:
        start = datetime.date.fromisoformat(str(start_date)[:10])
    except (TypeError, ValueError):
        return ""
    return (start + datetime.timedelta(days=days)).isoformat()

def init_db() -> None:
    if not ACTIONS_PATH.exists():
        ACTIONS_PATH.write_text("[]", encoding="utf-8")

def _write_actions(actions: list) -> None:
    """Grava o actions.json de forma atómica (tmp + replace) para evitar ficheiros corrompidos."""
    tmp_path = ACTIONS_PATH.with_name(ACTIONS_PATH.name + ".tmp")
    tmp_path.write_text(json.dumps(actions, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp_path, ACTIONS_PATH)

def _next_action_id(actions: list) -> int:
    """ID único e monotónico, compatível com os IDs (Date.now) gerados pelo site.js."""
    max_id = 0
    for item in actions:
        try:
            max_id = max(max_id, int(item.get("id") or 0))
        except (TypeError, ValueError):
            continue
    return max(int(time.time() * 1000), max_id + 1)

def save_action(filial: str, action: str, start_date: str, end_date: str = "", status: str = "Planejada") -> None:
    init_db()
    actions = json.loads(ACTIONS_PATH.read_text(encoding="utf-8"))
    start_date = str(start_date).strip()
    end_date = str(end_date).strip()
    if not end_date or end_date <= start_date:
        end_date = default_end_date(start_date)
    safe_status = str(status).strip()
    if safe_status not in STATUS_VALUES:
        safe_status = "Planejada"
    actions.append({
        "id": _next_action_id(actions),
        "filial": str(filial).strip()[:MAX_FILIAL_CHARS],
        "action": str(action).strip()[:MAX_ACTION_CHARS],
        "start_date": start_date,
        "end_date": end_date,
        "status": safe_status,
    })
    _write_actions(actions)

def delete_action(action_id) -> bool:
    """Remove a tratativa com o ID indicado. Devolve True se algo foi removido."""
    init_db()
    actions = json.loads(ACTIONS_PATH.read_text(encoding="utf-8"))
    remaining = [item for item in actions if str(item.get("id")) != str(action_id)]
    if len(remaining) == len(actions):
        return False
    _write_actions(remaining)
    return True

def read_actions() -> pd.DataFrame:
    init_db()
    actions = json.loads(ACTIONS_PATH.read_text(encoding="utf-8"))
    if not actions:
        return pd.DataFrame(columns=ACTION_COLUMNS)
    frame = pd.DataFrame(actions)
    for column in ACTION_COLUMNS:
        if column not in frame.columns:
            frame[column] = ""
    # Compatibilidade com registros antigos gravados sem data final (início + 14 dias)
    frame["end_date"] = [
        str(value).strip() or default_end_date(start)
        for value, start in zip(frame["end_date"], frame["start_date"])
    ]
    return frame[ACTION_COLUMNS].sort_values(["start_date", "id"], ascending=False)

def _read_csv(path: Path) -> pd.DataFrame:
    for encoding in ("utf-8-sig", "latin1"):
        try:
            return pd.read_csv(path, sep=";", encoding=encoding, low_memory=False)
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("csv", b"", 0, 1, f"Não foi possível ler {path.name}")

def read_occurrences() -> pd.DataFrame:
    damage = _read_csv(DAMAGE_CSV)
    missing = _read_csv(MISSING_CSV)

    damage = damage.rename(columns={"data": "date", "qtd_reclamada": "quantity"})
    missing = missing.rename(columns={"data_hr_faturamento": "date", "cantidad_itens": "quantity"})
    damage["type"] = "Dano"
    missing["type"] = "Falta"

    columns = ["date", "filial", "quantity", "type"]
    occurrences = pd.concat([damage[columns], missing[columns]], ignore_index=True)
    occurrences["date"] = pd.to_datetime(occurrences["date"], errors="coerce")
    occurrences["quantity"] = pd.to_numeric(occurrences["quantity"], errors="coerce").fillna(0)
    occurrences["filial"] = occurrences["filial"].fillna("Filial não informada").astype(str).str.strip()
    return occurrences.dropna(subset=["date"])

def action_records() -> list[dict[str, Any]]:
    return read_actions().to_dict("records")
