from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from departamentos.models import Departamento, DepartamentoMembro

from .models import AulaSala, ChamadaResponsavel, Crianca, SalaInfantil, SalaMembro
from .permissions import (
    usuario_eh_lider_departamento_infantil,
    usuario_pode_acessar_minhas_criancas,
    usuario_pode_cancelar_chamada,
    usuario_pode_criar_chamada_responsavel,
    usuario_pode_editar_crianca_do_responsavel,
    usuario_pode_editar_sala,
    usuario_pode_gerenciar_aulas,
    usuario_pode_gerenciar_criancas,
    usuario_pode_gerenciar_equipe_sala,
    usuario_pode_marcar_chamada_exibida,
    usuario_pode_operar_chamadas_na_midia,
    usuario_pode_reenviar_chamada,
    usuario_pode_revisar_cadastros_infantis,
    usuario_pode_resolver_chamada,
    usuario_pode_ver_aulas,
    usuario_pode_ver_cadastro_crianca,
    usuario_pode_ver_chamadas_sala,
    usuario_pode_ver_criancas,
    usuario_pode_ver_crianca_do_responsavel,
    usuario_pode_ver_equipe_sala,
    usuario_pode_ver_sala,
)


class InfantilModelsTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.professor = user_model.objects.create_user(
            username="professor.infantil",
            password="senha-forte-123",
            first_name="Clara",
            email="clara@example.com",
        )
        self.auxiliar = user_model.objects.create_user(
            username="auxiliar.infantil",
            password="senha-forte-123",
            first_name="Lucas",
            email="lucas@example.com",
        )

    def test_sala_valida_faixa_etaria(self):
        sala = SalaInfantil(
            nome="Sala invalida",
            idade_minima=10,
            idade_maxima=7,
        )

        with self.assertRaises(ValidationError):
            sala.full_clean()

    def test_membro_pode_servir_em_varias_salas(self):
        sala_um = SalaInfantil.objects.create(
            nome="8 a 10 anos",
            idade_minima=8,
            idade_maxima=10,
        )
        sala_dois = SalaInfantil.objects.create(
            nome="11 a 13 anos",
            idade_minima=11,
            idade_maxima=13,
        )

        SalaMembro.objects.create(
            membro=self.professor,
            sala=sala_um,
            papel=SalaMembro.Papel.PROFESSOR,
        )
        SalaMembro.objects.create(
            membro=self.professor,
            sala=sala_dois,
            papel=SalaMembro.Papel.APOIO,
        )

        self.assertEqual(self.professor.participacoes_salas_infantis.count(), 2)

    def test_nao_permite_duas_participacoes_ativas_na_mesma_sala(self):
        sala = SalaInfantil.objects.create(
            nome="5 a 7 anos",
            idade_minima=5,
            idade_maxima=7,
        )
        SalaMembro.objects.create(
            membro=self.auxiliar,
            sala=sala,
            papel=SalaMembro.Papel.AUXILIAR,
            ativo=True,
        )

        with self.assertRaises(IntegrityError):
            SalaMembro.objects.create(
                membro=self.auxiliar,
                sala=sala,
                papel=SalaMembro.Papel.APOIO,
                ativo=True,
            )

    def test_crianca_sinaliza_alertas(self):
        sala = SalaInfantil.objects.create(
            nome="3 a 4 anos",
            idade_minima=3,
            idade_maxima=4,
        )
        crianca = Crianca.objects.create(
            nome="Ana Clara",
            data_nascimento=date(2019, 5, 10),
            responsavel_nome="Maria Clara",
            responsavel_telefone="81999999999",
            sala=sala,
            alergias="Alergia a amendoim",
        )

        self.assertTrue(crianca.possui_alertas)
        self.assertGreaterEqual(crianca.idade_atual, 0)

    def test_crianca_nao_aceita_data_de_nascimento_futura(self):
        sala = SalaInfantil.objects.create(
            nome="Bercario",
            idade_minima=0,
            idade_maxima=2,
        )
        crianca = Crianca(
            nome="Bebe",
            data_nascimento=date.today().replace(year=date.today().year + 1),
            responsavel_nome="Responsavel",
            responsavel_telefone="81999999999",
            sala=sala,
        )

        with self.assertRaises(ValidationError):
            crianca.full_clean()

    def test_aula_exige_texto_ou_anexo(self):
        sala = SalaInfantil.objects.create(
            nome="Pre-adolescentes",
            idade_minima=11,
            idade_maxima=13,
        )
        aula = AulaSala(
            sala=sala,
            data=date(2026, 4, 26),
            tema="Frutos do Espirito",
        )

        with self.assertRaises(ValidationError):
            aula.full_clean()

    def test_aula_nao_permite_duplicidade_na_mesma_data(self):
        sala = SalaInfantil.objects.create(
            nome="Sala Unica de Aula",
            idade_minima=8,
            idade_maxima=10,
        )
        AulaSala.objects.create(
            sala=sala,
            data=date(2026, 4, 26),
            tema="Aula 1",
            conteudo_licao="Conteudo principal",
        )

        with self.assertRaises(IntegrityError):
            AulaSala.objects.create(
                sala=sala,
                data=date(2026, 4, 26),
                tema="Aula 2",
                conteudo_licao="Outro conteudo",
            )

    def test_chamada_responsavel_muda_status_com_timestamps(self):
        sala = SalaInfantil.objects.create(
            nome="Bercario - Chamada",
            idade_minima=0,
            idade_maxima=2,
        )
        chamada = ChamadaResponsavel.objects.create(
            sala=sala,
            numero_ficha="18",
            criado_por=self.professor,
        )

        self.assertTrue(chamada.esta_ativa)
        chamada.marcar_exibido()
        chamada.refresh_from_db()
        self.assertEqual(chamada.status, ChamadaResponsavel.Status.EXIBIDO)
        self.assertIsNotNone(chamada.exibido_em)

        chamada.marcar_reenviado()
        chamada.refresh_from_db()
        self.assertEqual(chamada.status, ChamadaResponsavel.Status.PENDENTE)
        self.assertIsNotNone(chamada.reenviado_em)

        chamada.marcar_exibido()
        chamada.refresh_from_db()

        chamada.marcar_resolvido()
        chamada.refresh_from_db()
        self.assertEqual(chamada.status, ChamadaResponsavel.Status.RESOLVIDO)
        self.assertIsNotNone(chamada.resolvido_em)

        chamada = ChamadaResponsavel.objects.create(
            sala=sala,
            numero_ficha="19",
            criado_por=self.auxiliar,
        )
        chamada.marcar_cancelado()
        chamada.refresh_from_db()
        self.assertEqual(chamada.status, ChamadaResponsavel.Status.CANCELADO)
        self.assertIsNotNone(chamada.cancelado_em)


class InfantilPermissionsTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.staff = user_model.objects.create_user(
            username="staff.infantil",
            password="senha-forte-123",
            first_name="Staff",
            email="staff.infantil@example.com",
            eh_pastor=True,
        )
        self.lider_sala = user_model.objects.create_user(
            username="lider.sala.infantil",
            password="senha-forte-123",
            first_name="Lider",
            email="lider.sala@example.com",
        )
        self.lider_departamento = user_model.objects.create_user(
            username="lider.departamento.infantil",
            password="senha-forte-123",
            first_name="Lider Departamento",
            email="lider.departamento.infantil@example.com",
        )
        self.professor = user_model.objects.create_user(
            username="professor.sala.infantil",
            password="senha-forte-123",
            first_name="Professor",
            email="professor.sala@example.com",
        )
        self.auxiliar = user_model.objects.create_user(
            username="auxiliar.sala.infantil",
            password="senha-forte-123",
            first_name="Auxiliar",
            email="auxiliar.sala@example.com",
        )
        self.midia = user_model.objects.create_user(
            username="midia.infantil",
            password="senha-forte-123",
            first_name="Midia",
            email="midia.infantil@example.com",
        )
        self.outsider = user_model.objects.create_user(
            username="visitante.infantil",
            password="senha-forte-123",
            first_name="Visitante",
            email="visitante.infantil@example.com",
        )

        self.sala_um = SalaInfantil.objects.create(
            nome="8 a 10 anos - Interna",
            descricao="Sala principal",
            idade_minima=8,
            idade_maxima=10,
            ativa=True,
        )
        self.sala_dois = SalaInfantil.objects.create(
            nome="11 a 13 anos - Interna",
            descricao="Sala secundaria",
            idade_minima=11,
            idade_maxima=13,
            ativa=True,
        )
        self.departamento_infantil = Departamento.objects.create(
            nome="Ministerio Infantil",
            codigo=Departamento.CodigoSistema.INFANTIL,
            descricao="Departamento infantil da igreja",
            ativo=True,
        )
        self.departamento_midia = Departamento.objects.create(
            nome="Transmissao e Projecao",
            codigo=Departamento.CodigoSistema.MIDIA,
            descricao="Departamento de midia da igreja",
            ativo=True,
        )
        DepartamentoMembro.objects.create(
            membro=self.lider_departamento,
            departamento=self.departamento_infantil,
            papel=DepartamentoMembro.Papel.LIDER,
            ativo=True,
        )
        DepartamentoMembro.objects.create(
            membro=self.midia,
            departamento=self.departamento_midia,
            papel=DepartamentoMembro.Papel.LIDER,
            ativo=True,
        )

        SalaMembro.objects.create(
            membro=self.lider_sala,
            sala=self.sala_um,
            papel=SalaMembro.Papel.LIDER_SALA,
            ativo=True,
        )
        SalaMembro.objects.create(
            membro=self.professor,
            sala=self.sala_um,
            papel=SalaMembro.Papel.PROFESSOR,
            ativo=True,
        )

        self.crianca = Crianca.objects.create(
            nome="Samuel",
            data_nascimento=date(2017, 6, 15),
            responsavel_nome="Ana Paula",
            responsavel_telefone="81999999999",
            sala=self.sala_um,
            alergias="Alergia a lactose",
            ativo=True,
        )
        self.aula = AulaSala.objects.create(
            sala=self.sala_um,
            data=date(2026, 4, 26),
            tema="Jesus ama as criancas",
            texto_base="Marcos 10:14",
            conteudo_licao="Conteudo inicial da licao",
        )
        self.chamada = ChamadaResponsavel.objects.create(
            sala=self.sala_um,
            numero_ficha="18",
            criado_por=self.lider_sala,
        )

    def test_perfis_de_acesso_por_sala(self):
        self.assertTrue(usuario_pode_ver_sala(self.staff, self.sala_dois))
        self.assertTrue(usuario_pode_editar_sala(self.staff, self.sala_dois))
        self.assertTrue(usuario_pode_gerenciar_equipe_sala(self.staff, self.sala_dois))

        self.assertTrue(usuario_eh_lider_departamento_infantil(self.lider_departamento))
        self.assertTrue(usuario_pode_ver_sala(self.lider_departamento, self.sala_dois))
        self.assertTrue(usuario_pode_editar_sala(self.lider_departamento, self.sala_dois))
        self.assertTrue(usuario_pode_gerenciar_criancas(self.lider_departamento, self.sala_dois))
        self.assertTrue(usuario_pode_gerenciar_aulas(self.lider_departamento, self.sala_dois))

        self.assertTrue(usuario_pode_ver_sala(self.lider_sala, self.sala_um))
        self.assertFalse(usuario_pode_editar_sala(self.lider_sala, self.sala_um))
        self.assertTrue(usuario_pode_ver_equipe_sala(self.lider_sala, self.sala_um))
        self.assertFalse(usuario_pode_gerenciar_equipe_sala(self.lider_sala, self.sala_um))
        self.assertTrue(usuario_pode_gerenciar_criancas(self.lider_sala, self.sala_um))
        self.assertTrue(usuario_pode_gerenciar_aulas(self.lider_sala, self.sala_um))

        self.assertTrue(usuario_pode_ver_sala(self.professor, self.sala_um))
        self.assertTrue(usuario_pode_ver_criancas(self.professor, self.sala_um))
        self.assertTrue(usuario_pode_ver_aulas(self.professor, self.sala_um))
        self.assertTrue(usuario_pode_ver_chamadas_sala(self.professor, self.sala_um))
        self.assertTrue(usuario_pode_criar_chamada_responsavel(self.professor, self.sala_um))
        self.assertTrue(usuario_pode_cancelar_chamada(self.professor, self.chamada))
        self.assertFalse(usuario_pode_ver_equipe_sala(self.professor, self.sala_um))
        self.assertFalse(usuario_pode_gerenciar_criancas(self.professor, self.sala_um))
        self.assertFalse(usuario_pode_gerenciar_aulas(self.professor, self.sala_um))

        self.assertTrue(usuario_pode_operar_chamadas_na_midia(self.midia))
        self.assertTrue(usuario_pode_marcar_chamada_exibida(self.midia, self.chamada))
        self.assertFalse(usuario_pode_resolver_chamada(self.midia, self.chamada))
        self.assertFalse(usuario_pode_reenviar_chamada(self.professor, self.chamada))
        self.assertFalse(usuario_pode_ver_sala(self.outsider, self.sala_um))
        self.assertTrue(usuario_pode_acessar_minhas_criancas(self.outsider))
        self.assertFalse(usuario_pode_revisar_cadastros_infantis(self.outsider))


