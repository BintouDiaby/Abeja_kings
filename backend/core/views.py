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
import logging

from django.db import models
from django.db.models import F
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.contrib.auth import views as auth_views

from .models import Client, Facture, FactureLine, UserProfile, Chantier, Personnel, Materiau, Fournisseur, Rapport, FactureActionLog
from .forms import ClientForm, FactureForm
from .forms import PaymentForm
from .models import Payment
from .models import PersonnelPayment
from .forms import PersonnelPaymentForm
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse
import csv
from decimal import Decimal
import datetime
import calendar
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from django.template.loader import render_to_string
from io import BytesIO
from django.contrib.staticfiles import finders
import os
try:
    from xhtml2pdf import pisa
except Exception:
    pisa = None

@ensure_csrf_cookie
@login_required
def commande_create(request, pk):
    """Serve a supplier-contact page on GET and create a Commande on POST.

    GET: render a small form where the user can pick a fournisseur, edit quantity
         and include a message before sending.
    POST: create the `Commande` and redirect back to the materials list with a flash.
    """
    profile = getattr(request.user, 'userprofile', None)
    materiau = get_object_or_404(Materiau, pk=pk)

    # Only allow certain roles to create commande
    if not profile or profile.role not in ('admin', 'directeur', 'comptable', 'chef'):
        messages.error(request, "Vous n'avez pas la permission de créer une commande.")
        return redirect(reverse('core:materiaux'))

    from .models import Commande

    # GET -> show supplier contact / order form
    if request.method == 'GET':
        fournisseurs = Fournisseur.objects.order_by('nom')
        context = {
            'materiau': materiau,
            'fournisseurs': fournisseurs,
            'quantite_recommandee': materiau.quantite_recommandee,
        }
        return render(request, 'core/commande_form.html', context)

    # POST -> create the commande (existing logic)
    try:
        quantite = int(request.POST.get('quantite', 0))
    except Exception:
        quantite = 0

    if quantite <= 0:
        # fallback: recommended = seuil - stock or 1
        recommended = materiau.seuil_minimum - materiau.quantite_stock
        quantite = recommended if recommended > 0 else 1

    fournisseur_id = request.POST.get('fournisseur')
    fournisseur = None
    if fournisseur_id:
        try:
            fournisseur = Fournisseur.objects.get(pk=int(fournisseur_id))
        except Exception:
            fournisseur = None

    commande = Commande.objects.create(
        materiau=materiau,
        quantite=quantite,
        fournisseur=fournisseur,
        demandeur=request.user,
        statut='preparée'
    )

    messages.success(request, f'Commande créée: {materiau.nom} x{quantite}.')
    return redirect(reverse('core:materiaux'))




@method_decorator(login_required, name='dispatch')
class DashboardView(View):
    def get(self, request):
        try:
            # Statistiques générales
            total_chantiers = Chantier.objects.count()
            chantiers_actifs = Chantier.objects.filter(statut='en_cours').count()  # Count active projects
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
            # Rapports récents
            # - admins et directeurs voient tous
            # - chefs voient seulement les rapports pour leurs chantiers ou ceux qu'ils ont rédigés
            # - autres rôles ne voient que leurs propres rapports
            if profile and profile.role in ('admin', 'directeur'):
                rapports_qs = Rapport.objects.select_related('chantier', 'auteur').order_by('-created_at')
            elif profile and profile.role == 'chef':
                # Les chefs peuvent être liés aux chantiers soit via le champ
                # `chantier.chef_chantier` (User) soit via
                # `chantier.chef_chantier_employee.user` (Employee -> User).
                # Inclure aussi les rapports rédigés par le chef.
                rapports_qs = Rapport.objects.select_related('chantier', 'auteur').filter(
                    models.Q(chantier__chef_chantier=request.user)
                    | models.Q(chantier__chef_chantier_employee__user=request.user)
                    | models.Q(auteur=request.user)
                ).order_by('-created_at')
            else:
                rapports_qs = Rapport.objects.select_related('chantier').filter(auteur=request.user).order_by('-created_at')

            rapports_count = rapports_qs.count()
            rapports_recents = rapports_qs[:5]
            # Nombre de rapports rédigés par l'utilisateur courant (toujours utile)
            try:
                rapports_user_count = Rapport.objects.filter(auteur=request.user).count()
            except Exception:
                rapports_user_count = 0

            # Contrôle d'accès selon le rôle -> les ouvriers n'ont pas accès au dashboard
            # Si l'utilisateur est un 'ouvrier', le rediriger vers la page de rapports
            if profile and profile.role == 'ouvrier':
                return redirect(reverse('core:rapports'))

            # Contrôle d'accès aux données financières selon le rôle
            show_finances = False
            # Only admin, directeur and comptable see finances; chefs should not
            if profile and profile.role in ('admin', 'directeur', 'comptable'):
                show_finances = True

            # Adapter le dashboard pour le rôle 'comptable' : ne montrer
            # que les informations financières / fournisseurs / matériaux
            if profile and profile.role == 'comptable':
                # masquer les sections opérationnelles non pertinentes
                chantiers_recents = []
                total_chantiers = 0
                chantiers_actifs = 0
                chantiers_termines = 0
                # Le comptable doit pouvoir voir et gérer le personnel (paiements,
                # fiches de paie, etc.). Ne pas écraser `total_personnel` ici.

                # Afficher les rapports rédigés par le comptable (au lieu de forcer 0)
                try:
                    rapports_qs = Rapport.objects.select_related('chantier').filter(auteur=request.user).order_by('-created_at')
                    rapports_count = rapports_qs.count()
                    rapports_recents = rapports_qs[:5]
                except Exception:
                    rapports_count = 0
                    rapports_recents = []

                # Compteurs et métriques utiles pour le comptable
                try:
                    factures_count = Facture.objects.count()
                except Exception:
                    factures_count = 0

                # garantir que les totals existants sont cohérents
                try:
                    total_fournisseurs = Fournisseur.objects.count()
                except Exception:
                    total_fournisseurs = 0

                try:
                    total_materiaux = Materiau.objects.count()
                except Exception:
                    total_materiaux = 0

                # exposer ces valeurs dans le contexte (montant_factures_mois est calculé plus haut)
                # note: montant_factures_mois reste disponible pour l'affichage monétaire

                # factures impayées récentes (annotate paiements et filtrer)
                try:
                    unpaid_qs = Facture.objects.annotate(
                        paid=Coalesce(models.Sum('payments__montant'), 0),
                    ).annotate(
                        diff=F('total') - F('paid')
                    ).filter(diff__gt=0).order_by('-date')[:5]
                    unpaid_factures = unpaid_qs
                except Exception:
                    try:
                        unpaid_factures = Facture.objects.all().order_by('-date')[:5]
                    except Exception:
                        unpaid_factures = []

                try:
                    fournisseurs_recents = Fournisseur.objects.order_by('-created_at')[:5]
                except Exception:
                    fournisseurs_recents = []

            # For 'chef' role: allow full dashboard visibility but hide invoices
            if profile and profile.role == 'chef':
                # do not restrict other dashboard metrics by chef ownership
                # ensure finances/factures remain hidden for chefs
                show_finances = False
                factures_recentes = []
                montant_factures_mois = 0

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
                'rapports_user_count': rapports_user_count,
                'show_finances': show_finances,
                'factures_count': locals().get('factures_count', None),
                'unpaid_factures': locals().get('unpaid_factures', []),
                'fournisseurs_recents': locals().get('fournisseurs_recents', []),
                'role': getattr(profile, 'role', None),
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
        profile = getattr(request.user, 'userprofile', None)
            # Restrict access: only admin, directeur, comptable, and chef can view clients
        if not profile or profile.role not in ('admin', 'directeur', 'comptable', 'chef'):
            return redirect(reverse('core:dashboard'))

        clients = Client.objects.all().order_by('-created_at')
        return render(request, 'core/client_list.html', {'clients': clients})


