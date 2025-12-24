from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.conf import settings
from django.views import View
from django.http import JsonResponse
import json
from django.views.decorators.csrf import ensure_csrf_cookie
from django.middleware.csrf import get_token
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db import models
from django.utils import timezone
from django.contrib.auth import views as auth_views

from .models import Client, Facture, FactureLine, UserProfile, Chantier, Personnel, Materiau, Fournisseur, Rapport
from .forms import ClientForm, FactureForm


from django.utils.decorators import method_decorator


@method_decorator(login_required, name='dispatch')
class DashboardView(View):
    def get(self, request):
        try:
            # Statistiques générales
            total_chantiers = Chantier.objects.count()
            chantiers_actifs = Chantier.objects.filter(statut='en_cours').count()
            chantiers_termines = Chantier.objects.filter(statut='termine').count()

            total_personnel = Personnel.objects.filter(est_actif=True).count()
            total_materiaux = Materiau.objects.count()
            materiaux_rupture = Materiau.objects.filter(quantite_stock__lte=models.F('seuil_minimum')).count()

            total_clients = Client.objects.count()
            total_fournisseurs = Fournisseur.objects.count()

            # Factures du mois en cours (utiliser les bons champs du modèle)
            now = timezone.now()
            debut_mois = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            factures_mois = Facture.objects.filter(date__gte=debut_mois)
            montant_factures_mois = factures_mois.aggregate(total=models.Sum('total'))['total'] or 0

            # Budget total des chantiers actifs
            budget_total = Chantier.objects.filter(statut__in=['planifie', 'en_cours']).aggregate(
                total=models.Sum('budget')
            )['total'] or 0

            # Chantiers récents
            chantiers_recents = Chantier.objects.select_related('client').order_by('-created_at')[:5]

            # Factures récentes
            factures_recentes = Facture.objects.select_related('client').order_by('-date')[:5]

            # Profil utilisateur (utilisé pour contrôle d'accès et visibilité des rapports)
            profile = getattr(request.user, 'userprofile', None)

            # Rapports récents (admin/chef voient tous, ouvriers seulement les leurs)
            if profile and profile.role in ('admin', 'chef'):
                rapports_qs = Rapport.objects.select_related('chantier', 'auteur').order_by('-created_at')
            else:
                rapports_qs = Rapport.objects.select_related('chantier').filter(auteur=request.user).order_by('-created_at')

            rapports_count = rapports_qs.count()
            rapports_recents = rapports_qs[:5]

            # Contrôle d'accès selon le rôle -> les ouvriers n'ont pas accès au dashboard
            # Si l'utilisateur est un 'ouvrier', le rediriger vers la page de rapports
            if profile and profile.role == 'ouvrier':
                return redirect(reverse('core:rapports'))

            # Contrôle d'accès aux données financières selon le rôle
            show_finances = False
            if profile and profile.role in ('admin', 'chef'):
                show_finances = True

            context = {
                'total_chantiers': total_chantiers,
                'chantiers_actifs': chantiers_actifs,
                'chantiers_termines': chantiers_termines,
                'total_personnel': total_personnel,
                'total_materiaux': total_materiaux,
                'materiaux_rupture': materiaux_rupture,
                'total_clients': total_clients,
                'total_fournisseurs': total_fournisseurs,
                'montant_factures_mois': montant_factures_mois,
                'budget_total': budget_total,
                'chantiers_recents': chantiers_recents,
                'factures_recentes': factures_recentes,
                'rapports_count': rapports_count,
                'rapports_recents': rapports_recents,
                'show_finances': show_finances,
            }

            return render(request, 'core/dashboard.html', context)
        except Exception as e:
            # En cas d'erreur, retourner un dashboard simplifié
            return render(request, 'core/dashboard.html', {
                'total_chantiers': 0,
                'chantiers_actifs': 0,
                'chantiers_termines': 0,
                'total_personnel': 0,
                'total_materiaux': 0,
                'materiaux_rupture': 0,
                'total_clients': 0,
                'total_fournisseurs': 0,
                'montant_factures_mois': 0,
                'budget_total': 0,
                'chantiers_recents': [],
                'factures_recentes': [],
            })


@method_decorator(login_required, name='dispatch')
class ClientListView(View):
    def get(self, request):
        clients = Client.objects.all().order_by('-created_at')
        return render(request, 'core/client_list.html', {'clients': clients})


