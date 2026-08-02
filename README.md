# QRcard_project

## Docker

User service is self-contained inside `user_service`.

```bash
cd user_service
docker compose up --build
```

API будет доступен на `http://localhost:8001`.
Nginx gateway для микросервисов находится в `../nginx_gateway` и запускается на `http://localhost:8000`.

Celery использует Redis из compose-файла. SMTP-настройки для отправки писем задаются в `user_service/.env` по примеру `user_service/.env.example`.
