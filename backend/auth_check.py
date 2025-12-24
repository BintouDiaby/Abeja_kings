import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()
from django.contrib.auth import authenticate

tests = [
    ('admin@abeja.kings', 'admin123'),
    ('admin', 'admin123'),
    ('chef@abeja.kings', 'password123'),
    ('chef', 'password123'),
    ('ouvrier@abeja.kings', 'password123'),
    ('ouvrier', 'password123'),
    ('admin_user@abeja.kings', 'password123'),
    ('admin_user', 'password123'),
]

for username, pwd in tests:
    user = authenticate(username=username, password=pwd)
    print(f"Trying {username} / {pwd} ->", 'OK' if user else 'FAIL')
    if user:
        print('  User:', user.username, 'is_active', user.is_active, 'is_superuser', user.is_superuser)
