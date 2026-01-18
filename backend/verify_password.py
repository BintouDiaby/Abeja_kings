import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()
username = 'chef'
pw = 'password123'

u = User.objects.filter(username__iexact=username).first()
if not u:
    print('User not found')
    sys.exit(1)

print('User:', u.username, 'email:', u.email)
print('is_active:', u.is_active)
print('check_password(password123):', u.check_password(pw))
