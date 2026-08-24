from .env import env, env_bool, env_list
from .settings_base import *


DEBUG = env_bool("DJANGO_DEBUG", False)

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", [])
if not ALLOWED_HOSTS:
    raise RuntimeError("Defina DJANGO_ALLOWED_HOSTS para o ambiente de producao.")
if "*" in ALLOWED_HOSTS:
    raise RuntimeError("DJANGO_ALLOWED_HOSTS nao pode usar '*' em producao.")

if SECRET_KEY == "django-insecure-dev-only-key-change-me":
    raise RuntimeError("Defina DJANGO_SECRET_KEY para o ambiente de producao.")

if not DATABASE_URL:
    raise RuntimeError("Defina DATABASE_URL ou DJANGO_DATABASE_URL para o banco PostgreSQL de producao.")

CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS", [])

SERVE_REACT_APP = env_bool("DJANGO_SERVE_REACT_APP", True)

SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", False)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_HSTS_SECONDS = int(env("DJANGO_SECURE_HSTS_SECONDS", "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool(
    "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS",
    False,
)
SECURE_HSTS_PRELOAD = env_bool("DJANGO_SECURE_HSTS_PRELOAD", False)

if env_bool("DJANGO_USE_X_FORWARDED_PROTO", True):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

X_FRAME_OPTIONS = "DENY"
