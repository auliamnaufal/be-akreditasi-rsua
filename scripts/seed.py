"""Seed default roles and admin user."""

from sqlmodel import Session, select

from src.app.db import engine
from src.app.models.role import Role
from src.app.models.user import User
from src.app.security.passwords import hash_password

DEFAULT_ROLES = {
    "perawat": "Perawat - dapat membuat laporan insiden",
    "pj": "Penanggung jawab unit - review awal",
    "mutu": "Tim mutu - review lanjutan",
    "admin": "Administrator sistem",
}


def run() -> None:
    with Session(engine) as session:
        existing_roles = {role.name for role in session.exec(select(Role)).all()}
        for name, description in DEFAULT_ROLES.items():
            if name not in existing_roles:
                session.add(Role(name=name, description=description))
        session.commit()

        admin = session.exec(select(User).where(User.email == "admin@rsua.local")).one_or_none()
        if not admin:
            admin_role = session.exec(select(Role).where(Role.name == "admin")).one()
            admin = User(
                email="admin@rsua.local",
                full_name="System Admin",
                hashed_password=hash_password("Admin123!"),
                is_active=True,
            )
            admin.roles.append(admin_role)
            session.add(admin)
            session.commit()


if __name__ == "__main__":
    run()
