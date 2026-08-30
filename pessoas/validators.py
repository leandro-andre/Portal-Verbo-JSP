import re

from django.core.exceptions import ValidationError


INVALID_BRAZILIAN_MOBILE_MESSAGE = "Informe um celular/WhatsApp valido com DDD."


def normalize_brazilian_mobile(value):
    return re.sub(r"\D+", "", value or "")


def validate_brazilian_mobile(value):
    digits = normalize_brazilian_mobile(value)
    if not digits:
        return ""
    if len(digits) != 11 or digits[2] != "9":
        raise ValidationError(INVALID_BRAZILIAN_MOBILE_MESSAGE)
    return digits