class CustomLoginView(auth_views.LoginView):
    """Custom LoginView to support a 'remember me' checkbox.

    If 'remember_me' is present in POST, create a persistent session (30 days).
    Otherwise use a session that expires at browser close.
    """
    template_name = 'registration/login.html'

    def form_valid(self, form):
        remember = self.request.POST.get('remember_me')
        if remember:
            # Persist session for 30 days
            self.request.session.set_expiry(60 * 60 * 24 * 30)
        else:
            # Session expires at browser close
            self.request.session.set_expiry(0)

        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class ClientCreateView(View):
    def get(self, request):
        form = ClientForm()
        return render(request, 'core/client_form.html', {'form': form})

    def post(self, request):
        form = ClientForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(reverse('core:clients'))
        return render(request, 'core/client_form.html', {'form': form})


@method_decorator(login_required, name='dispatch')
class ClientUpdateView(View):
    def get(self, request, pk):
        client = get_object_or_404(Client, pk=pk)
        form = ClientForm(instance=client)
        return render(request, 'core/client_form.html', {'form': form, 'client': client})

    def post(self, request, pk):
        client = get_object_or_404(Client, pk=pk)
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            return redirect(reverse('core:clients'))
        return render(request, 'core/client_form.html', {'form': form, 'client': client})


@method_decorator(login_required, name='dispatch')
class FactureListView(View):
    def get(self, request):
        factures = Facture.objects.select_related('client').all().order_by('-created_at')
        # Calculer le montant total des factures pour l'affichage (évite d'utiliser des filtres personnalisés en template)
        try:
            montant_total = factures.aggregate(total=models.Sum('total'))['total'] or 0
        except Exception:
            # fallback si l'aggregation échoue
            montant_total = sum([getattr(f, 'total', 0) or 0 for f in factures])

        return render(request, 'core/facture_list.html', {'factures': factures, 'montant_total': montant_total})


@method_decorator(login_required, name='dispatch')
class FactureCreateView(View):
    def get(self, request):
        form = FactureForm()
        return render(request, 'core/facture_form.html', {'form': form})
    
    def post(self, request):
        # Allow client to be sent as client id or as client_nom (frontend may send a name)
        data = request.POST.copy()
        client_nom = data.get('client_nom')
        if not data.get('client') and client_nom:
            client_obj, _ = Client.objects.get_or_create(nom=client_nom)
            data['client'] = str(client_obj.id)

        form = FactureForm(data)
        if form.is_valid():
            facture = form.save()

            # Process optional lines JSON (sent by frontend)
            lines_json = data.get('lines_json')
            if lines_json:
                try:
                    lines = json.loads(lines_json)
                    for ln in lines:
                        desc = ln.get('description') or ''
                        quantite = float(ln.get('quantite') or 0)
                        pu = float(ln.get('pu') or ln.get('prix_unitaire') or 0)
                        montant = float(ln.get('total') or (quantite * pu))
                        FactureLine.objects.create(
                            facture=facture,
                            description=desc,
                            quantite=int(quantite),
                            prix_unitaire=pu,
                            montant=montant
                        )
                except Exception:
                    # ignore malformed lines, continue saving facture
                    pass

            # Recalculer les totaux de la facture à partir des lignes (subtotal, tva_amount, total)
            try:
                agg = FactureLine.objects.filter(facture=facture).aggregate(subtotal=models.Sum('montant'))
                subtotal = agg['subtotal'] or 0
                facture.subtotal = subtotal
                # tva_pct peut être vide/0
                try:
                    tva_pct = float(getattr(facture, 'tva_pct') or 0)
                except Exception:
                    tva_pct = 0
                facture.tva_amount = (subtotal * tva_pct) / 100
                facture.total = subtotal + facture.tva_amount
                facture.save()
            except Exception:
                # si le recalcul échoue, ne pas bloquer la création
                pass

            # If AJAX (fetch) request, respond with JSON else redirect
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'redirect': reverse('core:factures')})

            return redirect(reverse('core:factures'))

        return render(request, 'core/facture_form.html', {'form': form})


@ensure_csrf_cookie
def set_csrf(request):
    """Endpoint simple pour forcer l'envoi du cookie CSRF vers le navigateur.
    Le frontend peut appeler `/set-csrf/` avec credentials: 'same-origin' pour récupérer
    le cookie `csrftoken` lorsque la page est servie depuis Django.
    """
    # Also return the token in JSON so frontend served from another origin
    # can read it and send it in the X-CSRFToken header.
    token = get_token(request)
    return JsonResponse({'ok': True, 'csrftoken': token})


