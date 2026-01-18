from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Check existence and flags of a user by username'

    def add_arguments(self, parser):
        parser.add_argument('--username', required=True, help='Username to check')

    def handle(self, *args, **options):
        username = options['username']
        User = get_user_model()
        try:
            user = User.objects.filter(username__iexact=username).first()
        except Exception as e:
            self.stderr.write(f'Error querying user: {e}')
            return

        if not user:
            self.stdout.write(self.style.WARNING(f'User "{username}" not found.'))
            return

        profile = getattr(user, 'userprofile', None)
        self.stdout.write(self.style.SUCCESS(f'User found: {user.username}'))
        self.stdout.write(f'  Email: {user.email}')
        self.stdout.write(f'  is_active: {user.is_active}')
        self.stdout.write(f'  is_staff: {user.is_staff}')
        self.stdout.write(f'  is_superuser: {user.is_superuser}')
        self.stdout.write(f'  last_login: {user.last_login}')
        self.stdout.write(f'  date_joined: {user.date_joined}')
        if profile:
            self.stdout.write(f'  role: {profile.role}')
            self.stdout.write(f'  telephone: {profile.telephone}')
        else:
            self.stdout.write('  No UserProfile linked')
