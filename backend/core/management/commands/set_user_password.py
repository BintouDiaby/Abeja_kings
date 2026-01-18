from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Set a user password non-interactively: --username USER --password PASS'

    def add_arguments(self, parser):
        parser.add_argument('--username', required=True, help='Username to update')
        parser.add_argument('--password', required=True, help='New password')

    def handle(self, *args, **options):
        User = get_user_model()
        username = options['username']
        password = options['password']
        try:
            user = User.objects.get(username__iexact=username)
        except User.DoesNotExist:
            raise CommandError(f"User '{username}' does not exist")

        user.set_password(password)
        user.save()
        self.stdout.write(self.style.SUCCESS(f"Password set for user '{user.username}'"))