@login_required
def personnel_payments(request, personnel_id):
    # Liste des paiements d'un membre du personnel et formulaire de création
    personnel = get_object_or_404(Personnel, pk=personnel_id)
    if request.method == 'POST':
        form = PersonnelPaymentForm(request.POST)
        if form.is_valid():
            pp = PersonnelPayment.objects.create(
                personnel=personnel,
                montant=form.cleaned_data['montant'],
                date=form.cleaned_data['date'],
                mode=form.cleaned_data['mode'],
                reference=form.cleaned_data.get('reference', ''),
                periode=form.cleaned_data.get('periode', ''),
                note=form.cleaned_data.get('note', ''),
                created_by=request.user
            )
            messages.success(request, f'Paiement de {pp.montant} enregistré pour {personnel.user.get_full_name()}')
            return redirect(reverse('core:personnel_payments', kwargs={'personnel_id': personnel.id}))
    else:
        form = PersonnelPaymentForm(initial={'date': timezone.now().date()})

    paiements = personnel.paiements.order_by('-date')[:50]
    # calculer salaire de base (mensuel) pour affichage dynamique
    try:
        if personnel.role == 'chef_chantier' and getattr(personnel, 'salaire_mensuel', None):
            base_salary = Decimal(getattr(personnel, 'salaire_mensuel') or 0)
        else:
            taux = Decimal(getattr(personnel, 'taux_journalier', 0) or 0)
            base_salary = taux * Decimal(22)
    except Exception:
        base_salary = Decimal(0)

    chantier = getattr(personnel, 'chantier_actuel', None)
    periode = request.GET.get('periode') or request.GET.get('month') or ''
    return render(request, 'core/personnel_payments.html', {'personnel': personnel, 'paiements': paiements, 'form': form, 'base_salary': base_salary, 'chantier': chantier, 'periode': periode})


@login_required
@user_passes_test(lambda u: getattr(getattr(u, 'userprofile', None), 'role', None) in ('comptable', 'admin', 'directeur') or u.is_superuser)
def personnel_payments_history(request):
    # Page globale pour le comptable: liste filtrable et export CSV
    # Support filtering by month (YYYY-MM) and chantier
    month = request.GET.get('month')  # expected format YYYY-MM
    chantier_id = request.GET.get('chantier')

    # Determine date range for the filter
    date_from = request.GET.get('from')
    date_to = request.GET.get('to')
    if month:
        try:
            year, mon = month.split('-')
            year = int(year); mon = int(mon)
            first_day = datetime.date(year, mon, 1)
            last_day = datetime.date(year, mon, calendar.monthrange(year, mon)[1])
            date_from = first_day.isoformat()
            date_to = last_day.isoformat()
        except Exception:
            date_from = date_from

    # Base personnels queryset, optionally filter by chantier
    personnels_qs = Personnel.objects.order_by('user__last_name')
    # sanitize chantier_id: ignore empty strings or the string 'None' (coming from UI)
    if chantier_id and chantier_id.lower() != 'none':
        try:
            chantier_id_int = int(chantier_id)
            personnels_qs = personnels_qs.filter(chantier_actuel_id=chantier_id_int)
        except Exception:
            # ignore invalid chantier filter values
            pass

    # Build rows: expected_net (salary) and paid for the date range
    rows = []
    for person in personnels_qs:
        # expected net: use salaire_mensuel for chefs, else taux_journalier * 22
        try:
            if person.role == 'chef_chantier' and getattr(person, 'salaire_mensuel', None):
                expected = Decimal(getattr(person, 'salaire_mensuel') or 0)
            else:
                taux = Decimal(getattr(person, 'taux_journalier', 0) or 0)
                expected = taux * Decimal(22)
        except Exception:
            expected = Decimal(0)

        paid_qs = PersonnelPayment.objects.filter(personnel=person)
        if date_from:
            paid_qs = paid_qs.filter(date__gte=date_from)
        if date_to:
            paid_qs = paid_qs.filter(date__lte=date_to)
        paid_agg = paid_qs.aggregate(total=Sum('montant'))['total'] or Decimal(0)

        status = 'Payé' if paid_agg >= expected and expected > 0 else 'En attente'

        rows.append({'personnel': person, 'expected': expected, 'paid': paid_agg, 'status': status})

    # Export CSV for aggregated rows
    if request.GET.get('export') == 'csv':
        resp = HttpResponse(content_type='text/csv')
        resp['Content-Disposition'] = 'attachment; filename="personnel_payments_summary.csv"'
        writer = csv.writer(resp)
        writer.writerow(['Personnel', 'Poste', 'Chantier', 'Net attendu (FCFA)', 'Payé (FCFA)', 'Statut'])
        for r in rows:
            writer.writerow([r['personnel'].user.get_full_name(), r['personnel'].get_role_display(), getattr(r['personnel'].chantier_actuel, 'nom', ''), int(r['expected']), int(r['paid']), r['status']])
        return resp

    # Pass list of chantiers for filter select
    chantiers = Chantier.objects.order_by('nom')
    return render(request, 'core/personnel_payments_history.html', {'rows': rows, 'chantiers': chantiers, 'filters': {'month': month, 'chantier': chantier_id, 'from': date_from, 'to': date_to}})


