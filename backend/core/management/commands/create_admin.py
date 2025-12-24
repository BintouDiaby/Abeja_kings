from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import getpass


class Command(BaseCommand):
    help = 'Créer un superuser sans demander l\'adresse email (prompt username + password)'

    def handle(self, *args, **options):
        User = get_user_model()

        # Username
        username = None
        while not username:
            username = input('Nom d\u2019utilisateur (username): ').strip()
            if not username:
                self.stdout.write(self.style.ERROR('Le nom d\u2019utilisateur est requis.'))

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.ERROR(f"L'utilisateur '{username}' existe déjà."))
            return

        # Password (masqué)
        password = None
        while True:
            password = getpass.getpass('Mot de passe: ')
            password2 = getpass.getpass('Mot de passe (confirmation): ')
            if password != password2:
                self.stdout.write(self.style.ERROR('Les mots de passe ne correspondent pas.'))
                continue
            if not password:
                self.stdout.write(self.style.ERROR('Le mot de passe ne peut pas être vide.'))
                continue
            break

        # Create superuser with empty email
        try:
            User.objects.create_superuser(username=username, email='', password=password)
            self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' créé avec succès (sans email)."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erreur lors de la création du superuser: {e}"))
