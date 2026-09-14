from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from .models import StockCategory, StockItem


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
