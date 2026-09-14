from datetime import datetime

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import AttendanceCount, AttendanceCountEntry, CountingEnvironment, StockCategory, StockItem, StockMovement
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
        self.no_access = self.user_model.objects.create_user(username="diaconia.no.access", password="senha-forte-123")
        view_permission = Permission.objects.get(content_type__app_label="diaconia", codename="view_diaconia_module")
        manage_permission = Permission.objects.get(content_type__app_label="diaconia", codename="manage_diaconia_stock")
        counting_permission = Permission.objects.get(
            content_type__app_label="diaconia",
            codename="manage_diaconia_counting",
        )
        self.viewer.user_permissions.add(view_permission)
        self.manager.user_permissions.add(view_permission, manage_permission, counting_permission)
        self.counting_manager.user_permissions.add(view_permission, counting_permission)

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