@method_decorator(login_required, name='dispatch')
class UserListView(View):
    def get(self, request):
        users = User.objects.select_related('userprofile').all().order_by('username')
        return render(request, 'core/user_list.html', {'users': users})


class UserCreateView(View):
    def get(self, request):
        return render(request, 'core/user_form.html', {'form': UserCreationForm()})

    def post(self, request):
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Créer le profil utilisateur
            UserProfile.objects.create(
                user=user,
                role=request.POST.get('role', 'ouvrier'),
                telephone=request.POST.get('telephone', ''),
            )
            messages.success(request, f'Utilisateur {user.username} créé avec succès.')
            return redirect(reverse('core:users'))
        return render(request, 'core/user_form.html', {'form': form})


class UserUpdateView(View):
    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        profile, created = UserProfile.objects.get_or_create(user=user)
        return render(request, 'core/user_form.html', {
            'form': UserCreationForm(instance=user),
            'profile': profile,
            'is_update': True
        })

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        profile, created = UserProfile.objects.get_or_create(user=user)

        # Mettre à jour le profil
        profile.role = request.POST.get('role', profile.role)
        profile.telephone = request.POST.get('telephone', profile.telephone)
        profile.save()

        messages.success(request, f'Utilisateur {user.username} mis à jour avec succès.')
        return redirect(reverse('core:users'))


@login_required
def get_current_user(request):
    """API endpoint to get current user information"""
    user = request.user
    profile = getattr(user, 'userprofile', None)

    return JsonResponse({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'full_name': user.get_full_name(),
        'role': profile.role if profile else 'ouvrier',
        'role_display': profile.get_role_display() if profile else 'Ouvrier',
        'telephone': profile.telephone if profile else '',
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
    })


# API endpoints pour les nouveaux modèles
@login_required
def api_chantiers(request):
    """API endpoint pour récupérer la liste des chantiers"""
    chantiers = Chantier.objects.select_related('client', 'chef_chantier').all()
    data = []
    for chantier in chantiers:
        data.append({
            'id': chantier.id,
            'nom': chantier.nom,
            'client': {
                'id': chantier.client.id,
                'nom': chantier.client.nom
            },
            'description': chantier.description,
            'date_debut': chantier.date_debut.isoformat(),
            'date_fin_prevue': chantier.date_fin_prevue.isoformat(),
            'date_fin_reelle': chantier.date_fin_reelle.isoformat() if chantier.date_fin_reelle else None,
            'budget': float(chantier.budget),
            'statut': chantier.statut,
            'statut_display': chantier.get_statut_display(),
            'avancement': chantier.avancement,
            'chef_chantier': {
                'id': chantier.chef_chantier.id,
                'nom': chantier.chef_chantier.get_full_name()
            } if chantier.chef_chantier else None,
            'created_at': chantier.created_at.isoformat(),
        })
    return JsonResponse({'chantiers': data})


@login_required
def api_personnel(request):
    """API endpoint pour récupérer la liste du personnel"""
    personnel = Personnel.objects.select_related('user', 'chantier_actuel').all()
    data = []
    for personne in personnel:
        data.append({
            'id': personne.id,
            'user': {
                'id': personne.user.id,
                'username': personne.user.username,
                'full_name': personne.user.get_full_name(),
                'email': personne.user.email,
            },
            'role': personne.role,
            'role_display': personne.get_role_display(),
            'taux_horaire': float(personne.taux_horaire),
            'telephone': personne.telephone,
            'adresse': personne.adresse,
            'date_embauche': personne.date_embauche.isoformat(),
            'chantier_actuel': {
                'id': personne.chantier_actuel.id,
                'nom': personne.chantier_actuel.nom
            } if personne.chantier_actuel else None,
            'est_actif': personne.est_actif,
            'created_at': personne.created_at.isoformat(),
        })
    return JsonResponse({'personnel': data})


