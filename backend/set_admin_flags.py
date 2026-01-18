import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.models import UserProfile

User = get_user_model()

admins = User.objects.filter(userprofile__role='admin')
if not admins.exists():
    print('No users with role "admin" found.')
else:
    for u in admins:
        changed = False
        if not u.is_staff:
            u.is_staff = True
            changed = True
        if not u.is_superuser:
            u.is_superuser = True
            changed = True
        if changed:
            u.save()
            print(f"Updated {u.username}: is_staff=True, is_superuser=True")
        else:
            print(f"No change for {u.username}: already has flags.")

print('Done.')
