from django.core.management.base import BaseCommand, CommandError

from core.email import send_transactional_email
from core.email.exceptions import EmailConfigurationError, EmailDeliveryError


class Command(BaseCommand):
    help = "Envia um e-mail transacional de teste pelo provedor configurado."

    def add_arguments(self, parser):
        parser.add_argument("recipient", help="Endereco de e-mail que recebera o teste.")

    def handle(self, *args, **options):
        recipient = options["recipient"]
        try:
            result = send_transactional_email(
                to=recipient,
                subject="Teste de e-mail - Portal Verbo da Vida",
                html=(
                    "<p>Ola!</p>"
                    "<p>Este e um e-mail de teste enviado pelo Portal Verbo da Vida.</p>"
                    "<p>Se voce recebeu esta mensagem, a integracao Django -> Resend esta funcionando.</p>"
                ),
                text=(
                    "Ola!\n\n"
                    "Este e um e-mail de teste enviado pelo Portal Verbo da Vida.\n\n"
                    "Se voce recebeu esta mensagem, a integracao Django -> Resend esta funcionando."
                ),
                idempotency_key=None,
            )
        except EmailConfigurationError as exc:
            raise CommandError(str(exc)) from exc
        except EmailDeliveryError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS("Email enviado com sucesso."))
        self.stdout.write(f"Provider: {result.provider}")
        self.stdout.write(f"Message ID: {result.message_id}")
