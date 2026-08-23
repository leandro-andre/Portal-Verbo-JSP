from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("departamentos", "0007_departamento_lifecycle_permissions"),
        ("pessoas", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="DepartmentRole",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, verbose_name="Nome")),
                ("code", models.SlugField(max_length=60, verbose_name="Codigo")),
                ("active", models.BooleanField(default=True, verbose_name="Ativo")),
                (
                    "can_manage_department",
                    models.BooleanField(default=False, verbose_name="Pode gerenciar departamento"),
                ),
                ("can_manage_members", models.BooleanField(default=False, verbose_name="Pode gerenciar pessoas")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Atualizado em")),
                (
                    "department",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="roles",
                        to="departamentos.departamento",
                        verbose_name="Departamento",
                    ),
                ),
            ],
            options={
                "verbose_name": "Cargo de departamento",
                "verbose_name_plural": "Cargos de departamento",
                "ordering": ["department__nome", "name", "id"],
                "permissions": [
                    ("deactivate_departmentrole", "Can deactivate department role"),
                    ("reactivate_departmentrole", "Can reactivate department role"),
                ],
            },
        ),
        migrations.CreateModel(
            name="DepartmentMembership",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "status",
                    models.CharField(
                        choices=[("ACTIVE", "Ativa"), ("INACTIVE", "Inativa")],
                        default="ACTIVE",
                        max_length=20,
                        verbose_name="Status",
                    ),
                ),
                (
                    "joined_at",
                    models.DateField(default=django.utils.timezone.localdate, verbose_name="Data de entrada"),
                ),
                ("left_at", models.DateField(blank=True, null=True, verbose_name="Data de saida")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Atualizado em")),
                (
                    "department",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="department_memberships",
                        to="departamentos.departamento",
                        verbose_name="Departamento",
                    ),
                ),
                (
                    "person",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="department_memberships",
                        to="pessoas.person",
                        verbose_name="Pessoa",
                    ),
                ),
                (
                    "role",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="memberships",
                        to="departamentos.departmentrole",
                        verbose_name="Cargo",
                    ),
                ),
            ],
            options={
                "verbose_name": "Pessoa no departamento",
                "verbose_name_plural": "Pessoas nos departamentos",
                "ordering": ["department__nome", "person__full_name", "id"],
                "permissions": [
                    ("deactivate_departmentmembership", "Can deactivate department membership"),
                    ("reactivate_departmentmembership", "Can reactivate department membership"),
                ],
            },
        ),
        migrations.AddConstraint(
            model_name="departmentrole",
            constraint=models.UniqueConstraint(
                fields=("department", "code"),
                name="uniq_department_role_code_per_department",
            ),
        ),
        migrations.AddConstraint(
            model_name="departmentmembership",
            constraint=models.UniqueConstraint(
                fields=("person", "department"),
                name="uniq_department_membership_person_department",
            ),
        ),
    ]