@login_required
def api_materiaux(request):
    """API endpoint pour récupérer la liste des matériaux"""
    materiaux = Materiau.objects.select_related('fournisseur').all()
    data = []
    for materiau in materiaux:
        data.append({
            'id': materiau.id,
            'nom': materiau.nom,
            'categorie': materiau.categorie,
            'categorie_display': materiau.get_categorie_display(),
            'description': materiau.description,
            'unite': materiau.unite,
            'quantite_stock': materiau.quantite_stock,
            'seuil_minimum': materiau.seuil_minimum,
            'prix_unitaire': float(materiau.prix_unitaire),
            'fournisseur': {
                'id': materiau.fournisseur.id,
                'nom': materiau.fournisseur.nom
            } if materiau.fournisseur else None,
            'est_en_rupture': materiau.est_en_rupture,
            'created_at': materiau.created_at.isoformat(),
            'updated_at': materiau.updated_at.isoformat(),
        })
    return JsonResponse({'materiaux': data})


@login_required
def api_fournisseurs(request):
    """API endpoint pour récupérer la liste des fournisseurs"""
    fournisseurs = Fournisseur.objects.all()
    data = []
    for fournisseur in fournisseurs:
        data.append({
            'id': fournisseur.id,
            'nom': fournisseur.nom,
            'contact': fournisseur.contact,
            'telephone': fournisseur.telephone,
            'email': fournisseur.email,
            'adresse': fournisseur.adresse,
            'specialite': fournisseur.specialite,
            'created_at': fournisseur.created_at.isoformat(),
        })
    return JsonResponse({'fournisseurs': data})


@login_required
def api_clients(request):
    """API endpoint pour récupérer la liste des clients"""
    clients = Client.objects.all()
    data = []
    for client in clients:
        data.append({
            'id': client.id,
            'nom': client.nom,
            'contact': client.contact,
            'telephone': client.telephone,
            'email': client.email,
            'adresse': client.adresse,
            'created_at': client.created_at.isoformat(),
        })
    return JsonResponse({'clients': data})


@login_required
def api_factures(request):
    """API endpoint pour récupérer la liste des factures"""
    factures = Facture.objects.select_related('client').prefetch_related('lignes').all()
    data = []
    for facture in factures:
        lignes_data = []
        for ligne in facture.lignes.all():
            lignes_data.append({
                'id': ligne.id,
                'description': ligne.description,
                'quantite': ligne.quantite,
                'prix_unitaire': float(ligne.prix_unitaire),
                'montant': float(ligne.montant),
            })

        data.append({
            'id': facture.id,
            'numero': facture.numero,
            'client': {
                'id': facture.client.id,
                'nom': facture.client.nom
            },
            'date': facture.date.isoformat(),
            'date_echeance': facture.date_echeance.isoformat() if facture.date_echeance else None,
            'total': float(facture.total),
            'statut': facture.statut,
            'statut_display': facture.get_statut_display(),
            'notes': facture.notes,
            'lignes': lignes_data,
            'created_at': facture.created_at.isoformat(),
        })
    return JsonResponse({'factures': data})


@login_required
def api_rapports(request):
    """API endpoint pour récupérer la liste des rapports"""
    rapports = Rapport.objects.select_related('chantier', 'auteur').all()
    data = []
    for rapport in rapports:
        data.append({
            'id': rapport.id,
            'titre': rapport.titre,
            'type_rapport': rapport.type_rapport,
            'type_display': rapport.get_type_rapport_display(),
            'chantier': {
                'id': rapport.chantier.id,
                'nom': rapport.chantier.nom
            } if rapport.chantier else None,
            'auteur': {
                'id': rapport.auteur.id,
                'full_name': rapport.auteur.get_full_name()
            },
            'date': rapport.date.isoformat() if rapport.date else None,
            'contenu': rapport.contenu,
            'created_at': rapport.created_at.isoformat(),
        })
    return JsonResponse({'rapports': data})