@login_required
@user_passes_test(lambda u: getattr(getattr(u, 'userprofile', None), 'role', None) in ('comptable', 'admin', 'directeur') or u.is_superuser)
def personnel_mark_paid(request, personnel_id):
    # Mark the expected net as paid for a personnel for a given period (month) or today.
    if request.method != 'POST':
        return redirect(reverse('core:personnel_payments_history'))

    personnel = get_object_or_404(Personnel, pk=personnel_id)
    period = request.POST.get('periode') or request.POST.get('month')

    # compute expected same way as the history view
    try:
        if personnel.role == 'chef_chantier' and getattr(personnel, 'salaire_mensuel', None):
            expected = Decimal(getattr(personnel, 'salaire_mensuel') or 0)
        else:
            taux = Decimal(getattr(personnel, 'taux_journalier', 0) or 0)
            expected = taux * Decimal(22)
    except Exception:
        expected = Decimal(0)

    # create a PersonnelPayment record marking the amount as paid
    pp = PersonnelPayment.objects.create(
        personnel=personnel,
        montant=expected,
        date=timezone.now().date(),
        mode=request.POST.get('mode', 'especes'),
        reference=request.POST.get('reference', ''),
        periode=period or '',
        note=f"Marqué payé via interface par {request.user.username}",
        created_by=request.user,
    )
    messages.success(request, f"Paiement de {int(expected)} FCFA enregistré pour {personnel.user.get_full_name()}")

    # redirect back to history with same filters
    redirect_url = reverse('core:personnel_payments_history')
    q = {}
    if period:
        q['month'] = period
    if request.POST.get('chantier'):
        q['chantier'] = request.POST.get('chantier')
    if q:
        from urllib.parse import urlencode
        redirect_url += '?' + urlencode(q)

    return redirect(redirect_url)


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

    def form_invalid(self, form):
        logger = logging.getLogger('core.views')
        username = self.request.POST.get('username') or self.request.POST.get('email')
        password = self.request.POST.get('password')
        try:
            from django.contrib.auth import authenticate
            user = authenticate(self.request, username=username, password=password)
            auth_ok = getattr(user, 'username', None) is not None
        except Exception as e:
            user = None
            auth_ok = False
            logger.exception('Exception while calling authenticate in form_invalid')

        logger.debug('Login form_invalid: username=%r, auth_ok=%s, form_errors=%s', username, auth_ok, form.errors.as_json())
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        """Ajouter `test_accounts` au contexte pour affichage dans le template de login.

        On récupère les utilisateurs dont l'email se termine par `@abeja.kings`.
        Pour les comptes créés par le script de test, le mot de passe par défaut
        est connu (password123) — on l'expose pour faciliter les tests.
        """
        context = super().get_context_data(**kwargs)
        try:
            test_qs = User.objects.filter(email__endswith='@abeja.kings').order_by('username')
            defaults = {
                'chef': 'password123',
                'ouvrier': 'password123',
                'admin_user': 'password123',
                'comptable': 'password123',
            }
            accounts = []
            for u in test_qs:
                try:
                    role = getattr(u.userprofile, 'role', '') or ''
                except Exception:
                    role = ''
                accounts.append({
                    'username': u.username,
                    'email': u.email,
                    'role': role,
                    'password': defaults.get(u.username),
                })
            # Si aucun compte trouvé, fournir un fallback visuel (exemples) pour faciliter les tests
            if not accounts:
                accounts = [
                    {'username': 'admin', 'email': 'admin@abeja.kings', 'role': 'admin', 'password': 'admin123'},
                    {'username': 'chef', 'email': 'chef@abeja.kings', 'role': 'chef', 'password': 'password123'},
                    {'username': 'ouvrier', 'email': 'ouvrier@abeja.kings', 'role': 'ouvrier', 'password': 'password123'},
                ]
            context['test_accounts'] = accounts
        except Exception:
            # En cas d'erreur imprévue, afficher aussi le fallback pour éviter la page vide
            context['test_accounts'] = [
                {'username': 'admin', 'email': 'admin@abeja.kings', 'role': 'admin', 'password': 'admin123'},
                {'username': 'chef', 'email': 'chef@abeja.kings', 'role': 'chef', 'password': 'password123'},
                {'username': 'ouvrier', 'email': 'ouvrier@abeja.kings', 'role': 'ouvrier', 'password': 'password123'},
            ]
        return context


@method_decorator(login_required, name='dispatch')
class ClientCreateView(View):
    def get(self, request):
        profile = getattr(request.user, 'userprofile', None)
        # Allow 'admin', 'directeur' and 'chef' to manage chantiers from the app
        if not profile or profile.role not in ('admin', 'directeur', 'chef'):
            return redirect(reverse('core:dashboard'))
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
        profile = getattr(request.user, 'userprofile', None)
        if not profile or profile.role not in ('admin', 'directeur', 'chef', 'comptable'):
            return redirect(reverse('core:dashboard'))
        client = get_object_or_404(Client, pk=pk)
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            return redirect(reverse('core:clients'))
        return render(request, 'core/client_form.html', {'form': form, 'client': client})


