from django.contrib import admin
from .models import Client, Facture, FactureLine, Rapport


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
