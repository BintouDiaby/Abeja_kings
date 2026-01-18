from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

from core.models import UserProfile


class Command(BaseCommand):
    help = 'Créer un utilisateur directeur non interactif (par défaut Directeur_Adams/Abeja123)'

    def add_arguments(self, parser):
        parser.add_argument('--username', default='Directeur_Adams', help='Nom d\'utilisateur')
        parser.add_argument('--password', default='Abeja123', help='Mot de passe')
        parser.add_argument('--email', default='directeur@example.com', help='Email')

    def handle(self, *args, **options):
        User = get_user_model()
        username = options['username']
        password = options['password']
        email = options['email']

        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': email, 'is_staff': False, 'is_superuser': False}
        )

        # (Re)définir le mot de passe et flags
        user.set_password(password)
        user.is_staff = False
        user.is_superuser = False
        user.save()

        profile, pcreated = UserProfile.objects.get_or_create(user=user, defaults={'role': 'directeur', 'telephone': ''})
        profile.role = 'directeur'
        profile.save()

        status = 'created' if created else 'updated'
        self.stdout.write(self.style.SUCCESS(f"User '{username}' {status} and role set to 'directeur'."))