class InfantilInternoViewsTests(InfantilPermissionsTests):

    def test_listagem_exige_acesso_ao_modulo_infantil(self):
        self.client.force_login(self.outsider)

        response = self.client.get(reverse("usuarios:infantil:sala_lista"))

        self.assertEqual(response.status_code, 403)

    def test_equipe_visualiza_apenas_suas_salas(self):
        self.client.force_login(self.professor)

        response = self.client.get(reverse("usuarios:infantil:sala_lista"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["salas"]), [self.sala_um])
        self.assertContains(response, "Criancas")
        self.assertNotContains(response, self.sala_dois.nome)

    def test_lider_do_departamento_visualiza_todas_as_salas(self):
        self.client.force_login(self.lider_departamento)

        response = self.client.get(reverse("usuarios:infantil:sala_lista"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.sala_um.nome)
        self.assertContains(response, self.sala_dois.nome)
        self.assertContains(response, "Nova sala")
        self.assertContains(response, "Chamar Responsavel")

    def test_staff_pode_criar_sala(self):
        self.client.force_login(self.staff)

        response = self.client.post(
            reverse("usuarios:infantil:sala_nova"),
            {
                "nome": "3 a 5 anos - Nova",
                "descricao": "Sala nova do infantil",
                "idade_minima": 3,
                "idade_maxima": 5,
                "ativa": "on",
            },
            follow=True,
        )

        self.assertRedirects(response, reverse("usuarios:infantil:sala_lista"))
        self.assertTrue(SalaInfantil.objects.filter(nome="3 a 5 anos - Nova").exists())
        self.assertContains(response, "Sala criada com sucesso")

    def test_lider_do_departamento_pode_criar_sala(self):
        self.client.force_login(self.lider_departamento)

        response = self.client.post(
            reverse("usuarios:infantil:sala_nova"),
            {
                "nome": "14 a 16 anos - Nova",
                "descricao": "Sala criada pela lideranca do infantil",
                "idade_minima": 14,
                "idade_maxima": 16,
                "ativa": "on",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(SalaInfantil.objects.filter(nome="14 a 16 anos - Nova").exists())
        self.assertContains(response, "Sala criada com sucesso")

    def test_lider_de_sala_nao_pode_editar_dados_da_sala(self):
        self.client.force_login(self.lider_sala)

        response = self.client.get(reverse("usuarios:infantil:sala_editar", args=[self.sala_um.pk]))

        self.assertEqual(response.status_code, 403)

    def test_professor_pode_criar_chamada_e_cancelar_pendente(self):
        self.client.force_login(self.professor)

        response = self.client.post(
            reverse("usuarios:infantil:sala_chamadas", args=[self.sala_um.pk]),
            {
                "numero_ficha": "23",
                "observacao": "Responsavel solicitado na porta.",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        chamada = ChamadaResponsavel.objects.get(numero_ficha="23")
        self.assertEqual(chamada.sala, self.sala_um)
        self.assertEqual(chamada.criado_por, self.professor)
        self.assertContains(response, "Chamada enviada para a Midia com sucesso")

        cancel = self.client.post(
            reverse("usuarios:infantil:chamada_cancelar", args=[self.sala_um.pk, chamada.pk]),
            follow=True,
        )

        self.assertEqual(cancel.status_code, 200)
        chamada.refresh_from_db()
        self.assertEqual(chamada.status, ChamadaResponsavel.Status.CANCELADO)
        self.assertIsNotNone(chamada.cancelado_em)

    def test_equipe_do_infantil_pode_resolver_e_reenviar_chamada_exibida(self):
        self.chamada.marcar_exibido()
        self.client.force_login(self.professor)

        response = self.client.post(
            reverse("usuarios:infantil:chamada_reenviar", args=[self.sala_um.pk, self.chamada.pk]),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.chamada.refresh_from_db()
        self.assertEqual(self.chamada.status, ChamadaResponsavel.Status.PENDENTE)
        self.assertIsNotNone(self.chamada.reenviado_em)
        self.assertContains(response, "Chamada reenviada para exibicao na Midia.")

        self.chamada.marcar_exibido()
        resolve = self.client.post(
            reverse("usuarios:infantil:chamada_resolver", args=[self.sala_um.pk, self.chamada.pk]),
            follow=True,
        )

        self.assertEqual(resolve.status_code, 200)
        self.chamada.refresh_from_db()
        self.assertEqual(self.chamada.status, ChamadaResponsavel.Status.RESOLVIDO)
        self.assertIsNotNone(self.chamada.resolvido_em)

    def test_usuario_sem_vinculo_nao_pode_acessar_chamadas_da_sala(self):
        self.client.force_login(self.outsider)

        response = self.client.get(reverse("usuarios:infantil:sala_chamadas", args=[self.sala_um.pk]))

        self.assertEqual(response.status_code, 403)

    def test_acesso_a_equipe_respeita_perfis(self):
        self.client.force_login(self.professor)

        response = self.client.get(reverse("usuarios:infantil:sala_equipe", args=[self.sala_um.pk]))

        self.assertEqual(response.status_code, 403)

        self.client.force_login(self.lider_sala)
        response = self.client.get(reverse("usuarios:infantil:sala_equipe", args=[self.sala_um.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Adicionar membro")

        response = self.client.post(
            reverse("usuarios:infantil:sala_equipe", args=[self.sala_um.pk]),
            {
                "membro": self.auxiliar.pk,
                "papel": SalaMembro.Papel.APOIO,
                "ativo": "on",
                "observacoes": "Tentativa de alteracao por lider de sala.",
            },
        )
        self.assertEqual(response.status_code, 403)

        self.client.force_login(self.lider_departamento)
        response = self.client.post(
            reverse("usuarios:infantil:sala_equipe", args=[self.sala_um.pk]),
            {
                "membro": self.staff.pk,
                "papel": SalaMembro.Papel.APOIO,
                "ativo": "on",
                "observacoes": "Apoio eventual na sala.",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            SalaMembro.objects.filter(
                membro=self.staff,
                sala=self.sala_um,
                papel=SalaMembro.Papel.APOIO,
            ).exists()
        )
        self.assertContains(response, "Membro adicionado a equipe da sala")

    def test_lider_de_sala_pode_cadastrar_crianca_e_ver_detalhes(self):
        self.client.force_login(self.lider_sala)

        response = self.client.post(
            reverse("usuarios:infantil:crianca_nova", args=[self.sala_um.pk]),
            {
                "nome": "Maria",
                "data_nascimento": "2018-08-20",
                "sexo": "",
                "responsavel_nome": "Carlos",
                "responsavel_telefone": "81888888888",
                "responsavel_email": "",
                "observacoes_gerais": "Chega cedo.",
                "alergias": "",
                "restricoes_alimentares": "Sem gluten",
                "necessidades_especiais": "",
                "pode_comer_lanche_igreja": "True",
                "medicacao_ou_cuidado_especial": "",
                "observacao_para_professor": "",
                "ativo": "on",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        crianca = Crianca.objects.get(nome="Maria")
        self.assertContains(response, "Crianca cadastrada com sucesso")

        detail = self.client.get(reverse("usuarios:infantil:crianca_detail", args=[crianca.pk]))

        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, "Restricoes alimentares")
        self.assertContains(detail, "Sem gluten")

    def test_professor_apenas_visualiza_criancas(self):
        self.client.force_login(self.professor)

        response = self.client.post(
            reverse("usuarios:infantil:crianca_nova", args=[self.sala_um.pk]),
            {
                "nome": "Maria",
                "data_nascimento": "2018-08-20",
                "sexo": "",
                "responsavel_nome": "Carlos",
                "responsavel_telefone": "81888888888",
                "responsavel_email": "",
                "observacoes_gerais": "Chega cedo.",
                "alergias": "",
                "restricoes_alimentares": "Sem gluten",
                "necessidades_especiais": "",
                "pode_comer_lanche_igreja": "True",
                "medicacao_ou_cuidado_especial": "",
                "observacao_para_professor": "",
                "ativo": "on",
            },
        )

        self.assertEqual(response.status_code, 403)

        listagem = self.client.get(reverse("usuarios:infantil:sala_criancas", args=[self.sala_um.pk]))
        self.assertEqual(listagem.status_code, 200)
        self.assertNotContains(listagem, "Nova crianca")
        self.assertNotContains(listagem, "Editar")

        detail = self.client.get(reverse("usuarios:infantil:crianca_detail", args=[self.crianca.pk]))
        self.assertEqual(detail.status_code, 200)
        self.assertNotContains(detail, "Editar")

    def test_usuario_sem_vinculo_nao_pode_ver_detalhe_da_crianca(self):
        self.client.force_login(self.outsider)

        response = self.client.get(reverse("usuarios:infantil:crianca_detail", args=[self.crianca.pk]))

        self.assertEqual(response.status_code, 403)

    def test_lider_de_sala_pode_cadastrar_aula_e_visualizar_detalhe(self):
        self.client.force_login(self.lider_sala)

        response = self.client.post(
            reverse("usuarios:infantil:aula_nova", args=[self.sala_um.pk]),
            {
                "data": "2026-05-03",
                "tema": "A fe de Daniel",
                "texto_base": "Daniel 6",
                "conteudo_licao": "Licao completa da semana.",
                "observacoes": "Levar atividade impressa.",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        aula = AulaSala.objects.get(tema="A fe de Daniel")
        self.assertContains(response, "Aula cadastrada com sucesso")

        detail = self.client.get(reverse("usuarios:infantil:aula_detail", args=[aula.pk]))

        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, "Licao completa da semana.")
        self.assertContains(detail, "Levar atividade impressa.")

    def test_professor_apenas_visualiza_aulas(self):
        self.client.force_login(self.professor)

        response = self.client.post(
            reverse("usuarios:infantil:aula_nova", args=[self.sala_um.pk]),
            {
                "data": "2026-05-03",
                "tema": "A fe de Daniel",
                "texto_base": "Daniel 6",
                "conteudo_licao": "Licao completa da semana.",
                "observacoes": "Levar atividade impressa.",
            },
        )

        self.assertEqual(response.status_code, 403)

        listagem = self.client.get(reverse("usuarios:infantil:sala_aulas", args=[self.sala_um.pk]))
        self.assertEqual(listagem.status_code, 200)
        self.assertNotContains(listagem, "Nova aula")
        self.assertNotContains(listagem, "Editar")

        detail = self.client.get(reverse("usuarios:infantil:aula_detail", args=[self.aula.pk]))
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, "Conteudo inicial da licao")
        self.assertNotContains(detail, "Editar")

    def test_lider_do_departamento_pode_gerenciar_criancas_e_aulas_de_qualquer_sala(self):
        self.client.force_login(self.lider_departamento)

        crianca_response = self.client.post(
            reverse("usuarios:infantil:crianca_nova", args=[self.sala_dois.pk]),
            {
                "nome": "Debora",
                "data_nascimento": "2014-03-11",
                "sexo": "",
                "responsavel_nome": "Joana",
                "responsavel_telefone": "81777777777",
                "responsavel_email": "",
                "observacoes_gerais": "Nova na turma.",
                "alergias": "Alergia a ovo",
                "restricoes_alimentares": "",
                "necessidades_especiais": "",
                "pode_comer_lanche_igreja": "True",
                "medicacao_ou_cuidado_especial": "",
                "observacao_para_professor": "",
                "ativo": "on",
            },
            follow=True,
        )
        self.assertEqual(crianca_response.status_code, 200)
        self.assertTrue(Crianca.objects.filter(nome="Debora", sala=self.sala_dois).exists())

        aula_response = self.client.post(
            reverse("usuarios:infantil:aula_nova", args=[self.sala_dois.pk]),
            {
                "data": "2026-05-10",
                "tema": "Samuel ouve a voz de Deus",
                "texto_base": "1 Samuel 3",
                "conteudo_licao": "Conteudo da licao da segunda sala.",
                "observacoes": "Levar cartazes.",
            },
            follow=True,
        )
        self.assertEqual(aula_response.status_code, 200)
        self.assertTrue(
            AulaSala.objects.filter(
                sala=self.sala_dois,
                tema="Samuel ouve a voz de Deus",
            ).exists()
        )

    def test_usuario_logado_pode_ver_minhas_criancas_sem_vinculo_infantil(self):
        self.client.force_login(self.outsider)

        response = self.client.get(reverse("usuarios:infantil:minhas_criancas"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Minhas criancas")
        self.assertContains(response, "Cadastrar nova crianca")

    def test_usuario_logado_pode_cadastrar_crianca_pendente(self):
        self.client.force_login(self.outsider)

        response = self.client.post(
            reverse("usuarios:infantil:minha_crianca_nova"),
            {
                "nome": "Helena",
                "data_nascimento": "2020-04-11",
                "sexo": Crianca.Sexo.FEMININO,
                "observacoes_gerais": "Primeira vez na igreja.",
                "alergias": "Alergia a corante",
                "restricoes_alimentares": "",
                "necessidades_especiais": "",
                "pode_comer_lanche_igreja": "True",
                "medicacao_ou_cuidado_especial": "",
                "observacao_para_professor": "Fica mais calma com brinquedo.",
                "responsavel_nome": "Visitante Infantil",
                "responsavel_telefone": "81911111111",
                "responsavel_email": "visitante.infantil@example.com",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        crianca = Crianca.objects.get(nome="Helena")
        self.assertEqual(crianca.responsavel_usuario, self.outsider)
        self.assertEqual(crianca.status, Crianca.Status.PENDENTE)
        self.assertIsNone(crianca.sala)
        self.assertFalse(crianca.ativo)
        self.assertContains(response, "Cadastro enviado com sucesso para revisao do Infantil.")
        self.assertTrue(usuario_pode_ver_crianca_do_responsavel(self.outsider, crianca))
        self.assertTrue(usuario_pode_editar_crianca_do_responsavel(self.outsider, crianca))

    def test_usuario_so_visualiza_as_proprias_criancas(self):
        crianca_outsider = Crianca.objects.create(
            nome="Ester",
            data_nascimento=date(2019, 7, 2),
            responsavel_usuario=self.outsider,
            responsavel_nome="Visitante Infantil",
            responsavel_telefone="81911111111",
            status=Crianca.Status.PENDENTE,
            ativo=False,
        )
        Crianca.objects.create(
            nome="Laura",
            data_nascimento=date(2018, 8, 8),
            responsavel_usuario=self.professor,
            responsavel_nome="Professor",
            responsavel_telefone="81922222222",
            status=Crianca.Status.PENDENTE,
            ativo=False,
        )

        self.client.force_login(self.outsider)
        response = self.client.get(reverse("usuarios:infantil:minhas_criancas"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, crianca_outsider.nome)
        self.assertNotContains(response, "Laura")

    def test_responsavel_pode_editar_apenas_cadastro_pendente_ou_recusado(self):
        pendente = Crianca.objects.create(
            nome="Davi",
            data_nascimento=date(2019, 3, 9),
            responsavel_usuario=self.outsider,
            responsavel_nome="Visitante Infantil",
            responsavel_telefone="81911111111",
            status=Crianca.Status.PENDENTE,
            ativo=False,
        )
        recusado = Crianca.objects.create(
            nome="Lia",
            data_nascimento=date(2020, 2, 7),
            responsavel_usuario=self.outsider,
            responsavel_nome="Visitante Infantil",
            responsavel_telefone="81911111111",
            status=Crianca.Status.RECUSADO,
            ativo=False,
        )
        aprovado = Crianca.objects.create(
            nome="Rafaela",
            data_nascimento=date(2018, 5, 6),
            responsavel_usuario=self.outsider,
            responsavel_nome="Visitante Infantil",
            responsavel_telefone="81911111111",
            sala=self.sala_um,
            status=Crianca.Status.APROVADO,
            ativo=True,
        )

        self.client.force_login(self.outsider)
        response = self.client.post(
            reverse("usuarios:infantil:minha_crianca_editar", args=[pendente.pk]),
            {
                "nome": "Davi Atualizado",
                "data_nascimento": "2019-03-09",
                "sexo": "",
                "observacoes_gerais": "Atualizado pelo responsavel.",
                "alergias": "",
                "restricoes_alimentares": "",
                "necessidades_especiais": "",
                "pode_comer_lanche_igreja": "True",
                "medicacao_ou_cuidado_especial": "",
                "observacao_para_professor": "",
                "responsavel_nome": "Visitante Infantil",
                "responsavel_telefone": "81911111111",
                "responsavel_email": "",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        pendente.refresh_from_db()
        self.assertEqual(pendente.nome, "Davi Atualizado")
        self.assertTrue(usuario_pode_ver_cadastro_crianca(self.outsider, pendente))

        retry_response = self.client.post(
            reverse("usuarios:infantil:minha_crianca_editar", args=[recusado.pk]),
            {
                "nome": "Lia",
                "data_nascimento": "2020-02-07",
                "sexo": "",
                "observacoes_gerais": "Documentacao corrigida.",
                "alergias": "",
                "restricoes_alimentares": "",
                "necessidades_especiais": "",
                "pode_comer_lanche_igreja": "True",
                "medicacao_ou_cuidado_especial": "",
                "observacao_para_professor": "",
                "responsavel_nome": "Visitante Infantil",
                "responsavel_telefone": "81911111111",
                "responsavel_email": "",
            },
            follow=True,
        )

        self.assertEqual(retry_response.status_code, 200)
        recusado.refresh_from_db()
        self.assertEqual(recusado.status, Crianca.Status.PENDENTE)
        self.assertFalse(recusado.ativo)
        self.assertContains(retry_response, "reenviado para nova revisao do Infantil")

        forbidden = self.client.get(reverse("usuarios:infantil:minha_crianca_editar", args=[aprovado.pk]))
        self.assertEqual(forbidden.status_code, 403)
        self.assertFalse(usuario_pode_editar_crianca_do_responsavel(self.outsider, aprovado))

    def test_usuario_nao_pode_editar_crianca_de_outro_responsavel(self):
        crianca = Crianca.objects.create(
            nome="Mateus",
            data_nascimento=date(2020, 1, 10),
            responsavel_usuario=self.professor,
            responsavel_nome="Professor",
            responsavel_telefone="81922222222",
            status=Crianca.Status.PENDENTE,
            ativo=False,
        )

        self.client.force_login(self.outsider)
        response = self.client.get(reverse("usuarios:infantil:minha_crianca_editar", args=[crianca.pk]))

        self.assertEqual(response.status_code, 403)

    def test_equipe_infantil_pode_revisar_aprovar_e_vincular_sala(self):
        crianca = Crianca.objects.create(
            nome="Isaque",
            data_nascimento=date(2019, 9, 1),
            responsavel_usuario=self.outsider,
            responsavel_nome="Visitante Infantil",
            responsavel_telefone="81911111111",
            responsavel_email="visitante.infantil@example.com",
            status=Crianca.Status.PENDENTE,
            ativo=False,
        )

        self.client.force_login(self.lider_departamento)

        fila = self.client.get(reverse("usuarios:infantil:cadastros_lista"))
        self.assertEqual(fila.status_code, 200)
        self.assertContains(fila, "Isaque")

        response = self.client.post(
            reverse("usuarios:infantil:cadastro_review", args=[crianca.pk]),
            {
                "nome": "Isaque",
                "data_nascimento": "2019-09-01",
                "sexo": "",
                "status": Crianca.Status.APROVADO,
                "sala": self.sala_um.pk,
                "responsavel_nome": "Visitante Infantil",
                "responsavel_telefone": "81911111111",
                "responsavel_email": "visitante.infantil@example.com",
                "observacoes_gerais": "Cadastro aprovado pela equipe.",
                "alergias": "Alergia a poeira",
                "restricoes_alimentares": "",
                "necessidades_especiais": "",
                "pode_comer_lanche_igreja": "True",
                "medicacao_ou_cuidado_especial": "",
                "observacao_para_professor": "Receber com calma.",
                "ativo": "on",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        crianca.refresh_from_db()
        self.assertEqual(crianca.status, Crianca.Status.APROVADO)
        self.assertEqual(crianca.sala, self.sala_um)
        self.assertTrue(crianca.ativo)
        self.assertContains(response, "Cadastro infantil atualizado com sucesso.")

    def test_usuario_comum_nao_pode_acessar_fila_de_cadastros(self):
        self.client.force_login(self.outsider)

        response = self.client.get(reverse("usuarios:infantil:cadastros_lista"))

        self.assertEqual(response.status_code, 403)
