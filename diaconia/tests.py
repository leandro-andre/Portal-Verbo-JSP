from datetime import datetime

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import (
    AttendanceCount,
    AttendanceCountEntry,
    CountingEnvironment,
    InventoryCategory,
    InventoryCount,
    InventoryCountEntry,
    InventoryItem,
    InventoryLocation,
    StockCategory,
    StockItem,
    StockMovement,
)
from .services import StockStatus


class DiaconiaStockApiTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.viewer = self.user_model.objects.create_user(username="diaconia.viewer", password="senha-forte-123")
        self.manager = self.user_model.objects.create_user(username="diaconia.manager", password="senha-forte-123")
        self.counting_manager = self.user_model.objects.create_user(
            username="diaconia.counting.manager",
            password="senha-forte-123",
        )
        self.inventory_manager = self.user_model.objects.create_user(
            username="diaconia.inventory.manager",
            password="senha-forte-123",
        )
        self.no_access = self.user_model.objects.create_user(username="diaconia.no.access", password="senha-forte-123")
        view_permission = Permission.objects.get(content_type__app_label="diaconia", codename="view_diaconia_module")
        manage_permission = Permission.objects.get(content_type__app_label="diaconia", codename="manage_diaconia_stock")
        counting_permission = Permission.objects.get(
            content_type__app_label="diaconia",
            codename="manage_diaconia_counting",
        )
        inventory_permission = Permission.objects.get(
            content_type__app_label="diaconia",
            codename="manage_diaconia_inventory",
        )
        self.viewer.user_permissions.add(view_permission)
        self.manager.user_permissions.add(view_permission, manage_permission, counting_permission, inventory_permission)
        self.counting_manager.user_permissions.add(view_permission, counting_permission)
        self.inventory_manager.user_permissions.add(view_permission, inventory_permission)

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

    def create_attendance_payload(self, environments, **overrides):
        payload = {
            "date": "2026-09-14",
            "shift": "MORNING",
            "notes": "Culto especial",
            "entries": [
                {"environment_id": environment.id, "quantity": index}
                for index, environment in enumerate(environments)
            ],
        }
        payload.update(overrides)
        return payload

    def create_attendance_count_record(self, *, date="2026-09-14", shift=AttendanceCount.Shift.MORNING, user=None, entries=None, notes=""):
        user = user or self.manager
        if entries is None:
            environment = CountingEnvironment.objects.create(name=f"Ambiente {CountingEnvironment.objects.count() + 1}")
            entries = [(environment, 10)]
        count = AttendanceCount.objects.create(date=date, shift=shift, notes=notes, created_by=user)
        for environment, quantity in entries:
            AttendanceCountEntry.objects.create(attendance_count=count, environment=environment, quantity=quantity)
        return count

    def create_inventory_item_record(self, *, name=None, category=None, is_active=True):
        category = category or InventoryCategory.objects.create(name=f"Categoria Inventario {InventoryCategory.objects.count() + 1}")
        return InventoryItem.objects.create(
            name=name or f"Item Inventario {InventoryItem.objects.count() + 1}",
            category=category,
            is_active=is_active,
        )

    def create_inventory_count_payload(self, *, items=None, locations=None, date="2026-09-15", notes="Contagem geral"):
        if items is None:
            items = [self.create_inventory_item_record(name="Cadeira plastica")]
        if locations is None:
            locations = [InventoryLocation.objects.create(name="Templo")]
        quantity = 1
        entries = []
        for item in items:
            for location in locations:
                entries.append({"item_id": item.id, "location_id": location.id, "quantity": quantity})
                quantity += 1
        return {"date": date, "notes": notes, "entries": entries}

    def create_inventory_count_record(self, *, date="2026-09-15", user=None, entries=None, notes=""):
        user = user or self.inventory_manager
        if entries is None:
            item = self.create_inventory_item_record(name=f"Item Contagem {InventoryItem.objects.count() + 1}")
            location = InventoryLocation.objects.create(name=f"Local {InventoryLocation.objects.count() + 1}")
            entries = [(item, location, 1)]
        count = InventoryCount.objects.create(date=date, notes=notes, created_by=user)
        for item, location, quantity in entries:
            InventoryCountEntry.objects.create(inventory_count=count, item=item, location=location, quantity=quantity)
        return count

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

    def test_cria_ambiente_de_contagem(self):
        self.login_manager()

        response = self.client.post(
            reverse("diaconia-counting-environment-list"),
            {"name": "Templo", "description": "Salao principal"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(CountingEnvironment.objects.filter(name="Templo", is_active=True).exists())

    def test_ambiente_exige_nome(self):
        self.login_manager()

        response = self.client.post(
            reverse("diaconia-counting-environment-list"),
            {"name": "   ", "description": ""},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("name", response.json())

    def test_ambiente_bloqueia_duplicidade_case_insensitive(self):
        self.login_manager()
        CountingEnvironment.objects.create(name="Templo")

        response = self.client.post(
            reverse("diaconia-counting-environment-list"),
            {"name": "templo", "description": ""},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("name", response.json())

    def test_edita_ambiente_de_contagem(self):
        self.login_manager()
        environment = CountingEnvironment.objects.create(name="Hall")

        response = self.client.patch(
            reverse("diaconia-counting-environment-detail", args=[environment.pk]),
            {"name": "Hall Principal", "description": "Entrada"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        environment.refresh_from_db()
        self.assertEqual(environment.name, "Hall Principal")
        self.assertEqual(environment.description, "Entrada")

    def test_inativa_e_reativa_ambiente(self):
        self.login_manager()
        environment = CountingEnvironment.objects.create(name="Juniores")

        deactivate = self.client.post(reverse("diaconia-counting-environment-deactivate", args=[environment.pk]))
        environment.refresh_from_db()
        self.assertEqual(deactivate.status_code, 200)
        self.assertFalse(environment.is_active)

        reactivate = self.client.post(reverse("diaconia-counting-environment-reactivate", args=[environment.pk]))
        environment.refresh_from_db()
        self.assertEqual(reactivate.status_code, 200)
        self.assertTrue(environment.is_active)

    def test_filtra_ambientes_por_status(self):
        self.login_manager()
        CountingEnvironment.objects.create(name="Ativo")
        CountingEnvironment.objects.create(name="Inativo", is_active=False)

        active = self.client.get(f"{reverse('diaconia-counting-environment-list')}?status=ACTIVE")
        inactive = self.client.get(f"{reverse('diaconia-counting-environment-list')}?status=INACTIVE")

        self.assertEqual([item["name"] for item in active.json()], ["Ativo"])
        self.assertEqual([item["name"] for item in inactive.json()], ["Inativo"])

    def test_busca_ambiente_por_nome(self):
        self.login_manager()
        CountingEnvironment.objects.create(name="Templo")
        CountingEnvironment.objects.create(name="Bercario")

        response = self.client.get(f"{reverse('diaconia-counting-environment-list')}?search=tem")

        self.assertEqual([item["name"] for item in response.json()], ["Templo"])

    def test_leitura_de_ambiente_com_diaconia_view(self):
        environment = CountingEnvironment.objects.create(name="Templo")
        self.client.force_login(self.viewer)

        list_response = self.client.get(reverse("diaconia-counting-environment-list"))
        detail_response = self.client.get(reverse("diaconia-counting-environment-detail", args=[environment.pk]))

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(detail_response.status_code, 200)

    def test_gestao_de_ambiente_exige_capability(self):
        self.client.force_login(self.viewer)

        response = self.client.post(
            reverse("diaconia-counting-environment-list"),
            {"name": "Sem permissao"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)

    def test_usuario_sem_acesso_nao_le_ambientes(self):
        self.client.force_login(self.no_access)

        response = self.client.get(reverse("diaconia-counting-environment-list"))

        self.assertEqual(response.status_code, 403)

    def test_cria_contagem_valida_com_todos_os_ambientes_ativos(self):
        self.client.force_login(self.counting_manager)
        templo = CountingEnvironment.objects.create(name="Templo")
        bercario = CountingEnvironment.objects.create(name="Bercario")
        CountingEnvironment.objects.create(name="Sala fechada", is_active=False)

        response = self.client.post(
            reverse("diaconia-attendance-count-list"),
            self.create_attendance_payload(
                [templo, bercario],
                entries=[
                    {"environment_id": templo.id, "quantity": 185},
                    {"environment_id": bercario.id, "quantity": 0},
                ],
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        body = response.json()
        count = AttendanceCount.objects.get()
        self.assertEqual(count.date.isoformat(), "2026-09-14")
        self.assertEqual(count.shift, AttendanceCount.Shift.MORNING)
        self.assertEqual(count.notes, "Culto especial")
        self.assertEqual(count.created_by, self.counting_manager)
        self.assertEqual(count.entries.count(), 2)
        self.assertEqual(body["total_people"], 185)
        self.assertEqual(body["created_by"]["display_name"], self.counting_manager.username)

    def test_contagem_permite_quantidade_zero_e_positiva(self):
        self.login_manager()
        templo = CountingEnvironment.objects.create(name="Templo")
        infantil = CountingEnvironment.objects.create(name="Infantil")

        response = self.client.post(
            reverse("diaconia-attendance-count-list"),
            self.create_attendance_payload(
                [templo, infantil],
                entries=[
                    {"environment_id": templo.id, "quantity": 0},
                    {"environment_id": infantil.id, "quantity": 25},
                ],
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["total_people"], 25)

    def test_contagem_rejeita_quantidade_negativa(self):
        self.login_manager()
        templo = CountingEnvironment.objects.create(name="Templo")

        response = self.client.post(
            reverse("diaconia-attendance-count-list"),
            self.create_attendance_payload([templo], entries=[{"environment_id": templo.id, "quantity": -1}]),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(AttendanceCount.objects.count(), 0)

    def test_contagem_rejeita_quantidade_nao_inteira(self):
        self.login_manager()
        templo = CountingEnvironment.objects.create(name="Templo")

        response = self.client.post(
            reverse("diaconia-attendance-count-list"),
            self.create_attendance_payload([templo], entries=[{"environment_id": templo.id, "quantity": "dez"}]),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(AttendanceCount.objects.count(), 0)

    def test_contagem_rejeita_mesma_data_e_turno(self):
        self.login_manager()
        templo = CountingEnvironment.objects.create(name="Templo")
        payload = self.create_attendance_payload([templo], entries=[{"environment_id": templo.id, "quantity": 10}])
        self.client.post(reverse("diaconia-attendance-count-list"), payload, content_type="application/json")

        response = self.client.post(reverse("diaconia-attendance-count-list"), payload, content_type="application/json")

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["message"], "Ja existe uma contagem registrada para esta data e turno.")
        self.assertEqual(AttendanceCount.objects.count(), 1)

    def test_contagem_rejeita_ambiente_inexistente(self):
        self.login_manager()
        CountingEnvironment.objects.create(name="Templo")

        response = self.client.post(
            reverse("diaconia-attendance-count-list"),
            {
                "date": "2026-09-14",
                "shift": "MORNING",
                "entries": [{"environment_id": 999, "quantity": 1}],
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(AttendanceCount.objects.count(), 0)

    def test_contagem_rejeita_ambiente_duplicado_no_payload(self):
        self.login_manager()
        templo = CountingEnvironment.objects.create(name="Templo")

        response = self.client.post(
            reverse("diaconia-attendance-count-list"),
            self.create_attendance_payload(
                [templo],
                entries=[
                    {"environment_id": templo.id, "quantity": 10},
                    {"environment_id": templo.id, "quantity": 12},
                ],
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["code"], "ATTENDANCE_COUNT_ENVIRONMENT_MISMATCH")
        self.assertEqual(AttendanceCount.objects.count(), 0)

    def test_contagem_rejeita_ausencia_de_ambiente_ativo_esperado(self):
        self.login_manager()
        CountingEnvironment.objects.create(name="Templo")
        infantil = CountingEnvironment.objects.create(name="Infantil")

        response = self.client.post(
            reverse("diaconia-attendance-count-list"),
            self.create_attendance_payload([infantil], entries=[{"environment_id": infantil.id, "quantity": 25}]),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["message"], "Os ambientes ativos mudaram. Atualize a tela e tente novamente.")
        self.assertEqual(AttendanceCount.objects.count(), 0)

    def test_contagem_rejeita_ambiente_inativo(self):
        self.login_manager()
        templo = CountingEnvironment.objects.create(name="Templo")
        inativo = CountingEnvironment.objects.create(name="Inativo", is_active=False)

        response = self.client.post(
            reverse("diaconia-attendance-count-list"),
            self.create_attendance_payload(
                [templo, inativo],
                entries=[
                    {"environment_id": templo.id, "quantity": 10},
                    {"environment_id": inativo.id, "quantity": 3},
                ],
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(AttendanceCount.objects.count(), 0)

    def test_contagem_rejeita_sem_ambiente_ativo(self):
        self.login_manager()

        response = self.client.post(
            reverse("diaconia-attendance-count-list"),
            {"date": "2026-09-14", "shift": "MORNING", "entries": []},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(AttendanceCount.objects.count(), 0)

    def test_erro_em_entrada_nao_deixa_cabecalho_orfao(self):
        self.login_manager()
        templo = CountingEnvironment.objects.create(name="Templo")

        response = self.client.post(
            reverse("diaconia-attendance-count-list"),
            self.create_attendance_payload(
                [templo],
                entries=[
                    {"environment_id": templo.id, "quantity": 10},
                    {"environment_id": templo.id, "quantity": 11},
                ],
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(AttendanceCount.objects.count(), 0)
        self.assertEqual(AttendanceCountEntry.objects.count(), 0)

    def test_detalhe_da_contagem_retorna_total_e_entries(self):
        self.login_manager()
        templo = CountingEnvironment.objects.create(name="Templo")
        infantil = CountingEnvironment.objects.create(name="Infantil")
        create_response = self.client.post(
            reverse("diaconia-attendance-count-list"),
            self.create_attendance_payload(
                [templo, infantil],
                entries=[
                    {"environment_id": templo.id, "quantity": 180},
                    {"environment_id": infantil.id, "quantity": 20},
                ],
            ),
            content_type="application/json",
        )

        response = self.client.get(reverse("diaconia-attendance-count-detail", args=[create_response.json()["id"]]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total_people"], 200)
        self.assertEqual(len(response.json()["entries"]), 2)

    def test_contagem_exige_capability_de_gestao(self):
        self.client.force_login(self.viewer)
        templo = CountingEnvironment.objects.create(name="Templo")

        response = self.client.post(
            reverse("diaconia-attendance-count-list"),
            self.create_attendance_payload([templo], entries=[{"environment_id": templo.id, "quantity": 10}]),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(AttendanceCount.objects.count(), 0)

    def test_usuario_sem_acesso_nao_consulta_contagem(self):
        count = AttendanceCount.objects.create(
            date="2026-09-14",
            shift=AttendanceCount.Shift.MORNING,
            created_by=self.manager,
        )
        self.client.force_login(self.no_access)

        response = self.client.get(reverse("diaconia-attendance-count-detail", args=[count.pk]))

        self.assertEqual(response.status_code, 403)

    def test_lista_contagens_com_total_e_ordenacao_recente(self):
        self.client.force_login(self.viewer)
        templo = CountingEnvironment.objects.create(name="Templo")
        old_count = self.create_attendance_count_record(
            date="2026-09-10",
            shift=AttendanceCount.Shift.EVENING,
            entries=[(templo, 50)],
        )
        morning = self.create_attendance_count_record(
            date="2026-09-14",
            shift=AttendanceCount.Shift.MORNING,
            entries=[(templo, 100)],
        )
        evening = self.create_attendance_count_record(
            date="2026-09-14",
            shift=AttendanceCount.Shift.EVENING,
            entries=[(templo, 200)],
        )

        response = self.client.get(reverse("diaconia-attendance-count-list"))

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual([item["id"] for item in body], [evening.id, morning.id, old_count.id])
        self.assertEqual(body[0]["total_people"], 200)
        self.assertEqual(body[0]["created_by"]["display_name"], self.manager.username)

    def test_filtra_contagens_por_turno_e_periodo(self):
        self.client.force_login(self.viewer)
        templo = CountingEnvironment.objects.create(name="Templo")
        self.create_attendance_count_record(date="2026-09-01", shift=AttendanceCount.Shift.MORNING, entries=[(templo, 10)])
        target = self.create_attendance_count_record(date="2026-09-14", shift=AttendanceCount.Shift.EVENING, entries=[(templo, 20)])
        self.create_attendance_count_record(date="2026-10-01", shift=AttendanceCount.Shift.EVENING, entries=[(templo, 30)])

        response = self.client.get(
            f"{reverse('diaconia-attendance-count-list')}?date_from=2026-09-10&date_to=2026-09-30&shift=EVENING"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.json()], [target.id])

    def test_filtra_contagens_por_responsavel(self):
        self.client.force_login(self.viewer)
        templo = CountingEnvironment.objects.create(name="Templo")
        mine = self.create_attendance_count_record(user=self.manager, entries=[(templo, 10)])
        self.create_attendance_count_record(date="2026-09-15", user=self.counting_manager, entries=[(templo, 20)])

        response = self.client.get(f"{reverse('diaconia-attendance-count-list')}?created_by={self.manager.id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.json()], [mine.id])

    def test_listagem_de_contagem_respeita_permissao_de_visualizacao(self):
        list_url = reverse("diaconia-attendance-count-list")

        self.client.force_login(self.no_access)
        self.assertEqual(self.client.get(list_url).status_code, 403)

        self.client.force_login(self.viewer)
        self.assertEqual(self.client.get(list_url).status_code, 200)

    def test_detalhe_preserva_ambiente_inativo_e_observacao(self):
        self.client.force_login(self.viewer)
        environment = CountingEnvironment.objects.create(name="Juniores", is_active=False)
        count = self.create_attendance_count_record(
            entries=[(environment, 17)],
            notes="Correcao apos conferencia",
        )

        response = self.client.get(reverse("diaconia-attendance-count-detail", args=[count.pk]))

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["notes"], "Correcao apos conferencia")
        self.assertEqual(body["total_people"], 17)
        self.assertEqual(body["entries"][0]["environment"]["name"], "Juniores")
        self.assertFalse(body["entries"][0]["environment"]["is_active"])

    def test_edita_contagem_quantidades_observacao_data_e_turno(self):
        self.login_manager()
        templo = CountingEnvironment.objects.create(name="Templo")
        infantil = CountingEnvironment.objects.create(name="Infantil")
        count = self.create_attendance_count_record(entries=[(templo, 100), (infantil, 20)])
        AttendanceCount.objects.filter(pk=count.pk).update(updated_at=datetime(2026, 1, 1, tzinfo=timezone.get_current_timezone()))
        count.refresh_from_db()
        old_updated_at = count.updated_at

        response = self.client.patch(
            reverse("diaconia-attendance-count-detail", args=[count.pk]),
            {
                "date": "2026-09-15",
                "shift": "EVENING",
                "notes": "Ajuste conferido",
                "entries": [
                    {"environment_id": templo.id, "quantity": 190},
                    {"environment_id": infantil.id, "quantity": 8},
                ],
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        count.refresh_from_db()
        self.assertEqual(count.date.isoformat(), "2026-09-15")
        self.assertEqual(count.shift, AttendanceCount.Shift.EVENING)
        self.assertEqual(count.notes, "Ajuste conferido")
        self.assertEqual(count.created_by, self.manager)
        self.assertGreater(count.updated_at, old_updated_at)
        self.assertEqual(response.json()["total_people"], 198)

    def test_edicao_rejeita_quantidade_negativa(self):
        self.login_manager()
        templo = CountingEnvironment.objects.create(name="Templo")
        count = self.create_attendance_count_record(entries=[(templo, 10)])

        response = self.client.patch(
            reverse("diaconia-attendance-count-detail", args=[count.pk]),
            self.create_attendance_payload([templo], entries=[{"environment_id": templo.id, "quantity": -1}]),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(AttendanceCountEntry.objects.get(attendance_count=count).quantity, 10)

    def test_edicao_rejeita_ambiente_extra_faltante_e_duplicado(self):
        self.login_manager()
        templo = CountingEnvironment.objects.create(name="Templo")
        infantil = CountingEnvironment.objects.create(name="Infantil")
        novo = CountingEnvironment.objects.create(name="Bercario")
        count = self.create_attendance_count_record(entries=[(templo, 10), (infantil, 5)])
        url = reverse("diaconia-attendance-count-detail", args=[count.pk])

        extra = self.client.patch(
            url,
            self.create_attendance_payload(
                [templo, infantil, novo],
                entries=[
                    {"environment_id": templo.id, "quantity": 10},
                    {"environment_id": infantil.id, "quantity": 5},
                    {"environment_id": novo.id, "quantity": 1},
                ],
            ),
            content_type="application/json",
        )
        missing = self.client.patch(
            url,
            self.create_attendance_payload([templo], entries=[{"environment_id": templo.id, "quantity": 10}]),
            content_type="application/json",
        )
        duplicated = self.client.patch(
            url,
            self.create_attendance_payload(
                [templo],
                entries=[
                    {"environment_id": templo.id, "quantity": 10},
                    {"environment_id": templo.id, "quantity": 11},
                ],
            ),
            content_type="application/json",
        )

        self.assertEqual(extra.status_code, 409)
        self.assertEqual(missing.status_code, 409)
        self.assertEqual(duplicated.status_code, 409)
        self.assertEqual(AttendanceCountEntry.objects.get(attendance_count=count, environment=templo).quantity, 10)

    def test_edicao_rejeita_data_turno_duplicados(self):
        self.login_manager()
        templo = CountingEnvironment.objects.create(name="Templo")
        self.create_attendance_count_record(date="2026-09-15", shift=AttendanceCount.Shift.EVENING, entries=[(templo, 30)])
        count = self.create_attendance_count_record(date="2026-09-14", shift=AttendanceCount.Shift.MORNING, entries=[(templo, 10)])

        response = self.client.patch(
            reverse("diaconia-attendance-count-detail", args=[count.pk]),
            self.create_attendance_payload(
                [templo],
                date="2026-09-15",
                shift="EVENING",
                entries=[{"environment_id": templo.id, "quantity": 11}],
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["message"], "Ja existe uma contagem registrada para esta data e turno.")

    def test_edicao_permite_corrigir_ambiente_historico_inativo(self):
        self.login_manager()
        environment = CountingEnvironment.objects.create(name="Juniores", is_active=False)
        count = self.create_attendance_count_record(entries=[(environment, 15)])

        response = self.client.patch(
            reverse("diaconia-attendance-count-detail", args=[count.pk]),
            self.create_attendance_payload([environment], entries=[{"environment_id": environment.id, "quantity": 17}]),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total_people"], 17)
        self.assertEqual(AttendanceCountEntry.objects.get(attendance_count=count, environment=environment).quantity, 17)

    def test_erro_na_edicao_nao_persiste_parcialmente(self):
        self.login_manager()
        templo = CountingEnvironment.objects.create(name="Templo")
        infantil = CountingEnvironment.objects.create(name="Infantil")
        count = self.create_attendance_count_record(entries=[(templo, 10), (infantil, 5)], notes="Original")

        response = self.client.patch(
            reverse("diaconia-attendance-count-detail", args=[count.pk]),
            self.create_attendance_payload(
                [templo],
                date="2026-09-20",
                shift="EVENING",
                notes="Nao deve salvar",
                entries=[{"environment_id": templo.id, "quantity": 99}],
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 409)
        count.refresh_from_db()
        self.assertEqual(count.date.isoformat(), "2026-09-14")
        self.assertEqual(count.shift, AttendanceCount.Shift.MORNING)
        self.assertEqual(count.notes, "Original")
        self.assertEqual(AttendanceCountEntry.objects.get(attendance_count=count, environment=templo).quantity, 10)

    def test_permissoes_de_edicao_de_contagem(self):
        templo = CountingEnvironment.objects.create(name="Templo")
        count = self.create_attendance_count_record(entries=[(templo, 10)])
        payload = self.create_attendance_payload([templo], entries=[{"environment_id": templo.id, "quantity": 11}])
        url = reverse("diaconia-attendance-count-detail", args=[count.pk])

        self.client.force_login(self.viewer)
        self.assertEqual(self.client.patch(url, payload, content_type="application/json").status_code, 403)

        self.client.force_login(self.no_access)
        self.assertEqual(self.client.patch(url, payload, content_type="application/json").status_code, 403)

        self.client.force_login(self.counting_manager)
        self.assertEqual(self.client.patch(url, payload, content_type="application/json").status_code, 200)

    def test_cria_categoria_de_inventario_com_trim(self):
        self.client.force_login(self.inventory_manager)

        response = self.client.post(
            reverse("diaconia-inventory-category-list"),
            {"name": "  Mobiliario  ", "description": "Cadeiras e mesas"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(InventoryCategory.objects.filter(name="Mobiliario", is_active=True).exists())

    def test_categoria_de_inventario_exige_nome_e_bloqueia_duplicidade(self):
        self.client.force_login(self.inventory_manager)
        InventoryCategory.objects.create(name="Audio")

        blank = self.client.post(
            reverse("diaconia-inventory-category-list"),
            {"name": "   ", "description": ""},
            content_type="application/json",
        )
        duplicate = self.client.post(
            reverse("diaconia-inventory-category-list"),
            {"name": "audio", "description": ""},
            content_type="application/json",
        )

        self.assertEqual(blank.status_code, 400)
        self.assertIn("name", blank.json())
        self.assertEqual(duplicate.status_code, 400)
        self.assertIn("name", duplicate.json())

    def test_edita_inativa_e_reativa_categoria_de_inventario(self):
        self.client.force_login(self.inventory_manager)
        category = InventoryCategory.objects.create(name="Video")

        update = self.client.patch(
            reverse("diaconia-inventory-category-detail", args=[category.pk]),
            {"name": "Video e projecao", "description": "Projetores e telas"},
            content_type="application/json",
        )
        deactivate = self.client.post(reverse("diaconia-inventory-category-deactivate", args=[category.pk]))
        reactivate = self.client.post(reverse("diaconia-inventory-category-reactivate", args=[category.pk]))

        category.refresh_from_db()
        self.assertEqual(update.status_code, 200)
        self.assertEqual(deactivate.status_code, 200)
        self.assertEqual(reactivate.status_code, 200)
        self.assertEqual(category.name, "Video e projecao")
        self.assertTrue(category.is_active)

    def test_filtra_e_busca_categoria_de_inventario(self):
        self.client.force_login(self.viewer)
        InventoryCategory.objects.create(name="Mobiliario")
        InventoryCategory.objects.create(name="Audio", is_active=False)

        active = self.client.get(f"{reverse('diaconia-inventory-category-list')}?status=ACTIVE")
        inactive = self.client.get(f"{reverse('diaconia-inventory-category-list')}?status=INACTIVE")
        search = self.client.get(f"{reverse('diaconia-inventory-category-list')}?search=mob")

        self.assertEqual([item["name"] for item in active.json()], ["Mobiliario"])
        self.assertEqual([item["name"] for item in inactive.json()], ["Audio"])
        self.assertEqual([item["name"] for item in search.json()], ["Mobiliario"])

    def test_permissoes_de_categoria_de_inventario(self):
        category = InventoryCategory.objects.create(name="Mobiliario")

        self.client.force_login(self.viewer)
        self.assertEqual(self.client.get(reverse("diaconia-inventory-category-list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("diaconia-inventory-category-detail", args=[category.pk])).status_code, 200)
        self.assertEqual(
            self.client.post(
                reverse("diaconia-inventory-category-list"),
                {"name": "Sem permissao"},
                content_type="application/json",
            ).status_code,
            403,
        )

        self.client.force_login(self.no_access)
        self.assertEqual(self.client.get(reverse("diaconia-inventory-category-list")).status_code, 403)

    def test_cria_local_de_inventario_com_trim(self):
        self.client.force_login(self.inventory_manager)

        response = self.client.post(
            reverse("diaconia-inventory-location-list"),
            {"name": "  Deposito da Diaconia  ", "description": "Armazenamento"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(InventoryLocation.objects.filter(name="Deposito da Diaconia", is_active=True).exists())

    def test_local_de_inventario_exige_nome_e_bloqueia_duplicidade(self):
        self.client.force_login(self.inventory_manager)
        InventoryLocation.objects.create(name="Templo")

        blank = self.client.post(
            reverse("diaconia-inventory-location-list"),
            {"name": "   ", "description": ""},
            content_type="application/json",
        )
        duplicate = self.client.post(
            reverse("diaconia-inventory-location-list"),
            {"name": "templo", "description": ""},
            content_type="application/json",
        )

        self.assertEqual(blank.status_code, 400)
        self.assertIn("name", blank.json())
        self.assertEqual(duplicate.status_code, 400)
        self.assertIn("name", duplicate.json())

    def test_edita_inativa_e_reativa_local_de_inventario(self):
        self.client.force_login(self.inventory_manager)
        location = InventoryLocation.objects.create(name="Sala Infantil")

        update = self.client.patch(
            reverse("diaconia-inventory-location-detail", args=[location.pk]),
            {"name": "Infantil", "description": "Sala das criancas"},
            content_type="application/json",
        )
        deactivate = self.client.post(reverse("diaconia-inventory-location-deactivate", args=[location.pk]))
        reactivate = self.client.post(reverse("diaconia-inventory-location-reactivate", args=[location.pk]))

        location.refresh_from_db()
        self.assertEqual(update.status_code, 200)
        self.assertEqual(deactivate.status_code, 200)
        self.assertEqual(reactivate.status_code, 200)
        self.assertEqual(location.name, "Infantil")
        self.assertTrue(location.is_active)

    def test_filtra_e_busca_local_de_inventario(self):
        self.client.force_login(self.viewer)
        InventoryLocation.objects.create(name="Templo")
        InventoryLocation.objects.create(name="Deposito", is_active=False)

        active = self.client.get(f"{reverse('diaconia-inventory-location-list')}?status=ACTIVE")
        inactive = self.client.get(f"{reverse('diaconia-inventory-location-list')}?status=INACTIVE")
        search = self.client.get(f"{reverse('diaconia-inventory-location-list')}?search=temp")

        self.assertEqual([item["name"] for item in active.json()], ["Templo"])
        self.assertEqual([item["name"] for item in inactive.json()], ["Deposito"])
        self.assertEqual([item["name"] for item in search.json()], ["Templo"])

    def test_permissoes_de_local_de_inventario(self):
        location = InventoryLocation.objects.create(name="Templo")

        self.client.force_login(self.viewer)
        self.assertEqual(self.client.get(reverse("diaconia-inventory-location-list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("diaconia-inventory-location-detail", args=[location.pk])).status_code, 200)
        self.assertEqual(
            self.client.post(
                reverse("diaconia-inventory-location-list"),
                {"name": "Sem permissao"},
                content_type="application/json",
            ).status_code,
            403,
        )

        self.client.force_login(self.no_access)
        self.assertEqual(self.client.get(reverse("diaconia-inventory-location-list")).status_code, 403)

    def test_cria_item_de_inventario_valido_com_trim(self):
        self.client.force_login(self.inventory_manager)
        category = InventoryCategory.objects.create(name="Mobiliario")

        response = self.client.post(
            reverse("diaconia-inventory-item-list"),
            {"name": "  Cadeira plastica  ", "description": "Branca", "category_id": category.id},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(InventoryItem.objects.filter(name="Cadeira plastica", category=category, is_active=True).exists())
        self.assertEqual(response.json()["category"]["name"], "Mobiliario")

    def test_item_de_inventario_valida_nome_categoria_e_duplicidade(self):
        self.client.force_login(self.inventory_manager)
        category = InventoryCategory.objects.create(name="Mobiliario")
        InventoryItem.objects.create(name="Cadeira plastica", category=category)

        blank_name = self.client.post(
            reverse("diaconia-inventory-item-list"),
            {"name": "   ", "description": "", "category_id": category.id},
            content_type="application/json",
        )
        missing_category = self.client.post(
            reverse("diaconia-inventory-item-list"),
            {"name": "Mesa", "description": ""},
            content_type="application/json",
        )
        duplicated = self.client.post(
            reverse("diaconia-inventory-item-list"),
            {"name": "cadeira plastica", "description": "", "category_id": category.id},
            content_type="application/json",
        )
        nonexistent = self.client.post(
            reverse("diaconia-inventory-item-list"),
            {"name": "Projetor", "description": "", "category_id": 999},
            content_type="application/json",
        )

        self.assertEqual(blank_name.status_code, 400)
        self.assertIn("name", blank_name.json())
        self.assertEqual(missing_category.status_code, 400)
        self.assertIn("category_id", missing_category.json())
        self.assertEqual(duplicated.status_code, 400)
        self.assertIn("name", duplicated.json())
        self.assertEqual(nonexistent.status_code, 400)
        self.assertIn("category_id", nonexistent.json())

    def test_item_rejeita_categoria_inativa_na_criacao(self):
        self.client.force_login(self.inventory_manager)
        category = InventoryCategory.objects.create(name="Audio", is_active=False)

        response = self.client.post(
            reverse("diaconia-inventory-item-list"),
            {"name": "Caixa de som", "description": "", "category_id": category.id},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["category_id"][0], "A categoria selecionada esta inativa.")
        self.assertFalse(InventoryItem.objects.exists())

    def test_edita_item_de_inventario_e_troca_para_categoria_ativa(self):
        self.client.force_login(self.inventory_manager)
        old_category = InventoryCategory.objects.create(name="Mobiliario")
        new_category = InventoryCategory.objects.create(name="Equipamentos")
        item = InventoryItem.objects.create(name="Mesa", category=old_category)

        response = self.client.patch(
            reverse("diaconia-inventory-item-detail", args=[item.pk]),
            {"name": "Mesa dobravel", "description": "1,80m", "category_id": new_category.id},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        item.refresh_from_db()
        self.assertEqual(item.name, "Mesa dobravel")
        self.assertEqual(item.description, "1,80m")
        self.assertEqual(item.category, new_category)

    def test_edicao_mantem_categoria_atual_inativa_mas_nao_troca_para_outra_inativa(self):
        self.client.force_login(self.inventory_manager)
        current_category = InventoryCategory.objects.create(name="Mobiliario", is_active=False)
        other_inactive = InventoryCategory.objects.create(name="Audio", is_active=False)
        item = InventoryItem.objects.create(name="Cadeira", category=current_category)

        keep_current = self.client.patch(
            reverse("diaconia-inventory-item-detail", args=[item.pk]),
            {"name": "Cadeira plastica", "description": "", "category_id": current_category.id},
            content_type="application/json",
        )
        change_to_inactive = self.client.patch(
            reverse("diaconia-inventory-item-detail", args=[item.pk]),
            {"name": "Cadeira plastica", "description": "", "category_id": other_inactive.id},
            content_type="application/json",
        )

        self.assertEqual(keep_current.status_code, 200)
        self.assertEqual(change_to_inactive.status_code, 400)
        self.assertEqual(change_to_inactive.json()["category_id"][0], "A categoria selecionada esta inativa.")

    def test_inativa_reativa_e_consulta_item_inativo_de_inventario(self):
        self.client.force_login(self.inventory_manager)
        category = InventoryCategory.objects.create(name="Mobiliario")
        item = InventoryItem.objects.create(name="Cadeira", category=category)

        deactivate = self.client.post(reverse("diaconia-inventory-item-deactivate", args=[item.pk]))
        detail = self.client.get(reverse("diaconia-inventory-item-detail", args=[item.pk]))
        reactivate = self.client.post(reverse("diaconia-inventory-item-reactivate", args=[item.pk]))

        item.refresh_from_db()
        self.assertEqual(deactivate.status_code, 200)
        self.assertEqual(detail.status_code, 200)
        self.assertFalse(detail.json()["is_active"])
        self.assertEqual(reactivate.status_code, 200)
        self.assertTrue(item.is_active)

    def test_filtra_itens_de_inventario(self):
        self.client.force_login(self.viewer)
        mobiliario = InventoryCategory.objects.create(name="Mobiliario")
        audio = InventoryCategory.objects.create(name="Audio")
        InventoryItem.objects.create(name="Cadeira plastica", category=mobiliario)
        InventoryItem.objects.create(name="Caixa de som", category=audio, is_active=False)

        search = self.client.get(f"{reverse('diaconia-inventory-item-list')}?search=cadeira")
        by_category = self.client.get(f"{reverse('diaconia-inventory-item-list')}?category={audio.id}")
        active = self.client.get(f"{reverse('diaconia-inventory-item-list')}?status=ACTIVE")
        inactive = self.client.get(f"{reverse('diaconia-inventory-item-list')}?status=INACTIVE")
        combined = self.client.get(f"{reverse('diaconia-inventory-item-list')}?search=caixa&category={audio.id}&status=INACTIVE")

        self.assertEqual([item["name"] for item in search.json()], ["Cadeira plastica"])
        self.assertEqual([item["name"] for item in by_category.json()], ["Caixa de som"])
        self.assertEqual([item["name"] for item in active.json()], ["Cadeira plastica"])
        self.assertEqual([item["name"] for item in inactive.json()], ["Caixa de som"])
        self.assertEqual([item["name"] for item in combined.json()], ["Caixa de som"])

    def test_permissoes_de_item_de_inventario(self):
        category = InventoryCategory.objects.create(name="Mobiliario")
        item = InventoryItem.objects.create(name="Cadeira", category=category)
        payload = {"name": "Mesa", "description": "", "category_id": category.id}

        self.client.force_login(self.viewer)
        self.assertEqual(self.client.get(reverse("diaconia-inventory-item-list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("diaconia-inventory-item-detail", args=[item.pk])).status_code, 200)
        self.assertEqual(self.client.post(reverse("diaconia-inventory-item-list"), payload, content_type="application/json").status_code, 403)
        self.assertEqual(self.client.patch(reverse("diaconia-inventory-item-detail", args=[item.pk]), payload, content_type="application/json").status_code, 403)

        self.client.force_login(self.no_access)
        self.assertEqual(self.client.get(reverse("diaconia-inventory-item-list")).status_code, 403)

        self.client.force_login(self.inventory_manager)
        self.assertEqual(self.client.post(reverse("diaconia-inventory-item-list"), payload, content_type="application/json").status_code, 201)

    def test_model_inventory_count_constraints(self):
        item = self.create_inventory_item_record(name="Cadeira")
        location = InventoryLocation.objects.create(name="Templo")
        count = InventoryCount.objects.create(date="2026-09-15", created_by=self.inventory_manager)

        InventoryCountEntry.objects.create(inventory_count=count, item=item, location=location, quantity=0)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                InventoryCount.objects.create(date="2026-09-15", created_by=self.inventory_manager)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                InventoryCount.objects.create(date="2026-09-16")

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                InventoryCountEntry.objects.create(inventory_count=count, item=item, location=location, quantity=1)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                InventoryCountEntry.objects.create(
                    inventory_count=InventoryCount.objects.create(date="2026-09-17", created_by=self.inventory_manager),
                    item=item,
                    location=location,
                    quantity=-1,
                )

    def test_cria_contagem_de_inventario_valida_com_matriz_completa(self):
        self.client.force_login(self.inventory_manager)
        category = InventoryCategory.objects.create(name="Mobiliario")
        cadeira = self.create_inventory_item_record(name="Cadeira plastica", category=category)
        mesa = self.create_inventory_item_record(name="Mesa dobravel", category=category)
        templo = InventoryLocation.objects.create(name="Templo")
        deposito = InventoryLocation.objects.create(name="Deposito")
        payload = {
            "date": "2026-09-15",
            "notes": "Contagem geral realizada pela Diaconia.",
            "entries": [
                {"item_id": cadeira.id, "location_id": templo.id, "quantity": 180},
                {"item_id": cadeira.id, "location_id": deposito.id, "quantity": 15},
                {"item_id": mesa.id, "location_id": templo.id, "quantity": 12},
                {"item_id": mesa.id, "location_id": deposito.id, "quantity": 8},
            ],
        }

        response = self.client.post(reverse("diaconia-inventory-count-list"), payload, content_type="application/json")

        self.assertEqual(response.status_code, 201)
        count = InventoryCount.objects.get()
        self.assertEqual(count.created_by, self.inventory_manager)
        self.assertEqual(count.notes, "Contagem geral realizada pela Diaconia.")
        self.assertEqual(InventoryCountEntry.objects.count(), 4)
        items = response.json()["items"]
        self.assertEqual(items[0]["item_name"], "Cadeira plastica")
        self.assertEqual(items[0]["total"], 195)
        self.assertEqual(items[1]["total"], 20)

    def test_cria_contagem_de_inventario_com_observacao_opcional(self):
        self.client.force_login(self.inventory_manager)
        payload = self.create_inventory_count_payload(notes="")
        payload.pop("notes")

        response = self.client.post(reverse("diaconia-inventory-count-list"), payload, content_type="application/json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(InventoryCount.objects.get().notes, "")

    def test_contagem_de_inventario_rejeita_data_duplicada_e_preserva_transacao(self):
        self.client.force_login(self.inventory_manager)
        payload = self.create_inventory_count_payload()
        InventoryCount.objects.create(date="2026-09-15", created_by=self.inventory_manager)

        response = self.client.post(reverse("diaconia-inventory-count-list"), payload, content_type="application/json")

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["code"], "INVENTORY_COUNT_DUPLICATE")
        self.assertEqual(InventoryCount.objects.count(), 1)
        self.assertEqual(InventoryCountEntry.objects.count(), 0)

    def test_contagem_de_inventario_rejeita_matriz_incompleta_extra_e_duplicada(self):
        self.client.force_login(self.inventory_manager)
        item = self.create_inventory_item_record(name="Cadeira")
        extra_item = self.create_inventory_item_record(name="Mesa", is_active=False)
        templo = InventoryLocation.objects.create(name="Templo")
        deposito = InventoryLocation.objects.create(name="Deposito")
        base_payload = self.create_inventory_count_payload(items=[item], locations=[templo, deposito])

        missing = {**base_payload, "entries": base_payload["entries"][:1]}
        duplicate = {**base_payload, "entries": [*base_payload["entries"], base_payload["entries"][0]]}
        extra = {
            **base_payload,
            "entries": [*base_payload["entries"], {"item_id": extra_item.id, "location_id": templo.id, "quantity": 0}],
        }

        for payload in (missing, duplicate, extra):
            response = self.client.post(reverse("diaconia-inventory-count-list"), payload, content_type="application/json")
            self.assertEqual(response.status_code, 409)
            self.assertEqual(response.json()["code"], "INVENTORY_COUNT_MATRIX_MISMATCH")

        self.assertEqual(InventoryCount.objects.count(), 0)
        self.assertEqual(InventoryCountEntry.objects.count(), 0)

    def test_contagem_de_inventario_rejeita_item_e_local_invalidos_ou_inativos(self):
        self.client.force_login(self.inventory_manager)
        item = self.create_inventory_item_record(name="Cadeira")
        inactive_item = self.create_inventory_item_record(name="Mesa", is_active=False)
        templo = InventoryLocation.objects.create(name="Templo")
        inactive_location = InventoryLocation.objects.create(name="Deposito", is_active=False)
        valid_payload = self.create_inventory_count_payload(items=[item], locations=[templo])

        item_inativo = {
            **valid_payload,
            "entries": [{"item_id": inactive_item.id, "location_id": templo.id, "quantity": 0}],
        }
        local_inativo = {
            **valid_payload,
            "entries": [{"item_id": item.id, "location_id": inactive_location.id, "quantity": 0}],
        }
        item_inexistente = {
            **valid_payload,
            "entries": [{"item_id": 99999, "location_id": templo.id, "quantity": 0}],
        }
        local_inexistente = {
            **valid_payload,
            "entries": [{"item_id": item.id, "location_id": 99999, "quantity": 0}],
        }
        quantidade_negativa = {
            **valid_payload,
            "entries": [{"item_id": item.id, "location_id": templo.id, "quantity": -1}],
        }

        for payload in (item_inativo, local_inativo):
            response = self.client.post(reverse("diaconia-inventory-count-list"), payload, content_type="application/json")
            self.assertEqual(response.status_code, 409)
            self.assertEqual(response.json()["code"], "INVENTORY_COUNT_MATRIX_MISMATCH")

        for payload in (item_inexistente, local_inexistente, quantidade_negativa):
            response = self.client.post(reverse("diaconia-inventory-count-list"), payload, content_type="application/json")
            self.assertEqual(response.status_code, 400)

        self.assertEqual(InventoryCount.objects.count(), 0)

    def test_contagem_de_inventario_rejeita_sem_itens_ou_sem_locais_ativos(self):
        self.client.force_login(self.inventory_manager)
        item = self.create_inventory_item_record(name="Cadeira")
        location = InventoryLocation.objects.create(name="Templo")

        item.is_active = False
        item.save(update_fields=["is_active", "updated_at"])
        response_without_items = self.client.post(
            reverse("diaconia-inventory-count-list"),
            {"date": "2026-09-15", "entries": [{"item_id": item.id, "location_id": location.id, "quantity": 0}]},
            content_type="application/json",
        )

        item.is_active = True
        item.save(update_fields=["is_active", "updated_at"])
        location.is_active = False
        location.save(update_fields=["is_active", "updated_at"])
        response_without_locations = self.client.post(
            reverse("diaconia-inventory-count-list"),
            {"date": "2026-09-15", "entries": [{"item_id": item.id, "location_id": location.id, "quantity": 0}]},
            content_type="application/json",
        )

        self.assertEqual(response_without_items.status_code, 409)
        self.assertEqual(response_without_items.json()["code"], "INVENTORY_COUNT_WITHOUT_ITEMS")
        self.assertEqual(response_without_locations.status_code, 409)
        self.assertEqual(response_without_locations.json()["code"], "INVENTORY_COUNT_WITHOUT_LOCATIONS")

    def test_detalhe_de_contagem_de_inventario_preserva_composicao_historica(self):
        self.client.force_login(self.inventory_manager)
        item = self.create_inventory_item_record(name="Cadeira")
        templo = InventoryLocation.objects.create(name="Templo")
        payload = self.create_inventory_count_payload(items=[item], locations=[templo])
        create_response = self.client.post(reverse("diaconia-inventory-count-list"), payload, content_type="application/json")
        count_id = create_response.json()["id"]

        InventoryLocation.objects.create(name="Sala Jovens")
        detail_response = self.client.get(reverse("diaconia-inventory-count-detail", args=[count_id]))

        self.assertEqual(detail_response.status_code, 200)
        locations = detail_response.json()["items"][0]["locations"]
        self.assertEqual([location["location_name"] for location in locations], ["Templo"])

    def test_detalhe_de_contagem_de_inventario_exibe_item_e_local_inativados_depois(self):
        self.client.force_login(self.inventory_manager)
        item = self.create_inventory_item_record(name="Cadeira")
        templo = InventoryLocation.objects.create(name="Templo")
        payload = self.create_inventory_count_payload(items=[item], locations=[templo])
        create_response = self.client.post(reverse("diaconia-inventory-count-list"), payload, content_type="application/json")
        count_id = create_response.json()["id"]
        item.is_active = False
        item.save(update_fields=["is_active", "updated_at"])
        templo.is_active = False
        templo.save(update_fields=["is_active", "updated_at"])

        detail_response = self.client.get(reverse("diaconia-inventory-count-detail", args=[count_id]))

        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.json()["items"][0]["item_name"], "Cadeira")
        self.assertEqual(detail_response.json()["items"][0]["locations"][0]["location_name"], "Templo")

    def test_permissoes_de_contagem_de_inventario(self):
        item = self.create_inventory_item_record(name="Cadeira")
        location = InventoryLocation.objects.create(name="Templo")
        payload = self.create_inventory_count_payload(items=[item], locations=[location])

        self.client.force_login(self.viewer)
        create_as_viewer = self.client.post(reverse("diaconia-inventory-count-list"), payload, content_type="application/json")

        self.client.force_login(self.inventory_manager)
        create_as_manager = self.client.post(reverse("diaconia-inventory-count-list"), payload, content_type="application/json")
        detail_url = reverse("diaconia-inventory-count-detail", args=[create_as_manager.json()["id"]])

        self.client.force_login(self.viewer)
        detail_as_viewer = self.client.get(detail_url)

        self.client.force_login(self.no_access)
        detail_without_access = self.client.get(detail_url)
        create_without_access = self.client.post(
            reverse("diaconia-inventory-count-list"),
            {**payload, "date": "2026-09-16"},
            content_type="application/json",
        )

        self.assertEqual(create_as_viewer.status_code, 403)
        self.assertEqual(create_as_manager.status_code, 201)
        self.assertEqual(detail_as_viewer.status_code, 200)
        self.assertEqual(detail_without_access.status_code, 403)
        self.assertEqual(create_without_access.status_code, 403)

    def test_lista_contagens_de_inventario_com_ordenacao_filtros_e_permissao(self):
        item = self.create_inventory_item_record(name="Cadeira")
        templo = InventoryLocation.objects.create(name="Templo")
        deposito = InventoryLocation.objects.create(name="Deposito")
        self.create_inventory_count_record(date="2026-09-01", entries=[(item, templo, 10)], user=self.viewer)
        latest = self.create_inventory_count_record(date="2026-09-15", entries=[(item, templo, 12), (item, deposito, 3)])
        self.create_inventory_count_record(date="2026-08-01", entries=[(item, templo, 9)])

        self.client.force_login(self.viewer)
        response = self.client.get(reverse("diaconia-inventory-count-list"))
        filtered_from = self.client.get(f"{reverse('diaconia-inventory-count-list')}?date_from=2026-09-10")
        filtered_to = self.client.get(f"{reverse('diaconia-inventory-count-list')}?date_to=2026-09-01")
        filtered_user = self.client.get(f"{reverse('diaconia-inventory-count-list')}?created_by={self.viewer.id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["date"] for item in response.json()], ["2026-09-15", "2026-09-01", "2026-08-01"])
        self.assertEqual(response.json()[0]["id"], latest.id)
        self.assertEqual(response.json()[0]["items_count"], 1)
        self.assertEqual(response.json()[0]["locations_count"], 2)
        self.assertEqual([item["date"] for item in filtered_from.json()], ["2026-09-15"])
        self.assertEqual([item["date"] for item in filtered_to.json()], ["2026-09-01", "2026-08-01"])
        self.assertEqual([item["date"] for item in filtered_user.json()], ["2026-09-01"])

        self.client.force_login(self.no_access)
        self.assertEqual(self.client.get(reverse("diaconia-inventory-count-list")).status_code, 403)

    def test_corrige_contagem_de_inventario_preservando_responsavel_criacao_e_composicao(self):
        item = self.create_inventory_item_record(name="Cadeira")
        templo = InventoryLocation.objects.create(name="Templo")
        deposito = InventoryLocation.objects.create(name="Deposito")
        count = self.create_inventory_count_record(
            date="2026-09-15",
            user=self.viewer,
            notes="Original",
            entries=[(item, templo, 10), (item, deposito, 0)],
        )
        original_created_at = count.created_at
        payload = {
            "date": "2026-09-16",
            "notes": "Corrigida",
            "entries": [
                {"item_id": item.id, "location_id": templo.id, "quantity": 12},
                {"item_id": item.id, "location_id": deposito.id, "quantity": 1},
            ],
        }

        self.client.force_login(self.inventory_manager)
        response = self.client.patch(reverse("diaconia-inventory-count-detail", args=[count.id]), payload, content_type="application/json")

        self.assertEqual(response.status_code, 200)
        count.refresh_from_db()
        self.assertEqual(str(count.date), "2026-09-16")
        self.assertEqual(count.notes, "Corrigida")
        self.assertEqual(count.created_by, self.viewer)
        self.assertEqual(count.created_at, original_created_at)
        self.assertEqual(InventoryCountEntry.objects.get(inventory_count=count, location=templo).quantity, 12)
        self.assertEqual(InventoryCountEntry.objects.get(inventory_count=count, location=deposito).quantity, 1)

    def test_corrige_contagem_rejeita_data_duplicada_matriz_invalida_e_quantidade_negativa(self):
        item = self.create_inventory_item_record(name="Cadeira")
        extra_item = self.create_inventory_item_record(name="Mesa")
        templo = InventoryLocation.objects.create(name="Templo")
        deposito = InventoryLocation.objects.create(name="Deposito")
        extra_location = InventoryLocation.objects.create(name="Juniores")
        count = self.create_inventory_count_record(date="2026-09-15", entries=[(item, templo, 10), (item, deposito, 2)])
        self.create_inventory_count_record(date="2026-09-16", entries=[(item, templo, 9)])
        valid_entries = [
            {"item_id": item.id, "location_id": templo.id, "quantity": 10},
            {"item_id": item.id, "location_id": deposito.id, "quantity": 2},
        ]

        self.client.force_login(self.inventory_manager)
        duplicate_date = self.client.patch(
            reverse("diaconia-inventory-count-detail", args=[count.id]),
            {"date": "2026-09-16", "notes": "", "entries": valid_entries},
            content_type="application/json",
        )
        missing = self.client.patch(
            reverse("diaconia-inventory-count-detail", args=[count.id]),
            {"date": "2026-09-15", "notes": "", "entries": valid_entries[:1]},
            content_type="application/json",
        )
        duplicated = self.client.patch(
            reverse("diaconia-inventory-count-detail", args=[count.id]),
            {"date": "2026-09-15", "notes": "", "entries": [*valid_entries, valid_entries[0]]},
            content_type="application/json",
        )
        extra_item_response = self.client.patch(
            reverse("diaconia-inventory-count-detail", args=[count.id]),
            {"date": "2026-09-15", "notes": "", "entries": [*valid_entries, {"item_id": extra_item.id, "location_id": templo.id, "quantity": 1}]},
            content_type="application/json",
        )
        extra_location_response = self.client.patch(
            reverse("diaconia-inventory-count-detail", args=[count.id]),
            {"date": "2026-09-15", "notes": "", "entries": [*valid_entries, {"item_id": item.id, "location_id": extra_location.id, "quantity": 1}]},
            content_type="application/json",
        )
        negative = self.client.patch(
            reverse("diaconia-inventory-count-detail", args=[count.id]),
            {"date": "2026-09-15", "notes": "", "entries": [{**valid_entries[0], "quantity": -1}, valid_entries[1]]},
            content_type="application/json",
        )

        self.assertEqual(duplicate_date.status_code, 409)
        self.assertEqual(duplicate_date.json()["code"], "INVENTORY_COUNT_DUPLICATE")
        for response in (missing, duplicated, extra_item_response, extra_location_response):
            self.assertEqual(response.status_code, 409)
            self.assertEqual(response.json()["code"], "INVENTORY_COUNT_MATRIX_MISMATCH")
        self.assertEqual(negative.status_code, 400)
        count.refresh_from_db()
        self.assertEqual(str(count.date), "2026-09-15")
        self.assertEqual(InventoryCountEntry.objects.get(inventory_count=count, location=templo).quantity, 10)

    def test_corrige_contagem_aceita_item_e_local_inativados_posteriormente(self):
        item = self.create_inventory_item_record(name="Cadeira")
        location = InventoryLocation.objects.create(name="Templo")
        count = self.create_inventory_count_record(date="2026-09-15", entries=[(item, location, 10)])
        item.is_active = False
        item.save(update_fields=["is_active", "updated_at"])
        location.is_active = False
        location.save(update_fields=["is_active", "updated_at"])

        self.client.force_login(self.inventory_manager)
        response = self.client.patch(
            reverse("diaconia-inventory-count-detail", args=[count.id]),
            {"date": "2026-09-15", "notes": "", "entries": [{"item_id": item.id, "location_id": location.id, "quantity": 11}]},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(InventoryCountEntry.objects.get(inventory_count=count).quantity, 11)

    def test_permissoes_de_correcao_de_contagem_de_inventario(self):
        item = self.create_inventory_item_record(name="Cadeira")
        location = InventoryLocation.objects.create(name="Templo")
        count = self.create_inventory_count_record(date="2026-09-15", entries=[(item, location, 10)])
        payload = {"date": "2026-09-15", "notes": "", "entries": [{"item_id": item.id, "location_id": location.id, "quantity": 10}]}

        self.client.force_login(self.viewer)
        self.assertEqual(self.client.patch(reverse("diaconia-inventory-count-detail", args=[count.id]), payload, content_type="application/json").status_code, 403)

        self.client.force_login(self.inventory_manager)
        self.assertEqual(self.client.patch(reverse("diaconia-inventory-count-detail", args=[count.id]), payload, content_type="application/json").status_code, 200)

    def test_comparativo_de_inventario_basico_statuses_e_percentual_zero(self):
        categoria = InventoryCategory.objects.create(name="Mobiliario")
        cadeira = self.create_inventory_item_record(name="Cadeira", category=categoria)
        mesa = self.create_inventory_item_record(name="Mesa", category=categoria)
        ventilador = self.create_inventory_item_record(name="Ventilador", category=categoria)
        microfone = self.create_inventory_item_record(name="Microfone", category=categoria)
        templo = InventoryLocation.objects.create(name="Templo")
        deposito = InventoryLocation.objects.create(name="Deposito")
        self.create_inventory_count_record(
            date="2026-09-01",
            entries=[(cadeira, templo, 180), (cadeira, deposito, 65), (mesa, templo, 26), (ventilador, templo, 15), (microfone, templo, 0)],
        )
        current = self.create_inventory_count_record(
            date="2026-09-15",
            entries=[(cadeira, templo, 177), (cadeira, deposito, 64), (mesa, templo, 27), (ventilador, templo, 15), (microfone, templo, 5)],
        )

        self.client.force_login(self.viewer)
        response = self.client.get(reverse("diaconia-inventory-count-comparison", args=[current.id]))

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["previous"]["date"], "2026-09-01")
        by_name = {item["item_name"]: item for item in data["items"]}
        self.assertEqual(by_name["Cadeira"]["previous_total"], 245)
        self.assertEqual(by_name["Cadeira"]["current_total"], 241)
        self.assertEqual(by_name["Cadeira"]["variation"], -4)
        self.assertEqual(by_name["Cadeira"]["variation_percent"], -1.63)
        self.assertEqual(by_name["Cadeira"]["status"], "DECREASE")
        self.assertEqual(by_name["Mesa"]["status"], "INCREASE")
        self.assertEqual(by_name["Ventilador"]["status"], "UNCHANGED")
        self.assertEqual(by_name["Microfone"]["variation"], 5)
        self.assertIsNone(by_name["Microfone"]["variation_percent"])

    def test_comparativo_primeira_contagem_nao_compara_contra_zero(self):
        item = self.create_inventory_item_record(name="Cadeira")
        location = InventoryLocation.objects.create(name="Templo")
        count = self.create_inventory_count_record(date="2026-09-01", entries=[(item, location, 10)])

        self.client.force_login(self.viewer)
        response = self.client.get(reverse("diaconia-inventory-count-comparison", args=[count.id]))

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["previous"])
        self.assertEqual(response.json()["items"], [])
        self.assertEqual(response.json()["summary"]["increase"], 0)

    def test_comparativo_trata_item_novo_e_nao_contabilizado_sem_falsa_variacao(self):
        cadeira = self.create_inventory_item_record(name="Cadeira")
        mesa = self.create_inventory_item_record(name="Mesa")
        projetor = self.create_inventory_item_record(name="Projetor")
        templo = InventoryLocation.objects.create(name="Templo")
        self.create_inventory_count_record(date="2026-09-01", entries=[(cadeira, templo, 10), (mesa, templo, 5)])
        current = self.create_inventory_count_record(date="2026-09-15", entries=[(cadeira, templo, 12), (projetor, templo, 1)])

        self.client.force_login(self.viewer)
        response = self.client.get(reverse("diaconia-inventory-count-comparison", args=[current.id]))

        by_name = {item["item_name"]: item for item in response.json()["items"]}
        self.assertEqual(by_name["Projetor"]["status"], "NEW")
        self.assertIsNone(by_name["Projetor"]["variation"])
        self.assertEqual(by_name["Mesa"]["status"], "NOT_COUNTED")
        self.assertIsNone(by_name["Mesa"]["variation"])

    def test_comparativo_trata_local_novo_ausente_e_redistribuicao(self):
        cadeira = self.create_inventory_item_record(name="Cadeira")
        templo = InventoryLocation.objects.create(name="Templo")
        juniores = InventoryLocation.objects.create(name="Juniores")
        deposito = InventoryLocation.objects.create(name="Deposito")
        self.create_inventory_count_record(date="2026-09-01", entries=[(cadeira, templo, 180), (cadeira, juniores, 20), (cadeira, deposito, 5)])
        current = self.create_inventory_count_record(date="2026-09-15", entries=[(cadeira, templo, 170), (cadeira, juniores, 30)])

        self.client.force_login(self.viewer)
        response = self.client.get(reverse("diaconia-inventory-count-comparison", args=[current.id]))

        item = response.json()["items"][0]
        self.assertEqual(item["previous_total"], 205)
        self.assertEqual(item["current_total"], 200)
        locations = {location["location_name"]: location for location in item["locations"]}
        self.assertEqual(locations["Templo"]["variation"], -10)
        self.assertEqual(locations["Juniores"]["variation"], 10)
        self.assertEqual(locations["Deposito"]["status"], "NOT_COUNTED")

        sala = InventoryLocation.objects.create(name="Sala Jovens")
        later = self.create_inventory_count_record(date="2026-09-30", entries=[(cadeira, templo, 170), (cadeira, juniores, 30), (cadeira, sala, 4)])
        response_later = self.client.get(reverse("diaconia-inventory-count-comparison", args=[later.id]))
        later_locations = {location["location_name"]: location for location in response_later.json()["items"][0]["locations"]}
        self.assertEqual(later_locations["Sala Jovens"]["status"], "NEW")

    def test_comparativo_redistribuicao_sem_alteracao_total(self):
        cadeira = self.create_inventory_item_record(name="Cadeira")
        templo = InventoryLocation.objects.create(name="Templo")
        juniores = InventoryLocation.objects.create(name="Juniores")
        self.create_inventory_count_record(date="2026-09-01", entries=[(cadeira, templo, 180), (cadeira, juniores, 20)])
        current = self.create_inventory_count_record(date="2026-09-15", entries=[(cadeira, templo, 170), (cadeira, juniores, 30)])

        self.client.force_login(self.viewer)
        response = self.client.get(reverse("diaconia-inventory-count-comparison", args=[current.id]))

        item = response.json()["items"][0]
        self.assertEqual(item["previous_total"], 200)
        self.assertEqual(item["current_total"], 200)
        self.assertEqual(item["variation"], 0)
        self.assertEqual(item["status"], "UNCHANGED")
        locations = {location["location_name"]: location for location in item["locations"]}
        self.assertEqual(locations["Templo"]["variation"], -10)
        self.assertEqual(locations["Juniores"]["variation"], 10)