@login_required
def api_dashboard_stats(request):
    """API endpoint pour récupérer les statistiques du dashboard"""
    # Statistiques générales
    total_chantiers = Chantier.objects.count()
    chantiers_actifs = Chantier.objects.filter(statut='en_cours').count()
    chantiers_termines = Chantier.objects.filter(statut='termine').count()

    total_personnel = Personnel.objects.filter(est_actif=True).count()
    total_materiaux = Materiau.objects.count()
    materiaux_rupture = Materiau.objects.filter(quantite_stock__lte=models.F('seuil_minimum')).count()

    total_clients = Client.objects.count()
    total_fournisseurs = Fournisseur.objects.count()

    # Factures du mois en cours
    now = timezone.now()
    debut_mois = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    factures_mois = Facture.objects.filter(date__gte=debut_mois)
    montant_factures_mois = factures_mois.aggregate(total=models.Sum('total'))['total'] or 0

    # Budget total des chantiers actifs
    budget_total = Chantier.objects.filter(statut__in=['planifie', 'en_cours']).aggregate(
        total=models.Sum('budget')
    )['total'] or 0

    return JsonResponse({
        'chantiers': {
            'total': total_chantiers,
            'actifs': chantiers_actifs,
            'termines': chantiers_termines,
        },
        'personnel': {
            'total': total_personnel,
        },
        'materiaux': {
            'total': total_materiaux,
            'en_rupture': materiaux_rupture,
        },
        'clients': {
            'total': total_clients,
        },
        'fournisseurs': {
            'total': total_fournisseurs,
        },
        'finances': {
            'budget_total': float(budget_total),
            'factures_mois': float(montant_factures_mois),
        }
    })


# Page pour gérer / visualiser les rapports
@login_required
def rapports_view(request):
    """Affiche la page des rapports :
    - les ouvriers voient uniquement leurs rapports
    - les chefs et admins voient tous les rapports
    """
    profile = getattr(request.user, 'userprofile', None)
    if profile and profile.role in ('admin', 'chef'):
        rapports = Rapport.objects.select_related('chantier', 'auteur').all().order_by('-created_at')
    else:
        rapports = Rapport.objects.select_related('chantier').filter(auteur=request.user).order_by('-created_at')

    return render(request, 'core/rapports.html', {'rapports': rapports})


def landing(request):
    """Landing page showing company info, active projects and team before login."""
    chantiers = Chantier.objects.filter(statut__in=['planifie', 'en_cours']).select_related('client', 'chef_chantier').order_by('-created_at')[:6]
    personnel_actif = Personnel.objects.filter(est_actif=True).select_related('user', 'chantier_actuel').order_by('user__last_name')[:12]
    
    total_chantiers = Chantier.objects.filter(statut='en_cours').count()
    total_personnel = Personnel.objects.filter(est_actif=True).count()
    
    return render(request, 'core/landing.html', {
        'chantiers': chantiers,
        'personnel': personnel_actif,
        'total_chantiers': total_chantiers,
        'total_personnel': total_personnel,
    })


@login_required
def post_login(request):
    """Dispatch après login : redirige en fonction du rôle.

    - 'ouvrier' -> page 'rapports'
    - 'chef' or 'admin' -> dashboard
    - fallback -> dashboard
    """
    profile = getattr(request.user, 'userprofile', None)
    if profile and profile.role == 'ouvrier':
        return redirect(reverse('core:rapports'))

    # Par défaut envoyer vers le dashboard (admin/chef)
    return redirect(reverse('core:dashboard'))


@login_required
def create_rapport(request):
    """Crée un rapport à partir d'un POST simple. Attend : titre, description, chantier (optionnel), type_rapport, contenu.
    Renvoie une redirection vers la liste des rapports (ou JSON si requête Ajax).
    """
    if request.method != 'POST':
        return redirect(reverse('core:rapports'))

    titre = request.POST.get('titre', '').strip()
    description = request.POST.get('description', '').strip()
    chantier_id = request.POST.get('chantier') or None
    type_rapport = request.POST.get('type_rapport') or 'journalier'
    contenu = request.POST.get('contenu', '')

    chantier = None
    if chantier_id:
        try:
            chantier = Chantier.objects.get(pk=int(chantier_id))
        except Exception:
            chantier = None

    # If frontend provided only a short 'description', use it as fallback for 'contenu'
    if not contenu:
        contenu = description

    rapport = Rapport.objects.create(
        titre=titre or f'Rapport de {request.user.get_full_name() or request.user.username}',
        chantier=chantier,
        auteur=request.user,
        type_rapport=type_rapport,
        contenu=contenu,
        date=timezone.now().date(),
    )

    # Si AJAX, retourner JSON
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
        return JsonResponse({'ok': True, 'id': rapport.id})

    return redirect(reverse('core:rapports'))


