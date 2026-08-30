R2_REQUIRED_ENV_VARS = (
    "R2_ACCESS_KEY_ID",
    "R2_SECRET_ACCESS_KEY",
    "R2_BUCKET_NAME",
    "R2_ENDPOINT_URL",
)


def build_media_storage_config(env):
    values = {name: (env(name, "") or "").strip() for name in R2_REQUIRED_ENV_VARS}
    configured = {name for name, value in values.items() if value}
    if not configured:
        return {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        }

    missing = [name for name in R2_REQUIRED_ENV_VARS if not values[name]]
    if missing:
        raise RuntimeError(
            "Configuracao Cloudflare R2 incompleta. Defina as variaveis: "
            + ", ".join(missing)
        )

    try:
        querystring_expire = int(env("R2_QUERYSTRING_EXPIRE", "3600"))
    except ValueError as exc:
        raise RuntimeError("R2_QUERYSTRING_EXPIRE deve ser um numero inteiro em segundos.") from exc

    return {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "access_key": values["R2_ACCESS_KEY_ID"],
            "secret_key": values["R2_SECRET_ACCESS_KEY"],
            "bucket_name": values["R2_BUCKET_NAME"],
            "endpoint_url": values["R2_ENDPOINT_URL"],
            "region_name": "auto",
            "signature_version": "s3v4",
            "default_acl": "private",
            "file_overwrite": False,
            "querystring_auth": True,
            "querystring_expire": querystring_expire,
            "object_parameters": {
                "CacheControl": env("R2_OBJECT_CACHE_CONTROL", "private, max-age=3600"),
            },
        },
    }
