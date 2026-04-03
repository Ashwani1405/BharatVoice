"""
Sprint 6 — Notification Tasks
Celery tasks for sending SMS via AWS SNS or Twilio upon transaction completion or KYC approval.
"""
# TODO: Sprint 6 — implement this module

from app.worker import celery_app

@celery_app.task
def send_sms_alert(phone_number: str, message: str):
    """
    Background task to send an SMS alert to a user.
    """
    raise NotImplementedError("Sprint 6: implement background SMS sending")
