import os
import django
import sys
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.backend_project.settings')
# Compute reliable project paths based on this file's location so the script
# works when invoked from any CWD.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# `export_comptable_logs.py` lives inside the `backend/` package
BACKEND_PKG = SCRIPT_DIR
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
for p in (PROJECT_ROOT, BACKEND_PKG):
    if p and p not in sys.path:
        sys.path.insert(0, p)

django.setup()

from django.contrib.auth import get_user_model
from core.models import Payment, Facture, Rapport
User = get_user_model()

users = User.objects.filter(userprofile__role='comptable')
if not users.exists():
    print('Aucun utilisateur avec le rôle "comptable" trouvé.')
    sys.exit(0)

for u in users:
    print('='*80)
    print(f"Comptable: {u.get_full_name() or u.username} <{u.email}>")
    print('='*80)

    print('\nPaiements créés:')
    pays = Payment.objects.filter(created_by=u).order_by('-created_at')[:200]
    if not pays.exists():
        print('  Aucun paiement créé par cet utilisateur.')
    else:
        for p in pays:
            print(f"  - [{p.created_at.strftime('%Y-%m-%d %H:%M:%S')}] Paiement {p.montant} FCFA sur facture {p.facture.numero} (mode: {p.get_mode_display()}) ref={p.reference}")

    print('\nFactures affectées via paiements:')
    facts = Facture.objects.filter(payments__created_by=u).distinct().order_by('-id')[:200]
    if not facts.exists():
        print('  Aucune facture liée à des paiements créés par cet utilisateur.')
    else:
        for f in facts:
            print(f"  - Facture {f.numero} montant={f.total} (id={f.id})")

    print('\nRapports écrits:')
    reps = Rapport.objects.filter(auteur=u).order_by('-created_at')[:200]
    if not reps.exists():
        print('  Aucun rapport écrit par cet utilisateur.')
    else:
        for r in reps:
            print(f"  - [{r.created_at.strftime('%Y-%m-%d %H:%M:%S')}] {r.type_rapport} {r.titre} (chantier={r.chantier})")

print('\nFin de l\'export\'')