@method_decorator(login_required, name='dispatch')
class FactureListView(View):
    def get(self, request):
        # Seuls les admins peuvent accéder aux factures
        profile = getattr(request.user, 'userprofile', None)
        if not profile or profile.role not in ('admin', 'directeur', 'comptable', 'chef'):
            return redirect(reverse('core:dashboard'))
        
        factures = Facture.objects.select_related('client').all().order_by('-created_at')
        # Calculer le montant total des factures pour l'affichage (évite d'utiliser des filtres personnalisés en template)
        try:
            montant_total = factures.aggregate(total=models.Sum('total'))['total'] or 0
        except Exception:
            # fallback si l'aggregation échoue
            montant_total = sum([getattr(f, 'total', 0) or 0 for f in factures])

        today = timezone.now().date()
        return render(request, 'core/facture_list.html', {'factures': factures, 'montant_total': montant_total, 'today': today})


@method_decorator(login_required, name='dispatch')
class FactureDetailView(View):
    def get(self, request, pk):
        profile = getattr(request.user, 'userprofile', None)
        # Seuls admin (et potentiellement gerant) peuvent voir les détails financiers
        if not profile or profile.role not in ('admin', 'directeur', 'comptable', 'gerant', 'chef'):
            # Les chefs ne doivent pas accéder aux factures
            return redirect(reverse('core:dashboard'))

        facture = get_object_or_404(Facture, pk=pk)
        payments = facture.payments.order_by('-date') if hasattr(facture, 'payments') else []
        payment_form = PaymentForm()

        printable = request.GET.get('print')
        context = {
            'facture': facture,
            'payments': payments,
            'payment_form': payment_form,
            'printable': bool(printable),
        }
        return render(request, 'core/facture_detail.html', context)

    def post(self, request, pk):
        # Permet d'ajouter un paiement via le formulaire dans la page detail
        profile = getattr(request.user, 'userprofile', None)
        if not profile or profile.role not in ('admin', 'comptable', 'gerant'):
            return redirect(reverse('core:dashboard'))

        facture = get_object_or_404(Facture, pk=pk)
        form = PaymentForm(request.POST)
        if form.is_valid():
            Payment.objects.create(
                facture=facture,
                montant=form.cleaned_data['montant'],
                date=form.cleaned_data['date'],
                mode=form.cleaned_data['mode'],
                reference=form.cleaned_data.get('reference',''),
                created_by=request.user
            )
            # mettre à jour le statut si payé
            if facture.reste_a_payer <= 0:
                facture.statut = 'payee'
                facture.save()
        return redirect(reverse('core:facture_detail', args=[pk]))


@login_required
def facture_pdf(request, pk):
    profile = getattr(request.user, 'userprofile', None)
    if not profile or profile.role not in ('admin', 'directeur', 'comptable', 'gerant', 'chef'):
        return redirect(reverse('core:dashboard'))

    facture = get_object_or_404(Facture, pk=pk)
    payments = facture.payments.order_by('-date') if hasattr(facture, 'payments') else []

    context = {
        'facture': facture,
        'payments': payments,
        'payment_form': PaymentForm(),
        'printable': True,
    }

    html = render_to_string('core/facture_detail.html', context, request=request)

    if pisa is None:
        return HttpResponse('PDF generation library not installed. Please install xhtml2pdf.', status=500)

    result = BytesIO()

    def link_callback(uri, rel):
        # Resolve static and media URIs to filesystem paths for xhtml2pdf
        if uri.startswith(settings.STATIC_URL):
            path = finders.find(uri.replace(settings.STATIC_URL, ''))
            if path:
                return path
        if uri.startswith(settings.MEDIA_URL):
            media_path = uri.replace(settings.MEDIA_URL, '')
            return os.path.join(settings.MEDIA_ROOT, media_path)
        return uri

    pdf = pisa.CreatePDF(src=html, dest=result, link_callback=link_callback)
    if pdf.err:
        return HttpResponse('Erreur lors de la génération du PDF', status=500)

    response = HttpResponse(result.getvalue(), content_type='application/pdf')
    filename = f"facture-{facture.numero}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@method_decorator(login_required, name='dispatch')
class FactureUpdateView(View):
    def get(self, request, pk):
        profile = getattr(request.user, 'userprofile', None)
        if not profile or profile.role not in ('admin', 'directeur', 'comptable'):
            return redirect(reverse('core:dashboard'))

        facture = get_object_or_404(Facture, pk=pk)
        form = FactureForm(instance=facture)
        clients = Client.objects.all().order_by('nom')
        chantiers = Chantier.objects.all().order_by('nom')
        return render(request, 'core/facture_form.html', {'form': form, 'clients': clients, 'chantiers': chantiers, 'is_update': True, 'facture': facture})

    def post(self, request, pk):
        profile = getattr(request.user, 'userprofile', None)
        if not profile or profile.role not in ('admin', 'directeur', 'comptable'):
            return redirect(reverse('core:dashboard'))

        facture = get_object_or_404(Facture, pk=pk)
        data = request.POST.copy()
        form = FactureForm(data, instance=facture)
        if form.is_valid():
            facture = form.save()
            # Replace lines if provided
            lines_json = data.get('lines_json')
            if lines_json:
                try:
                    FactureLine.objects.filter(facture=facture).delete()
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
                    pass

            # Recalculate totals
            try:
                agg = FactureLine.objects.filter(facture=facture).aggregate(subtotal=models.Sum('montant'))
                subtotal = agg['subtotal'] or 0
                facture.subtotal = subtotal
                try:
                    tva_pct = float(getattr(facture, 'tva_pct') or 0)
                except Exception:
                    tva_pct = 0
                facture.tva_amount = (subtotal * tva_pct) / 100
                facture.total = subtotal + facture.tva_amount
                facture.save()
            except Exception:
                pass

            # log
            try:
                FactureActionLog.objects.create(facture=facture, action='partial_payment' if facture.reste_a_payer>0 else 'mark_paid', user=request.user, note='Modifiée depuis la liste')
            except Exception:
                pass

            return redirect(reverse('core:factures'))


