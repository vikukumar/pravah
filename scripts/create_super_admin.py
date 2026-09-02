import argparse
import asyncio
import os
import sys
from pathlib import Path

# Add apps/api to path
api_dir = Path(__file__).resolve().parent.parent / "apps" / "api"
sys.path.insert(0, str(api_dir))
os.chdir(str(api_dir))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal, Base, engine
from app.models import *
from app.services.auth_service import AuthService
from app.services.billing_service import BillingService
from app.services.cms_service import CMSService
from app.services.organisation_service import OrganisationService
from app.services.rbac_service import RBACService
from app.services.social_service import SocialService

async def main():
    parser = argparse.ArgumentParser(description="Create or promote a Super Administrator on PRAVAH")
    parser.add_argument("--email", required=True, help="Super admin email address")
    parser.add_argument("--password", help="Password for new super admin user")
    parser.add_argument("--first-name", default="Super", help="First name")
    parser.add_argument("--last-name", default="Admin", help="Last name")
    args = parser.parse_args()

    email = args.email.lower().strip()

    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # 1. Seed system data
        rbac = RBACService(db)
        await rbac.seed_system_permissions_and_roles()
        billing = BillingService(db)
        await billing.seed_plans()
        social = SocialService(db)
        await social.seed_providers()
        cms = CMSService(db)
        await cms.seed_system_pages()

        # 2. Check if user already exists
        res = await db.execute(select(User).where(User.email == email))
        user = res.scalar_one_or_none()

        if user:
            user.is_super_admin = True
            user.is_verified = True
            user.is_active = True
            await db.commit()
            print(f"[SUCCESS] User '{email}' was already registered and is now a SUPER ADMINISTRATOR.")
        else:
            if not args.password:
                print("[ERROR] --password is required to create a new user.")
                sys.exit(1)

            auth_svc = AuthService(db)
            org_svc = OrganisationService(db)

            new_user = await auth_svc.register_user(
                email=email,
                password=args.password,
                first_name=args.first_name,
                last_name=args.last_name,
                is_super_admin=True,
                auto_verify=True,
            )

            # Create default workspace
            await org_svc.create_organisation(
                name=f"{args.first_name}'s Primary Workspace",
                user=new_user,
            )

            print(f"[SUCCESS] New SUPER ADMINISTRATOR '{email}' created successfully with primary workspace!")

if __name__ == "__main__":
    asyncio.run(main())