@login_required
def update_rapport(request, rapport_id):
    """Modifie un rapport existant (admin uniquement)."""
    profile = getattr(request.user, 'userprofile', None)
    if not profile or profile.role != 'admin':
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        rapport = Rapport.objects.get(pk=rapport_id)
    except Rapport.DoesNotExist:
        return JsonResponse({'error': 'Rapport not found'}, status=404)
    
    if request.method == 'POST':
        rapport.titre = request.POST.get('titre', rapport.titre)
        rapport.contenu = request.POST.get('contenu', rapport.contenu)
        rapport.type_rapport = request.POST.get('type_rapport', rapport.type_rapport)
        
        chantier_id = request.POST.get('chantier')
        if chantier_id:
            try:
                rapport.chantier = Chantier.objects.get(pk=int(chantier_id))
            except Exception:
                pass
        
        rapport.save()
        return redirect(reverse('core:rapports'))
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def delete_rapport(request, rapport_id):
    """Supprime un rapport (admin uniquement)."""
    profile = getattr(request.user, 'userprofile', None)
    if not profile or profile.role != 'admin':
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    if request.method != 'POST':
        return redirect(reverse('core:rapports'))
    
    try:
        rapport = Rapport.objects.get(pk=rapport_id)
        rapport.delete()
    except Rapport.DoesNotExist:
        pass
    
    return redirect(reverse('core:rapports'))


# Vues pour Chantier
@method_decorator(login_required, name='dispatch')
class ChantierListView(View):
    def get(self, request):
        # Support des filtres via query params :
        # - statut: e.g. 'en_cours', 'termine', 'planifie'
        # - budget_min: valeur numérique (montant minimum)
        # - budget_max: valeur numérique (montant maximum)
        qs = Chantier.objects.select_related('client', 'chef_chantier').all()

        statut = request.GET.get('statut')
        budget_min = request.GET.get('budget_min')
        budget_max = request.GET.get('budget_max')

        if statut:
            qs = qs.filter(statut=statut)

        # Filtrage par budget si fourni (tolère les valeurs non numériques)
        try:
            if budget_min:
                qs = qs.filter(budget__gte=float(budget_min))
        except Exception:
            pass

        try:
            if budget_max:
                qs = qs.filter(budget__lte=float(budget_max))
        except Exception:
            pass

        chantiers = qs.order_by('-created_at')

        # Fournir aussi les filtres appliqués pour l'UI si besoin
        applied_filters = {
            'statut': statut,
            'budget_min': budget_min,
            'budget_max': budget_max,
        }

        return render(request, 'core/chantier_list.html', {'chantiers': chantiers, 'applied_filters': applied_filters})


@method_decorator(login_required, name='dispatch')
class ChantierCreateView(View):
    def get(self, request):
        clients = Client.objects.all().order_by('nom')
        chefs_chantier = User.objects.filter(userprofile__role='chef').order_by('last_name')
        return render(request, 'core/chantier_form.html', {
            'clients': clients,
            'chefs_chantier': chefs_chantier
        })

    def post(self, request):
        try:
            chantier = Chantier.objects.create(
                nom=request.POST['nom'],
                client_id=request.POST['client'],
                description=request.POST.get('description', ''),
                date_debut=request.POST['date_debut'],
                date_fin_prevue=request.POST['date_fin_prevue'],
                budget=request.POST['budget'],
                statut=request.POST.get('statut', 'planifie'),
                avancement=request.POST.get('avancement', 0),
                chef_chantier_id=request.POST.get('chef_chantier') or None
            )
            messages.success(request, f'Chantier "{chantier.nom}" créé avec succès.')
            return redirect(reverse('core:chantiers'))
        except Exception as e:
            messages.error(request, f'Erreur lors de la création du chantier: {str(e)}')
            return redirect(reverse('core:chantier_create'))


@method_decorator(login_required, name='dispatch')
class ChantierUpdateView(View):
    def get(self, request, pk):
        chantier = get_object_or_404(Chantier, pk=pk)
        clients = Client.objects.all().order_by('nom')
        chefs_chantier = User.objects.filter(userprofile__role='chef').order_by('last_name')
        return render(request, 'core/chantier_form.html', {
            'chantier': chantier,
            'clients': clients,
            'chefs_chantier': chefs_chantier
        })

    def post(self, request, pk):
        chantier = get_object_or_404(Chantier, pk=pk)
        try:
            chantier.nom = request.POST['nom']
            chantier.client_id = request.POST['client']
            chantier.description = request.POST.get('description', '')
            chantier.date_debut = request.POST['date_debut']
            chantier.date_fin_prevue = request.POST['date_fin_prevue']
            chantier.budget = request.POST['budget']
            chantier.statut = request.POST.get('statut', chantier.statut)
            chantier.avancement = request.POST.get('avancement', chantier.avancement)
            chantier.chef_chantier_id = request.POST.get('chef_chantier') or None
            chantier.save()
            messages.success(request, f'Chantier "{chantier.nom}" mis à jour avec succès.')
            return redirect(reverse('core:chantiers'))
        except Exception as e:
            messages.error(request, f'Erreur lors de la mise à jour du chantier: {str(e)}')
            return redirect(reverse('core:chantier_update', kwargs={'pk': pk}))


