try:
    import smtplib
    from email.message import EmailMessage

    from celery import Celery

    from app.config import config
except ImportError:
    Celery = None


if Celery is not None:
    celery_app = Celery(
        "user_service",
        broker=config.env_data.CELERY_BROKER_URL,
        backend=config.env_data.CELERY_RESULT_BACKEND,
    )
    celery_app.conf.update(
        timezone="UTC",
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        task_track_started=True,
    )

    @celery_app.task(name="send_email")
    def send_email(to_email: str, subject: str, message: str):
        env = config.env_data
        if not env.SMTP_HOST or not env.SMTP_FROM_EMAIL:
            print(f"Email task skipped for {to_email}: SMTP is not configured")
            return {"status": "skipped", "reason": "smtp_not_configured"}

        email = EmailMessage()
        email["From"] = env.SMTP_FROM_EMAIL
        email["To"] = to_email
        email["Subject"] = subject
        email.set_content(message)

        with smtplib.SMTP(env.SMTP_HOST, env.SMTP_PORT) as smtp:
            if env.SMTP_USE_TLS:
                smtp.starttls()
            if env.SMTP_USERNAME and env.SMTP_PASSWORD:
                smtp.login(env.SMTP_USERNAME, env.SMTP_PASSWORD)
            smtp.send_message(email)

        print(f"Email sent to {to_email}: {subject}")
        return {"status": "sent", "to": to_email}
else:
    class _SendEmailStub:
        def delay(self, to_email: str, subject: str, message: str):
            print(f"Email task skipped for {to_email}: {subject}")

    send_email = _SendEmailStub()
