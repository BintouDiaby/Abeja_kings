from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
import os


class Command(BaseCommand):
    help = "Send an example email (uses current EMAIL_BACKEND)."

    def add_arguments(self, parser):
        parser.add_argument('--to', default='test@example.com', help='Destination email')
        parser.add_argument('--subject', default="Exemple d'email Abeja Kings", help='Subject')
        parser.add_argument('--body', default='Ceci est un email de test envoyé par send_example_email.', help='Body')

    def handle(self, *args, **options):
        to = options['to']
        subject = options['subject']
        body = options['body']

        # If file backend is used, ensure directory exists
        if settings.EMAIL_BACKEND == 'django.core.mail.backends.filebased.EmailBackend':
            path = getattr(settings, 'EMAIL_FILE_PATH', None)
            if path:
                try:
                    os.makedirs(path, exist_ok=True)
                    self.stdout.write(self.style.SUCCESS(f'Email file path ready: {path}'))
                except Exception as e:
                    self.stderr.write(f'Impossible de créer le dossier d\'emails: {e}')

        # Send the email using Django's send_mail (uses settings.EMAIL_BACKEND)
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or None
        send_mail(subject, body, from_email, [to])

        self.stdout.write(self.style.SUCCESS(f'Email d\'exemple envoyé à {to} (backend={settings.EMAIL_BACKEND})'))
