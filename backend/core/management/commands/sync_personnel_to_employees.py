from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from core.models import Personnel, Employee, OuvrierDetails, ChefChantierDetails

ROLE_MAP = {
    'ouvrier': 'OUVRIER',
    'maitre_ouvrier': 'OUVRIER',  # regrouper côté métier
    'apprenti': 'APPRENTI',
    'chef_chantier': 'CHEF_CHANTIER',
}

class Command(BaseCommand):
    help = 'Convertit les entrées Personnel vers le nouveau modèle Employee'

    def handle(self, *args, **options):
        created = 0
        skipped = 0
        updated = 0
        for p in Personnel.objects.select_related('user', 'chantier_actuel').all():
            if not p.user:
                skipped += 1
                continue
            role = ROLE_MAP.get(p.role, 'OUVRIER')
            # Créer ou mettre à jour Employee
            emp, emp_created = Employee.objects.update_or_create(
                user=p.user,
                defaults={
                    'nom': p.user.last_name or p.user.username,
                    'prenom': p.user.first_name or '',
                    'telephone': p.telephone or '',
                    'role': role,
                    'statut': 'ACTIF' if p.est_actif else 'INACTIF',
                    'date_embauche': p.date_embauche or timezone.now().date(),
                    'type_remuneration': 'JOURNALIER',  # défaut
                    'montant_remuneration': p.taux_horaire or 0,
                }
            )
            if emp_created:
                created += 1
            else:
                updated += 1

            # Détails spécifiques
            if role in ['OUVRIER', 'APPRENTI']:
                OuvrierDetails.objects.get_or_create(employee=emp)
            elif role == 'CHEF_CHANTIER':
                ChefChantierDetails.objects.get_or_create(employee=emp)
        
        self.stdout.write(self.style.SUCCESS(f"✓ Employees créés: {created}, mis à jour: {updated}, ignorés: {skipped}"))
