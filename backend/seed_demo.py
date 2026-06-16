"""
Run once to seed a demo account with realistic health data.

Usage:
    cd backend
    python seed_demo.py

Demo credentials:
    Email:    demo@heallio.in
    Password: Demo@1234
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from app.db.session import SessionLocal
from app.models.user import User
from app.models.medications import Medication
from app.models.appointments import Appointment

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DEMO_EMAIL    = "demo@heallio.in"
DEMO_PASSWORD = "Demo@1234"

def run():
    db = SessionLocal()
    try:
        # ── 1. Create (or find) demo user ──────────────────────────
        user = db.query(User).filter(User.email == DEMO_EMAIL).first()
        if not user:
            user = User(
                name="Demo User",
                email=DEMO_EMAIL,
                hashed_password=pwd_context.hash(DEMO_PASSWORD),
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"[seed] Created user: {DEMO_EMAIL} (id={user.id})")
        else:
            print(f"[seed] User already exists: {DEMO_EMAIL} (id={user.id})")

        now = datetime.now(timezone.utc)

        # ── 2. Medications ─────────────────────────────────────────
        existing_meds = db.query(Medication).filter(Medication.user_id == user.id).count()
        if existing_meds == 0:
            meds = [
                Medication(
                    user_id=user.id,
                    medication_name="Metformin",
                    dosage="500mg",
                    frequency="Twice daily (after meals)",
                    start_date=(now - timedelta(days=30)).date(),
                    notes="For blood sugar management. Take with food.",
                    next_reminder_time=now + timedelta(hours=6),
                ),
                Medication(
                    user_id=user.id,
                    medication_name="Amlodipine",
                    dosage="5mg",
                    frequency="Once daily (morning)",
                    start_date=(now - timedelta(days=60)).date(),
                    notes="For blood pressure. Do not stop abruptly.",
                    next_reminder_time=now + timedelta(hours=2),
                ),
                Medication(
                    user_id=user.id,
                    medication_name="Vitamin D3",
                    dosage="60,000 IU",
                    frequency="Once weekly (Sunday)",
                    start_date=now.date(),
                    notes="Take with a fatty meal for better absorption.",
                    next_reminder_time=now + timedelta(days=5),
                ),
            ]
            for m in meds:
                db.add(m)
            db.commit()
            print(f"[seed] Added {len(meds)} medications.")
        else:
            print(f"[seed] Medications already exist ({existing_meds}), skipping.")

        # ── 3. Appointments ────────────────────────────────────────
        existing_appts = db.query(Appointment).filter(Appointment.user_id == user.id).count()
        if existing_appts == 0:
            appts = [
                Appointment(
                    user_id=user.id,
                    doctor_name="Dr. Priya Sharma",
                    clinic_name="Apollo Hospitals, Delhi",
                    appointment_time=now + timedelta(days=3, hours=10),
                    notes="Follow-up for diabetes management. Bring last 3 months blood sugar reports.",
                ),
                Appointment(
                    user_id=user.id,
                    doctor_name="Dr. Rajesh Kumar",
                    clinic_name="Fortis Heart Institute",
                    appointment_time=now + timedelta(days=14, hours=15, minutes=30),
                    notes="Annual cardiac checkup. ECG and echo required.",
                ),
            ]
            for a in appts:
                db.add(a)
            db.commit()
            print(f"[seed] Added {len(appts)} appointments.")
        else:
            print(f"[seed] Appointments already exist ({existing_appts}), skipping.")

        print("\n[seed] Done!")
        print(f"  Login with: {DEMO_EMAIL} / {DEMO_PASSWORD}")

    finally:
        db.close()

if __name__ == "__main__":
    run()