@method_decorator(login_required, name='dispatch')
class ChantierDeleteView(View):
    def post(self, request, pk):
        chantier = get_object_or_404(Chantier, pk=pk)
        chantier_name = chantier.nom

        try:
            chantier.delete()
            messages.success(request, f'Chantier "{chantier_name}" supprimé avec succès.')
        except Exception as e:
            messages.error(request, f'Erreur lors de la suppression du chantier: {str(e)}')

        return redirect(reverse('core:chantiers'))


# Vues pour Personnel
@method_decorator(login_required, name='dispatch')
class PersonnelListView(View):
    def get(self, request):
        personnel = Personnel.objects.select_related('user', 'chantier_actuel').all().order_by('user__last_name')
        return render(request, 'core/personnel_list.html', {'personnel': personnel})


@method_decorator(login_required, name='dispatch')
class PersonnelCreateView(View):
    def get(self, request):
        # Utilisateurs qui n'ont pas encore de profil personnel
        available_users = User.objects.exclude(personnel__isnull=False).order_by('last_name')
        chantiers = Chantier.objects.filter(statut__in=['planifie', 'en_cours']).order_by('nom')
        return render(request, 'core/personnel_form.html', {
            'available_users': available_users,
            'chantiers': chantiers
        })

    def post(self, request):
        try:
            personnel = Personnel.objects.create(
                user_id=request.POST['user'],
                role=request.POST['role'],
                taux_horaire=request.POST['taux_horaire'],
                telephone=request.POST.get('telephone', ''),
                adresse=request.POST.get('adresse', ''),
                date_embauche=request.POST['date_embauche'],
                chantier_actuel_id=request.POST.get('chantier_actuel') or None,
                est_actif=request.POST.get('est_actif', 'on') == 'on'
            )
            messages.success(request, f'Personnel "{personnel.user.get_full_name()}" ajouté avec succès.')
            return redirect(reverse('core:personnel'))
        except Exception as e:
            messages.error(request, f'Erreur lors de l\'ajout du personnel: {str(e)}')
            return redirect(reverse('core:personnel_create'))


@method_decorator(login_required, name='dispatch')
class PersonnelUpdateView(View):
    def get(self, request, pk):
        personnel = get_object_or_404(Personnel, pk=pk)
        chantiers = Chantier.objects.filter(statut__in=['planifie', 'en_cours']).order_by('nom')
        return render(request, 'core/personnel_form.html', {
            'personnel': personnel,
            'chantiers': chantiers
        })

    def post(self, request, pk):
        personnel = get_object_or_404(Personnel, pk=pk)
        try:
            personnel.role = request.POST['role']
            personnel.taux_horaire = request.POST['taux_horaire']
            personnel.telephone = request.POST.get('telephone', '')
            personnel.adresse = request.POST.get('adresse', '')
            personnel.date_embauche = request.POST['date_embauche']
            personnel.chantier_actuel_id = request.POST.get('chantier_actuel') or None
            personnel.est_actif = request.POST.get('est_actif', 'on') == 'on'
            personnel.save()
            messages.success(request, f'Personnel "{personnel.user.get_full_name()}" mis à jour avec succès.')
            return redirect(reverse('core:personnel'))
        except Exception as e:
            messages.error(request, f'Erreur lors de la mise à jour du personnel: {str(e)}')
            return redirect(reverse('core:personnel_update', kwargs={'pk': pk}))


# Vues pour Materiau
@method_decorator(login_required, name='dispatch')
class MateriauListView(View):
    def get(self, request):
        materiaux = Materiau.objects.select_related('fournisseur').all().order_by('nom')
        return render(request, 'core/materiau_list.html', {'materiaux': materiaux})


