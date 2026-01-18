from django import forms
from .models import Client, Facture, FactureLine, Chantier, Personnel, Materiau, Fournisseur


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['nom', 'contact', 'telephone', 'email', 'adresse']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'nice-input', 'placeholder': 'Nom'}),
            'contact': forms.TextInput(attrs={'class': 'nice-input', 'placeholder': 'Contact'}),
            'telephone': forms.TextInput(attrs={'class': 'nice-input', 'placeholder': 'Téléphone'}),
            'email': forms.EmailInput(attrs={'class': 'nice-input', 'placeholder': 'Email'}),
            'adresse': forms.Textarea(attrs={'class': 'nice-input', 'placeholder': 'Adresse', 'rows': 3}),
        }


class FactureForm(forms.ModelForm):
    class Meta:
        model = Facture
        fields = ['client', 'date', 'subtotal', 'tva_pct', 'tva_amount', 'total']


class FactureLineForm(forms.ModelForm):
    class Meta:
        model = FactureLine
        fields = ['description', 'quantite', 'prix_unitaire', 'montant']


class PaymentForm(forms.Form):
    montant = forms.DecimalField(max_digits=12, decimal_places=2)
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    mode = forms.ChoiceField(choices=[('espece','Espèces'),('virement','Virement'),('cheque','Chèque'),('carte','Carte'),('autre','Autre')])
    reference = forms.CharField(max_length=200, required=False)


class PersonnelPaymentForm(forms.Form):
    montant = forms.DecimalField(max_digits=12, decimal_places=2)
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    mode = forms.ChoiceField(choices=[('espece','Espèces'),('virement','Virement'),('cheque','Chèque'),('carte','Carte'),('autre','Autre')])
    reference = forms.CharField(max_length=200, required=False)
    periode = forms.CharField(max_length=32, required=False, help_text='Période (ex: 2026-01)')
    note = forms.CharField(widget=forms.Textarea(attrs={'rows':2}), required=False)


class ChantierForm(forms.ModelForm):
    class Meta:
        model = Chantier
        fields = ['nom', 'client', 'description', 'date_debut', 'date_fin_prevue', 'budget', 'statut', 'avancement', 'chef_chantier']
        widgets = {
            'date_debut': forms.DateInput(attrs={'type': 'date'}),
            'date_fin_prevue': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class PersonnelForm(forms.ModelForm):
    class Meta:
        model = Personnel
        fields = ['user', 'role', 'taux_journalier', 'salaire_mensuel', 'telephone', 'adresse', 'date_embauche', 'chantier_actuel', 'est_actif']
        widgets = {
            'date_embauche': forms.DateInput(attrs={'type': 'date'}),
            'adresse': forms.Textarea(attrs={'rows': 2}),
        }


class MateriauForm(forms.ModelForm):
    class Meta:
        model = Materiau
        fields = ['nom', 'categorie', 'description', 'unite', 'quantite_stock', 'seuil_minimum', 'prix_unitaire', 'fournisseur']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }


class FournisseurForm(forms.ModelForm):
    class Meta:
        model = Fournisseur
        fields = ['nom', 'contact', 'telephone', 'email', 'adresse', 'specialite']
        widgets = {
            'adresse': forms.Textarea(attrs={'rows': 2}),
        }