@login_required
def facture_delete(request, pk):
    profile = getattr(request.user, 'userprofile', None)
    if not profile or profile.role not in ('admin', 'directeur'):
        return redirect(reverse('core:dashboard'))

    if request.method != 'POST':
        return redirect(reverse('core:factures'))

    facture = get_object_or_404(Facture, pk=pk)
    try:
        FactureActionLog.objects.create(facture=facture, action='mark_unpaid', user=request.user, note='Supprimée depuis la liste')
    except Exception:
        pass
    facture.delete()
    return redirect(reverse('core:factures'))


@login_required
def facture_mark_paid(request, pk):
    profile = getattr(request.user, 'userprofile', None)
    if not profile or profile.role not in ('admin', 'comptable', 'directeur'):
        return redirect(reverse('core:dashboard'))

    if request.method != 'POST':
        return redirect(reverse('core:factures'))

    facture = get_object_or_404(Facture, pk=pk)
    reste = facture.reste_a_payer or 0
    if reste > 0:
        Payment.objects.create(
            facture=facture,
            montant=reste,
            date=timezone.now().date(),
            mode='autre',
            reference='Marqué comme payé (liste)',
            created_by=request.user
        )
    # Mettre à jour le statut
    try:
        if facture.reste_a_payer <= 0:
            facture.statut = 'payee'
            facture.save()
    except Exception:
        facture.statut = 'payee'
        facture.save()

    return redirect(reverse('core:factures'))


@login_required
def facture_mark_annulee(request, pk):
    profile = getattr(request.user, 'userprofile', None)
    if not profile or profile.role not in ('admin', 'comptable', 'directeur'):
        return redirect(reverse('core:dashboard'))

    if request.method != 'POST':
        return redirect(reverse('core:factures'))

    facture = get_object_or_404(Facture, pk=pk)
    facture.statut = 'annulee'
    facture.save()
    # log action
    try:
        FactureActionLog.objects.create(
            facture=facture,
            action='cancel',
            user=request.user,
            note='Annulée depuis la liste'
        )
    except Exception:
        pass

    return redirect(reverse('core:factures'))


@login_required
def facture_reopen(request, pk):
    profile = getattr(request.user, 'userprofile', None)
    if not profile or profile.role not in ('admin', 'comptable', 'directeur'):
        return redirect(reverse('core:dashboard'))

    if request.method != 'POST':
        return redirect(reverse('core:factures'))

    facture = get_object_or_404(Facture, pk=pk)
    facture.statut = 'envoyee'
    facture.save()
    # log action
    try:
        FactureActionLog.objects.create(
            facture=facture,
            action='reopen',
            user=request.user,
            note='Rouverte depuis la liste'
        )
    except Exception:
        pass

    return redirect(reverse('core:factures'))


@method_decorator(login_required, name='dispatch')
class FactureCreateView(View):
    def get(self, request):
        # Seuls les admins peuvent créer des factures
        profile = getattr(request.user, 'userprofile', None)
        if not profile or profile.role not in ('admin', 'directeur', 'comptable'):
            return redirect(reverse('core:dashboard'))
        
        form = FactureForm()
        clients = Client.objects.all().order_by('nom')
        chantiers = Chantier.objects.all().order_by('nom')
        return render(request, 'core/facture_form.html', {'form': form, 'clients': clients, 'chantiers': chantiers})
    
    def post(self, request):
        # Seuls les admins peuvent créer des factures
        profile = getattr(request.user, 'userprofile', None)
        if not profile or profile.role not in ('admin', 'directeur', 'comptable'):
            return redirect(reverse('core:dashboard'))
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

        clients = Client.objects.all().order_by('nom')
        chantiers = Chantier.objects.all().order_by('nom')
        return render(request, 'core/facture_form.html', {'form': form, 'clients': clients, 'chantiers': chantiers})


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
        profile = getattr(request.user, 'userprofile', None)
        if not profile or profile.role not in ('admin', 'directeur', 'chef'):
            return redirect(reverse('core:dashboard'))
        users = User.objects.select_related('userprofile').all().order_by('username')
        return render(request, 'core/user_list.html', {'users': users})



@method_decorator(login_required, name='dispatch')
class UserCreateView(View):
    def get(self, request):
        profile = getattr(request.user, 'userprofile', None)
        if not profile or profile.role not in ('admin', 'directeur'):
            return redirect(reverse('core:dashboard'))
        return render(request, 'core/user_form.html', {'form': UserCreationForm()})

    def post(self, request):
        profile = getattr(request.user, 'userprofile', None)
        if not profile or profile.role not in ('admin', 'directeur'):
            return redirect(reverse('core:dashboard'))
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # save additional fields provided in the template
            user.first_name = request.POST.get('first_name', '')
            user.last_name = request.POST.get('last_name', '')
            user.email = request.POST.get('email', '')
            user.save()
            # Créer le profil utilisateur
            UserProfile.objects.create(
                user=user,
                role=request.POST.get('role', 'ouvrier'),
                telephone=request.POST.get('telephone', ''),
            )
            messages.success(request, f'Utilisateur {user.username} créé avec succès.')
            return redirect(reverse('core:users'))
        return render(request, 'core/user_form.html', {'form': form})



@method_decorator(login_required, name='dispatch')
class UserUpdateView(View):
    def get(self, request, pk):
        profile = getattr(request.user, 'userprofile', None)
        if not profile or profile.role not in ('admin', 'directeur'):
            return redirect(reverse('core:dashboard'))
        user = get_object_or_404(User, pk=pk)
        profile_obj, created = UserProfile.objects.get_or_create(user=user)
        return render(request, 'core/user_form.html', {
            'form': UserCreationForm(instance=user),
            'profile': profile_obj,
            'is_update': True
        })

    def post(self, request, pk):
        profile = getattr(request.user, 'userprofile', None)
        if not profile or profile.role not in ('admin', 'directeur'):
            return redirect(reverse('core:dashboard'))
        user = get_object_or_404(User, pk=pk)
        profile_obj, created = UserProfile.objects.get_or_create(user=user)

        # Mettre à jour le profil
        profile_obj.role = request.POST.get('role', profile_obj.role)
        profile_obj.telephone = request.POST.get('telephone', profile_obj.telephone)
        profile_obj.save()
        messages.success(request, f'Profil mis à jour pour {user.username}.')
        return redirect(reverse('core:users'))


