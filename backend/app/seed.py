from __future__ import annotations

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.schemas.enums import CaseMode
from app.services.case_service import CaseService


MEDICAL_DEMO = "58-year-old diabetic male with chest pain, sweating, and shortness of breath for 20 minutes."
DISASTER_DEMO = "Flooding in Sector 9, 12 people trapped, one elderly injured, roads blocked, water above knee height."


def main() -> None:
    Base.metadata.create_all(bind=engine)
    service = CaseService(get_settings())
    with SessionLocal() as db:
        service.seed_case(db, mode=CaseMode.MEDICAL_TRIAGE, raw_input=MEDICAL_DEMO)
        service.seed_case(db, mode=CaseMode.DISASTER_RESPONSE, raw_input=DISASTER_DEMO)
    print("Seeded demo cases.")


if __name__ == "__main__":
    main()

