"""Seed incidents from an Excel file.

Usage:
    PYTHONPATH=. ./venv/bin/python scripts/seed_incidents.py --file "Copy of REKAP FULL.xlsx" --sheet "Sheet1" --limit 50

The script expects columns whose names map to the Incident fields. Adjust COLUMN_MAP
below if your spreadsheet uses different headers.
"""

import argparse
import math
from datetime import datetime
from typing import Any, Dict, Optional

import pandas as pd
from sqlmodel import Session

# Import models to ensure SQLAlchemy registry has all relationships loaded
from src.app.models.user import User  # noqa: F401
from src.app.models.location import Location  # noqa: F401
from src.app.models.department import Department  # noqa: F401
from src.app.db import engine
from src.app.models.incident import (
    AgeGroup,
    Gender,
    Incident,
    IncidentOutcome,
    IncidentPlace,
    IncidentStatus,
    PayerType,
    ReporterType,
)


# Adjust these if your Excel column headers differ
COLUMN_MAP = {
    "patient_name": "patient_name",
    "patient_identifier": "patient_identifier",
    "reporter_type": "reporter_type",
    "age": "age",
    "age_group": "age_group",
    "gender": "gender",
    "payer_type": "payer_type",
    "admission_at": "admission_at",
    "occurred_at": "occurred_at",
    "incident_place": "incident_place",
    "incident_unit": "incident_unit",
    "incident_outcome": "incident_outcome",
    "immediate_action": "immediate_action",
    "has_similar_event": "has_similar_event",
    "location_id": "location_id",
    "department_id": "department_id",
    "free_text_description": "free_text_description",
    "harm_indicator": "harm_indicator",
}


def parse_enum(enum_cls, raw: Any):
    if raw is None or (isinstance(raw, float) and math.isnan(raw)):
        return None
    val = str(raw).strip()
    for item in enum_cls:
        if val.lower() in {item.value.lower(), item.name.lower()}:
            return item
    raise ValueError(f"Cannot map '{val}' to {enum_cls.__name__}")


def parse_bool(raw: Any) -> Optional[bool]:
    if raw is None or (isinstance(raw, float) and math.isnan(raw)):
        return None
    if isinstance(raw, bool):
        return raw
    val = str(raw).strip().lower()
    if val in {"1", "true", "ya", "yes", "y"}:
        return True
    if val in {"0", "false", "tidak", "no", "n"}:
        return False
    return None


def parse_datetime(raw: Any) -> Optional[datetime]:
    if raw is None or (isinstance(raw, float) and math.isnan(raw)):
        return None
    try:
        return pd.to_datetime(raw, utc=True).to_pydatetime()
    except Exception:
        return None


def clean_value(row: Dict[str, Any], key: str):
    col = COLUMN_MAP[key]
    val = row.get(col)
    if isinstance(val, float) and math.isnan(val):
        return None
    return val


def build_incident(row: Dict[str, Any]) -> Incident:
    return Incident(
        patient_name=clean_value(row, "patient_name"),
        patient_identifier=clean_value(row, "patient_identifier"),
        reporter_type=parse_enum(ReporterType, clean_value(row, "reporter_type")) if clean_value(row, "reporter_type") else None,
        reporter_id=2,
        age=int(clean_value(row, "age")) if clean_value(row, "age") is not None else None,
        age_group=parse_enum(AgeGroup, clean_value(row, "age_group")) if clean_value(row, "age_group") else None,
        gender=parse_enum(Gender, clean_value(row, "gender")) if clean_value(row, "gender") else None,
        payer_type=parse_enum(PayerType, clean_value(row, "payer_type")) if clean_value(row, "payer_type") else None,
        admission_at=parse_datetime(clean_value(row, "admission_at")),
        occurred_at=parse_datetime(clean_value(row, "occurred_at")) or datetime.utcnow(),
        incident_place=parse_enum(IncidentPlace, clean_value(row, "incident_place")) if clean_value(row, "incident_place") else None,
        incident_unit=clean_value(row, "incident_unit"),
        incident_outcome=parse_enum(IncidentOutcome, clean_value(row, "incident_outcome")) if clean_value(row, "incident_outcome") else None,
        immediate_action=clean_value(row, "immediate_action"),
        has_similar_event=parse_bool(clean_value(row, "has_similar_event")),
        location_id=clean_value(row, "location_id"),
        department_id=clean_value(row, "department_id"),
        free_text_description=clean_value(row, "free_text_description") or "N/A",
        harm_indicator=clean_value(row, "harm_indicator"),
        attachments=[],
        status=IncidentStatus.DRAFT,
    )


def main():
    parser = argparse.ArgumentParser(description="Seed incidents from Excel")
    parser.add_argument("--file", required=True, help="Path to Excel file")
    parser.add_argument("--sheet", default=None, help="Worksheet name (defaults to first)")
    parser.add_argument("--limit", type=int, default=None, help="Optional limit on rows to import")
    args = parser.parse_args()

    df = pd.read_excel(args.file, sheet_name=args.sheet)
    if args.limit:
        df = df.head(args.limit)

    records = df.to_dict(orient="records")
    print(f"Loaded {len(records)} rows from {args.file}")

    created = 0
    skipped = 0
    with Session(engine) as session:
        for idx, row in enumerate(records, start=1):
            try:
                incident = build_incident(row)
                session.add(incident)
                created += 1
            except Exception as exc:
                skipped += 1
                print(f"[skip row {idx}] {exc}")
        session.commit()

    print(f"Inserted {created} incidents. Skipped {skipped}.")


if __name__ == "__main__":
    main()
