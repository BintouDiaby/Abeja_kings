from django.contrib import admin
from .models import (
    Client, Facture, FactureLine, Rapport,
    Employee, OuvrierDetails, ChefChantierDetails,
    Affectation, Presence, Chantier, RapportChantier
)
from .models import Personnel, PersonnelPayment, FactureActionLog


class FactureLineInline(admin.TabularInline):
    model = FactureLine
    extra = 1


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('nom', 'contact', 'telephone', 'email')


@admin.register(Facture)
class FactureAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'date', 'total')
    inlines = [FactureLineInline]


@admin.register(Rapport)
class RapportAdmin(admin.ModelAdmin):
    list_display = ('date', 'titre', 'auteur')


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('id', 'prenom', 'nom', 'role', 'statut', 'date_embauche', 'type_remuneration', 'montant_remuneration')
    list_filter = ('role', 'statut', 'type_remuneration')
    search_fields = ('nom', 'prenom', 'telephone')


@admin.register(OuvrierDetails)
class OuvrierDetailsAdmin(admin.ModelAdmin):
    list_display = ('employee', 'metier', 'chef_responsable')


@admin.register(ChefChantierDetails)
class ChefChantierDetailsAdmin(admin.ModelAdmin):
    list_display = ('employee', 'zone', 'prime_responsabilite')


@admin.register(Affectation)
class AffectationAdmin(admin.ModelAdmin):
    list_display = ('employee', 'chantier', 'date_debut', 'date_fin', 'actif')
    list_filter = ('actif',)


@admin.register(Presence)
class PresenceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'chantier', 'date', 'statut', 'valide_par')
    list_filter = ('statut',)


@admin.register(Chantier)
class ChantierAdmin(admin.ModelAdmin):
    list_display = ('nom', 'statut', 'chef_chantier', 'chef_chantier_employee')


@admin.register(RapportChantier)
class RapportChantierAdmin(admin.ModelAdmin):
    list_display = ('chantier', 'chef_chantier', 'date', 'avancement')


@admin.register(Personnel)
class PersonnelAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'role', 'chantier_actuel', 'est_actif')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    list_filter = ('role', 'est_actif')


@admin.register(PersonnelPayment)
class PersonnelPaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'personnel', 'montant', 'date', 'mode', 'periode', 'created_by', 'created_at')
    search_fields = ('personnel__user__username', 'personnel__user__first_name', 'personnel__user__last_name', 'reference')
    list_filter = ('mode',)
    date_hierarchy = 'date'


@admin.register(FactureActionLog)
class FactureActionLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'facture', 'action', 'user', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('facture__numero', 'user__username')
