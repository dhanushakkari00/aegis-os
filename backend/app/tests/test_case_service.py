from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.schemas.case import CaseCreate
from app.services.case_service import CaseService


def test_case_service_create_fetch_and_update(db_session: Session) -> None:
    service = CaseService(Settings())
    created_case = service.create_case(
        db_session,
        CaseCreate(
            mode="auto_detect",
            raw_input="Test medical emergency with callback requested.",
            contact_email="ops@example.com",
        ),
    )

    assert created_case.id is not None
    assert created_case.contact_email == "ops@example.com"
    assert created_case.urgency_level == "moderate"

    fetched_case = service.get_case(db_session, created_case.id)
    assert fetched_case.id == created_case.id

    updated_case = service.update_case(
        db_session,
        created_case.id,
        mode=None,
        raw_input="Updated case note",
        contact_email="dispatch@example.com",
    )
    assert updated_case.raw_input == "Updated case note"
    assert updated_case.contact_email == "dispatch@example.com"


def test_case_service_list_cases_returns_newest_first(db_session: Session) -> None:
    service = CaseService(Settings())
    service.create_case(db_session, CaseCreate(mode="auto_detect", raw_input="First case"))
    service.create_case(db_session, CaseCreate(mode="auto_detect", raw_input="Second case"))

    cases = service.list_cases(db_session)

    assert len(cases) == 2
    assert cases[0].created_at >= cases[1].created_at
