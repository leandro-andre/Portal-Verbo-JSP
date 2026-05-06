from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from departamentos.models import Departamento, DepartamentoMembro
from departamentos.permissions import usuario_pode_acessar_departamentos
from escalas.permissions import usuario_pode_acessar_escalas
from ministros.models import Ministro
from usuarios.context_processors import internal_permissions

from .permissions import (
    usuario_eh_lider_departamento,
    usuario_eh_lider_em_algum_departamento,
    usuario_eh_membro,
    usuario_eh_ministro,
    usuario_eh_pastor,
    usuario_eh_secretaria,
    usuario_eh_visitante,
    usuario_pode_montar_escala,
    usuario_pode_ser_escalado_verbo_no_lar,
    usuario_tem_acesso_midia,
    usuario_tem_acesso_secretaria,
    usuario_tem_acesso_tecnico_total,
    usuario_tem_acesso_total_pastoral,
    usuario_tem_acesso_total_sistema,
)


class UsuarioQualificacaoTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()

    def test_usuario_novo_nasce_como_visitante(self):
        usuario = self.user_model.objects.create_user(
            username="visitante",
            password="senha-forte-123",
        )

        self.assertTrue(usuario_eh_visitante(usuario))
        self.assertFalse(usuario_eh_membro(usuario))

    def test_qualificar_como_membro_registra_responsavel_e_data(self):
        secretaria = self.user_model.objects.create_user(
            username="secretaria",
            password="senha-forte-123",
            status_eclesiastico=self.user_model.StatusEclesiastico.MEMBRO,
        )
        visitante = self.user_model.objects.create_user(
            username="novo.membro",
            password="senha-forte-123",
        )

        visitante.qualificar_como_membro(secretaria)
        visitante.save()

        visitante.refresh_from_db()
        self.assertTrue(usuario_eh_membro(visitante))
        self.assertTrue(visitante.discipulado_concluido)
        self.assertEqual(visitante.qualificado_por, secretaria)
        self.assertIsNotNone(visitante.qualificado_em)

    def test_lideranca_vem_do_vinculo_departamental(self):
        lider = self.user_model.objects.create_user(
            username="lider",
            password="senha-forte-123",
            status_eclesiastico=self.user_model.StatusEclesiastico.MEMBRO,
        )
        departamento = Departamento.objects.create(nome="Louvor", codigo="louvor")
        DepartamentoMembro.objects.create(
            membro=lider,
            departamento=departamento,
            papel=DepartamentoMembro.Papel.LIDER,
        )

        self.assertTrue(usuario_eh_lider_departamento(lider, departamento))

    def test_ministro_vem_do_vinculo_ministerial(self):
        usuario = self.user_model.objects.create_user(
            username="ministro",
            password="senha-forte-123",
            status_eclesiastico=self.user_model.StatusEclesiastico.MEMBRO,
        )
        Ministro.objects.create(
            usuario=usuario,
            nome_completo="Ministro Teste",
            tipo=Ministro.Tipo.CASA,
            status=Ministro.Status.APROVADO,
            ativo=True,
        )

        self.assertTrue(usuario_eh_ministro(usuario))
        self.assertTrue(usuario_pode_ser_escalado_verbo_no_lar(usuario))

    def test_pastor_tem_acesso_total_pastoral_sem_ser_staff(self):
        pastor = self.user_model.objects.create_user(
            username="pastor",
            password="senha-forte-123",
            eh_pastor=True,
        )

        self.assertFalse(pastor.is_staff)
        self.assertTrue(usuario_eh_pastor(pastor))
        self.assertTrue(usuario_tem_acesso_total_pastoral(pastor))


class PermissoesPorPerfilTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.departamento = Departamento.objects.create(nome="Louvor Permissoes Globais")

        self.visitante = self.user_model.objects.create_user(
            username="perfil.visitante",
            password="senha-forte-123",
        )
        self.membro = self.user_model.objects.create_user(
            username="perfil.membro",
            password="senha-forte-123",
            status_eclesiastico=self.user_model.StatusEclesiastico.MEMBRO,
        )
        self.liderado = self.user_model.objects.create_user(
            username="perfil.liderado",
            password="senha-forte-123",
            status_eclesiastico=self.user_model.StatusEclesiastico.MEMBRO,
        )
        self.lider = self.user_model.objects.create_user(
            username="perfil.lider",
            password="senha-forte-123",
            status_eclesiastico=self.user_model.StatusEclesiastico.MEMBRO,
        )
        self.ministro = self.user_model.objects.create_user(
            username="perfil.ministro",
            password="senha-forte-123",
            status_eclesiastico=self.user_model.StatusEclesiastico.MEMBRO,
        )
        self.pastor = self.user_model.objects.create_user(
            username="perfil.pastor",
            password="senha-forte-123",
            eh_pastor=True,
        )
        self.superuser = self.user_model.objects.create_superuser(
            username="perfil.superuser",
            password="senha-forte-123",
            email="perfil.superuser@example.com",
        )

        DepartamentoMembro.objects.create(
            membro=self.liderado,
            departamento=self.departamento,
            papel=DepartamentoMembro.Papel.LIDERADO,
            ativo=True,
        )
        DepartamentoMembro.objects.create(
            membro=self.lider,
            departamento=self.departamento,
            papel=DepartamentoMembro.Papel.LIDER,
            ativo=True,
        )
        Ministro.objects.create(
            usuario=self.ministro,
            nome_completo="Ministro Perfil",
            tipo=Ministro.Tipo.CASA,
            status=Ministro.Status.APROVADO,
            ativo=True,
        )

    def test_identidades_globais_nao_confundem_acesso(self):
        self.assertTrue(usuario_eh_visitante(self.visitante))
        self.assertTrue(usuario_eh_membro(self.membro))
        self.assertTrue(usuario_eh_lider_departamento(self.lider, self.departamento))
        self.assertTrue(usuario_eh_lider_em_algum_departamento(self.lider))
        self.assertTrue(usuario_eh_ministro(self.ministro))
        self.assertTrue(usuario_eh_pastor(self.pastor))
        self.assertTrue(usuario_tem_acesso_tecnico_total(self.superuser))

        self.assertFalse(usuario_eh_secretaria(self.pastor))
        self.assertFalse(usuario_eh_lider_em_algum_departamento(self.pastor))
        self.assertFalse(usuario_eh_ministro(self.pastor))
        self.assertFalse(usuario_eh_pastor(self.superuser))

    def test_acesso_a_secretaria_por_perfil(self):
        self.assertFalse(usuario_tem_acesso_secretaria(self.visitante))
        self.assertFalse(usuario_tem_acesso_secretaria(self.membro))
        self.assertFalse(usuario_tem_acesso_secretaria(self.liderado))
        self.assertFalse(usuario_tem_acesso_secretaria(self.lider))
        self.assertFalse(usuario_tem_acesso_secretaria(self.ministro))
        self.assertTrue(usuario_tem_acesso_secretaria(self.pastor))
        self.assertTrue(usuario_tem_acesso_secretaria(self.superuser))

    def test_acesso_a_midia_por_perfil(self):
        self.assertFalse(usuario_tem_acesso_midia(self.visitante))
        self.assertFalse(usuario_tem_acesso_midia(self.membro))
        self.assertFalse(usuario_tem_acesso_midia(self.liderado))
        self.assertFalse(usuario_tem_acesso_midia(self.lider))
        self.assertFalse(usuario_tem_acesso_midia(self.ministro))
        self.assertTrue(usuario_tem_acesso_midia(self.pastor))
        self.assertTrue(usuario_tem_acesso_midia(self.superuser))

    def test_acesso_a_escalas_por_perfil(self):
        self.assertFalse(usuario_pode_acessar_escalas(self.visitante))
        self.assertFalse(usuario_pode_acessar_escalas(self.membro))
        self.assertFalse(usuario_pode_acessar_escalas(self.liderado))
        self.assertTrue(usuario_pode_acessar_escalas(self.lider))
        self.assertFalse(usuario_pode_acessar_escalas(self.ministro))
        self.assertTrue(usuario_pode_acessar_escalas(self.pastor))
        self.assertTrue(usuario_pode_acessar_escalas(self.superuser))

        self.assertTrue(usuario_pode_montar_escala(self.lider, self.departamento))
        self.assertTrue(usuario_pode_montar_escala(self.pastor, self.departamento))
        self.assertTrue(usuario_pode_montar_escala(self.superuser, self.departamento))
        self.assertFalse(usuario_pode_montar_escala(self.liderado, self.departamento))

    def test_acesso_a_departamentos_por_perfil(self):
        self.assertFalse(usuario_pode_acessar_departamentos(self.visitante))
        self.assertFalse(usuario_pode_acessar_departamentos(self.membro))
        self.assertTrue(usuario_pode_acessar_departamentos(self.liderado))
        self.assertTrue(usuario_pode_acessar_departamentos(self.lider))
        self.assertFalse(usuario_pode_acessar_departamentos(self.ministro))
        self.assertTrue(usuario_pode_acessar_departamentos(self.pastor))
        self.assertTrue(usuario_pode_acessar_departamentos(self.superuser))

    def test_acesso_total_do_sistema_e_apenas_pastoral_ou_tecnico(self):
        self.assertFalse(usuario_tem_acesso_total_sistema(self.visitante))
        self.assertFalse(usuario_tem_acesso_total_sistema(self.lider))
        self.assertFalse(usuario_tem_acesso_total_sistema(self.ministro))
        self.assertTrue(usuario_tem_acesso_total_sistema(self.pastor))
        self.assertTrue(usuario_tem_acesso_total_sistema(self.superuser))


