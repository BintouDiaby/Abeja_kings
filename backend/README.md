Mini-backend Django (scaffold)

But : fournir un backend simple sans API REST complète. Vues basées sur POST + templates.

Quick start (Windows PowerShell)

1) Créer un virtualenv et l'activer :

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2) Installer dépendances :

```powershell
pip install -r requirements.txt
```

3) Se rendre dans le dossier `backend` et lancer les migrations :

```powershell
cd backend
python manage.py migrate
python manage.py createsuperuser  # optionnel
python manage.py runserver
```

4) Ouvrir http://127.0.0.1:8000/ pour voir les pages core (clients, factures).

Notes
- Ce scaffold crée un app `core` avec modèles simples `Client`, `Facture`, `FactureLine`, `Rapport`.
- On va brancher progressivement le frontend existant pour soumettre via POST.
