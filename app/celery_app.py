try:
    from celery import Celery
except ImportError:
    Celery = None


if Celery is not None:
    celery_app = Celery(
        "user_service",
        broker="redis://redis:6379/0",
        backend="redis://redis:6379/0",
    )
    celery_app.conf.timezone = "UTC"

    @celery_app.task(name="send_email")
    def send_email(to_email: str, subject: str, message: str):
        print(f"Email task queued for {to_email}: {subject}")
else:
    class _SendEmailStub:
        def delay(self, to_email: str, subject: str, message: str):
            print(f"Email task skipped for {to_email}: {subject}")

    send_email = _SendEmailStub()
