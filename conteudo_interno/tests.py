from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import SiteConfig, SobrePage
from departamentos.models import Departamento, DepartamentoMembro
from eventos.models import Evento
from infantil.models import ChamadaResponsavel, SalaInfantil
from noticias.models import Noticia


class ConteudoInternoViewsTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.superuser = user_model.objects.create_superuser(
            username="super.conteudo",
            password="senha-forte-123",
            email="super.conteudo@example.com",
        )
        self.secretaria = user_model.objects.create_user(
            username="secretaria.conteudo",
            password="senha-forte-123",
            email="secretaria.conteudo@example.com",
        )
        self.midia = user_model.objects.create_user(
            username="midia.conteudo",
            password="senha-forte-123",
            email="midia.conteudo@example.com",
        )
        self.sem_permissao = user_model.objects.create_user(
            username="sem.permissao.conteudo",
            password="senha-forte-123",
            email="sem.permissao.conteudo@example.com",
        )

        secretaria = Departamento.objects.create(
            nome="Coordenacao de Conteudo",
            codigo=Departamento.CodigoSistema.SECRETARIA,
            ativo=True,
        )
        midia = Departamento.objects.create(
            nome="Transmissao e Projecao",
            codigo=Departamento.CodigoSistema.MIDIA,
            ativo=True,
        )
        louvor = Departamento.objects.create(nome="Louvor", ativo=True)

        DepartamentoMembro.objects.create(
            membro=self.secretaria,
            departamento=secretaria,
            papel=DepartamentoMembro.Papel.LIDER,
            ativo=True,
        )
        DepartamentoMembro.objects.create(
            membro=self.midia,
            departamento=midia,
            papel=DepartamentoMembro.Papel.LIDER,
            ativo=True,
        )
        DepartamentoMembro.objects.create(
            membro=self.sem_permissao,
            departamento=louvor,
            papel=DepartamentoMembro.Papel.MEMBRO,
            ativo=True,
        )

        self.site_config = SiteConfig.objects.create(
            nome_igreja="Igreja Teste",
            telefone="(81) 3000-0000",
            whatsapp="(81) 99999-0000",
            email="contato@teste.com",
            endereco="Rua Teste, 123",
            youtube_embed_url="https://www.youtube.com/watch?v=AAAA1111BBB",
        )
        self.sala_infantil = SalaInfantil.objects.create(
            nome="Bercario",
            descricao="Sala infantil do culto",
            idade_minima=0,
            idade_maxima=2,
            ativa=True,
        )
        self.chamada = ChamadaResponsavel.objects.create(
            sala=self.sala_infantil,
            numero_ficha="18",
            observacao="Precisa do responsavel no apoio.",
            criado_por=self.midia,
        )
        self.sobre = SobrePage.load()
        self.evento = Evento.objects.create(
            titulo="Culto especial",
            descricao="Descricao inicial",
            data="2026-05-10",
            horario="19:00",
            local="Templo",
            tipo=Evento.TipoEvento.CULTO,
            publicado=True,
            destaque_home=False,
        )
        self.noticia = Noticia.objects.create(
            titulo="Noticia teste",
            resumo="Resumo inicial",
            conteudo="Conteudo inicial",
            publicado=True,
            destaque_home=False,
        )

    def test_secretaria_pode_acessar_dashboard(self):
        self.client.force_login(self.secretaria)

        response = self.client.get(reverse("usuarios:conteudo:secretaria_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Painel da Secretaria")
        self.assertContains(response, "Gerenciar eventos")

    def test_secretaria_pode_editar_site_e_contato(self):
        self.client.force_login(self.secretaria)

        response = self.client.post(
            reverse("usuarios:conteudo:secretaria_site"),
            {
                "nome_igreja": "Igreja Atualizada",
                "telefone": "(81) 3111-1111",
                "whatsapp": "(81) 98888-1111",
                "email": "novo@teste.com",
                "endereco": "Rua Nova, 456",
                "instagram": "",
                "facebook": "",
                "texto_institucional": "Texto novo",
                "horarios_cultos": "Domingo 19:00",
                "youtube_embed_url": "https://youtu.be/BBBB2222CCC",
                "mapa_embed_url": "",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.site_config.refresh_from_db()
        self.assertEqual(self.site_config.nome_igreja, "Igreja Atualizada")
        self.assertEqual(
            self.site_config.youtube_embed_url,
            "https://www.youtube-nocookie.com/embed/BBBB2222CCC",
        )

        contato_response = self.client.post(
            reverse("usuarios:conteudo:secretaria_contato"),
            {
                "telefone": "(81) 3222-2222",
                "whatsapp": "(81) 97777-2222",
                "email": "contato2@teste.com",
                "endereco": "Rua Contato, 789",
                "horarios_cultos": "Quarta 20:00",
                "mapa_embed_url": "https://maps.google.com/example",
            },
            follow=True,
        )

        self.assertEqual(contato_response.status_code, 200)
        self.site_config.refresh_from_db()
        self.assertEqual(self.site_config.endereco, "Rua Contato, 789")

    def test_secretaria_form_site_exibe_uploads_de_hero(self):
        self.client.force_login(self.secretaria)

        response = self.client.get(reverse("usuarios:conteudo:secretaria_site"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="hero_home"', html=False)
        self.assertContains(response, 'name="hero_contato"', html=False)

    def test_secretaria_form_sobre_nao_duplica_campos_de_contato(self):
        self.client.force_login(self.secretaria)

        response = self.client.get(reverse("usuarios:conteudo:secretaria_sobre"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'name="horarios"', html=False)
        self.assertNotContains(response, 'name="endereco"', html=False)
        self.assertNotContains(response, 'name="telefone"', html=False)
        self.assertNotContains(response, 'name="whatsapp"', html=False)
        self.assertNotContains(response, 'name="email"', html=False)
        self.assertContains(response, "Contato e localizacao")

    def test_secretaria_pode_criar_e_publicar_evento_e_noticia(self):
        self.client.force_login(self.secretaria)

        evento_response = self.client.post(
            reverse("usuarios:conteudo:secretaria_evento_novo"),
            {
                "titulo": "Novo evento interno",
                "descricao": "Descricao do evento",
                "data": "2026-05-17",
                "horario": "20:00",
                "local": "Auditorio",
                "tipo": Evento.TipoEvento.EVENTO,
                "publicado": "",
                "destaque_home": "on",
            },
            follow=True,
        )
        self.assertEqual(evento_response.status_code, 200)
        evento = Evento.objects.get(titulo="Novo evento interno")

        publish_evento = self.client.post(
            reverse("usuarios:conteudo:secretaria_evento_status", args=[evento.pk]),
            follow=True,
        )
        self.assertEqual(publish_evento.status_code, 200)
        evento.refresh_from_db()
        self.assertTrue(evento.publicado)

        noticia_response = self.client.post(
            reverse("usuarios:conteudo:secretaria_noticia_nova"),
            {
                "titulo": "Nova noticia interna",
                "slug": "",
                "resumo": "Resumo",
                "conteudo": "Conteudo da noticia",
                "publicado": "",
                "destaque_home": "",
                "data_publicacao": "2026-05-17",
            },
            follow=True,
        )
        self.assertEqual(noticia_response.status_code, 200)
        noticia = Noticia.objects.get(titulo="Nova noticia interna")

        publish_noticia = self.client.post(
            reverse("usuarios:conteudo:secretaria_noticia_status", args=[noticia.pk]),
            follow=True,
        )
        self.assertEqual(publish_noticia.status_code, 200)
        noticia.refresh_from_db()
        self.assertTrue(noticia.publicado)

    def test_midia_pode_acessar_apenas_tela_ao_vivo(self):
        self.client.force_login(self.midia)

        response = self.client.get(reverse("usuarios:conteudo:midia_ao_vivo"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Transmissao Ao Vivo")
        self.assertNotContains(response, 'name="nome_igreja"', html=False)
        self.assertContains(response, "https://www.youtube-nocookie.com/embed/AAAA1111BBB")
        self.assertContains(response, "https://www.youtube.com/watch?v=AAAA1111BBB")
        self.assertContains(response, "Chamadas do Infantil")
        self.assertContains(response, "Bercario")
        self.assertContains(response, "Ficha 18")
        self.assertContains(response, "location.reload()")
        self.assertNotContains(response, "Resolvido")
        self.assertNotContains(response, 'name="hero_home"', html=False)

    def test_midia_nao_pode_acessar_secretaria(self):
        self.client.force_login(self.midia)

        dashboard = self.client.get(reverse("usuarios:conteudo:secretaria_dashboard"))
        eventos = self.client.get(reverse("usuarios:conteudo:secretaria_eventos"))

        self.assertEqual(dashboard.status_code, 403)
        self.assertEqual(eventos.status_code, 403)

    def test_midia_nao_consegue_alterar_outros_campos_por_post_manual(self):
        self.client.force_login(self.midia)

        response = self.client.post(
            reverse("usuarios:conteudo:midia_ao_vivo"),
            {
                "youtube_embed_url": "https://youtu.be/CCCC3333DDD",
                "nome_igreja": "Tentativa indevida",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.site_config.refresh_from_db()
        self.assertEqual(
            self.site_config.youtube_embed_url,
            "https://www.youtube-nocookie.com/embed/CCCC3333DDD",
        )
        self.assertEqual(self.site_config.nome_igreja, "Igreja Teste")

    def test_midia_preview_exibe_fallback_quando_link_for_invalido(self):
        self.site_config.youtube_embed_url = ""
        self.site_config.save(update_fields=["youtube_embed_url"])
        self.client.force_login(self.midia)

        response = self.client.post(
            reverse("usuarios:conteudo:midia_ao_vivo"),
            {
                "youtube_embed_url": "https://www.youtube.com/watch?v=curto",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Informe uma URL válida do YouTube com um vídeo válido.")
        self.assertContains(response, "Informe uma URL valida do YouTube para visualizar o preview.")
        self.assertContains(
            response,
            "Se o preview nao carregar, confirme no YouTube Studio se o video permite incorporacao.",
        )
        self.assertNotContains(response, "<iframe", html=False)

    def test_midia_pode_apenas_marcar_chamada_como_exibida(self):
        self.client.force_login(self.midia)

        exibido = self.client.post(
            reverse("usuarios:conteudo:midia_chamada_exibido", args=[self.chamada.pk]),
            follow=True,
        )

        self.assertEqual(exibido.status_code, 200)
        self.chamada.refresh_from_db()
        self.assertEqual(self.chamada.status, ChamadaResponsavel.Status.EXIBIDO)
        self.assertIsNotNone(self.chamada.exibido_em)

        resolvido = self.client.post(
            reverse("usuarios:conteudo:midia_chamada_resolvido", args=[self.chamada.pk]),
        )

        self.assertEqual(resolvido.status_code, 403)
        self.chamada.refresh_from_db()
        self.assertEqual(self.chamada.status, ChamadaResponsavel.Status.EXIBIDO)
        self.assertIsNone(self.chamada.resolvido_em)

    def test_endpoint_json_de_chamadas_exige_permissao_de_midia(self):
        self.client.force_login(self.midia)

        response = self.client.get(reverse("usuarios:conteudo:midia_chamadas_pendentes"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "chamadas": [
                    {
                        "id": self.chamada.pk,
                        "sala": "Bercario",
                        "numero_ficha": "18",
                        "status": "pendente",
                    }
                ]
            },
        )

        self.client.force_login(self.sem_permissao)
        forbidden = self.client.get(reverse("usuarios:conteudo:midia_chamadas_pendentes"))
        self.assertEqual(forbidden.status_code, 403)

    def test_usuario_sem_permissao_recebe_403(self):
        self.client.force_login(self.sem_permissao)

        secretaria = self.client.get(reverse("usuarios:conteudo:secretaria_dashboard"))
        midia = self.client.get(reverse("usuarios:conteudo:midia_ao_vivo"))

        self.assertEqual(secretaria.status_code, 403)
        self.assertEqual(midia.status_code, 403)

    def test_superuser_pode_acessar_tudo(self):
        self.client.force_login(self.superuser)

        secretaria = self.client.get(reverse("usuarios:conteudo:secretaria_dashboard"))
        midia = self.client.get(reverse("usuarios:conteudo:midia_ao_vivo"))

        self.assertEqual(secretaria.status_code, 200)
        self.assertEqual(midia.status_code, 200)
