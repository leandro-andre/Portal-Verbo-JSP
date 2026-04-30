from django.test import TestCase

from .models import Noticia


class NoticiaModelTests(TestCase):
    def test_gera_slug_unico_para_titulos_repetidos(self):
        primeira = Noticia.objects.create(
            titulo="Culto Especial",
            conteudo="Primeira noticia",
        )
        segunda = Noticia.objects.create(
            titulo="Culto Especial",
            conteudo="Segunda noticia",
        )

        self.assertEqual(primeira.slug, "culto-especial")
        self.assertEqual(segunda.slug, "culto-especial-2")
