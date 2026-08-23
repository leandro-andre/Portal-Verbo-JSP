from datetime import date, time

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import (
    CultoPadrao,
    Departamento,
    DepartamentoMembro,
    DepartmentMembership,
    DepartmentRole,
    Escala,
    EscalaItem,
    IndisponibilidadeMembro,
)
from .permissions import (
    get_departamentos_do_usuario,
    get_departamentos_gerenciaveis,
    usuario_eh_lider,
    usuario_pode_acessar_indisponibilidades,
    usuario_pode_acessar_departamentos,
    usuario_pertence_departamento,
    usuario_pode_criar_departamentos,
    usuario_pode_editar_propria_indisponibilidade,
    usuario_pode_gerenciar_cultos_padrao,
    usuario_pode_gerenciar_escalas,
    usuario_pode_gerenciar_membros,
)
from .services import (
    DEPARTMENT_MEMBERSHIP_ALREADY_EXISTS,
    DEPARTMENT_NOT_ACTIVE,
    DEPARTMENT_ROLE_MISMATCH,
    DEPARTMENT_ROLE_NOT_ACTIVE,
    INVALID_DEPARTMENT_TRANSITION,
    INVALID_DEPARTMENT_MEMBERSHIP_TRANSITION,
    INVALID_DEPARTMENT_ROLE_TRANSITION,
    PERSON_IS_NOT_ACTIVE_MEMBER,
    DepartmentError,
    create_department_membership,
    create_department_role,
    deactivate_department,
    deactivate_department_membership,
    deactivate_department_role,
    reactivate_department,
    reactivate_department_membership,
    reactivate_department_role,
)
from .selectors import (
    DEPARTMENT_INACTIVE as ELIGIBILITY_DEPARTMENT_INACTIVE,
    DEPARTMENT_MEMBERSHIP_ALREADY_EXISTS as ELIGIBILITY_MEMBERSHIP_ALREADY_EXISTS,
    DEPARTMENT_MEMBERSHIP_INACTIVE,
    DEPARTMENT_ROLE_INACTIVE,
    MEMBERSHIP_NOT_ACTIVE,
    NO_DEPARTMENT_MEMBERSHIP,
    get_department_entry_eligibility,
    get_department_membership_eligibility,
    get_person_department_eligibility,
)
from church_journey.models import ChurchJourney, DiscipleshipClass, DiscipleshipEnrollment
from church_journey.services import approve_membership, deactivate_membership, reactivate_membership
from pessoas.models import Person
from .utils import gerar_escalas_do_mes_para_departamento, membro_esta_indisponivel
from usuarios.roles import (
    PASTOR_GROUP,
    PORTAL_ADMIN_GROUP,
    SECRETARY_GROUP,
    get_role_codes,
    setup_portal_roles,
)


class DepartamentosModelsTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.maria = user_model.objects.create_user(
            username="maria.depto",
            password="senha-forte-123",
            first_name="Maria",
            last_name="Silva",
            email="maria.depto@example.com",
        )
        self.joao = user_model.objects.create_user(
            username="joao.depto",
            password="senha-forte-123",
            first_name="Joao",
            email="joao.depto@example.com",
        )

    def test_membro_pode_participar_de_varios_departamentos(self):
        infantil = Departamento.objects.create(nome="Infantil")
        louvor = Departamento.objects.create(nome="Louvor")

        DepartamentoMembro.objects.create(
            membro=self.maria,
            departamento=infantil,
            papel=DepartamentoMembro.Papel.LIDER,
        )
        DepartamentoMembro.objects.create(
            membro=self.maria,
            departamento=louvor,
            papel=DepartamentoMembro.Papel.VOLUNTARIO,
        )

        self.assertEqual(self.maria.participacoes_departamentais.count(), 2)
        self.assertEqual(self.maria.departamentos.count(), 2)

    def test_departamento_gera_codigo_estavel_para_modulos_do_sistema(self):
        secretaria = Departamento.objects.create(nome="Secretaria")
        midia = Departamento.objects.create(nome="Midia")
        infantil = Departamento.objects.create(nome="Departamento Infantil")

        self.assertEqual(secretaria.codigo, Departamento.CodigoSistema.SECRETARIA)
        self.assertEqual(midia.codigo, Departamento.CodigoSistema.MIDIA)
        self.assertEqual(infantil.codigo, Departamento.CodigoSistema.INFANTIL)

    def test_departamento_mantem_codigo_unico_para_nomes_genericos(self):
        primeiro = Departamento.objects.create(nome="Equipe de Apoio")
        segundo = Departamento.objects.create(nome="Equipe de Apoio 2", codigo="equipe-de-apoio")

        self.assertEqual(primeiro.codigo, "equipe-de-apoio")
        self.assertEqual(segundo.codigo, "equipe-de-apoio-2")

    def test_nao_permite_duas_participacoes_ativas_no_mesmo_departamento(self):
        infantil = Departamento.objects.create(nome="Infantil")
        DepartamentoMembro.objects.create(
            membro=self.maria,
            departamento=infantil,
            papel=DepartamentoMembro.Papel.LIDER,
            ativo=True,
        )

        with self.assertRaises(IntegrityError):
            DepartamentoMembro.objects.create(
                membro=self.maria,
                departamento=infantil,
                papel=DepartamentoMembro.Papel.MEMBRO,
                ativo=True,
            )

    def test_item_da_escala_precisa_pertencer_ao_mesmo_departamento(self):
        infantil = Departamento.objects.create(nome="Infantil")
        louvor = Departamento.objects.create(nome="Louvor")
        participacao = DepartamentoMembro.objects.create(
            membro=self.maria,
            departamento=infantil,
            papel=DepartamentoMembro.Papel.LIDER,
        )
        escala = Escala.objects.create(
            departamento=louvor,
            titulo="Escala de Domingo",
            data="2026-05-10",
            horario="19:00",
        )
        item = EscalaItem(
            escala=escala,
            participacao=participacao,
            funcao="Recepcao",
        )

        with self.assertRaises(ValidationError):
            item.full_clean()

    def test_item_da_escala_nao_permite_conflito_de_horario(self):
        infantil = Departamento.objects.create(nome="Infantil")
        louvor = Departamento.objects.create(nome="Louvor")
        participacao_infantil = DepartamentoMembro.objects.create(
            membro=self.maria,
            departamento=infantil,
            papel=DepartamentoMembro.Papel.LIDER,
        )
        participacao_louvor = DepartamentoMembro.objects.create(
            membro=self.maria,
            departamento=louvor,
            papel=DepartamentoMembro.Papel.VOLUNTARIO,
        )
        escala_infantil = Escala.objects.create(
            departamento=infantil,
            titulo="Escala Infantil",
            data="2026-05-10",
            horario="19:00",
            ativa=True,
        )
        escala_louvor = Escala.objects.create(
            departamento=louvor,
            titulo="Escala Louvor",
            data="2026-05-10",
            horario="19:00",
            ativa=True,
        )
        EscalaItem.objects.create(
            escala=escala_infantil,
            participacao=participacao_infantil,
            funcao="Recepcao",
        )
        item = EscalaItem(
            escala=escala_louvor,
            participacao=participacao_louvor,
            funcao="Vocal",
        )

        with self.assertRaises(ValidationError) as exc:
            item.full_clean()

        self.assertIn("ja esta escalado em Infantil", str(exc.exception))

    def test_indisponibilidade_valida_datas_horarios_e_utilitario(self):
        indisponibilidade = IndisponibilidadeMembro.objects.create(
            membro=self.maria,
            data_inicio=date(2026, 5, 10),
            data_fim=date(2026, 5, 12),
            horario_inicio=time(18, 0),
            horario_fim=time(21, 0),
            motivo="Viagem",
            ativo=True,
        )

        self.assertEqual(indisponibilidade.periodo_label, "10/05/2026 ate 12/05/2026 das 18:00 as 21:00")
        self.assertTrue(membro_esta_indisponivel(self.maria, data=date(2026, 5, 10), horario=time(19, 0)))
        self.assertFalse(membro_esta_indisponivel(self.maria, data=date(2026, 5, 10), horario=time(22, 0)))

        invalida = IndisponibilidadeMembro(
            membro=self.joao,
            data_inicio=date(2026, 5, 12),
            data_fim=date(2026, 5, 10),
        )
        with self.assertRaises(ValidationError):
            invalida.full_clean()

        horario_invalido = IndisponibilidadeMembro(
            membro=self.joao,
            data_inicio=date(2026, 5, 10),
            data_fim=date(2026, 5, 10),
            horario_inicio=time(20, 0),
            horario_fim=time(19, 0),
        )
        with self.assertRaises(ValidationError):
            horario_invalido.full_clean()

    def test_item_da_escala_bloqueia_membro_indisponivel(self):
        infantil = Departamento.objects.create(nome="Infantil Disponibilidade")
        participacao = DepartamentoMembro.objects.create(
            membro=self.maria,
            departamento=infantil,
            papel=DepartamentoMembro.Papel.LIDER,
        )
        escala = Escala.objects.create(
            departamento=infantil,
            titulo="Escala com bloqueio",
            data="2026-05-10",
            horario="19:00",
            ativa=True,
        )
        IndisponibilidadeMembro.objects.create(
            membro=self.maria,
            data_inicio="2026-05-10",
            data_fim="2026-05-10",
            horario_inicio="18:00",
            horario_fim="20:00",
            motivo="Compromisso familiar",
            ativo=True,
        )
        item = EscalaItem(
            escala=escala,
            participacao=participacao,
            funcao="Recepcao",
        )

        with self.assertRaises(ValidationError) as exc:
            item.full_clean()

        self.assertIn("indisponivel para servir", str(exc.exception))

    def test_escala_com_culto_padrao_exige_dia_e_horario_compativeis(self):
        departamento = Departamento.objects.create(nome="Louvor Culto")
        culto = CultoPadrao.objects.create(
            nome="Domingo Manha",
            dia_semana=CultoPadrao.DiaSemana.DOMINGO,
            horario="10:00",
            ativo=True,
        )
        escala = Escala(
            departamento=departamento,
            culto_padrao=culto,
            titulo="Domingo Manha",
            data="2026-05-04",
            horario="10:00",
            ativa=True,
        )

        with self.assertRaises(ValidationError):
            escala.full_clean()

        escala = Escala(
            departamento=departamento,
            culto_padrao=culto,
            titulo="Domingo Manha",
            data="2026-05-03",
            horario="11:00",
            ativa=True,
        )

        with self.assertRaises(ValidationError):
            escala.full_clean()

    def test_geracao_mensal_evita_duplicidade(self):
        departamento = Departamento.objects.create(nome="Midia Mensal")
        culto = CultoPadrao.objects.create(
            nome="Quinta-feira",
            dia_semana=CultoPadrao.DiaSemana.QUINTA,
            horario="20:00",
            ativo=True,
        )
        Escala.objects.create(
            departamento=departamento,
            culto_padrao=culto,
            titulo="Quinta-feira",
            data="2026-05-07",
            horario="20:00",
            ativa=True,
        )

        resultado = gerar_escalas_do_mes_para_departamento(
            departamento=departamento,
            ano=2026,
            mes=5,
            cultos_padroes=[culto],
        )

        self.assertEqual(len(resultado["criadas"]), 3)
        self.assertEqual(len(resultado["ignoradas"]), 1)


class DepartamentosDashboardTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="ana.departamento",
            password="senha-forte-123",
            first_name="Ana",
            email="ana.departamento@example.com",
        )

    def test_dashboard_exibe_departamentos_e_escalas_do_usuario(self):
        self.client.force_login(self.user)
        louvor = Departamento.objects.create(nome="Louvor")
        participacao = DepartamentoMembro.objects.create(
            membro=self.user,
            departamento=louvor,
            papel=DepartamentoMembro.Papel.VOLUNTARIO,
        )
        escala = Escala.objects.create(
            departamento=louvor,
            titulo="Escala de Louvor",
            data="2026-05-20",
            horario="18:30",
            ativa=True,
        )
        EscalaItem.objects.create(
            escala=escala,
            participacao=participacao,
            funcao="Vocal",
            confirmado=True,
        )

        response = self.client.get(reverse("usuarios:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Louvor")
        self.assertContains(response, "Escala de Louvor")
        self.assertContains(response, "Vocal")


class PermissionHelpersTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.lider = user_model.objects.create_user(
            username="lider.permissoes",
            password="senha-forte-123",
            first_name="Lider",
            email="lider.permissoes@example.com",
        )
        self.membro = user_model.objects.create_user(
            username="membro.permissoes",
            password="senha-forte-123",
            first_name="Membro",
            email="membro.permissoes@example.com",
        )
        self.staff = user_model.objects.create_user(
            username="staff.permissoes",
            password="senha-forte-123",
            first_name="Staff",
            email="staff.permissoes@example.com",
            is_staff=True,
        )
        self.pastor = user_model.objects.create_user(
            username="pastor.permissoes",
            password="senha-forte-123",
            first_name="Pastor",
            email="pastor.permissoes@example.com",
            eh_pastor=True,
        )
        self.infantil = Departamento.objects.create(nome="Infantil Permissoes")
        self.louvor = Departamento.objects.create(nome="Louvor Permissoes")
        DepartamentoMembro.objects.create(
            membro=self.lider,
            departamento=self.infantil,
            papel=DepartamentoMembro.Papel.LIDER,
            ativo=True,
        )
        DepartamentoMembro.objects.create(
            membro=self.lider,
            departamento=self.louvor,
            papel=DepartamentoMembro.Papel.VOLUNTARIO,
            ativo=True,
        )
        DepartamentoMembro.objects.create(
            membro=self.membro,
            departamento=self.infantil,
            papel=DepartamentoMembro.Papel.MEMBRO,
            ativo=True,
        )

    def test_usuario_pertence_departamento(self):
        self.assertTrue(usuario_pertence_departamento(self.lider, self.infantil))
        self.assertFalse(usuario_pertence_departamento(self.staff, self.infantil))

    def test_usuario_eh_lider(self):
        self.assertTrue(usuario_eh_lider(self.lider, self.infantil))
        self.assertFalse(usuario_eh_lider(self.lider, self.louvor))
        self.assertFalse(usuario_eh_lider(self.membro, self.infantil))
        self.assertFalse(usuario_eh_lider(self.pastor, self.infantil))

    def test_get_departamentos_do_usuario(self):
        departamentos = list(get_departamentos_do_usuario(self.lider).order_by("nome"))
        self.assertEqual(departamentos, [self.infantil, self.louvor])

    def test_get_departamentos_gerenciaveis(self):
        departamentos = list(get_departamentos_gerenciaveis(self.lider))
        self.assertEqual(departamentos, [self.infantil])
        self.assertEqual(
            set(get_departamentos_gerenciaveis(self.pastor)),
            {self.infantil, self.louvor},
        )

    def test_funcoes_de_gestao_respeitam_cargo(self):
        self.assertTrue(usuario_pode_gerenciar_membros(self.lider, self.infantil))
        self.assertTrue(usuario_pode_gerenciar_escalas(self.lider, self.infantil))
        self.assertFalse(usuario_pode_gerenciar_membros(self.lider, self.louvor))
        self.assertFalse(usuario_pode_gerenciar_escalas(self.lider, self.louvor))
        self.assertFalse(usuario_pode_gerenciar_membros(self.membro, self.infantil))
        self.assertFalse(usuario_pode_gerenciar_escalas(self.membro, self.infantil))
        self.assertTrue(usuario_pode_gerenciar_membros(self.pastor, self.infantil))
        self.assertTrue(usuario_pode_gerenciar_escalas(self.pastor, self.louvor))
        self.assertFalse(usuario_pode_criar_departamentos(self.staff))
        self.assertFalse(usuario_pode_gerenciar_cultos_padrao(self.staff))
        self.assertTrue(usuario_pode_criar_departamentos(self.pastor))
        self.assertTrue(usuario_pode_gerenciar_cultos_padrao(self.pastor))
        self.assertFalse(usuario_pode_criar_departamentos(self.lider))
        self.assertTrue(usuario_pode_acessar_indisponibilidades(self.membro))

    def test_acesso_a_departamentos_respeita_vinculo_ou_acesso_total(self):
        self.assertTrue(usuario_pode_acessar_departamentos(self.lider))
        self.assertTrue(usuario_pode_acessar_departamentos(self.membro))
        self.assertTrue(usuario_pode_acessar_departamentos(self.pastor))
        self.assertFalse(usuario_pode_acessar_departamentos(self.staff))


class IndisponibilidadesViewsTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.usuario = user_model.objects.create_user(
            username="indisponivel.usuario",
            password="senha-forte-123",
            first_name="Usuario",
            email="indisponivel.usuario@example.com",
        )
        self.outro_usuario = user_model.objects.create_user(
            username="outro.indisponivel",
            password="senha-forte-123",
            first_name="Outro",
            email="outro.indisponivel@example.com",
        )

    def test_usuario_logado_pode_cadastrar_e_ver_suas_indisponibilidades(self):
        self.client.force_login(self.usuario)

        response = self.client.post(
            reverse("usuarios:departamentos:indisponibilidade_nova"),
            {
                "data_inicio": "2026-05-01",
                "data_fim": "2026-05-02",
                "horario_inicio": "",
                "horario_fim": "",
                "motivo": "Viagem com a familia.",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        indisponibilidade = IndisponibilidadeMembro.objects.get(membro=self.usuario)
        self.assertContains(response, "Indisponibilidade cadastrada com sucesso")
        self.assertContains(response, "Viagem com a familia.")
        self.assertTrue(usuario_pode_editar_propria_indisponibilidade(self.usuario, indisponibilidade))

    def test_usuario_nao_pode_ver_ou_editar_indisponibilidades_de_outro(self):
        indisponibilidade = IndisponibilidadeMembro.objects.create(
            membro=self.outro_usuario,
            data_inicio="2026-05-03",
            data_fim="2026-05-03",
            motivo="Outro compromisso",
            ativo=True,
        )

        self.client.force_login(self.usuario)
        response = self.client.get(reverse("usuarios:departamentos:minhas_indisponibilidades"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Outro compromisso")

        edit = self.client.get(
            reverse("usuarios:departamentos:indisponibilidade_editar", args=[indisponibilidade.pk])
        )
        self.assertEqual(edit.status_code, 403)

    def test_usuario_pode_cancelar_propria_indisponibilidade(self):
        indisponibilidade = IndisponibilidadeMembro.objects.create(
            membro=self.usuario,
            data_inicio="2026-05-04",
            data_fim="2026-05-04",
            motivo="Consulta",
            ativo=True,
        )
        self.client.force_login(self.usuario)

        response = self.client.post(
            reverse("usuarios:departamentos:indisponibilidade_cancelar", args=[indisponibilidade.pk]),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        indisponibilidade.refresh_from_db()
        self.assertFalse(indisponibilidade.ativo)
        self.assertContains(response, "Indisponibilidade cancelada com sucesso")


class DepartamentosInternosViewsTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.lider = user_model.objects.create_user(
            username="lider.departamento",
            password="senha-forte-123",
            first_name="Lider",
            email="lider.departamento@example.com",
        )
        self.staff = user_model.objects.create_user(
            username="staff.departamento",
            password="senha-forte-123",
            first_name="Staff",
            email="staff.departamento@example.com",
            eh_pastor=True,
        )
        self.membro = user_model.objects.create_user(
            username="membro.comum",
            password="senha-forte-123",
            first_name="Membro",
            last_name="Comum",
            email="membro.comum@example.com",
        )
        self.departamento = Departamento.objects.create(
            nome="Infantil",
            descricao="Departamento infantil da igreja.",
            ativo=True,
        )
        DepartamentoMembro.objects.create(
            membro=self.lider,
            departamento=self.departamento,
            papel=DepartamentoMembro.Papel.LIDER,
            ativo=True,
        )
        DepartamentoMembro.objects.create(
            membro=self.membro,
            departamento=self.departamento,
            papel=DepartamentoMembro.Papel.MEMBRO,
            ativo=True,
        )

    def test_listagem_exige_vinculo_ou_permissao_global(self):
        outsider = get_user_model().objects.create_user(
            username="outsider.departamento",
            password="senha-forte-123",
        )
        self.client.force_login(outsider)

        response = self.client.get(reverse("usuarios:departamentos:lista"))

        self.assertEqual(response.status_code, 403)

    def test_listagem_filtra_por_nome_e_status(self):
        self.client.force_login(self.lider)
        Departamento.objects.create(nome="Louvor", ativo=False)

        response = self.client.get(
            reverse("usuarios:departamentos:lista"),
            {"q": "Inf", "status": "ativos"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Infantil")
        self.assertContains(response, "Lider")
        self.assertEqual(list(response.context["departamentos"]), [self.departamento])

    def test_membro_vinculado_pode_visualizar_departamentos_sem_gerenciar(self):
        self.client.force_login(self.membro)

        response = self.client.get(reverse("usuarios:departamentos:lista"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Infantil")
        self.assertContains(response, "Somente leitura")

    def test_cadastro_de_departamento_funciona(self):
        self.client.force_login(self.staff)

        response = self.client.post(
            reverse("usuarios:departamentos:novo"),
            {
                "nome": "Midia",
                "descricao": "Equipe de apoio tecnico.",
                "ativo": "on",
            },
            follow=True,
        )

        self.assertRedirects(response, reverse("usuarios:departamentos:lista"))
        self.assertTrue(Departamento.objects.filter(nome="Midia").exists())
        self.assertContains(response, "Departamento criado com sucesso")

    def test_gestao_de_membros_exige_lider_do_departamento(self):
        self.client.force_login(self.membro)

        response = self.client.get(reverse("usuarios:departamentos:membros", args=[self.departamento.pk]))

        self.assertEqual(response.status_code, 403)

    def test_tela_de_membros_adiciona_e_atualiza_vinculo(self):
        self.client.force_login(self.lider)

        response = self.client.post(
            reverse("usuarios:departamentos:membros", args=[self.departamento.pk]),
            {
                "membro": self.staff.pk,
                "papel": DepartamentoMembro.Papel.VOLUNTARIO,
                "ativo": "on",
                "data_entrada": "2026-04-23",
                "observacoes": "Chegou recentemente ao departamento.",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        participacao = DepartamentoMembro.objects.get(
            membro=self.staff,
            departamento=self.departamento,
        )
        self.assertEqual(participacao.papel, DepartamentoMembro.Papel.VOLUNTARIO)
        self.assertContains(response, "Membro vinculado ao departamento com sucesso")

        response = self.client.post(
            reverse("usuarios:departamentos:membros", args=[self.departamento.pk]),
            {
                "participacao_id": participacao.pk,
                "membro": self.staff.pk,
                "papel": DepartamentoMembro.Papel.VICE_LIDER,
                "ativo": "on",
                "data_entrada": "2026-04-23",
                "observacoes": "Assumiu apoio a lideranca.",
            },
            follow=True,
        )

        participacao.refresh_from_db()
        self.assertEqual(participacao.papel, DepartamentoMembro.Papel.VICE_LIDER)
        self.assertContains(response, "Vinculo atualizado com sucesso")

    def test_tela_de_membros_permite_desativar_vinculo(self):
        self.client.force_login(self.lider)
        participacao = DepartamentoMembro.objects.create(
            membro=self.staff,
            departamento=self.departamento,
            papel=DepartamentoMembro.Papel.MEMBRO,
            ativo=True,
        )

        response = self.client.post(
            reverse(
                "usuarios:departamentos:membro_status",
                args=[self.departamento.pk, participacao.pk],
            ),
            follow=True,
        )

        participacao.refresh_from_db()
        self.assertFalse(participacao.ativo)
        self.assertContains(response, "Vinculo desativado com sucesso")


class EscalasInternasViewsTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.lider = user_model.objects.create_user(
            username="lider.escala",
            password="senha-forte-123",
            first_name="Paulo",
            email="lider.escala@example.com",
            status_eclesiastico=user_model.StatusEclesiastico.MEMBRO,
        )
        self.outro_usuario = user_model.objects.create_user(
            username="visitante.escala",
            password="senha-forte-123",
            first_name="Visitante",
            email="visitante.escala@example.com",
        )
        self.membro = user_model.objects.create_user(
            username="maria.escala",
            password="senha-forte-123",
            first_name="Maria",
            last_name="Escalada",
            email="maria.escala@example.com",
            status_eclesiastico=user_model.StatusEclesiastico.MEMBRO,
        )
        self.departamento_louvor = Departamento.objects.create(
            nome="Louvor Escalas",
            ativo=True,
        )
        self.departamento_midia = Departamento.objects.create(
            nome="Midia Escalas",
            ativo=True,
        )
        self.departamento_infantil = Departamento.objects.create(
            nome="Infantil Escalas",
            ativo=True,
        )
        self.staff = user_model.objects.create_user(
            username="staff.culto",
            password="senha-forte-123",
            first_name="Staff",
            email="staff.culto@example.com",
            eh_pastor=True,
        )
        DepartamentoMembro.objects.create(
            membro=self.lider,
            departamento=self.departamento_louvor,
            papel=DepartamentoMembro.Papel.LIDER,
            ativo=True,
        )
        self.participacao_membro_louvor = DepartamentoMembro.objects.create(
            membro=self.membro,
            departamento=self.departamento_louvor,
            papel=DepartamentoMembro.Papel.VOLUNTARIO,
            ativo=True,
        )
        self.participacao_membro_midia = DepartamentoMembro.objects.create(
            membro=self.membro,
            departamento=self.departamento_midia,
            papel=DepartamentoMembro.Papel.VOLUNTARIO,
            ativo=True,
        )

    def test_listagem_de_escalas_exige_lideranca(self):
        self.client.force_login(self.outro_usuario)

        response = self.client.get(reverse("usuarios:departamentos:escala_lista"))

        self.assertEqual(response.status_code, 403)

    def test_listagem_exibe_apenas_departamentos_que_usuario_lidera(self):
        self.client.force_login(self.lider)
        escala_louvor = Escala.objects.create(
            departamento=self.departamento_louvor,
            titulo="Escala Louvor Domingo",
            data="2026-05-20",
            horario="19:00",
            ativa=True,
        )
        Escala.objects.create(
            departamento=self.departamento_midia,
            titulo="Escala Midia Domingo",
            data="2026-05-20",
            horario="19:00",
            ativa=True,
        )

        response = self.client.get(reverse("usuarios:departamentos:escala_lista"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Escala Louvor Domingo")
        self.assertEqual(list(response.context["escalas"]), [escala_louvor])

    def test_form_de_escala_restringe_departamentos_por_lideranca(self):
        self.client.force_login(self.lider)

        response = self.client.get(reverse("usuarios:departamentos:escala_nova"))

        queryset = response.context["form"].fields["departamento"].queryset
        self.assertEqual(list(queryset), [self.departamento_louvor])

    def test_nao_permite_criar_escala_em_departamento_sem_lideranca(self):
        self.client.force_login(self.lider)

        response = self.client.post(
            reverse("usuarios:departamentos:escala_nova"),
            {
                "departamento": self.departamento_midia.pk,
                "titulo": "Escala indevida",
                "data": "2026-05-21",
                "horario": "18:00",
                "observacoes": "",
                "ativa": "on",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Escala.objects.filter(titulo="Escala indevida").exists())

    def test_itens_da_escala_filtram_membros_do_departamento(self):
        self.client.force_login(self.lider)
        escala = Escala.objects.create(
            departamento=self.departamento_louvor,
            titulo="Escala de Teste",
            data="2026-05-22",
            horario="19:00",
            ativa=True,
        )

        response = self.client.get(reverse("usuarios:departamentos:escala_itens", args=[escala.pk]))

        queryset = response.context["form"].fields["participacao"].queryset
        self.assertEqual(
            list(queryset),
            [
                self.participacao_membro_louvor,
                DepartamentoMembro.objects.get(
                    membro=self.lider,
                    departamento=self.departamento_louvor,
                ),
            ],
        )

    def test_bloqueia_conflito_ao_adicionar_item_da_escala(self):
        DepartamentoMembro.objects.create(
            membro=self.lider,
            departamento=self.departamento_midia,
            papel=DepartamentoMembro.Papel.LIDER,
            ativo=True,
        )
        escala_louvor = Escala.objects.create(
            departamento=self.departamento_louvor,
            titulo="Escala Louvor 19h",
            data="2026-05-23",
            horario="19:00",
            ativa=True,
        )
        escala_midia = Escala.objects.create(
            departamento=self.departamento_midia,
            titulo="Escala Midia 19h",
            data="2026-05-23",
            horario="19:00",
            ativa=True,
        )
        EscalaItem.objects.create(
            escala=escala_louvor,
            participacao=self.participacao_membro_louvor,
            funcao="Vocal",
        )

        self.client.force_login(self.lider)
        response = self.client.post(
            reverse("usuarios:departamentos:escala_itens", args=[escala_midia.pk]),
            {
                "participacao": self.participacao_membro_midia.pk,
                "funcao": "Camera",
                "confirmado": "on",
                "observacoes": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ja esta escalado em Louvor Escalas")
        self.assertEqual(escala_midia.itens.count(), 0)

    def test_tela_da_escala_mostra_membros_indisponiveis(self):
        self.client.force_login(self.lider)
        escala = Escala.objects.create(
            departamento=self.departamento_louvor,
            titulo="Escala com alerta",
            data="2026-05-25",
            horario="19:00",
            ativa=True,
        )
        IndisponibilidadeMembro.objects.create(
            membro=self.membro,
            data_inicio="2026-05-25",
            data_fim="2026-05-25",
            horario_inicio="18:00",
            horario_fim="20:00",
            motivo="Plantao",
            ativo=True,
        )

        response = self.client.get(reverse("usuarios:departamentos:escala_itens", args=[escala.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Indisponiveis nesta data")
        self.assertContains(response, self.membro.get_full_name() or self.membro.username)

    def test_bloqueia_adicao_de_membro_indisponivel_na_escala(self):
        self.client.force_login(self.lider)
        escala = Escala.objects.create(
            departamento=self.departamento_louvor,
            titulo="Escala bloqueada por indisponibilidade",
            data="2026-05-26",
            horario="19:00",
            ativa=True,
        )
        IndisponibilidadeMembro.objects.create(
            membro=self.membro,
            data_inicio="2026-05-26",
            data_fim="2026-05-26",
            horario_inicio="18:00",
            horario_fim="20:00",
            motivo="Compromisso pessoal",
            ativo=True,
        )

        response = self.client.post(
            reverse("usuarios:departamentos:escala_itens", args=[escala.pk]),
            {
                "participacao": self.participacao_membro_louvor.pk,
                "funcao": "Vocal",
                "observacoes": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "indisponivel para servir")
        self.assertEqual(escala.itens.count(), 0)

    def test_staff_pode_gerenciar_cultos_padrao(self):
        self.client.force_login(self.staff)

        response = self.client.post(
            reverse("usuarios:departamentos:culto_padrao_novo"),
            {
                "nome": "Domingo Noite",
                "dia_semana": CultoPadrao.DiaSemana.DOMINGO,
                "horario": "18:00",
                "ativo": "on",
                "observacoes": "Culto principal da noite.",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(CultoPadrao.objects.filter(nome="Domingo Noite").exists())
        self.assertContains(response, "Culto padrao criado com sucesso")

    def test_lider_pode_gerar_escalas_do_mes_para_departamento_que_lidera(self):
        self.client.force_login(self.lider)
        culto_domingo = CultoPadrao.objects.create(
            nome="Domingo Manha",
            dia_semana=CultoPadrao.DiaSemana.DOMINGO,
            horario="10:00",
            ativo=True,
        )
        culto_quinta = CultoPadrao.objects.create(
            nome="Quinta-feira",
            dia_semana=CultoPadrao.DiaSemana.QUINTA,
            horario="20:00",
            ativo=True,
        )

        response = self.client.post(
            reverse("usuarios:departamentos:escala_gerar_mes"),
            {
                "departamento": self.departamento_louvor.pk,
                "mes": 5,
                "ano": 2026,
                "cultos_padrao": [culto_domingo.pk, culto_quinta.pk],
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Geracao concluida")
        self.assertTrue(
            Escala.objects.filter(
                departamento=self.departamento_louvor,
                culto_padrao=culto_domingo,
            ).exists()
        )
        self.assertTrue(
            Escala.objects.filter(
                departamento=self.departamento_louvor,
                culto_padrao=culto_quinta,
            ).exists()
        )

    def test_nova_escala_preenche_horario_a_partir_do_culto_padrao(self):
        self.client.force_login(self.lider)
        culto = CultoPadrao.objects.create(
            nome="Domingo Manha",
            dia_semana=CultoPadrao.DiaSemana.DOMINGO,
            horario="10:00",
            ativo=True,
        )

        response = self.client.post(
            reverse("usuarios:departamentos:escala_nova"),
            {
                "departamento": self.departamento_louvor.pk,
                "culto_padrao": culto.pk,
                "titulo": "",
                "data": "2026-05-03",
                "horario": "09:00",
                "observacoes": "",
                "ativa": "on",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        escala = Escala.objects.get(departamento=self.departamento_louvor, data="2026-05-03")
        self.assertEqual(escala.culto_padrao, culto)
        self.assertEqual(escala.titulo, "Domingo Manha")
        self.assertEqual(escala.horario.strftime("%H:%M"), "10:00")

    def test_lider_pode_criar_escala_personalizada_fora_do_padrao(self):
        self.client.force_login(self.lider)

        response = self.client.post(
            reverse("usuarios:departamentos:escala_nova"),
            {
                "departamento": self.departamento_louvor.pk,
                "culto_padrao": "",
                "titulo": "Vigilia especial",
                "data": "2026-05-29",
                "horario": "22:00",
                "observacoes": "Escala manual para evento especial.",
                "ativa": "on",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Escala.objects.filter(
                departamento=self.departamento_louvor,
                titulo="Vigilia especial",
                culto_padrao__isnull=True,
            ).exists()
        )

    def test_permite_remover_item_da_escala(self):
        self.client.force_login(self.lider)
        escala = Escala.objects.create(
            departamento=self.departamento_louvor,
            titulo="Escala para remover item",
            data="2026-05-24",
            horario="18:00",
            ativa=True,
        )
        item = EscalaItem.objects.create(
            escala=escala,
            participacao=self.participacao_membro_louvor,
            funcao="Backing vocal",
        )

        response = self.client.post(
            reverse("usuarios:departamentos:escala_item_remover", args=[escala.pk, item.pk]),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(EscalaItem.objects.filter(pk=item.pk).exists())
        self.assertContains(response, "Membro removido da escala com sucesso")


class DepartmentLifecycleServiceTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="department.lifecycle",
            password="senha-forte-123",
            status_eclesiastico=user_model.StatusEclesiastico.MEMBRO,
        )
        self.department = Departamento.objects.create(nome="Juniores")
        self.participacao = DepartamentoMembro.objects.create(
            membro=self.user,
            departamento=self.department,
            papel=DepartamentoMembro.Papel.LIDERADO,
            ativo=True,
        )
        self.escala = Escala.objects.create(
            departamento=self.department,
            titulo="Escala Juniores",
            data="2026-09-06",
            horario="18:00",
            ativa=True,
        )

    def test_deactivate_e_reactivate_preservam_relacoes_legadas(self):
        department_id = self.department.pk

        department = deactivate_department(self.department)

        self.assertEqual(department.pk, department_id)
        self.assertFalse(department.ativo)
        self.assertTrue(Departamento.objects.filter(pk=department_id).exists())
        self.assertTrue(DepartamentoMembro.objects.filter(pk=self.participacao.pk, ativo=True).exists())
        self.assertTrue(Escala.objects.filter(pk=self.escala.pk).exists())

        department = reactivate_department(department)

        self.assertEqual(department.pk, department_id)
        self.assertTrue(department.ativo)

    def test_transicoes_invalidas_retornam_erro(self):
        with self.assertRaises(DepartmentError) as active_ctx:
            reactivate_department(self.department)
        self.assertEqual(active_ctx.exception.code, INVALID_DEPARTMENT_TRANSITION)

        department = deactivate_department(self.department)
        with self.assertRaises(DepartmentError) as inactive_ctx:
            deactivate_department(department)
        self.assertEqual(inactive_ctx.exception.code, INVALID_DEPARTMENT_TRANSITION)


class DepartmentApiTests(APITestCase):
    def setUp(self):
        setup_portal_roles()
        self.user_model = get_user_model()
        self.department = Departamento.objects.create(
            nome="Louvor API",
            codigo="louvor-api",
            descricao="Equipe de louvor.",
        )
        self.admin = self.make_user_with_role("department.api.admin", PORTAL_ADMIN_GROUP)
        self.secretary = self.make_user_with_role("department.api.secretary", SECRETARY_GROUP)
        self.pastor = self.make_user_with_role("department.api.pastor", PASTOR_GROUP, eh_pastor=True)
        self.common = self.user_model.objects.create_user(
            username="department.api.common",
            password="senha-forte-123",
        )

    def make_user_with_role(self, username, group_name, **kwargs):
        usuario = self.user_model.objects.create_user(
            username=username,
            password="senha-forte-123",
            **kwargs,
        )
        usuario.groups.add(Group.objects.get(name=group_name))
        return usuario

    def test_list_e_detail(self):
        self.client.force_authenticate(self.pastor)

        list_response = self.client.get(reverse("department-list"))
        detail_response = self.client.get(reverse("department-detail", args=[self.department.pk]))

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.json()["codigo"], "louvor-api")
        self.assertNotIn("membros", detail_response.json())

    def test_list_filtra_status(self):
        Departamento.objects.create(nome="Inativo API", codigo="inativo-api", ativo=False)
        self.client.force_authenticate(self.admin)

        active_response = self.client.get(reverse("department-list"), {"status": "ACTIVE"})
        inactive_response = self.client.get(reverse("department-list"), {"status": "INACTIVE"})

        self.assertEqual({item["codigo"] for item in active_response.json()}, {"louvor-api"})
        self.assertEqual({item["codigo"] for item in inactive_response.json()}, {"inativo-api"})

    def test_create_department_nasce_ativo_e_normaliza_codigo(self):
        self.client.force_authenticate(self.secretary)

        response = self.client.post(
            reverse("department-list"),
            {
                "nome": "Juniores",
                "codigo": "Departamento Juniores",
                "descricao": "Equipe de juniores.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["codigo"], "departamento-juniores")
        self.assertTrue(response.json()["ativo"])
        self.assertTrue(Departamento.objects.get(codigo="departamento-juniores").ativo)

    def test_create_rejeita_overposting_status_e_membros(self):
        self.client.force_authenticate(self.admin)

        status_response = self.client.post(
            reverse("department-list"),
            {"nome": "Status Indevido", "codigo": "status-indevido", "ativo": False},
            format="json",
        )
        membros_response = self.client.post(
            reverse("department-list"),
            {"nome": "Membros Indevidos", "codigo": "membros-indevidos", "membros": [self.admin.pk]},
            format="json",
        )

        self.assertEqual(status_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(membros_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Departamento.objects.filter(codigo="status-indevido").exists())
        self.assertFalse(Departamento.objects.filter(codigo="membros-indevidos").exists())

    def test_create_valida_nome_e_codigo_unico(self):
        self.client.force_authenticate(self.admin)

        blank_response = self.client.post(
            reverse("department-list"),
            {"nome": "   ", "codigo": "novo-codigo"},
            format="json",
        )
        duplicate_response = self.client.post(
            reverse("department-list"),
            {"nome": "Outro Louvor", "codigo": "Louvor API"},
            format="json",
        )

        self.assertEqual(blank_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(duplicate_response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_permite_nome_descricao_e_codigo_eh_imutavel(self):
        self.client.force_authenticate(self.secretary)

        response = self.client.patch(
            reverse("department-detail", args=[self.department.pk]),
            {
                "nome": "Louvor Atualizado",
                "descricao": "Descricao nova.",
            },
            format="json",
        )
        codigo_response = self.client.patch(
            reverse("department-detail", args=[self.department.pk]),
            {"codigo": "outro-codigo"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["nome"], "Louvor Atualizado")
        self.assertEqual(response.json()["codigo"], "louvor-api")
        self.assertEqual(codigo_response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_lifecycle_api(self):
        self.client.force_authenticate(self.admin)

        deactivate_response = self.client.post(reverse("department-deactivate", args=[self.department.pk]))
        invalid_deactivate = self.client.post(reverse("department-deactivate", args=[self.department.pk]))
        reactivate_response = self.client.post(reverse("department-reactivate", args=[self.department.pk]))
        invalid_reactivate = self.client.post(reverse("department-reactivate", args=[self.department.pk]))

        self.assertEqual(deactivate_response.status_code, status.HTTP_200_OK)
        self.assertFalse(deactivate_response.json()["ativo"])
        self.assertEqual(invalid_deactivate.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(invalid_deactivate.json()["code"], INVALID_DEPARTMENT_TRANSITION)
        self.assertEqual(reactivate_response.status_code, status.HTTP_200_OK)
        self.assertTrue(reactivate_response.json()["ativo"])
        self.assertEqual(invalid_reactivate.status_code, status.HTTP_409_CONFLICT)

    def test_delete_nao_e_permitido(self):
        self.client.force_authenticate(self.admin)

        response = self.client.delete(reverse("department-detail", args=[self.department.pk]))

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertTrue(Departamento.objects.filter(pk=self.department.pk).exists())

    def test_permissions_por_global_role(self):
        for user in [self.admin, self.secretary]:
            self.client.force_authenticate(user)
            self.assertEqual(self.client.get(reverse("department-list")).status_code, status.HTTP_200_OK)
            self.assertEqual(
                self.client.post(
                    reverse("department-list"),
                    {"nome": f"Novo {user.username}", "codigo": f"novo-{user.pk}"},
                    format="json",
                ).status_code,
                status.HTTP_201_CREATED,
            )

        self.client.force_authenticate(self.pastor)
        self.assertEqual(self.client.get(reverse("department-list")).status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.client.patch(
                reverse("department-detail", args=[self.department.pk]),
                {"nome": "Pastor Change"},
                format="json",
            ).status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(
            self.client.post(reverse("department-deactivate", args=[self.department.pk])).status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.client.force_authenticate(self.common)
        self.assertEqual(self.client.get(reverse("department-list")).status_code, status.HTTP_403_FORBIDDEN)

    def test_secretaria_departamento_nao_atribui_global_role(self):
        secretaria = Departamento.objects.create(nome="Secretaria API", codigo=Departamento.CodigoSistema.SECRETARIA)
        usuario = self.user_model.objects.create_user(
            username="department.secretaria.member",
            password="senha-forte-123",
        )
        DepartamentoMembro.objects.create(
            membro=usuario,
            departamento=secretaria,
            papel=DepartamentoMembro.Papel.LIDER,
        )

        self.assertNotIn("SECRETARY", get_role_codes(usuario))
        self.assertFalse(usuario.groups.filter(name=SECRETARY_GROUP).exists())

    def test_midia_departamento_nao_cria_global_role(self):
        midia = Departamento.objects.create(nome="Midia API", codigo=Departamento.CodigoSistema.MIDIA)
        usuario = self.user_model.objects.create_user(
            username="department.midia.member",
            password="senha-forte-123",
        )
        DepartamentoMembro.objects.create(
            membro=usuario,
            departamento=midia,
            papel=DepartamentoMembro.Papel.LIDER,
        )

        self.assertEqual(get_role_codes(usuario), [])


class DepartmentRoleMembershipTests(APITestCase):
    def setUp(self):
        setup_portal_roles()
        self.user_model = get_user_model()
        self.admin = self.make_user_with_role("department.membership.admin", PORTAL_ADMIN_GROUP)
        self.secretary = self.make_user_with_role("department.membership.secretary", SECRETARY_GROUP)
        self.pastor = self.make_user_with_role("department.membership.pastor", PASTOR_GROUP, eh_pastor=True)
        self.common = self.user_model.objects.create_user(
            username="department.membership.common",
            password="senha-forte-123",
        )
        self.department = Departamento.objects.create(nome="Recepcao API", codigo="recepcao-api")
        self.other_department = Departamento.objects.create(nome="Intercessao API", codigo="intercessao-api")

    def make_user_with_role(self, username, group_name, **kwargs):
        usuario = self.user_model.objects.create_user(
            username=username,
            password="senha-forte-123",
            **kwargs,
        )
        usuario.groups.add(Group.objects.get(name=group_name))
        return usuario

    def make_person(self, name):
        return Person.objects.create(full_name=name, birth_date=date(1990, 1, 1))

    def make_active_member_person(self, name):
        person = self.make_person(name)
        teacher = self.make_person(f"Professor {name}")
        ChurchJourney.objects.create(person=person)
        discipleship_class = DiscipleshipClass.objects.create(
            name=f"Discipulado {name}",
            teacher=teacher,
            start_date=date(2026, 1, 1),
            expected_end_date=date(2026, 2, 1),
            planned_sessions=4,
            status=DiscipleshipClass.Status.COMPLETED,
        )
        DiscipleshipEnrollment.objects.create(
            person=person,
            discipleship_class=discipleship_class,
            status=DiscipleshipEnrollment.Status.COMPLETED,
            enrolled_at=date(2026, 1, 1),
            completed_at=date(2026, 2, 1),
        )
        approve_membership(person, approved_by=self.admin)
        return person

    def test_role_codigo_unico_por_departamento_e_permite_mesmo_codigo_em_outro(self):
        role = create_department_role(
            department=self.department,
            name="Lider",
            code="lider",
            can_manage_department=True,
            can_manage_members=True,
        )
        same_code_other_department = create_department_role(
            department=self.other_department,
            name="Lider",
            code="lider",
        )

        self.assertEqual(role.code, "lider")
        self.assertEqual(same_code_other_department.code, "lider")
        with self.assertRaises(DepartmentError):
            create_department_role(department=self.department, name="Outro Lider", code="lider")

    def test_role_lifecycle_e_codigo_imutavel_pela_api(self):
        role = create_department_role(department=self.department, name="Voluntario", code="voluntario")
        self.client.force_authenticate(self.admin)

        code_response = self.client.patch(
            reverse("department-role-detail", args=[self.department.pk, role.pk]),
            {"code": "novo-codigo"},
            format="json",
        )
        deactivate_response = self.client.post(
            reverse("department-role-deactivate", args=[self.department.pk, role.pk])
        )
        invalid_deactivate = self.client.post(
            reverse("department-role-deactivate", args=[self.department.pk, role.pk])
        )
        reactivate_response = self.client.post(
            reverse("department-role-reactivate", args=[self.department.pk, role.pk])
        )

        self.assertEqual(code_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(deactivate_response.status_code, status.HTTP_200_OK)
        self.assertFalse(deactivate_response.json()["active"])
        self.assertEqual(invalid_deactivate.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(invalid_deactivate.json()["code"], INVALID_DEPARTMENT_ROLE_TRANSITION)
        self.assertEqual(reactivate_response.status_code, status.HTTP_200_OK)

    def test_membership_exige_membresia_ativa_e_aceita_person_sem_usuario(self):
        person = self.make_active_member_person("Maria Sem Usuario")
        visitor = self.make_person("Visitante Departamento")
        role = create_department_role(department=self.department, name="Auxiliar", code="auxiliar")

        membership = create_department_membership(
            person=person,
            department=self.department,
            role=role,
        )

        self.assertFalse(hasattr(person, "user_account"))
        self.assertEqual(membership.status, DepartmentMembership.Status.ACTIVE)
        with self.assertRaises(DepartmentError) as ctx:
            create_department_membership(person=visitor, department=self.department, role=role)
        self.assertEqual(ctx.exception.code, PERSON_IS_NOT_ACTIVE_MEMBER)

    def test_membership_valida_departamento_role_e_unicidade(self):
        person = self.make_active_member_person("Joao Departamento")
        role = create_department_role(department=self.department, name="Equipe", code="equipe")
        other_role = create_department_role(department=self.other_department, name="Equipe", code="equipe")

        create_department_membership(person=person, department=self.department, role=role)

        with self.assertRaises(DepartmentError) as duplicate_ctx:
            create_department_membership(person=person, department=self.department, role=role)
        with self.assertRaises(DepartmentError) as mismatch_ctx:
            create_department_membership(person=person, department=self.department, role=other_role)

        self.assertEqual(duplicate_ctx.exception.code, DEPARTMENT_MEMBERSHIP_ALREADY_EXISTS)
        self.assertEqual(mismatch_ctx.exception.code, DEPARTMENT_ROLE_MISMATCH)
        self.assertTrue(
            create_department_membership(
                person=person,
                department=self.other_department,
                role=other_role,
            )
        )

    def test_membership_bloqueia_role_inativo_e_departamento_inativo(self):
        person = self.make_active_member_person("Ana Departamento")
        role = create_department_role(department=self.department, name="Equipe", code="equipe")

        deactivate_department_role(role)
        with self.assertRaises(DepartmentError) as role_ctx:
            create_department_membership(person=person, department=self.department, role=role)

        role = reactivate_department_role(role)
        deactivate_department(self.department)
        with self.assertRaises(DepartmentError) as department_ctx:
            create_department_membership(person=person, department=self.department, role=role)

        self.assertEqual(role_ctx.exception.code, DEPARTMENT_ROLE_NOT_ACTIVE)
        self.assertEqual(department_ctx.exception.code, DEPARTMENT_NOT_ACTIVE)

    def test_membership_lifecycle_preserva_joined_at_e_elegibilidade_operacional(self):
        person = self.make_active_member_person("Pedro Departamento")
        role = create_department_role(department=self.department, name="Equipe", code="equipe")
        membership = create_department_membership(
            person=person,
            department=self.department,
            role=role,
            joined_at=date(2026, 3, 10),
        )

        membership = deactivate_department_membership(membership)
        self.assertEqual(membership.status, DepartmentMembership.Status.INACTIVE)
        self.assertIsNotNone(membership.left_at)
        with self.assertRaises(DepartmentError) as invalid_ctx:
            deactivate_department_membership(membership)

        membership = reactivate_department_membership(membership)
        self.assertEqual(membership.joined_at, date(2026, 3, 10))
        self.assertIsNone(membership.left_at)
        deactivate_membership(person.membership, changed_by=self.admin, reason="Homologacao")

        self.client.force_authenticate(self.admin)
        response = self.client.get(reverse("department-membership-list", args=[self.department.pk]))
        self.assertEqual(invalid_ctx.exception.code, INVALID_DEPARTMENT_MEMBERSHIP_TRANSITION)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.json()[0]["operationally_eligible"])

    def test_api_global_roles_e_delete_405(self):
        role = create_department_role(department=self.department, name="Equipe", code="equipe")
        person = self.make_active_member_person("Clara Departamento")

        self.client.force_authenticate(self.pastor)
        self.assertEqual(
            self.client.get(reverse("department-role-list", args=[self.department.pk])).status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            self.client.post(
                reverse("department-membership-list", args=[self.department.pk]),
                {"person_id": person.pk, "role_id": role.pk},
                format="json",
            ).status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.client.force_authenticate(self.secretary)
        create_response = self.client.post(
            reverse("department-membership-list", args=[self.department.pk]),
            {"person_id": person.pk, "role_id": role.pk},
            format="json",
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            self.client.delete(reverse("department-role-detail", args=[self.department.pk, role.pk])).status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
        self.assertEqual(
            self.client.delete(
                reverse("department-membership-detail", args=[self.department.pk, create_response.json()["id"]])
            ).status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def test_permissao_contextual_por_flags_do_cargo(self):
        manager_person = self.make_active_member_person("Gestor Local")
        manager_user = self.user_model.objects.create_user(
            username="department.context.manager",
            password="senha-forte-123",
            person=manager_person,
        )
        manager_role = create_department_role(
            department=self.department,
            name="Coordenador",
            code="coordenador",
            can_manage_department=True,
            can_manage_members=True,
        )
        create_department_membership(
            person=manager_person,
            department=self.department,
            role=manager_role,
        )

        self.client.force_authenticate(manager_user)
        detail_response = self.client.get(reverse("department-detail", args=[self.department.pk]))
        update_response = self.client.patch(
            reverse("department-detail", args=[self.department.pk]),
            {"descricao": "Atualizada por gestor local."},
            format="json",
        )
        role_response = self.client.post(
            reverse("department-role-list", args=[self.department.pk]),
            {
                "name": "Novo cargo local",
                "code": "novo-cargo-local",
                "can_manage_department": False,
                "can_manage_members": False,
            },
            format="json",
        )

        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertTrue(detail_response.json()["permissions"]["can_manage_department"])
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(role_response.status_code, status.HTTP_201_CREATED)

    def test_operational_eligibility_retorna_resultado_estruturado(self):
        person = self.make_active_member_person("Elegivel Departamento")
        role = create_department_role(department=self.department, name="Professor", code="professor")
        membership = create_department_membership(person=person, department=self.department, role=role)

        eligibility = get_department_membership_eligibility(membership)

        self.assertTrue(eligibility.eligible)
        self.assertEqual(eligibility.as_dict(), {"eligible": True, "reasons": []})

    def test_operational_eligibility_acumula_multiplos_motivos(self):
        person = self.make_active_member_person("Multiplos Motivos")
        role = create_department_role(department=self.department, name="Auxiliar Motivos", code="auxiliar-motivos")
        membership = create_department_membership(person=person, department=self.department, role=role)

        membership = deactivate_department_membership(membership)
        deactivate_department_role(role)
        deactivate_department(self.department)
        deactivate_membership(person.membership, changed_by=self.admin, reason="Homologacao")

        reason_codes = {
            reason.code
            for reason in get_department_membership_eligibility(membership).reasons
        }

        self.assertEqual(
            reason_codes,
            {
                DEPARTMENT_MEMBERSHIP_INACTIVE,
                ELIGIBILITY_DEPARTMENT_INACTIVE,
                DEPARTMENT_ROLE_INACTIVE,
                MEMBERSHIP_NOT_ACTIVE,
            },
        )

    def test_person_department_eligibility_sem_vinculo(self):
        person = self.make_active_member_person("Sem Vinculo Departamento")

        eligibility = get_person_department_eligibility(person, self.department)

        self.assertFalse(eligibility.eligible)
        self.assertEqual(eligibility.reasons[0].code, NO_DEPARTMENT_MEMBERSHIP)

    def test_entry_eligibility_cobre_member_departamento_e_vinculo_existente(self):
        active_person = self.make_active_member_person("Candidata Departamento")
        visitor = self.make_person("Visitante Entry")
        inactive_member = self.make_active_member_person("Membro Inativo Entry")
        deactivate_membership(inactive_member.membership, changed_by=self.admin, reason="Homologacao")
        role = create_department_role(department=self.department, name="Entrada", code="entrada")

        self.assertTrue(get_department_entry_eligibility(active_person, self.department).eligible)
        self.assertEqual(
            get_department_entry_eligibility(visitor, self.department).reasons[0].code,
            MEMBERSHIP_NOT_ACTIVE,
        )
        self.assertEqual(
            get_department_entry_eligibility(inactive_member, self.department).reasons[0].code,
            MEMBERSHIP_NOT_ACTIVE,
        )

        create_department_membership(person=active_person, department=self.department, role=role)
        self.assertEqual(
            get_department_entry_eligibility(active_person, self.department).reasons[0].code,
            ELIGIBILITY_MEMBERSHIP_ALREADY_EXISTS,
        )

        inactive_department = Departamento.objects.create(nome="Departamento Entry Inativo", ativo=False)
        self.assertEqual(
            get_department_entry_eligibility(self.make_active_member_person("Entry Dept Inativo"), inactive_department)
            .reasons[0]
            .code,
            ELIGIBILITY_DEPARTMENT_INACTIVE,
        )

    def test_api_membership_retorna_eligibility_e_endpoint_de_candidatos(self):
        candidate = self.make_active_member_person("Candidata Sem Usuario")
        linked_person = self.make_active_member_person("Pessoa Ja Vinculada")
        visitor = self.make_person("Visitante Sem Membership")
        role = create_department_role(department=self.department, name="Recepcao", code="recepcao")
        membership = create_department_membership(person=linked_person, department=self.department, role=role)
        deactivate_membership(linked_person.membership, changed_by=self.admin, reason="Homologacao")

        self.client.force_authenticate(self.secretary)
        candidates_response = self.client.get(reverse("department-eligible-people", args=[self.department.pk]))
        members_response = self.client.get(reverse("department-membership-detail", args=[self.department.pk, membership.pk]))

        candidate_ids = {item["id"] for item in candidates_response.json()}
        self.assertEqual(candidates_response.status_code, status.HTTP_200_OK)
        self.assertIn(candidate.pk, candidate_ids)
        self.assertNotIn(linked_person.pk, candidate_ids)
        self.assertNotIn(visitor.pk, candidate_ids)
        self.assertEqual(members_response.status_code, status.HTTP_200_OK)
        self.assertFalse(members_response.json()["eligibility"]["eligible"])
        self.assertEqual(members_response.json()["eligibility"]["reasons"][0]["code"], MEMBERSHIP_NOT_ACTIVE)

    def test_lider_inelegivel_perde_autorizacao_contextual_e_recupera_ao_reativar_membership(self):
        manager_person = self.make_active_member_person("Gestor Inelegivel")
        manager_user = self.user_model.objects.create_user(
            username="department.context.ineligible",
            password="senha-forte-123",
            person=manager_person,
        )
        manager_role = create_department_role(
            department=self.department,
            name="Gestor",
            code="gestor",
            can_manage_members=True,
        )
        create_department_membership(person=manager_person, department=self.department, role=manager_role)

        self.client.force_authenticate(manager_user)
        allowed_response = self.client.post(
            reverse("department-role-list", args=[self.department.pk]),
            {"name": "Criado Contexto", "code": "criado-contexto"},
            format="json",
        )
        deactivate_membership(manager_person.membership, changed_by=self.admin, reason="Homologacao")
        denied_response = self.client.post(
            reverse("department-role-list", args=[self.department.pk]),
            {"name": "Bloqueado Contexto", "code": "bloqueado-contexto"},
            format="json",
        )
        manager_person.refresh_from_db()
        reactivate_membership(manager_person.membership, changed_by=self.admin, reason="Homologacao")
        restored_response = self.client.post(
            reverse("department-role-list", args=[self.department.pk]),
            {"name": "Restaurado Contexto", "code": "restaurado-contexto"},
            format="json",
        )

        self.assertEqual(allowed_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(denied_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(restored_response.status_code, status.HTTP_201_CREATED)

    def test_lider_perde_contexto_com_role_ou_departamento_inativo(self):
        manager_person = self.make_active_member_person("Gestor Role Inativo")
        manager_user = self.user_model.objects.create_user(
            username="department.context.role.inactive",
            password="senha-forte-123",
            person=manager_person,
        )
        manager_role = create_department_role(
            department=self.department,
            name="Gestor Role",
            code="gestor-role",
            can_manage_members=True,
        )
        membership = create_department_membership(person=manager_person, department=self.department, role=manager_role)
        deactivate_department_role(manager_role)

        self.client.force_authenticate(manager_user)
        role_inactive_response = self.client.get(reverse("department-role-list", args=[self.department.pk]))

        manager_role = reactivate_department_role(manager_role)
        membership.refresh_from_db()
        deactivate_department(self.department)
        department_inactive_response = self.client.get(reverse("department-role-list", args=[self.department.pk]))

        self.assertEqual(membership.status, DepartmentMembership.Status.ACTIVE)
        self.assertEqual(role_inactive_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(department_inactive_response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.secretary)
        self.assertEqual(
            self.client.get(reverse("department-role-list", args=[self.department.pk])).status_code,
            status.HTTP_200_OK,
        )
