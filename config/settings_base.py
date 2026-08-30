from pathlib import Path

import dj_database_url

from .env import env, env_bool, env_list, load_env_file


BASE_DIR = Path(__file__).resolve().parent.parent
load_env_file(BASE_DIR / ".env")


SECRET_KEY = env("DJANGO_SECRET_KEY", "django-insecure-dev-only-key-change-me")

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", [])


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_extensions",
    "rest_framework",
    "governanca",
    "conteudo_interno",
    "church_journey",
    "usuarios",
    "pessoas",
    "worship",
    "scheduling",
    "core",
    "departamentos",
    "escalas",
    "infantil",
    "eventos",
    "noticias",
    "ministros",
    "verbo_no_lar",
    "financeiro",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.site_config",
                "usuarios.context_processors.internal_permissions",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


DATABASE_URL = env("DATABASE_URL") or env("DJANGO_DATABASE_URL", "")
DB_CONN_MAX_AGE = int(env("DJANGO_DB_CONN_MAX_AGE", "60"))

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=DB_CONN_MAX_AGE,
            ssl_require=env_bool("DJANGO_DB_SSL_REQUIRE", False),
        )
    }
else:
    db_engine = env("DJANGO_DB_ENGINE", "django.db.backends.sqlite3")
    db_name = env("DJANGO_DB_NAME", "db.sqlite3")
    if db_engine == "django.db.backends.sqlite3":
        db_name = str(BASE_DIR / db_name)
    DATABASES = {
        "default": {
            "ENGINE": db_engine,
            "NAME": db_name,
            "USER": env("DJANGO_DB_USER", ""),
            "PASSWORD": env("DJANGO_DB_PASSWORD", ""),
            "HOST": env("DJANGO_DB_HOST", ""),
            "PORT": env("DJANGO_DB_PORT", ""),
            "CONN_MAX_AGE": DB_CONN_MAX_AGE,
        }
    }


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True


AUTH_USER_MODEL = "usuarios.Usuario"

LOGIN_URL = "usuarios:login"
LOGIN_REDIRECT_URL = "usuarios:dashboard"
LOGOUT_REDIRECT_URL = "core:home"


STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
FRONTEND_DIST_DIR = BASE_DIR / "frontend" / "dist"
if FRONTEND_DIST_DIR.exists():
    STATICFILES_DIRS.append(FRONTEND_DIST_DIR)
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

REACT_BUILD_DIR = FRONTEND_DIST_DIR
SERVE_REACT_APP = env_bool("DJANGO_SERVE_REACT_APP", False)


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

X_FRAME_OPTIONS = "SAMEORIGIN"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": True,
        },
    },
}
