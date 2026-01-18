from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # root goes to landing view which redirects to the login page
    path('', views.landing, name='home'),
    path('a-propos/', views.a_propos, name='a_propos'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('clients/', views.ClientListView.as_view(), name='clients'),
    path('clients/new/', views.ClientCreateView.as_view(), name='client_new'),
    path('clients/<int:pk>/edit/', views.ClientUpdateView.as_view(), name='client_edit'),
    path('factures/', views.FactureListView.as_view(), name='factures'),
    path('factures/new/', views.FactureCreateView.as_view(), name='facture_new'),
    path('factures/<int:pk>/', views.FactureDetailView.as_view(), name='facture_detail'),
    path('factures/<int:pk>/edit/', views.FactureUpdateView.as_view(), name='facture_edit'),
    path('factures/<int:pk>/delete/', views.facture_delete, name='facture_delete'),
    path('factures/<int:pk>/marquer_payee/', views.facture_mark_paid, name='facture_mark_paid'),
    path('factures/<int:pk>/annuler/', views.facture_mark_annulee, name='facture_mark_annulee'),
    path('factures/<int:pk>/reouvrir/', views.facture_reopen, name='facture_reopen'),
    path('users/', views.UserListView.as_view(), name='users'),
    path('users/new/', views.UserCreateView.as_view(), name='user_new'),
    path('users/<int:pk>/edit/', views.UserUpdateView.as_view(), name='user_edit'),
    path('api/user/', views.get_current_user, name='current_user'),
    path('set-csrf/', views.set_csrf, name='set_csrf'),

    # URLs pour Chantier
    path('chantiers/', views.ChantierListView.as_view(), name='chantiers'),
    path('chantiers/new/', views.ChantierCreateView.as_view(), name='chantier_create'),
    path('chantiers/<int:pk>/edit/', views.ChantierUpdateView.as_view(), name='chantier_update'),
    path('chantiers/<int:pk>/delete/', views.ChantierDeleteView.as_view(), name='chantier_delete'),

    # URLs pour Personnel
    path('personnel/', views.PersonnelListView.as_view(), name='personnel'),
    path('personnel/role/<str:role>/', views.PersonnelListView.as_view(), name='personnel_role'),
    path('personnel/new/', views.PersonnelCreateView.as_view(), name='personnel_create'),
    path('personnel/<int:pk>/edit/', views.PersonnelUpdateView.as_view(), name='personnel_update'),
    path('personnel/<int:personnel_id>/paiements/', views.personnel_payments, name='personnel_payments'),
    path('personnel/paiements/historique/', views.personnel_payments_history, name='personnel_payments_history'),
    path('personnel/<int:personnel_id>/paiements/marquer_payee/', views.personnel_mark_paid, name='personnel_mark_paid'),

    # URLs pour Materiau
    path('materiaux/', views.MateriauListView.as_view(), name='materiaux'),
    path('materiaux/new/', views.MateriauCreateView.as_view(), name='materiau_create'),
    path('materiaux/<int:pk>/edit/', views.MateriauUpdateView.as_view(), name='materiau_update'),

    # URLs pour Fournisseur
    path('fournisseurs/', views.FournisseurListView.as_view(), name='fournisseurs'),
    path('fournisseurs/new/', views.FournisseurCreateView.as_view(), name='fournisseur_create'),
    path('fournisseurs/<int:pk>/edit/', views.FournisseurUpdateView.as_view(), name='fournisseur_update'),
    path('fournisseurs/<int:pk>/delete/', views.fournisseur_delete, name='fournisseur_delete'),

    # API endpoints
    path('api/chantiers/', views.api_chantiers, name='api_chantiers'),
    path('api/personnel/', views.api_personnel, name='api_personnel'),
    path('api/materiaux/', views.api_materiaux, name='api_materiaux'),
    path('api/fournisseurs/', views.api_fournisseurs, name='api_fournisseurs'),
    path('api/clients/', views.api_clients, name='api_clients'),
    path('api/factures/', views.api_factures, name='api_factures'),
    path('api/rapports/', views.api_rapports, name='api_rapports'),
    path('api/dashboard/', views.api_dashboard_stats, name='api_dashboard'),
    # Pages pour rapports
    path('rapports/', views.rapports_view, name='rapports'),
    path('rapports/new/', views.create_rapport, name='rapport_new'),
    path('rapports/<int:rapport_id>/update/', views.update_rapport, name='rapport_update'),
    path('rapports/<int:rapport_id>/delete/', views.delete_rapport, name='rapport_delete'),
    # Post-login dispatcher: redirect users to the right landing depending on role
    path('post-login/', views.post_login, name='post_login'),
]
