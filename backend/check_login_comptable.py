import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from django.contrib.auth import authenticate, get_user_model
User = get_user_model()

username = 'comptable'
password = 'Compta123'

user = authenticate(username=username, password=password)
if not user:
    # try email
    u = User.objects.filter(username__iexact=username).first()
    if u and u.email:
        user = authenticate(username=u.email, password=password)

if not user:
    print('AUTHENTICATION: FAILED')
else:
    profile = getattr(user, 'userprofile', None)
    print('AUTHENTICATION: SUCCESS')
    print('username:', user.username)
    print('email:', user.email)
    print('is_active:', user.is_active)
    print('is_staff:', user.is_staff)
    print('is_superuser:', user.is_superuser)
    print('role:', getattr(profile, 'role', None))
