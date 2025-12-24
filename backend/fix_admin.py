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
        # Récupérer le superuser admin
        admin_user = User.objects.get(username='admin')
        print(f"Superuser trouvé: {admin_user.username}")
        print(f"Email: {admin_user.email}")
        print(f"Is superuser: {admin_user.is_superuser}")
        print(f"Is staff: {admin_user.is_staff}")

        # Vérifier/créer le profil
        profile, created = UserProfile.objects.get_or_create(
            user=admin_user,
            defaults={'role': 'admin'}
        )

        if created:
            print("✅ Profil créé avec rôle 'admin'")
        else:
            print(f"📝 Profil existait déjà avec rôle '{profile.role}'")
            if profile.role != 'admin':
                profile.role = 'admin'
                profile.save()
                print("🔄 Rôle mis à jour vers 'admin'")

        print(f"✅ Profil final: rôle='{profile.role}', téléphone='{profile.telephone}'")

    except User.DoesNotExist:
        print("❌ Superuser 'admin' non trouvé")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)