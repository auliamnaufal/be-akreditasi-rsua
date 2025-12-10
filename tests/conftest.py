import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from src.app.db import get_session
from src.app.main import app
from src.app.models.incident import Incident
from src.app.models.role import Role
from src.app.models.department import Department
from src.app.models.user import User
from src.app.security.passwords import hash_password

TEST_DB_URL = "sqlite:///:memory:"


def get_engine():
    return create_engine(TEST_DB_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)


def create_roles(session: Session) -> None:
    roles = [
        Role(name="perawat", description="Perawat"),
        Role(name="pj", description="PJ"),
        Role(name="mutu", description="Mutu"),
        Role(name="admin", description="Admin"),
    ]
    session.add_all(roles)
    session.commit()


def create_departments(session: Session) -> list[Department]:
    deps = [
        Department(name="Dept A", description="Test Department A"),
        Department(name="Dept B", description="Test Department B"),
    ]
    session.add_all(deps)
    session.commit()
    session.refresh(deps[0])
    session.refresh(deps[1])
    return deps


def create_user(session: Session, email: str, password: str, role_name: str, department_id: int | None = None) -> User:
    role = session.exec(select(Role).where(Role.name == role_name)).one()
    user = User(email=email, full_name=email.split("@")[0], hashed_password=hash_password(password), is_active=True)
    user.department_id = department_id
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
        deps = create_departments(session)
        session._test_departments = deps
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
    deps = getattr(session, "_test_departments")
    return create_user(session, "perawat@example.com", "Password123", "perawat", department_id=deps[0].id)


@pytest.fixture
def pj_user(session):
    deps = getattr(session, "_test_departments")
    return create_user(session, "pj@example.com", "Password123", "pj", department_id=deps[0].id)


@pytest.fixture
def mutu_user(session):
    deps = getattr(session, "_test_departments")
    return create_user(session, "mutu@example.com", "Password123", "mutu", department_id=deps[0].id)


@pytest.fixture
def admin_user(session):
    deps = getattr(session, "_test_departments")
    return create_user(session, "admin@example.com", "Password123", "admin", department_id=deps[0].id)
