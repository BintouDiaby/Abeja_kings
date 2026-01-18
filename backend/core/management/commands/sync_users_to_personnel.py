from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from core.models import UserProfile, Personnel


class Command(BaseCommand):
    help = 'Synchronise tous les utilisateurs (ouvrier/chef) vers la table Personnel'

    def handle(self, *args, **options):
        self.stdout.write('Début de la synchronisation...')
        
        # Récupérer tous les utilisateurs avec leur profil
        users = User.objects.select_related('userprofile').all()
        
        created_count = 0
        skipped_count = 0
        
        for user in users:
            profile = getattr(user, 'userprofile', None)
            
            if not profile:
                self.stdout.write(self.style.WARNING(f'⚠️  {user.username} n\'a pas de profil, ignoré'))
                skipped_count += 1
                continue
            
            # Vérifier si l'utilisateur a déjà une entrée Personnel
            if hasattr(user, 'personnel'):
                self.stdout.write(f'  {user.username} existe déjà dans Personnel, ignoré')
                skipped_count += 1
                continue
            
            # Créer Personnel uniquement pour ouvrier et chef
            if profile.role in ['ouvrier', 'chef']:
                role_mapping = {
                    'ouvrier': 'ouvrier',
                    'chef': 'chef_chantier',
                }
                
                Personnel.objects.create(
                    user=user,
                    role=role_mapping.get(profile.role, 'ouvrier'),
                    taux_horaire=0.00,
                    telephone=profile.telephone or '',
                    date_embauche=profile.date_embauche or timezone.now().date(),
                    est_actif=True,
                )
                
                self.stdout.write(self.style.SUCCESS(f'✓ {user.username} ({profile.get_role_display()}) ajouté au Personnel'))
                created_count += 1
            else:
                self.stdout.write(f'  {user.username} est admin, non ajouté au Personnel')
                skipped_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ Synchronisation terminée !'))
        self.stdout.write(f'  {created_count} personnel(s) créé(s)')
        self.stdout.write(f'  {skipped_count} utilisateur(s) ignoré(s)')
