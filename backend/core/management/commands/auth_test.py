from django.core.management.base import BaseCommand
from django.contrib.auth import authenticate, get_user_model


class Command(BaseCommand):
    help = 'Test authentication for a user (username or email)'

    def add_arguments(self, parser):
        parser.add_argument('--username', required=True, help='Username or email to test')
        parser.add_argument('--password', required=True, help='Password to test')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        User = get_user_model()

        user = authenticate(username=username, password=password)
        if user:
            self.stdout.write(self.style.SUCCESS('AUTHENTICATION: SUCCESS'))
            self.stdout.write(f'username: {user.username}')
            self.stdout.write(f'email: {user.email}')
            self.stdout.write(f'is_active: {user.is_active}')
            self.stdout.write(f'is_staff: {user.is_staff}')
            self.stdout.write(f'is_superuser: {user.is_superuser}')
            return

        # if not found, try resolving as username -> email
        u = User.objects.filter(username__iexact=username).first()
        if u and u.email:
            user = authenticate(username=u.email, password=password)
            if user:
                self.stdout.write(self.style.SUCCESS('AUTHENTICATION: SUCCESS (via email)'))
                self.stdout.write(f'username: {user.username}')
                self.stdout.write(f'email: {user.email}')
                self.stdout.write(f'is_active: {user.is_active}')
                self.stdout.write(f'is_staff: {user.is_staff}')
                self.stdout.write(f'is_superuser: {user.is_superuser}')
                return

        # final: show helpful info
        self.stdout.write(self.style.ERROR('AUTHENTICATION: FAILED'))
        if u:
            self.stdout.write(f'User exists: {u.username} (is_active={u.is_active})')
        else:
            self.stdout.write('No user found with that username')