class InternalPermissionsContextProcessorTests(TestCase):
    def test_context_processor_reutiliza_cache_por_request(self):
        user = get_user_model().objects.create_user(
            username="cache.context.processor",
            password="senha-forte-123",
        )
        request = SimpleNamespace(user=user)
        departamentos_do_usuario = Mock()
        departamentos_do_usuario.exists.return_value = False
        departamentos_gerenciaveis = Mock()
        departamentos_gerenciaveis.exists.return_value = False

        patches = (
            patch(
                "usuarios.context_processors.get_departamentos_do_usuario",
                return_value=departamentos_do_usuario,
            ),
            patch(
                "usuarios.context_processors.get_departamentos_gerenciaveis",
                return_value=departamentos_gerenciaveis,
            ),
            patch("usuarios.context_processors.usuario_pode_criar_departamentos", return_value=False),
            patch("usuarios.context_processors.usuario_pode_visualizar_infantil", return_value=False),
            patch("usuarios.context_processors.usuario_pode_acessar_painel_secretaria", return_value=False),
            patch("usuarios.context_processors.usuario_pode_acessar_painel_midia", return_value=False),
            patch("usuarios.context_processors.usuario_pode_gerenciar_eventos", return_value=False),
            patch("usuarios.context_processors.usuario_pode_gerenciar_ministros", return_value=False),
            patch("usuarios.context_processors.usuario_pode_acessar_verbo_no_lar", return_value=False),
            patch("usuarios.context_processors.usuario_pode_gerenciar_financeiro", return_value=False),
        )

        with patches[0] as get_departamentos, patches[1] as get_gerenciaveis, patches[2] as pode_criar, patches[
            3
        ], patches[4], patches[5], patches[6], patches[7], patches[8], patches[9]:
            first_result = internal_permissions(request)
            second_result = internal_permissions(request)

        self.assertIs(first_result, second_result)
        self.assertIs(request._internal_permissions_cache, first_result)
        get_departamentos.assert_called_once_with(user)
        get_gerenciaveis.assert_called_once_with(user)
        pode_criar.assert_called_once_with(user)
        self.assertFalse(first_result["can_view_departamentos"])
        self.assertFalse(first_result["can_manage_escalas"])
