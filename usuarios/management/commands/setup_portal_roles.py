from django.core.management.base import BaseCommand

from usuarios.roles import ROLE_PERMISSIONS, setup_portal_roles


class Command(BaseCommand):
    help = "Cria e sincroniza as Global Roles funcionais do Portal."

    def handle(self, *args, **options):
        groups = setup_portal_roles()
        for group in groups:
            self.stdout.write(
                self.style.SUCCESS(
                    f"{group.name}: {len(ROLE_PERMISSIONS[group.name])} permissions"
                )
            )
