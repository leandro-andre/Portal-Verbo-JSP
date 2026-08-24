from django.http import HttpResponseForbidden
from django.shortcuts import render


LEGACY_SCHEDULING_READ_ONLY = "LEGACY_SCHEDULING_READ_ONLY"
LEGACY_SCHEDULING_MESSAGE = "A gestao de escalas foi migrada para o novo Portal."
LEGACY_SCHEDULING_URL = "/escalas"


class LegacySchedulingReadOnlyMixin:
    legacy_title = "Gestao de escalas migrada"
    legacy_text = LEGACY_SCHEDULING_MESSAGE
    legacy_target_url = LEGACY_SCHEDULING_URL

    def dispatch(self, request, *args, **kwargs):
        if request.method == "GET":
            return render(
                request,
                "departamentos/legacy_scheduling_read_only.html",
                {
                    "active_section": "escalas",
                    "page_title": self.legacy_title,
                    "page_text": self.legacy_text,
                    "target_url": self.legacy_target_url,
                    "error_code": LEGACY_SCHEDULING_READ_ONLY,
                },
            )
        return legacy_scheduling_read_only_response()


def legacy_scheduling_read_only_response():
    return HttpResponseForbidden(LEGACY_SCHEDULING_READ_ONLY)