@login_required
def user_delete(request, pk):
    """Delete a user. Only admin or directeur may delete users.
    Confirmation must be a POST request from the edit form.
    """
    profile = getattr(request.user, 'userprofile', None)
    if not profile or profile.role not in ('admin', 'directeur'):
        return redirect(reverse('core:dashboard'))

    if request.method != 'POST':
        return redirect(reverse('core:user_edit', args=[pk]))

    user = get_object_or_404(User, pk=pk)
    # Prevent deleting self
    if user == request.user:
        messages.error(request, "Vous ne pouvez pas supprimer votre propre compte.")
        return redirect(reverse('core:user_edit', args=[pk]))

    try:
        user.delete()
        messages.success(request, f'Utilisateur {user.username} supprimé.')
    except Exception:
        messages.error(request, "Erreur lors de la suppression de l'utilisateur.")

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
    # Si l'utilisateur connecté est un chef de chantier, ne renvoyer
    # que les ouvriers (il ne doit pas voir les autres rôles).
    user_role = None
    try:
        user_role = getattr(request.user, 'userprofile', None)
        if user_role is not None:
            user_role = request.user.userprofile.role
    except Exception:
        user_role = None
    if user_role == 'chef':
        personnel = personnel.filter(role='ouvrier')
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
            'taux_horaire': float(personne.taux_journalier) if getattr(personne, 'taux_journalier', None) is not None else None,
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
    profile = getattr(request.user, 'userprofile', None)
    if not profile or profile.role not in ('admin', 'directeur', 'comptable', 'chef'):
        return JsonResponse({'error': 'forbidden'}, status=403)

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
    profile = getattr(request.user, 'userprofile', None)
    if not profile or profile.role not in ('admin', 'directeur', 'comptable'):
        return JsonResponse({'error': 'forbidden'}, status=403)

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

    # Fournir la liste des chantiers et quelques compteurs pour le template
    chantiers_list = Chantier.objects.select_related('chef_chantier', 'chef_chantier_employee__user').order_by('-created_at')
    rapports_count = rapports.count() if hasattr(rapports, 'count') else len(rapports)
    rapports_pending = 0
    chantiers_actifs = Chantier.objects.filter(statut='en_cours').count()

    context = {
        'rapports': rapports,
        'chantiers_list': chantiers_list,
        'rapports_count': rapports_count,
        'rapports_pending': rapports_pending,
        'chantiers_actifs': chantiers_actifs,
    }

    return render(request, 'core/rapports.html', context)


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
    nom_remplisseur = request.POST.get('nom_remplisseur') or None
    chef_concerne = request.POST.get('chef_concerne') or None
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

    # If the form provided a custom 'nom_remplisseur' or 'chef_concerne', embed it in the contenu
    extra_lines = []
    if nom_remplisseur:
        extra_lines.append(f"Remplisseur: {nom_remplisseur}")
    if chef_concerne:
        extra_lines.append(f"Chef concerné: {chef_concerne}")
    if extra_lines:
        contenu = "\n".join(extra_lines) + "\n\n" + contenu

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
    if not profile or profile.role not in ('admin', 'directeur'):
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
    if not profile or profile.role not in ('admin', 'directeur'):
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
        logger = logging.getLogger('core.views')
        profile = getattr(request.user, 'userprofile', None)
        logger.debug('ChantierCreateView.get called by user=%s id=%s role=%r', request.user.username, getattr(request.user, 'id', None), profile and profile.role)
        if not profile or profile.role not in ('admin', 'directeur', 'chef'):
            logger.info('ChantierCreateView.get: access denied for user=%s role=%r', request.user.username, profile and profile.role)
            return redirect(reverse('core:dashboard'))
        clients = Client.objects.all().order_by('nom')
        chefs_chantier = User.objects.filter(userprofile__role='chef').order_by('last_name')
        return render(request, 'core/chantier_form.html', {
            'clients': clients,
            'chefs_chantier': chefs_chantier
        })

    def post(self, request):
        logger = logging.getLogger('core.views')
        profile = getattr(request.user, 'userprofile', None)
        logger.debug('ChantierCreateView.post called by user=%s id=%s role=%r POST_keys=%s', request.user.username, getattr(request.user, 'id', None), profile and profile.role, list(request.POST.keys()))
        if not profile or profile.role not in ('admin', 'directeur', 'chef'):
            logger.info('ChantierCreateView.post: access denied for user=%s role=%r', request.user.username, profile and profile.role)
            return redirect(reverse('core:dashboard'))
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
                chef_chantier_id=(request.POST.get('chef_chantier') or None)
            )
            # Si l'utilisateur connecté est un 'chef' et qu'aucun chef_chantier
            # n'a été fourni, assigner automatiquement le chef connecté.
            profile = getattr(request.user, 'userprofile', None)
            if profile and profile.role == 'chef' and not chantier.chef_chantier:
                chantier.chef_chantier = request.user
                chantier.save()
            messages.success(request, f'Chantier "{chantier.nom}" créé avec succès.')
            return redirect(reverse('core:chantiers'))
        except Exception as e:
            messages.error(request, f'Erreur lors de la création du chantier: {str(e)}')
            return redirect(reverse('core:chantier_create'))


