#!/usr/bin/env python
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import UserProfile

def main():
    print("=== UTILISATEURS EXISTANTS ===")
    users = User.objects.all()
    for user in users:
        print(f"Username: {user.username}")
        print(f"Email: {user.email}")
        print(f"Superuser: {user.is_superuser}")
        print(f"Staff: {user.is_staff}")
        try:
            profile = UserProfile.objects.get(user=user)
            print(f"Rôle: {profile.role}")
        except UserProfile.DoesNotExist:
            print("Rôle: Aucun profil")
        print("---")

if __name__ == '__main__':
    main()