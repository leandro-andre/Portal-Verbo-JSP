from django import forms
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import SiteConfig, SobrePage
from departamentos.models import Departamento, DepartamentoMembro
from eventos.models import Evento
from noticias.models import Noticia

from .forms import GovernedModelFormMixin
from .models import ConteudoAuditLog
from .permissions import (
    usuario_eh_midia,
    usuario_eh_secretaria,
    usuario_pode_editar_campo,
    usuario_pode_executar_acao_conteudo,
    usuario_pode_gerenciar_ao_vivo,
    usuario_pode_gerenciar_site_publico,
    usuario_tem_acesso_midia,
    usuario_tem_acesso_secretaria,
)


class SiteConfigGovernedForm(GovernedModelFormMixin, forms.ModelForm):
    class Meta:
        model = SiteConfig
        fields = ["nome_igreja", "youtube_embed_url"]


class GovernancaPermissionsTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.superuser = user_model.objects.create_superuser(
            username="admin.governanca",
            password="senha-forte-123",
            email="admin.governanca@example.com",
        )
        self.secretaria = user_model.objects.create_user(
            username="secretaria.lider",
            password="senha-forte-123",
            email="secretaria.lider@example.com",
            is_staff=True,
        )
        self.midia = user_model.objects.create_user(
            username="midia.lider",
            password="senha-forte-123",
            email="midia.lider@example.com",
            is_staff=True,
        )
        self.pastor = user_model.objects.create_user(
            username="pastor.negocio",
            password="senha-forte-123",
            email="pastor.negocio@example.com",
            eh_pastor=True,
        )
        self.sem_permissao = user_model.objects.create_user(
            username="usuario.sem.permissao",
            password="senha-forte-123",
            email="usuario.sem.permissao@example.com",
            is_staff=True,
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
            nome_igreja="Igreja Base",
            telefone="(81) 3000-0000",
            youtube_embed_url="https://www.youtube.com/watch?v=AAAA1111BBB",
        )
        self.sobre = SobrePage.load()
        self.evento = Evento.objects.create(
            titulo="Conferencia de Familias",
            descricao="Descricao inicial",
            data_inicio="2026-05-10",
            horario="19:00",
            local="Templo sede",
            tipo=Evento.TipoEvento.CONFERENCIA,
            publicado=True,
            destaque_home=False,
        )
        self.noticia = Noticia.objects.create(
            titulo="Noticia inicial",
            resumo="Resumo inicial",
            conteudo="Conteudo inicial",
            publicado=True,
            destaque_home=False,
        )

    def test_funcoes_utilitarias_por_departamento(self):
        self.assertTrue(usuario_eh_secretaria(self.secretaria))
        self.assertFalse(usuario_eh_secretaria(self.midia))
        self.assertTrue(usuario_eh_midia(self.midia))
        self.assertFalse(usuario_eh_midia(self.secretaria))
        self.assertFalse(usuario_eh_secretaria(self.pastor))
        self.assertFalse(usuario_eh_midia(self.pastor))
        self.assertFalse(usuario_eh_secretaria(self.superuser))
        self.assertFalse(usuario_eh_midia(self.superuser))

        self.assertTrue(usuario_pode_gerenciar_site_publico(self.secretaria))
        self.assertFalse(usuario_pode_gerenciar_site_publico(self.midia))

        self.assertTrue(usuario_pode_gerenciar_ao_vivo(self.secretaria))
        self.assertTrue(usuario_pode_gerenciar_ao_vivo(self.midia))
        self.assertFalse(usuario_pode_gerenciar_ao_vivo(self.sem_permissao))

    def test_acesso_nao_altera_identidade_de_secretaria_ou_midia(self):
        self.assertTrue(usuario_tem_acesso_secretaria(self.secretaria))
        self.assertFalse(usuario_tem_acesso_secretaria(self.midia))
        self.assertTrue(usuario_tem_acesso_midia(self.midia))
        self.assertFalse(usuario_tem_acesso_midia(self.secretaria))

        self.assertTrue(usuario_tem_acesso_secretaria(self.pastor))
        self.assertTrue(usuario_tem_acesso_midia(self.pastor))
        self.assertTrue(usuario_tem_acesso_secretaria(self.superuser))
        self.assertTrue(usuario_tem_acesso_midia(self.superuser))
        self.assertFalse(usuario_tem_acesso_secretaria(self.sem_permissao))
        self.assertFalse(usuario_tem_acesso_midia(self.sem_permissao))

    def test_permissoes_por_modelo_e_campo(self):
        self.assertTrue(usuario_pode_executar_acao_conteudo(self.secretaria, SiteConfig, "change"))
        self.assertTrue(usuario_pode_executar_acao_conteudo(self.midia, SiteConfig, "change"))
        self.assertFalse(usuario_pode_executar_acao_conteudo(self.midia, Evento, "change"))
        self.assertFalse(usuario_pode_executar_acao_conteudo(self.sem_permissao, Noticia, "change"))

        self.assertTrue(usuario_pode_editar_campo(self.secretaria, SiteConfig, "nome_igreja"))
        self.assertTrue(usuario_pode_editar_campo(self.secretaria, SiteConfig, "youtube_embed_url"))
        self.assertTrue(usuario_pode_editar_campo(self.midia, SiteConfig, "youtube_embed_url"))
        self.assertFalse(usuario_pode_editar_campo(self.midia, SiteConfig, "nome_igreja"))
        self.assertFalse(usuario_pode_editar_campo(self.midia, Evento, "titulo"))

    def test_form_mixin_bloqueia_campo_sem_permissao(self):
        form = SiteConfigGovernedForm(
            data={
                "nome_igreja": "Igreja Alterada",
                "youtube_embed_url": "https://youtu.be/BBBB2222CCC",
            },
            instance=self.site_config,
            request_user=self.midia,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("nome_igreja", form.errors)
        self.assertNotIn("youtube_embed_url", form.errors)


class GovernancaAdminTests(GovernancaPermissionsTests):
    def test_midia_ve_apenas_campo_de_ao_vivo_em_siteconfig(self):
        self.client.force_login(self.midia)

        response = self.client.get(
            reverse("admin:core_siteconfig_change", args=[self.site_config.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="youtube_embed_url"', html=False)
        self.assertNotContains(response, 'name="nome_igreja"', html=False)
        self.assertNotContains(response, 'name="telefone"', html=False)

    def test_midia_nao_consegue_alterar_outros_campos_do_siteconfig(self):
        self.client.force_login(self.midia)

        response = self.client.post(
            reverse("admin:core_siteconfig_change", args=[self.site_config.pk]),
            {
                "youtube_embed_url": "https://www.youtube.com/watch?v=CCCC3333DDD",
                "nome_igreja": "Nome malicioso",
                "_save": "Salvar",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)

        self.site_config.refresh_from_db()
        self.assertEqual(self.site_config.nome_igreja, "Igreja Base")
        self.assertEqual(
            self.site_config.youtube_embed_url,
            "https://www.youtube-nocookie.com/embed/CCCC3333DDD",
        )

        self.assertEqual(ConteudoAuditLog.objects.count(), 1)
        log = ConteudoAuditLog.objects.first()
        self.assertEqual(log.campo, "youtube_embed_url")
        self.assertEqual(log.usuario, self.midia)

    def test_midia_recebe_bloqueio_por_url_direta_em_eventos(self):
        self.client.force_login(self.midia)

        response = self.client.get(reverse("admin:eventos_evento_change", args=[self.evento.pk]))

        self.assertEqual(response.status_code, 403)

    def test_usuario_sem_permissao_recebe_bloqueio_no_siteconfig(self):
        self.client.force_login(self.sem_permissao)

        response = self.client.get(
            reverse("admin:core_siteconfig_change", args=[self.site_config.pk])
        )

        self.assertEqual(response.status_code, 403)

    def test_secretaria_pode_editar_evento_e_gera_auditoria(self):
        self.client.force_login(self.secretaria)

        response = self.client.post(
            reverse("admin:eventos_evento_change", args=[self.evento.pk]),
            {
                "titulo": "Conferencia de Familias Atualizada",
                "descricao": "Descricao revisada",
                "data_inicio": "2026-05-10",
                "horario": "19:00",
                "local": "Templo sede",
                "tipo": Evento.TipoEvento.CONFERENCIA,
                "destaque_home": "on",
                "_save": "Salvar",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)

        self.evento.refresh_from_db()
        self.assertEqual(self.evento.titulo, "Conferencia de Familias Atualizada")
        self.assertFalse(self.evento.publicado)
        self.assertTrue(self.evento.destaque_home)

        logs = ConteudoAuditLog.objects.filter(
            object_id=str(self.evento.pk),
            content_type__app_label="eventos",
            content_type__model="evento",
        )
        self.assertTrue(logs.filter(campo="titulo", acao=ConteudoAuditLog.Acao.UPDATE).exists())
        self.assertTrue(
            logs.filter(campo="publicado", acao=ConteudoAuditLog.Acao.UNPUBLISH).exists()
        )

    def test_superuser_tem_acesso_total(self):
        self.client.force_login(self.superuser)

        response = self.client.get(reverse("admin:noticias_noticia_change", args=[self.noticia.pk]))

        self.assertEqual(response.status_code, 200)
