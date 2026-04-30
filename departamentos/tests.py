from datetime import date, time

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from .models import (
    CultoPadrao,
    Departamento,
    DepartamentoMembro,
    Escala,
    EscalaItem,
    IndisponibilidadeMembro,
)
from .permissions import (
    get_departamentos_do_usuario,
    get_departamentos_gerenciaveis,
    usuario_eh_lider,
    usuario_pode_acessar_indisponibilidades,
    usuario_pertence_departamento,
    usuario_pode_criar_departamentos,
    usuario_pode_editar_propria_indisponibilidade,
    usuario_pode_gerenciar_cultos_padrao,
    usuario_pode_gerenciar_escalas,
    usuario_pode_gerenciar_membros,
)
from .utils import gerar_escalas_do_mes_para_departamento, membro_esta_indisponivel


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

    def test_get_departamentos_do_usuario(self):
        departamentos = list(get_departamentos_do_usuario(self.lider).order_by("nome"))
        self.assertEqual(departamentos, [self.infantil, self.louvor])

    def test_get_departamentos_gerenciaveis(self):
        departamentos = list(get_departamentos_gerenciaveis(self.lider))
        self.assertEqual(departamentos, [self.infantil])

    def test_funcoes_de_gestao_respeitam_cargo(self):
        self.assertTrue(usuario_pode_gerenciar_membros(self.lider, self.infantil))
        self.assertTrue(usuario_pode_gerenciar_escalas(self.lider, self.infantil))
        self.assertFalse(usuario_pode_gerenciar_membros(self.membro, self.infantil))
        self.assertFalse(usuario_pode_gerenciar_escalas(self.membro, self.infantil))
        self.assertTrue(usuario_pode_criar_departamentos(self.staff))
        self.assertTrue(usuario_pode_gerenciar_cultos_padrao(self.staff))
        self.assertFalse(usuario_pode_criar_departamentos(self.lider))
        self.assertTrue(usuario_pode_acessar_indisponibilidades(self.membro))


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
            is_staff=True,
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
            is_staff=True,
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
