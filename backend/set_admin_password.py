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
    try:
        # Récupérer ou créer le superuser admin
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@abeja.kings',
                'is_superuser': True,
                'is_staff': True
            }
        )

        if created:
            print("✅ Superuser 'admin' créé")
        else:
            print(f"📝 Superuser 'admin' existait déjà")

        # Définir le mot de passe
        admin_user.set_password('admin123')
        admin_user.save()
        print("🔑 Mot de passe défini: admin123")

        # Vérifier/créer le profil
        profile, profile_created = UserProfile.objects.get_or_create(
            user=admin_user,
            defaults={'role': 'admin'}
        )

        if profile_created:
            print("✅ Profil créé avec rôle 'admin'")
        else:
            print(f"📝 Profil existait avec rôle '{profile.role}'")
            if profile.role != 'admin':
                profile.role = 'admin'
                profile.save()
                print("🔄 Rôle mis à jour vers 'admin'")

        print("\n✅ Configuration terminée !")
        print("📧 Email: admin@abeja.kings")
        print("🔑 Mot de passe: admin123")
        print("👤 Rôle: admin")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)