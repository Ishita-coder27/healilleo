# app/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timezone, timedelta, date
from app.db.session import SessionLocal


def delete_expired_appointments(db):
    from app.models.appointments import Appointment
    now = datetime.now(timezone.utc)
    expired = db.query(Appointment).filter(Appointment.appointment_time < now).all()
    for appt in expired:
        db.delete(appt)
    if expired:
        print(f"[Scheduler] Deleted {len(expired)} expired appointment(s).")
    db.commit()


def delete_expired_medications(db):
    from app.models.medications import Medication
    today = date.today()
    expired = db.query(Medication).filter(
        Medication.end_date != None,
        Medication.end_date < today
    ).all()
    for med in expired:
        db.delete(med)
    if expired:
        print(f"[Scheduler] Deleted {len(expired)} expired medication(s).")
    db.commit()


def mark_appointment_reminders(db):
    from app.models.appointments import Appointment
    now         = datetime.now(timezone.utc)
    window_end  = now + timedelta(hours=1, minutes=5)
    due = db.query(Appointment).filter(
        Appointment.appointment_time >= now,
        Appointment.appointment_time <= window_end,
        Appointment.reminder_sent == False,
    ).all()
    for appt in due:
        appt.reminder_sent = True
        print(f"[Scheduler] Reminder marked for appointment: {appt.doctor_name} at {appt.appointment_time}")
    if due:
        db.commit()


def mark_medication_reminders(db):
    from app.models.medications import Medication
    now        = datetime.now(timezone.utc)
    window_end = now + timedelta(minutes=15, seconds=30)
    due = db.query(Medication).filter(
        Medication.next_reminder_time != None,
        Medication.next_reminder_time >= now,
        Medication.next_reminder_time <= window_end,
        Medication.reminder_sent == False,
    ).all()
    for med in due:
        med.reminder_sent = True
        print(f"[Scheduler] Reminder marked for medication: {med.medication_name}")
    if due:
        db.commit()


def run_cleanup():
    db = SessionLocal()
    try:
        delete_expired_appointments(db)
        delete_expired_medications(db)
    except Exception as e:
        print(f"[Scheduler] Cleanup error: {e}")
    finally:
        db.close()


def run_reminders():
    db = SessionLocal()
    try:
        mark_appointment_reminders(db)
        mark_medication_reminders(db)
    except Exception as e:
        print(f"[Scheduler] Reminder error: {e}")
    finally:
        db.close()


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        run_cleanup,
        trigger=IntervalTrigger(hours=1),
        id="cleanup_job",
        replace_existing=True,
    )
    scheduler.add_job(
        run_reminders,
        trigger=IntervalTrigger(minutes=1),
        id="reminder_job",
        replace_existing=True,
    )
    scheduler.start()
    print("[Scheduler] Started — cleanup every hour, reminders checked every minute.")
    return scheduler