@method_decorator(login_required, name='dispatch')
class ChantierUpdateView(View):
    def get(self, request, pk):
        profile = getattr(request.user, 'userprofile', None)
        chantier = get_object_or_404(Chantier, pk=pk)
        # Admins and directeurs can edit any chantier. A 'chef' can edit only their own chantier.
        if not profile:
            return redirect(reverse('core:dashboard'))
        if profile.role in ('admin', 'directeur'):
            pass
        elif profile.role == 'chef':
            if chantier.chef_chantier != request.user:
                return redirect(reverse('core:dashboard'))
        else:
            return redirect(reverse('core:dashboard'))
        clients = Client.objects.all().order_by('nom')
        chefs_chantier = User.objects.filter(userprofile__role='chef').order_by('last_name')
        return render(request, 'core/chantier_form.html', {
            'chantier': chantier,
            'clients': clients,
            'chefs_chantier': chefs_chantier
        })

    def post(self, request, pk):
        profile = getattr(request.user, 'userprofile', None)
        chantier = get_object_or_404(Chantier, pk=pk)
        if not profile:
            return redirect(reverse('core:dashboard'))
        if profile.role in ('admin', 'directeur'):
            pass
        elif profile.role == 'chef':
            if chantier.chef_chantier != request.user:
                return redirect(reverse('core:dashboard'))
        else:
            return redirect(reverse('core:dashboard'))
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
        profile = getattr(request.user, 'userprofile', None)

        allowed = False
        if profile:
            if profile.role in ('admin', 'directeur'):
                allowed = True
            elif profile.role == 'chef' and chantier.chef_chantier and chantier.chef_chantier.pk == request.user.pk:
                allowed = True

        if not allowed:
            return redirect(reverse('core:dashboard'))

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
    def get(self, request, *args, **kwargs):
        # Filtrage côté serveur par rôle si fourni via l'URL
        role = kwargs.get('role')

        qs = Personnel.objects.select_related('user', 'chantier_actuel').all()
        if role:
            qs = qs.filter(role=role)
        personnel = qs.order_by('user__last_name')

        # Comptes par rôle pour l'affichage dans les onglets
        counts = {
            'total': Personnel.objects.count(),
            'chef_chantier': Personnel.objects.filter(role='chef_chantier').count(),
            'maitre_ouvrier': Personnel.objects.filter(role='maitre_ouvrier').count(),
            'ouvrier': Personnel.objects.filter(role='ouvrier').count(),
            'apprenti': Personnel.objects.filter(role='apprenti').count(),
        }

        return render(request, 'core/personnel_list.html', {
            'personnel': personnel,
            'active_role': role or 'tous',
            'counts': counts,
        })


@method_decorator(login_required, name='dispatch')
class PersonnelCreateView(View):
    def get(self, request):
        profile = getattr(request.user, 'userprofile', None)
        if not profile or profile.role not in ('admin', 'directeur'):
            return redirect(reverse('core:dashboard'))
        # Utilisateurs qui n'ont pas encore de profil personnel
        available_users = User.objects.exclude(personnel__isnull=False).order_by('last_name')
        chantiers = Chantier.objects.filter(statut__in=['planifie', 'en_cours']).order_by('nom')
        return render(request, 'core/personnel_form.html', {
            'available_users': available_users,
            'chantiers': chantiers
        })

    def post(self, request):
        profile = getattr(request.user, 'userprofile', None)
        if not profile or profile.role not in ('admin', 'directeur'):
            return redirect(reverse('core:dashboard'))
        try:
            role = request.POST['role']
            # Déterminer rémunération selon le rôle
            taux_journalier = None
            salaire_mensuel = None
            if role == 'chef_chantier':
                salaire_mensuel = request.POST.get('salaire_mensuel') or None
            else:
                taux_journalier = request.POST.get('taux_journalier') or None

            personnel = Personnel.objects.create(
                user_id=request.POST['user'],
                role=role,
                taux_journalier=taux_journalier,
                salaire_mensuel=salaire_mensuel,
                telephone=request.POST.get('telephone', ''),
                adresse=request.POST.get('adresse', ''),
                date_embauche=request.POST['date_embauche'],
                chantier_actuel_id=request.POST.get('chantier_actuel') or None,
                est_actif=request.POST.get('est_actif', 'on') == 'on',
                # Champs spécifiques
                metier=request.POST.get('metier', ''),
                specialite=request.POST.get('specialite', ''),
                zone=request.POST.get('zone', ''),
                prime_responsabilite=request.POST.get('prime_responsabilite') or 0,
                tuteur=request.POST.get('tuteur', ''),
                formation=request.POST.get('formation', '')
            )
            messages.success(request, f'Personnel "{personnel.user.get_full_name()}" ajouté avec succès.')
            return redirect(reverse('core:personnel'))
        except Exception as e:
            messages.error(request, f'Erreur lors de l\'ajout du personnel: {str(e)}')
            return redirect(reverse('core:personnel_create'))


@method_decorator(login_required, name='dispatch')
class PersonnelUpdateView(View):
    def get(self, request, pk):
        profile = getattr(request.user, 'userprofile', None)
        if not profile or profile.role not in ('admin', 'directeur', 'comptable'):
            return redirect(reverse('core:dashboard'))
        personnel = get_object_or_404(Personnel, pk=pk)
        chantiers = Chantier.objects.filter(statut__in=['planifie', 'en_cours']).order_by('nom')
        return render(request, 'core/personnel_form.html', {
            'personnel': personnel,
            'chantiers': chantiers
        })

    def post(self, request, pk):
        profile = getattr(request.user, 'userprofile', None)
        if not profile or profile.role not in ('admin', 'directeur', 'comptable'):
            return redirect(reverse('core:dashboard'))
        personnel = get_object_or_404(Personnel, pk=pk)
        try:
            personnel.role = request.POST['role']
            # Mettre à jour rémunération selon rôle
            if personnel.role == 'chef_chantier':
                personnel.taux_journalier = None
                personnel.salaire_mensuel = request.POST.get('salaire_mensuel') or personnel.salaire_mensuel
            else:
                personnel.salaire_mensuel = None
                personnel.taux_journalier = request.POST.get('taux_journalier') or personnel.taux_journalier
            personnel.telephone = request.POST.get('telephone', '')
            personnel.adresse = request.POST.get('adresse', '')
            personnel.date_embauche = request.POST['date_embauche']
            personnel.chantier_actuel_id = request.POST.get('chantier_actuel') or None
            personnel.est_actif = request.POST.get('est_actif', 'on') == 'on'
            # Champs spécifiques
            personnel.metier = request.POST.get('metier', '')
            personnel.specialite = request.POST.get('specialite', '')
            personnel.zone = request.POST.get('zone', '')
            personnel.prime_responsabilite = request.POST.get('prime_responsabilite') or personnel.prime_responsabilite
            personnel.tuteur = request.POST.get('tuteur', '')
            personnel.formation = request.POST.get('formation', '')
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
        profile = getattr(request.user, 'userprofile', None)
        # Seul l'admin, le directeur applicatif, le chef ou le comptable peuvent créer/modifier les matériaux
        if not profile or profile.role not in ('admin', 'directeur', 'chef', 'comptable'):
            return redirect(reverse('core:dashboard'))
        fournisseurs = Fournisseur.objects.all().order_by('nom')
        return render(request, 'core/materiau_form.html', {'fournisseurs': fournisseurs})

    def post(self, request):
        profile = getattr(request.user, 'userprofile', None)
        if not profile or profile.role not in ('admin', 'directeur', 'chef', 'comptable'):
            return redirect(reverse('core:dashboard'))
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
        profile = getattr(request.user, 'userprofile', None)
        if not profile or profile.role not in ('admin', 'directeur', 'chef', 'comptable'):
            return redirect(reverse('core:dashboard'))
        materiau = get_object_or_404(Materiau, pk=pk)
        fournisseurs = Fournisseur.objects.all().order_by('nom')
        return render(request, 'core/materiau_form.html', {
            'materiau': materiau,
            'fournisseurs': fournisseurs
        })

    def post(self, request, pk):
        profile = getattr(request.user, 'userprofile', None)
        if not profile or profile.role not in ('admin', 'directeur', 'chef', 'comptable'):
            return redirect(reverse('core:dashboard'))
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


