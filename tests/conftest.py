import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select

from src.app.db import get_session
from src.app.main import app
from src.app.models.incident import Incident
from src.app.models.role import Role
from src.app.models.user import User
from src.app.security.passwords import hash_password

TEST_DB_URL = "sqlite:///:memory:"


def get_engine():
    return create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})


def create_roles(session: Session) -> None:
    roles = [
        Role(name="perawat", description="Perawat"),
        Role(name="pj", description="PJ"),
        Role(name="mutu", description="Mutu"),
        Role(name="admin", description="Admin"),
    ]
    session.add_all(roles)
    session.commit()


def create_user(session: Session, email: str, password: str, role_name: str) -> User:
    role = session.exec(select(Role).where(Role.name == role_name)).one()
    user = User(email=email, full_name=email.split("@")[0], hashed_password=hash_password(password), is_active=True)
    user.roles.append(role)
    session.add(user)
    session.commit()
    session.refresh(user)
    session.refresh(user, attribute_names=["roles"])
    return user


@pytest.fixture(name="engine")
def engine_fixture():
    engine = get_engine()
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="session")
def session_fixture(engine):
    with Session(engine) as session:
        create_roles(session)
        yield session
        session.rollback()


@pytest.fixture(name="client")
def client_fixture(session):
    def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def perawat_user(session):
    return create_user(session, "perawat@example.com", "Password123", "perawat")


@pytest.fixture
def pj_user(session):
    return create_user(session, "pj@example.com", "Password123", "pj")


@pytest.fixture
def mutu_user(session):
    return create_user(session, "mutu@example.com", "Password123", "mutu")


@pytest.fixture
def admin_user(session):
    return create_user(session, "admin@example.com", "Password123", "admin")
