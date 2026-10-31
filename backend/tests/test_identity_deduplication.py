import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.db import Base
from app.models.person import Person
from app.database.schemas import PersonRecord
from app.services.person_service import PersonService, normalize_profile_url

@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_url_normalization():
    assert normalize_profile_url("https://www.linkedin.com/in/johndoe/") == "https://linkedin.com/in/johndoe"
    assert normalize_profile_url("https://LINKEDIN.COM/in/JaneDoe?trk=profile") == "https://linkedin.com/in/janedoe"
    assert normalize_profile_url(None) is None

def test_deduplication_by_profile_url(test_db):
    rec1 = PersonRecord(
        person_id="id-1",
        profile_url="https://www.linkedin.com/in/johndoe/",
        origin="crustdata_sourced",
        membership_status="not_registered",
        name="John Doe"
    )
    p1 = PersonService.get_or_create_person(test_db, rec1)

    rec2 = PersonRecord(
        person_id="id-2",
        profile_url="https://linkedin.com/in/johndoe",
        origin="crustdata_sourced",
        membership_status="not_registered",
        name="John Doe Updated"
    )
    p2 = PersonService.get_or_create_person(test_db, rec2)

    assert p1.id == p2.id
    assert test_db.query(Person).count() == 1

def test_registration_upgrades_sourced_person(test_db):
    # Ingest sourced person first
    rec = PersonRecord(
        person_id="sourced-1",
        profile_url="https://linkedin.com/in/alice",
        origin="crustdata_sourced",
        membership_status="not_registered",
        name="Alice"
    )
    PersonService.get_or_create_person(test_db, rec)
    assert test_db.query(Person).count() == 1

    # Candidate later signs up with the same profile URL
    reg_rec = PersonService.register_candidate(
        db=test_db,
        email="alice@example.com",
        name="Alice Smith",
        profile_url="https://www.linkedin.com/in/alice/",
        preferences={"remote_only": True}
    )

    assert reg_rec.membership_status == "registered"
    assert test_db.query(Person).count() == 1  # No duplicate created!
