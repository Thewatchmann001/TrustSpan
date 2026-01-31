"""
Migration script to backfill credentials from existing CV and startup data.

This script is safe to run multiple times (idempotent).
It checks for existing credentials before creating new ones.

Usage:
    python -m scripts.migrate_to_credentials
"""
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import (
    CV,
    Startup,
    Employee,
    User,
    Credential,
    CredentialType,
    CredentialSource,
    VerificationStatus,
)
from app.services.trust_service import CredentialService
from app.utils.logger import logger
from datetime import datetime
import json


def parse_date(date_str):
    """Parse date string to datetime object."""
    if not date_str:
        return None

    if isinstance(date_str, datetime):
        return date_str

    if isinstance(date_str, int):
        # Assume it's a year
        return datetime(date_str, 1, 1)

    # Try common date formats
    formats = ["%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%Y"]
    for fmt in formats:
        try:
            return datetime.strptime(str(date_str), fmt)
        except ValueError:
            continue

    return None


def migrate_cv_to_credentials(db: Session):
    """Migrate CV education and experience to credentials."""
    logger.info("Starting CV to credentials migration...")
    credential_service = CredentialService()
    cvs = db.query(CV).all()

    migrated_education = 0
    migrated_experience = 0
    skipped_education = 0
    skipped_experience = 0

    for cv in cvs:
        cv_data = cv.json_content or {}

        # Migrate education
        education = cv_data.get("education", [])
        if not isinstance(education, list):
            education = []

        for edu in education:
            if not isinstance(edu, dict):
                continue

            degree = edu.get("degree") or edu.get("qualification") or ""
            institution = edu.get("institution") or edu.get("school") or ""

            if not degree:
                continue

            # Check if credential already exists
            existing = (
                db.query(Credential)
                .filter(
                    Credential.user_id == cv.user_id,
                    Credential.type == CredentialType.EDUCATION,
                    Credential.title == degree,
                    Credential.organization == institution,
                )
                .first()
            )

            if existing:
                skipped_education += 1
                continue

            try:
                credential_service.create_credential(
                    db=db,
                    user_id=cv.user_id,
                    credential_type=CredentialType.EDUCATION,
                    title=degree,
                    organization=institution,
                    start_date=parse_date(edu.get("start_date")),
                    end_date=parse_date(
                        edu.get("graduation_year") or edu.get("end_date")
                    ),
                    description=edu.get("field_of_study", ""),
                    source=CredentialSource.SYSTEM_GENERATED,
                )
                migrated_education += 1
            except Exception as e:
                logger.error(f"Error migrating education: {e}")
                continue

        # Migrate experience
        experience = (
            cv_data.get("experience", [])
            or cv_data.get("work_experience", [])
            or []
        )
        if not isinstance(experience, list):
            experience = []

        for exp in experience:
            if not isinstance(exp, dict):
                continue

            job_title = exp.get("job_title") or exp.get("position") or ""
            company = exp.get("company") or exp.get("employer") or ""

            if not job_title and not company:
                continue

            # Check if credential already exists
            existing = (
                db.query(Credential)
                .filter(
                    Credential.user_id == cv.user_id,
                    Credential.type == CredentialType.EMPLOYMENT,
                    Credential.title == job_title,
                    Credential.organization == company,
                )
                .first()
            )

            if existing:
                skipped_experience += 1
                continue

            try:
                credential_service.create_credential(
                    db=db,
                    user_id=cv.user_id,
                    credential_type=CredentialType.EMPLOYMENT,
                    title=job_title or "Employee",
                    organization=company,
                    start_date=parse_date(exp.get("start_date")),
                    end_date=parse_date(exp.get("end_date")),
                    description=exp.get("description", ""),
                    source=CredentialSource.SYSTEM_GENERATED,
                )
                migrated_experience += 1
            except Exception as e:
                logger.error(f"Error migrating experience: {e}")
                continue

    logger.info(
        f"CV migration complete: {migrated_education} education, {migrated_experience} experience migrated. "
        f"Skipped {skipped_education} education, {skipped_experience} experience (already exist)."
    )
    return migrated_education + migrated_experience


def migrate_startup_roles_to_credentials(db: Session):
    """Migrate startup founder/employee roles to credentials."""
    logger.info("Starting startup roles to credentials migration...")
    credential_service = CredentialService()

    migrated_founders = 0
    migrated_employees = 0
    skipped_founders = 0
    skipped_employees = 0

    # Migrate founders
    startups = db.query(Startup).all()
    for startup in startups:
        # Check if credential already exists
        existing = (
            db.query(Credential)
            .filter(
                Credential.user_id == startup.founder_id,
                Credential.type == CredentialType.STARTUP_ROLE,
                Credential.title == "Founder",
                Credential.organization == startup.name,
            )
            .first()
        )

        if existing:
            skipped_founders += 1
            continue

        try:
            start_date = None
            if startup.year_founded:
                start_date = datetime(startup.year_founded, 1, 1)

            credential_service.create_credential(
                db=db,
                user_id=startup.founder_id,
                credential_type=CredentialType.STARTUP_ROLE,
                title="Founder",
                organization=startup.name,
                start_date=start_date,
                description=f"Founded {startup.name} in {startup.sector}",
                source=CredentialSource.SYSTEM_GENERATED,
            )
            migrated_founders += 1
        except Exception as e:
            logger.error(f"Error migrating founder credential: {e}")
            continue

    # Migrate employees
    employees = db.query(Employee).all()
    for emp in employees:
        startup = db.query(Startup).filter(Startup.id == emp.startup_id).first()
        if not startup:
            continue

        # Check if credential already exists
        existing = (
            db.query(Credential)
            .filter(
                Credential.user_id == emp.user_id,
                Credential.type == CredentialType.STARTUP_ROLE,
                Credential.organization == startup.name,
            )
            .first()
        )

        if existing:
            skipped_employees += 1
            continue

        try:
            credential_service.create_credential(
                db=db,
                user_id=emp.user_id,
                credential_type=CredentialType.STARTUP_ROLE,
                title=emp.role or "Employee",
                organization=startup.name,
                start_date=emp.start_date,
                description=f"Worked at {startup.name}",
                source=CredentialSource.SYSTEM_GENERATED,
            )
            migrated_employees += 1
        except Exception as e:
            logger.error(f"Error migrating employee credential: {e}")
            continue

    logger.info(
        f"Startup migration complete: {migrated_founders} founders, {migrated_employees} employees migrated. "
        f"Skipped {skipped_founders} founders, {skipped_employees} employees (already exist)."
    )
    return migrated_founders + migrated_employees


def main():
    """Run the migration."""
    db = SessionLocal()
    try:
        logger.info("=" * 60)
        logger.info("Starting credentials migration")
        logger.info("=" * 60)

        print("\n📋 Migrating CV data to credentials...")
        cv_count = migrate_cv_to_credentials(db)
        print(f"✓ CV migration complete: {cv_count} credentials created")

        print("\n🏢 Migrating startup roles to credentials...")
        startup_count = migrate_startup_roles_to_credentials(db)
        print(f"✓ Startup migration complete: {startup_count} credentials created")

        # Summary
        total_creds = db.query(Credential).count()
        print(f"\n✅ Migration complete!")
        print(f"   Total credentials in database: {total_creds}")
        print(f"   New credentials created: {cv_count + startup_count}")

        logger.info("=" * 60)
        logger.info("Migration completed successfully")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        print(f"\n❌ Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
