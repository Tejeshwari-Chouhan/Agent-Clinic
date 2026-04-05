"""Persistent store for patient context such as reports and medications."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import json


class PatientContextStore:
    """Simple JSON-file backed patient context store."""

    def __init__(self, db_path: Path | None = None):
        base_dir = Path(__file__).resolve().parents[2]
        self.db_path = db_path or (base_dir / "data" / "patient_context.json")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def get(self, patient_id: str) -> Dict[str, Any]:
        """Fetch stored context for patient_id."""
        data = self._read_all()
        return data.get(patient_id, {})

    def upsert(self, patient_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Insert or update context for a patient."""
        data = self._read_all()
        existing = data.get(patient_id, {})

        merged = {
            "patient_id": patient_id,
            "test_reports": self._merge_lists(existing.get("test_reports", []), context.get("test_reports", [])),
            "medications": self._merge_lists(existing.get("medications", []), context.get("medications", [])),
            "allergies": self._merge_lists(existing.get("allergies", []), context.get("allergies", [])),
            "known_conditions": self._merge_lists(
                existing.get("known_conditions", []), context.get("known_conditions", [])
            ),
            "context_notes": self._merge_lists(existing.get("context_notes", []), context.get("context_notes", [])),
        }

        data[patient_id] = merged
        self._write_all(data)
        return merged

    def _read_all(self) -> Dict[str, Any]:
        if not self.db_path.exists():
            return {}
        try:
            return json.loads(self.db_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def _write_all(self, payload: Dict[str, Any]) -> None:
        self.db_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _merge_lists(self, old_values: Any, new_values: Any) -> list:
        old_values = old_values if isinstance(old_values, list) else []
        new_values = new_values if isinstance(new_values, list) else []
        merged = []
        seen = set()
        for value in [*old_values, *new_values]:
            marker = json.dumps(value, sort_keys=True) if isinstance(value, dict) else str(value).strip().lower()
            if marker and marker not in seen:
                merged.append(value)
                seen.add(marker)
        return merged