@method_decorator(login_required, name='dispatch')
class MateriauDeleteView(View):
    def post(self, request, pk):
        materiau = get_object_or_404(Materiau, pk=pk)
        profile = getattr(request.user, 'userprofile', None)

        # Allow admin, directeur, comptable and chef to delete materials
        if not profile or profile.role not in ('admin', 'directeur', 'comptable', 'chef'):
            messages.error(request, "Vous n'avez pas la permission de supprimer ce matériau.")
            return redirect(reverse('core:materiaux'))

        materiau_name = materiau.nom
        try:
            materiau.delete()
            messages.success(request, f'Matériau "{materiau_name}" supprimé avec succès.')
        except Exception as e:
            messages.error(request, f'Erreur lors de la suppression du matériau: {str(e)}')

        return redirect(reverse('core:materiaux'))


# Vues pour Fournisseur
@method_decorator(login_required, name='dispatch')
class FournisseurListView(View):
    def get(self, request):
        fournisseurs = Fournisseur.objects.all().order_by('nom')
        return render(request, 'core/fournisseur_list.html', {'fournisseurs': fournisseurs})


@method_decorator(login_required, name='dispatch')
class FournisseurCreateView(View):
    def get(self, request):
        profile = getattr(request.user, 'userprofile', None)
        if not profile or profile.role not in ('admin', 'directeur', 'comptable', 'chef'):
            return redirect(reverse('core:dashboard'))
        return render(request, 'core/fournisseur_form.html')

    def post(self, request):
        profile = getattr(request.user, 'userprofile', None)
        if not profile or profile.role not in ('admin', 'directeur', 'comptable', 'chef'):
            return redirect(reverse('core:dashboard'))

        try:
            fournisseur = Fournisseur.objects.create(
                nom=request.POST['nom'],
                contact=request.POST.get('contact', ''),
                telephone=request.POST.get('telephone', ''),
                email=request.POST.get('email', ''),
                adresse=request.POST.get('adresse', ''),
                specialite=request.POST.get('specialite', '')
            )
            # If AJAX request, return JSON for client-side handling
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
                return JsonResponse({
                    'ok': True,
                    'id': fournisseur.id,
                    'nom': fournisseur.nom,
                    'telephone': fournisseur.telephone,
                    'email': fournisseur.email,
                }, status=201)

            messages.success(request, f'Fournisseur "{fournisseur.nom}" ajouté avec succès.')
            return redirect(reverse('core:fournisseurs'))
        except Exception as e:
            # On AJAX, return error JSON
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': str(e)}, status=400)
            messages.error(request, f'Erreur lors de l\'ajout du fournisseur: {str(e)}')
            return redirect(reverse('core:fournisseur_create'))



@login_required
def fournisseur_delete(request, pk):
    """Supprime un fournisseur. Accepte POST (form) ou AJAX POST et renvoie JSON."""
    profile = getattr(request.user, 'userprofile', None)
    if not profile or profile.role not in ('admin', 'directeur', 'comptable'):
        return JsonResponse({'error': 'forbidden'}, status=403) if (request.headers.get('x-requested-with') == 'XMLHttpRequest') else redirect(reverse('core:dashboard'))

    fournisseur = get_object_or_404(Fournisseur, pk=pk)
    try:
        fournisseur.delete()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            return JsonResponse({'ok': True, 'id': pk})
        messages.success(request, f'Fournisseur "{fournisseur.nom}" supprimé.')
        return redirect(reverse('core:fournisseurs'))
    except Exception as e:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            return JsonResponse({'ok': False, 'error': str(e)}, status=400)
        messages.error(request, f'Erreur lors de la suppression: {str(e)}')
        return redirect(reverse('core:fournisseurs'))


class FournisseurUpdateView(View):
    def get(self, request, pk):
        profile = getattr(request.user, 'userprofile', None)
        if not profile or profile.role not in ('admin', 'directeur', 'comptable'):
            return redirect(reverse('core:dashboard'))
        fournisseur = get_object_or_404(Fournisseur, pk=pk)
        return render(request, 'core/fournisseur_form.html', {'fournisseur': fournisseur})

    def post(self, request, pk):
        profile = getattr(request.user, 'userprofile', None)
        if not profile or profile.role not in ('admin', 'comptable'):
            return redirect(reverse('core:dashboard'))

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


def a_propos(request):
    """Page À propos avec informations et ressources."""
    from django.db.models import Q
    chantiers_en_cours = Chantier.objects.filter(statut='en_cours').count()
    total_chantiers_realises = Chantier.objects.filter(statut__in=['termine', 'en_cours', 'planifie']).count()
    total_clients = Client.objects.count()
    annees_experience = 5  # À ajuster selon votre contexte
    
    return render(request, 'core/a_propos.html', {
        'chantiers_en_cours': chantiers_en_cours,
        'total_chantiers_realises': total_chantiers_realises,
        'total_clients': total_clients,
        'annees_experience': annees_experience,
    })