@method_decorator(login_required, name='dispatch')
class MateriauCreateView(View):
    def get(self, request):
        fournisseurs = Fournisseur.objects.all().order_by('nom')
        return render(request, 'core/materiau_form.html', {'fournisseurs': fournisseurs})

    def post(self, request):
        try:
            materiau = Materiau.objects.create(
                nom=request.POST['nom'],
                categorie=request.POST['categorie'],
                description=request.POST.get('description', ''),
                unite=request.POST.get('unite', 'unités'),
                quantite_stock=request.POST.get('quantite_stock', 0),
                seuil_minimum=request.POST.get('seuil_minimum', 0),
                prix_unitaire=request.POST['prix_unitaire'],
                fournisseur_id=request.POST.get('fournisseur') or None
            )
            messages.success(request, f'Matériau "{materiau.nom}" ajouté avec succès.')
            return redirect(reverse('core:materiaux'))
        except Exception as e:
            messages.error(request, f'Erreur lors de l\'ajout du matériau: {str(e)}')
            return redirect(reverse('core:materiau_create'))


@method_decorator(login_required, name='dispatch')
class MateriauUpdateView(View):
    def get(self, request, pk):
        materiau = get_object_or_404(Materiau, pk=pk)
        fournisseurs = Fournisseur.objects.all().order_by('nom')
        return render(request, 'core/materiau_form.html', {
            'materiau': materiau,
            'fournisseurs': fournisseurs
        })

    def post(self, request, pk):
        materiau = get_object_or_404(Materiau, pk=pk)
        try:
            materiau.nom = request.POST['nom']
            materiau.categorie = request.POST['categorie']
            materiau.description = request.POST.get('description', '')
            materiau.unite = request.POST.get('unite', materiau.unite)
            materiau.quantite_stock = request.POST.get('quantite_stock', materiau.quantite_stock)
            materiau.seuil_minimum = request.POST.get('seuil_minimum', materiau.seuil_minimum)
            materiau.prix_unitaire = request.POST['prix_unitaire']
            materiau.fournisseur_id = request.POST.get('fournisseur') or None
            materiau.save()
            messages.success(request, f'Matériau "{materiau.nom}" mis à jour avec succès.')
            return redirect(reverse('core:materiaux'))
        except Exception as e:
            messages.error(request, f'Erreur lors de la mise à jour du matériau: {str(e)}')
            return redirect(reverse('core:materiau_update', kwargs={'pk': pk}))


# Vues pour Fournisseur
@method_decorator(login_required, name='dispatch')
class FournisseurListView(View):
    def get(self, request):
        fournisseurs = Fournisseur.objects.all().order_by('nom')
        return render(request, 'core/fournisseur_list.html', {'fournisseurs': fournisseurs})


@method_decorator(login_required, name='dispatch')
class FournisseurCreateView(View):
    def get(self, request):
        return render(request, 'core/fournisseur_form.html')

    def post(self, request):
        try:
            fournisseur = Fournisseur.objects.create(
                nom=request.POST['nom'],
                contact=request.POST.get('contact', ''),
                telephone=request.POST.get('telephone', ''),
                email=request.POST.get('email', ''),
                adresse=request.POST.get('adresse', ''),
                specialite=request.POST.get('specialite', '')
            )
            messages.success(request, f'Fournisseur "{fournisseur.nom}" ajouté avec succès.')
            return redirect(reverse('core:fournisseurs'))
        except Exception as e:
            messages.error(request, f'Erreur lors de l\'ajout du fournisseur: {str(e)}')
            return redirect(reverse('core:fournisseur_create'))


class FournisseurUpdateView(View):
    def get(self, request, pk):
        fournisseur = get_object_or_404(Fournisseur, pk=pk)
        return render(request, 'core/fournisseur_form.html', {'fournisseur': fournisseur})

    def post(self, request, pk):
        fournisseur = get_object_or_404(Fournisseur, pk=pk)
        try:
            fournisseur.nom = request.POST['nom']
            fournisseur.contact = request.POST.get('contact', '')
            fournisseur.telephone = request.POST.get('telephone', '')
            fournisseur.email = request.POST.get('email', '')
            fournisseur.adresse = request.POST.get('adresse', '')
            fournisseur.specialite = request.POST.get('specialite', '')
            fournisseur.save()
            messages.success(request, f'Fournisseur "{fournisseur.nom}" mis à jour avec succès.')
            return redirect(reverse('core:fournisseurs'))
        except Exception as e:
            messages.error(request, f'Erreur lors de la mise à jour du fournisseur: {str(e)}')
            return redirect(reverse('core:fournisseur_update', kwargs={'pk': pk}))
