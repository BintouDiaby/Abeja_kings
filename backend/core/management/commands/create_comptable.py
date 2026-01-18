from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from core.models import UserProfile

User = get_user_model()


class Command(BaseCommand):
    help = 'Create or update a comptable user (role=comptable)'

    def add_arguments(self, parser):
        parser.add_argument('--username', required=True, help='Username to create or update')
        parser.add_argument('--password', required=True, help='Password to set')
        parser.add_argument('--email', default='', help='Optional email')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        email = options.get('email') or ''

        user, created = User.objects.get_or_create(username=username, defaults={'email': email})
        user.email = email or user.email
        user.is_active = True
        user.is_staff = False
        user.is_superuser = False
        user.set_password(password)
        user.save()

        profile = getattr(user, 'userprofile', None)
        if profile is None:
            UserProfile.objects.create(user=user, role='comptable')
            self.stdout.write(self.style.SUCCESS(f"Created user '{username}' with role 'comptable'."))
        else:
            profile.role = 'comptable'
            profile.save()
            self.stdout.write(self.style.SUCCESS(f"Updated user '{username}' and set role to 'comptable'."))

        self.stdout.write(self.style.SUCCESS('Done.'))
