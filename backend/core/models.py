from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Administrateur'),
        ('chef', 'Chef de Chantier'),
        ('ouvrier', 'Ouvrier'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='ouvrier')
    telephone = models.CharField(max_length=20, blank=True)
    date_embauche = models.DateField(null=True, blank=True)
    salaire = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_role_display()}"

    class Meta:
        verbose_name = "Profil utilisateur"
        verbose_name_plural = "Profils utilisateurs"


class Chantier(models.Model):
    STATUT_CHOICES = [
        ('planifie', 'Planifié'),
        ('en_cours', 'En Cours'),
        ('termine', 'Terminé'),
        ('annule', 'Annulé'),
    ]

    nom = models.CharField(max_length=200)
    client = models.ForeignKey('Client', on_delete=models.CASCADE, related_name='chantiers')
    description = models.TextField(blank=True)
    date_debut = models.DateField()
    date_fin_prevue = models.DateField()
    date_fin_reelle = models.DateField(null=True, blank=True)
    budget = models.DecimalField(max_digits=12, decimal_places=2)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='planifie')
    avancement = models.IntegerField(default=0, help_text="Pourcentage d'avancement (0-100)")
    chef_chantier = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='chantiers_diriges')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nom} - {self.client.nom}"

    class Meta:
        verbose_name = "Chantier"
        verbose_name_plural = "Chantiers"


class Personnel(models.Model):
    ROLE_CHOICES = [
        ('chef_chantier', 'Chef de Chantier'),
        ('maitre_ouvrier', 'Maître Ouvrier'),
        ('ouvrier', 'Ouvrier'),
        ('apprenti', 'Apprenti'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='ouvrier')
    taux_horaire = models.DecimalField(max_digits=8, decimal_places=2)
    telephone = models.CharField(max_length=20, blank=True)
    adresse = models.CharField(max_length=300, blank=True)
    date_embauche = models.DateField()
    chantier_actuel = models.ForeignKey(Chantier, on_delete=models.SET_NULL, null=True, blank=True, related_name='personnel_actuel')
    est_actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_role_display()}"

    class Meta:
        verbose_name = "Personnel"
        verbose_name_plural = "Personnel"


class Materiau(models.Model):
    CATEGORIE_CHOICES = [
        ('construction', 'Matériaux de construction'),
        ('electricite', 'Électricité'),
        ('plomberie', 'Plomberie'),
        ('peinture', 'Peinture'),
        ('outillage', 'Outillage'),
        ('autre', 'Autre'),
    ]

    nom = models.CharField(max_length=200)
    categorie = models.CharField(max_length=50, choices=CATEGORIE_CHOICES, default='construction')
    description = models.TextField(blank=True)
    unite = models.CharField(max_length=20, default='unités')
    quantite_stock = models.IntegerField(default=0)
    seuil_minimum = models.IntegerField(default=0)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)
    fournisseur = models.ForeignKey('Fournisseur', on_delete=models.SET_NULL, null=True, blank=True, related_name='materiaux')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nom} ({self.quantite_stock} {self.unite})"

    @property
    def est_en_rupture(self):
        return self.quantite_stock <= self.seuil_minimum

    class Meta:
        verbose_name = "Matériau"
        verbose_name_plural = "Matériaux"


class Fournisseur(models.Model):
    nom = models.CharField(max_length=200)
    contact = models.CharField(max_length=200, blank=True)
    telephone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    adresse = models.CharField(max_length=300, blank=True)
    specialite = models.CharField(max_length=200, blank=True, help_text="Domaine de spécialisation")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nom} ({self.specialite})"

    class Meta:
        verbose_name = "Fournisseur"
        verbose_name_plural = "Fournisseurs"


class Client(models.Model):
    nom = models.CharField(max_length=200)
    contact = models.CharField(max_length=200, blank=True)
    telephone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    adresse = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nom} ({self.contact})"

    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"


class Facture(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='factures')
    chantier = models.ForeignKey(Chantier, on_delete=models.SET_NULL, null=True, blank=True, related_name='factures')
    numero = models.CharField(max_length=50, unique=True, null=True, blank=True)
    date = models.DateField()
    date_echeance = models.DateField(null=True, blank=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tva_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tva_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    statut = models.CharField(max_length=20, choices=[
        ('brouillon', 'Brouillon'),
        ('envoyee', 'Envoyée'),
        ('payee', 'Payée'),
        ('annulee', 'Annulée'),
    ], default='brouillon')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Facture {self.numero} - {self.client.nom} - {self.total} FCFA"

    def save(self, *args, **kwargs):
        if not self.numero:
            # Générer automatiquement un numéro de facture
            year = self.date.year if self.date else 2024
            last_facture = Facture.objects.filter(date__year=year).order_by('-numero').first()
            if last_facture and last_facture.numero.startswith(str(year)):
                try:
                    num = int(last_facture.numero.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.numero = f"{year}-FAC-{str(num).zfill(3)}"
        super().save(*args, **kwargs)


class FactureLine(models.Model):
    facture = models.ForeignKey(Facture, on_delete=models.CASCADE, related_name='lignes')
    materiau = models.ForeignKey(Materiau, on_delete=models.SET_NULL, null=True, blank=True, related_name='lignes_facture')
    description = models.CharField(max_length=300)
    quantite = models.DecimalField(max_digits=8, decimal_places=2, default=1)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)
    montant = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.description} x{self.quantite} -> {self.montant} FCFA"

    def save(self, *args, **kwargs):
        self.montant = self.quantite * self.prix_unitaire
        super().save(*args, **kwargs)


class Rapport(models.Model):
    TYPE_CHOICES = [
        ('journalier', 'Rapport Journalier'),
        ('hebdomadaire', 'Rapport Hebdomadaire'),
        ('mensuel', 'Rapport Mensuel'),
        ('incident', 'Rapport d\'Incident'),
    ]

    titre = models.CharField(max_length=200)
    type_rapport = models.CharField(max_length=20, choices=TYPE_CHOICES, default='journalier')
    contenu = models.TextField()
    date = models.DateField()
    auteur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rapports')
    chantier = models.ForeignKey(Chantier, on_delete=models.SET_NULL, null=True, blank=True, related_name='rapports')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.date} - {self.titre}"

    class Meta:
        verbose_name = "Rapport"
        verbose_name_plural = "Rapports"
