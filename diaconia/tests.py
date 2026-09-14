from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from .models import StockCategory, StockItem, StockMovement
from .services import StockStatus


class DiaconiaStockApiTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.viewer = self.user_model.objects.create_user(username="diaconia.viewer", password="senha-forte-123")
        self.manager = self.user_model.objects.create_user(username="diaconia.manager", password="senha-forte-123")
        self.no_access = self.user_model.objects.create_user(username="diaconia.no.access", password="senha-forte-123")
        view_permission = Permission.objects.get(content_type__app_label="diaconia", codename="view_diaconia_module")
        manage_permission = Permission.objects.get(content_type__app_label="diaconia", codename="manage_diaconia_stock")
        self.viewer.user_permissions.add(view_permission)
        self.manager.user_permissions.add(view_permission, manage_permission)

    def login_manager(self):
        self.client.force_login(self.manager)

    def create_item(self, *, is_active=True):
        category = StockCategory.objects.create(name=f"Categoria {StockCategory.objects.count() + 1}")
        return StockItem.objects.create(
            name=f"Item {StockItem.objects.count() + 1}",
            category=category,
            unit=StockItem.Unit.UN,
            minimum_stock=0,
            is_active=is_active,
        )

    def test_cria_categoria(self):
        self.login_manager()

        response = self.client.post(
            reverse("diaconia-stock-category-list"),
            {"name": "Limpeza", "description": "Materiais de limpeza"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["name"], "Limpeza")
        self.assertTrue(StockCategory.objects.filter(name="Limpeza", is_active=True).exists())

    def test_edita_categoria(self):
        self.login_manager()
        category = StockCategory.objects.create(name="Higiene")

        response = self.client.patch(
            reverse("diaconia-stock-category-detail", args=[category.pk]),
            {"name": "Higiene pessoal", "description": "Itens de higiene"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        category.refresh_from_db()
        self.assertEqual(category.name, "Higiene pessoal")
        self.assertEqual(category.description, "Itens de higiene")

    def test_inativa_categoria(self):
        self.login_manager()
        category = StockCategory.objects.create(name="Descartaveis")

        response = self.client.post(reverse("diaconia-stock-category-deactivate", args=[category.pk]))

        self.assertEqual(response.status_code, 200)
        category.refresh_from_db()
        self.assertFalse(category.is_active)

    def test_cria_item(self):
        self.login_manager()
        category = StockCategory.objects.create(name="Limpeza")

        response = self.client.post(
            reverse("diaconia-stock-item-list"),
            {
                "name": "Detergente 500 ml",
                "category_id": category.pk,
                "unit": StockItem.Unit.UN,
                "minimum_stock": 5,
                "notes": "Uso geral",
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        item = StockItem.objects.get(name="Detergente 500 ml")
        self.assertEqual(item.category, category)
        self.assertEqual(item.minimum_stock, 5)

    def test_item_aceita_estoque_minimo_zero(self):
        self.login_manager()
        category = StockCategory.objects.create(name="Agua")

        response = self.client.post(
            reverse("diaconia-stock-item-list"),
            {
                "name": "Garrafa de agua",
                "category_id": category.pk,
                "unit": StockItem.Unit.GARRAFAO,
                "minimum_stock": 0,
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(StockItem.objects.get(name="Garrafa de agua").minimum_stock, 0)

    def test_rejeita_estoque_minimo_negativo(self):
        self.login_manager()
        category = StockCategory.objects.create(name="Limpeza")

        response = self.client.post(
            reverse("diaconia-stock-item-list"),
            {
                "name": "Sabao",
                "category_id": category.pk,
                "unit": StockItem.Unit.UN,
                "minimum_stock": -1,
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("minimum_stock", response.json())

    def test_rejeita_unidade_invalida(self):
        self.login_manager()
        category = StockCategory.objects.create(name="Limpeza")

        response = self.client.post(
            reverse("diaconia-stock-item-list"),
            {
                "name": "Pano",
                "category_id": category.pk,
                "unit": "METRO",
                "minimum_stock": 1,
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("unit", response.json())

    def test_rejeita_categoria_inativa_para_novo_item(self):
        self.login_manager()
        category = StockCategory.objects.create(name="Inativa", is_active=False)

        response = self.client.post(
            reverse("diaconia-stock-item-list"),
            {
                "name": "Item bloqueado",
                "category_id": category.pk,
                "unit": StockItem.Unit.UN,
                "minimum_stock": 1,
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("category_id", response.json())

    def test_endpoints_exigem_autenticacao_e_autorizacao(self):
        category_url = reverse("diaconia-stock-category-list")

        self.assertEqual(self.client.get(category_url).status_code, 403)

        self.client.force_login(self.no_access)
        self.assertEqual(self.client.get(category_url).status_code, 403)

        self.client.force_login(self.viewer)
        self.assertEqual(self.client.get(category_url).status_code, 200)
        self.assertEqual(
            self.client.post(category_url, {"name": "Sem permissao"}, content_type="application/json").status_code,
            403,
        )

        self.login_manager()
        self.assertEqual(
            self.client.post(category_url, {"name": "Com permissao"}, content_type="application/json").status_code,
            201,
        )

    def test_cria_entrada_e_saldo_aumenta(self):
        self.login_manager()
        item = self.create_item()

        response = self.client.post(
            reverse("diaconia-stock-movement-list"),
            {
                "item_id": item.pk,
                "movement_type": StockMovement.Type.ENTRADA,
                "quantity": 12,
                "notes": "Compra mensal",
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["created_by"]["id"], self.manager.id)
        item_list = self.client.get(reverse("diaconia-stock-item-list")).json()
        self.assertEqual(item_list[0]["current_stock"], 12)

    def test_cria_saida_e_saldo_diminui(self):
        self.login_manager()
        item = self.create_item()
        StockMovement.objects.create(
            item=item,
            movement_type=StockMovement.Type.ENTRADA,
            quantity=12,
            created_by=self.manager,
        )

        response = self.client.post(
            reverse("diaconia-stock-movement-list"),
            {
                "item_id": item.pk,
                "movement_type": StockMovement.Type.SAIDA,
                "quantity": 3,
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        item_list = self.client.get(reverse("diaconia-stock-item-list")).json()
        self.assertEqual(item_list[0]["current_stock"], 9)

    def test_impede_saida_maior_que_saldo(self):
        self.login_manager()
        item = self.create_item()
        StockMovement.objects.create(
            item=item,
            movement_type=StockMovement.Type.ENTRADA,
            quantity=3,
            created_by=self.manager,
        )

        response = self.client.post(
            reverse("diaconia-stock-movement-list"),
            {
                "item_id": item.pk,
                "movement_type": StockMovement.Type.SAIDA,
                "quantity": 5,
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(StockMovement.objects.filter(item=item).count(), 1)
        self.assertIn("saldo disponivel", response.json()["message"])

    def test_impede_saida_com_saldo_zero(self):
        self.login_manager()
        item = self.create_item()

        response = self.client.post(
            reverse("diaconia-stock-movement-list"),
            {
                "item_id": item.pk,
                "movement_type": StockMovement.Type.SAIDA,
                "quantity": 1,
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["message"], "Nao ha saldo disponivel para este item.")

    def test_impede_movimentacao_de_item_inativo(self):
        self.login_manager()
        item = self.create_item(is_active=False)

        response = self.client.post(
            reverse("diaconia-stock-movement-list"),
            {
                "item_id": item.pk,
                "movement_type": StockMovement.Type.ENTRADA,
                "quantity": 1,
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 409)
        self.assertIn("inativo", response.json()["message"])

    def test_rejeita_quantidade_zero_e_negativa(self):
        self.login_manager()
        item = self.create_item()

        zero = self.client.post(
            reverse("diaconia-stock-movement-list"),
            {
                "item_id": item.pk,
                "movement_type": StockMovement.Type.ENTRADA,
                "quantity": 0,
            },
            content_type="application/json",
        )
        negative = self.client.post(
            reverse("diaconia-stock-movement-list"),
            {
                "item_id": item.pk,
                "movement_type": StockMovement.Type.ENTRADA,
                "quantity": -1,
            },
            content_type="application/json",
        )

        self.assertEqual(zero.status_code, 400)
        self.assertEqual(negative.status_code, 400)
        self.assertIn("quantity", zero.json())
        self.assertIn("quantity", negative.json())

    def test_movimentacao_registra_usuario_autenticado(self):
        self.login_manager()
        item = self.create_item()

        self.client.post(
            reverse("diaconia-stock-movement-list"),
            {
                "item_id": item.pk,
                "movement_type": StockMovement.Type.ENTRADA,
                "quantity": 2,
            },
            content_type="application/json",
        )

        self.assertEqual(StockMovement.objects.get(item=item).created_by, self.manager)

    def test_movimentacao_nao_pode_ser_editada_ou_excluida_por_api(self):
        self.login_manager()
        item = self.create_item()
        movement = StockMovement.objects.create(
            item=item,
            movement_type=StockMovement.Type.ENTRADA,
            quantity=2,
            created_by=self.manager,
        )
        url = reverse("diaconia-stock-movement-detail", args=[movement.pk])

        self.assertEqual(self.client.patch(url, {"quantity": 9}, content_type="application/json").status_code, 405)
        self.assertEqual(self.client.delete(url).status_code, 405)
        movement.refresh_from_db()
        self.assertEqual(movement.quantity, 2)

    def test_usuario_sem_capability_nao_pode_movimentar(self):
        item = self.create_item()
        self.client.force_login(self.viewer)

        response = self.client.post(
            reverse("diaconia-stock-movement-list"),
            {
                "item_id": item.pk,
                "movement_type": StockMovement.Type.ENTRADA,
                "quantity": 1,
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)

    def test_historico_lista_mais_recente_primeiro_e_filtra_item(self):
        self.login_manager()
        first_item = self.create_item()
        second_item = self.create_item()
        old_movement = StockMovement.objects.create(
            item=first_item,
            movement_type=StockMovement.Type.ENTRADA,
            quantity=1,
            created_by=self.manager,
        )
        new_movement = StockMovement.objects.create(
            item=first_item,
            movement_type=StockMovement.Type.SAIDA,
            quantity=1,
            created_by=self.manager,
        )
        StockMovement.objects.create(
            item=second_item,
            movement_type=StockMovement.Type.ENTRADA,
            quantity=1,
            created_by=self.manager,
        )

        response = self.client.get(f"{reverse('diaconia-stock-movement-list')}?item={first_item.pk}")

        self.assertEqual(response.status_code, 200)
        movement_ids = [movement["id"] for movement in response.json()]
        self.assertEqual(movement_ids, [new_movement.id, old_movement.id])

    def test_status_normal_quando_saldo_maior_que_minimo(self):
        self.login_manager()
        item = self.create_item()
        item.minimum_stock = 5
        item.save(update_fields=["minimum_stock"])
        StockMovement.objects.create(
            item=item,
            movement_type=StockMovement.Type.ENTRADA,
            quantity=6,
            created_by=self.manager,
        )

        response = self.client.get(reverse("diaconia-stock-item-list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["stock_status"], StockStatus.NORMAL)

    def test_status_baixo_quando_saldo_menor_que_minimo(self):
        self.login_manager()
        item = self.create_item()
        item.minimum_stock = 5
        item.save(update_fields=["minimum_stock"])
        StockMovement.objects.create(
            item=item,
            movement_type=StockMovement.Type.ENTRADA,
            quantity=3,
            created_by=self.manager,
        )

        response = self.client.get(reverse("diaconia-stock-item-list"))

        self.assertEqual(response.json()[0]["stock_status"], StockStatus.LOW_STOCK)

    def test_status_baixo_quando_saldo_igual_ao_minimo(self):
        self.login_manager()
        item = self.create_item()
        item.minimum_stock = 5
        item.save(update_fields=["minimum_stock"])
        StockMovement.objects.create(
            item=item,
            movement_type=StockMovement.Type.ENTRADA,
            quantity=5,
            created_by=self.manager,
        )

        response = self.client.get(reverse("diaconia-stock-item-list"))

        self.assertEqual(response.json()[0]["stock_status"], StockStatus.LOW_STOCK)

    def test_status_sem_controle_quando_minimo_zero(self):
        self.login_manager()
        self.create_item()

        response = self.client.get(reverse("diaconia-stock-item-list"))

        self.assertEqual(response.json()[0]["stock_status"], StockStatus.WITHOUT_MINIMUM)

    def test_item_inativo_nao_entra_no_indicador_de_reposicao(self):
        self.login_manager()
        inactive = self.create_item(is_active=False)
        inactive.minimum_stock = 5
        inactive.save(update_fields=["minimum_stock"])

        response = self.client.get(reverse("diaconia-stock-summary"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["active_items"], 0)
        self.assertEqual(response.json()["low_stock_items"], 0)
        self.assertEqual(response.json()["replenishment_items"], [])

    def test_resumo_retorna_contagens_corretas(self):
        self.login_manager()
        low = self.create_item()
        low.minimum_stock = 5
        low.save(update_fields=["minimum_stock"])
        normal = self.create_item()
        normal.minimum_stock = 5
        normal.save(update_fields=["minimum_stock"])
        without_control = self.create_item()
        StockMovement.objects.create(
            item=normal,
            movement_type=StockMovement.Type.ENTRADA,
            quantity=8,
            created_by=self.manager,
        )

        response = self.client.get(reverse("diaconia-stock-summary"))

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["active_items"], 3)
        self.assertEqual(body["low_stock_items"], 1)
        self.assertEqual(body["without_minimum_control"], 1)
        self.assertEqual(body["replenishment_items"][0]["id"], low.id)

    def test_filtro_por_estoque_baixo(self):
        self.login_manager()
        low = self.create_item()
        low.minimum_stock = 5
        low.save(update_fields=["minimum_stock"])
        normal = self.create_item()
        normal.minimum_stock = 5
        normal.save(update_fields=["minimum_stock"])
        StockMovement.objects.create(
            item=normal,
            movement_type=StockMovement.Type.ENTRADA,
            quantity=8,
            created_by=self.manager,
        )

        response = self.client.get(f"{reverse('diaconia-stock-item-list')}?stock_status={StockStatus.LOW_STOCK}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.json()], [low.id])

    def test_resumo_respeita_permissao_de_visualizacao(self):
        summary_url = reverse("diaconia-stock-summary")

        self.client.force_login(self.no_access)
        self.assertEqual(self.client.get(summary_url).status_code, 403)

        self.client.force_login(self.viewer)
        self.assertEqual(self.client.get(summary_url).status_code, 200)
