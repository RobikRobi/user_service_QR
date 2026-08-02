import os
import tempfile
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

os.environ.setdefault("USERS_DATABASE_URL", "postgresql://test:test@localhost/test")

if not os.environ.get("JWT_PRIVATE_KEY_PATH") or not os.environ.get("JWT_PUBLIC_KEY_PATH"):
    key_dir = Path(tempfile.mkdtemp(prefix="user-service-jwt-"))
    private_key_path = key_dir / "jwt-private.pem"
    public_key_path = key_dir / "jwt-public.pem"

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_key_path.write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    public_key_path.write_bytes(
        private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )

    os.environ["JWT_PRIVATE_KEY_PATH"] = str(private_key_path)
    os.environ["JWT_PUBLIC_KEY_PATH"] = str(public_key_path)
