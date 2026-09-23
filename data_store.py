from pathlib import Path
import json
from typing import Any

import pandas as pd

ROOT = Path(__file__).parent
ACTIONS_PATH = ROOT / "actions.json"
DAMAGE_CSV = ROOT / "base_pronta.csv"
MISSING_CSV = ROOT / "base_falta_pronta.csv"

def init_db() -> None:
    if not ACTIONS_PATH.exists():
        ACTIONS_PATH.write_text("[]", encoding="utf-8")

def save_action(filial: str, action: str, start_date: str, status: str) -> None:
    init_db()
    actions = json.loads(ACTIONS_PATH.read_text(encoding="utf-8"))
    actions.append({"id": len(actions) + 1, "filial": filial.strip(), "action": action.strip(), "start_date": start_date, "status": status})
    ACTIONS_PATH.write_text(json.dumps(actions, ensure_ascii=False, indent=2), encoding="utf-8")

def read_actions() -> pd.DataFrame:
    init_db()
    actions = json.loads(ACTIONS_PATH.read_text(encoding="utf-8"))
    return pd.DataFrame(actions, columns=["id", "filial", "action", "start_date", "status"]).sort_values(
        ["start_date", "id"], ascending=False
    ) if actions else pd.DataFrame(columns=["id", "filial", "action", "start_date", "status"])

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
