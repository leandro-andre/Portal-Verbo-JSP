from django.db import models


class DiaconiaModule(models.Model):
    class Meta:
        managed = False
        default_permissions = ()
        permissions = (
            ("view_diaconia_module", "Can view Diaconia module"),
        )
        verbose_name = "Modulo Diaconia"
        verbose_name_plural = "Modulo Diaconia"
