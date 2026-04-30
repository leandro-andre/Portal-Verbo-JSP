import os


DJANGO_ENV = os.environ.get("DJANGO_ENV", "dev").strip().lower()

if DJANGO_ENV in {"prod", "production"}:
    from .settings_prod import *  # noqa: F401,F403
else:
    from .settings_dev import *  # noqa: F401,F403
