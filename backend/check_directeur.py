import os
import sys
import django

# Ensure backend package is importable when running from repo root
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

u = User.objects.filter(username__iexact='Directeur_Adams').first()
if not u:
    print('EXISTS: False')
else:
    # ensure no admin access
    changed = False
    if u.is_staff:
        u.is_staff = False
        changed = True
    if u.is_superuser:
        u.is_superuser = False
        changed = True
    if changed:
        u.save()

    profile = getattr(u, 'userprofile', None)
    print('EXISTS: True')
    print('username:', u.username)
    print('is_active:', u.is_active)
    print('is_staff:', u.is_staff)
    print('is_superuser:', u.is_superuser)
    print('email:', u.email)
    print('role:', getattr(profile, 'role', None))
