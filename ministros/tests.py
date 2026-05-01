from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from departamentos.models import Departamento, DepartamentoMembro

from .models import FotoMinistro, Ministro
from .permissions import usuario_pode_gerenciar_ministros


class MinistrosTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.secretaria_user = user_model.objects.create_user(
            username="secretaria.ministros",
            password="senha-forte-123",
            email="secretaria.ministros@example.com",
            is_staff=True,
        )
        self.usuario_comum = user_model.objects.create_user(
            username="usuario.ministros",
            password="senha-forte-123",
            email="usuario.ministros@example.com",
        )
        secretaria = Departamento.objects.create(
            nome="Secretaria",
            codigo=Departamento.CodigoSistema.SECRETARIA,
            ativo=True,
        )
        DepartamentoMembro.objects.create(
            membro=self.secretaria_user,
            departamento=secretaria,
            papel=DepartamentoMembro.Papel.LIDER,
            ativo=True,
        )
        self.ministro = Ministro.objects.create(
            nome_completo="Visitante Teste",
            nome_ministerial="Pr. Visitante",
            tipo=Ministro.Tipo.VISITANTE,
            status=Ministro.Status.PENDENTE,
            igreja_origem="Igreja Origem",
            cidade="Recife",
            estado="PE",
            chave_pix="pix-secreto@example.com",
            observacoes_financeiras="Honorario combinado internamente.",
        )

    def test_secretaria_pode_gerenciar_ministros(self):
        self.assertTrue(usuario_pode_gerenciar_ministros(self.secretaria_user))
        self.assertFalse(usuario_pode_gerenciar_ministros(self.usuario_comum))

    def test_listagem_exige_permissao(self):
        self.client.force_login(self.usuario_comum)
        response = self.client.get(reverse("usuarios:ministros:lista"))
        self.assertEqual(response.status_code, 403)

    def test_secretaria_acessa_listagem_e_detalhe_com_dados_financeiros(self):
        self.client.force_login(self.secretaria_user)

        lista = self.client.get(reverse("usuarios:ministros:lista"))
        self.assertEqual(lista.status_code, 200)
        self.assertContains(lista, "Pr. Visitante")

        detalhe = self.client.get(reverse("usuarios:ministros:detalhe", args=[self.ministro.pk]))
        self.assertEqual(detalhe.status_code, 200)
        self.assertContains(detalhe, "pix-secreto@example.com")
        self.assertContains(detalhe, "Honorario combinado internamente.")

    def test_formulario_externo_nao_expoe_lista_nem_observacoes_internas(self):
        url = reverse("ministros:formulario_externo", args=[self.ministro.token_formulario])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Atualize suas informacoes")
        self.assertNotContains(response, "Honorario combinado internamente.")
        self.assertNotContains(response, "Lista de ministros")

    def test_formulario_externo_atualiza_dados_e_marca_pendente(self):
        self.ministro.status = Ministro.Status.APROVADO
        self.ministro.save(update_fields=["status"])

        response = self.client.post(
            reverse("ministros:formulario_externo", args=[self.ministro.token_formulario]),
            {
                "nome_completo": "Visitante Teste Atualizado",
                "nome_ministerial": "Pr. Visitante Atualizado",
                "telefone_whatsapp": "(81) 99999-0000",
                "email": "visitante@example.com",
                "igreja_origem": "Igreja Origem",
                "cidade": "Recife",
                "estado": "PE",
                "pais": "Brasil",
                "biografia": "Bio curta",
                "tipo_chave_pix": Ministro.TipoChavePix.EMAIL,
                "chave_pix": "visitante@example.com",
                "favorecido_nome": "Visitante Teste",
                "favorecido_documento": "",
                "banco": "",
                "restricao_alimentar": "Sem lactose",
                "alergias": "Amendoim",
                "preferencia_alimentacao": "",
                "observacoes_hospedagem": "",
                "observacoes_transporte": "",
                "necessidades_especiais": "",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.ministro.refresh_from_db()
        self.assertEqual(self.ministro.nome_ministerial, "Pr. Visitante Atualizado")
        self.assertEqual(self.ministro.status, Ministro.Status.ATUALIZADO)
        self.assertEqual(self.ministro.tipo, Ministro.Tipo.VISITANTE)

    def test_apenas_uma_foto_fica_em_destaque(self):
        primeira = FotoMinistro.objects.create(
            ministro=self.ministro,
            imagem="ministros/galeria/primeira.jpg",
            destaque=True,
        )
        segunda = FotoMinistro.objects.create(
            ministro=self.ministro,
            imagem="ministros/galeria/segunda.jpg",
            destaque=True,
        )

        primeira.refresh_from_db()
        segunda.refresh_from_db()
        self.assertFalse(primeira.destaque)
        self.assertTrue(segunda.destaque)

    def test_galeria_geral_filtra_por_nome_do_ministro(self):
        outro = Ministro.objects.create(
            nome_completo="Outro Ministro",
            nome_ministerial="Pr. Outro",
            tipo=Ministro.Tipo.VISITANTE,
        )
        FotoMinistro.objects.create(
            ministro=self.ministro,
            imagem="ministros/galeria/visitante.jpg",
            legenda="Foto visitante",
        )
        FotoMinistro.objects.create(
            ministro=outro,
            imagem="ministros/galeria/outro.jpg",
            legenda="Foto outro",
        )

        self.client.force_login(self.secretaria_user)
        response = self.client.get(reverse("usuarios:ministros:galeria_lista"), {"q": "Visitante"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Foto visitante")
        self.assertNotContains(response, "Foto outro")
