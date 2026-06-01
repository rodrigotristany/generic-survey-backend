"""
Create an admin user.

Usage:
    python -m scripts.create_admin --email admin@example.com --password MyPass123! --role superadmin
"""
import argparse
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.admin_user import AdminUser, AdminRole
from app.utils.password import hash_password


async def create_admin(email: str, password: str, role: AdminRole) -> None:
    async with AsyncSessionLocal() as db:
        existing = (await db.execute(select(AdminUser).where(AdminUser.email == email))).scalar_one_or_none()
        if existing:
            print(f"Admin with email '{email}' already exists.")
            return

        admin = AdminUser(email=email, hashed_password=hash_password(password), role=role)
        db.add(admin)
        await db.commit()
        print(f"Admin created: {email} ({role.value})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an admin user")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--role", choices=[r.value for r in AdminRole], default=AdminRole.superadmin.value)
    args = parser.parse_args()

    asyncio.run(create_admin(args.email, args.password, AdminRole(args.role)))


if __name__ == "__main__":
    main()
