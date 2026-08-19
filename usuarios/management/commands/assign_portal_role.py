from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError

from usuarios.roles import ROLE_CODES, setup_portal_roles


class Command(BaseCommand):
    help = "Atribui uma Global Role permitida a um usuario."

    def add_arguments(self, parser):
        parser.add_argument("username")
        parser.add_argument("role_code", choices=ROLE_CODES.values())

    def handle(self, *args, **options):
        setup_portal_roles()
        role_code = options["role_code"]
        group_name = next(
            group_name
            for group_name, code in ROLE_CODES.items()
            if code == role_code
        )
        user_model = get_user_model()
        try:
            usuario = user_model.objects.get(username=options["username"])
        except user_model.DoesNotExist as exc:
            raise CommandError("Usuario nao encontrado.") from exc

        group = Group.objects.get(name=group_name)
        usuario.groups.add(group)
        self.stdout.write(
            self.style.SUCCESS(f"{usuario.username} recebeu a role {role_code}.")
        )
