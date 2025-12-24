from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import UserProfile


class Command(BaseCommand):
    help = 'Create test users with different roles'

    def handle(self, *args, **options):
        # Créer un chef de chantier
        if not User.objects.filter(username='chef').exists():
            user = User.objects.create_user(
                username='chef',
                email='chef@abeja.kings',
                password='password123',
                first_name='Yao',
                last_name='Kouassi'
            )
            UserProfile.objects.create(
                user=user,
                role='chef',
                telephone='+225 01 02 03 04 05'
            )
            self.stdout.write(self.style.SUCCESS(f'Utilisateur chef créé'))

        # Créer un ouvrier
        if not User.objects.filter(username='ouvrier').exists():
            user = User.objects.create_user(
                username='ouvrier',
                email='ouvrier@abeja.kings',
                password='password123',
                first_name='Aïcha',
                last_name='Coulibaly'
            )
            UserProfile.objects.create(
                user=user,
                role='ouvrier',
                telephone='+225 06 07 08 09 10'
            )
            self.stdout.write(self.style.SUCCESS(f'Utilisateur ouvrier créé'))

        # Créer un admin (en plus du superuser)
        if not User.objects.filter(username='admin_user').exists():
            user = User.objects.create_user(
                username='admin_user',
                email='admin_user@abeja.kings',
                password='password123',
                first_name='Admin',
                last_name='System'
            )
            UserProfile.objects.create(
                user=user,
                role='admin',
                telephone='+225 11 12 13 14 15'
            )
            self.stdout.write(self.style.SUCCESS(f'Utilisateur admin_user créé'))

        self.stdout.write(self.style.SUCCESS('Utilisateurs de test créés avec succès!'))
        self.stdout.write('Comptes de test:')
        self.stdout.write('  admin: admin@abeja.kings / (mot de passe défini lors de createsuperuser)')
        self.stdout.write('  chef: chef@abeja.kings / password123')
        self.stdout.write('  ouvrier: ouvrier@abeja.kings / password123')
        self.stdout.write('  admin_user: admin_user@abeja.kings / password123')