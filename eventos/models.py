from django.db import models

class Evento(models.Model):

    class TipoEvento(models.TextChoices):
        CULTO = "culto", "Culto"
        EVENTO = "evento", "Evento"
        ENSINO = "ensino", "Ensino"
        CONFERENCIA = "conferencia", "Conferência"
        REUNIAO = "reuniao", "Reunião"
        USINA_DE_FORCA = "usina_de_forca", "Usina de Força"

    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)

    data = models.DateField()
    horario = models.TimeField()

    local = models.CharField(max_length=200, blank=True)

    tipo = models.CharField(
        max_length=20,
        choices=TipoEvento.choices,
        blank=True
    )

    imagem = models.ImageField(upload_to="eventos/", blank=True, null=True)

    publicado = models.BooleanField(default=True)
    destaque_home = models.BooleanField(default=False)

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["data", "horario"]
        verbose_name = "Evento"
        verbose_name_plural = "Eventos"

    def __str__(self) -> str:
        data_str = self.data.strftime("%d/%m/%Y") if self.data else "Sem data"
        return f"{self.titulo} ({data_str})"