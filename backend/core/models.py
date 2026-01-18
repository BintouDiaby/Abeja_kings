from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Administrateur'),
        ('comptable', 'Comptable'),
        ('directeur', 'Directeur'),
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
    # Chef historique (User) conservé pour compatibilité
    chef_chantier = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='chantiers_diriges')
    # Nouveau lien vers le chef en tant qu'Employee (logique BTP)
    chef_chantier_employee = models.ForeignKey('Employee', on_delete=models.SET_NULL, null=True, blank=True, related_name='chantiers_diriges_employee')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nom} - {self.client.nom}"

    class Meta:
        verbose_name = "Chantier"
        verbose_name_plural = "Chantiers"


# ==========================
# Modèle métier BTP: Employee
# ==========================

class Employee(models.Model):
    ROLE_CHOICES = [
        ('OUVRIER', 'Ouvrier'),
        ('APPRENTI', 'Apprenti'),
        ('CHEF_CHANTIER', 'Chef de Chantier'),
        ('ADMIN', 'Administrateur'),
    ]
    STATUT_CHOICES = [
        ('ACTIF', 'Actif'),
        ('INACTIF', 'Inactif'),
        ('SUSPENDU', 'Suspendu'),
    ]
    REMUN_TYPE_CHOICES = [
        ('JOURNALIER', 'Journalier'),
        ('MENSUEL', 'Mensuel'),
        ('FORFAIT', 'Forfait'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='employee')
    nom = models.CharField(max_length=150)
    prenom = models.CharField(max_length=150)
    telephone = models.CharField(max_length=30, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='ACTIF')
    date_embauche = models.DateField()
    type_remuneration = models.CharField(max_length=20, choices=REMUN_TYPE_CHOICES)
    montant_remuneration = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.get_role_display()})"

    class Meta:
        verbose_name = 'Employé'
        verbose_name_plural = 'Employés'


class OuvrierDetails(models.Model):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='ouvrier_details')
    metier = models.CharField(max_length=100, blank=True)
    chef_responsable = models.ForeignKey('Employee', on_delete=models.SET_NULL, null=True, blank=True, related_name='ouvriers_responsables')

    def __str__(self):
        return f"Détails ouvrier - {self.employee}"


class ChefChantierDetails(models.Model):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='chef_details')
    zone = models.CharField(max_length=100, blank=True)
    prime_responsabilite = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"Détails chef - {self.employee}"


class Affectation(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='affectations')
    chantier = models.ForeignKey(Chantier, on_delete=models.CASCADE, related_name='affectations')
    date_debut = models.DateField()
    date_fin = models.DateField(null=True, blank=True)
    actif = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['employee'], condition=Q(actif=True), name='unique_active_affectation_per_employee')
        ]
        verbose_name = 'Affectation'
        verbose_name_plural = 'Affectations'

    def clean(self):
        # Règle: un ouvrier/app seul sur 1 chantier actif max
        if self.employee and self.actif and self.employee.role in ['OUVRIER', 'APPRENTI']:
            qs = Affectation.objects.filter(employee=self.employee, actif=True)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise models.ValidationError('Cet ouvrier a déjà une affectation active.')


class Presence(models.Model):
    STATUT_CHOICES = [
        ('PRESENT', 'Présent'),
        ('ABSENT', 'Absent'),
        ('RETARD', 'Retard'),
    ]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='presences')
    chantier = models.ForeignKey(Chantier, on_delete=models.CASCADE, related_name='presences')
    date = models.DateField()
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES)
    valide_par = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='presences_validees')

    def clean(self):
        if self.valide_par and self.valide_par.role != 'CHEF_CHANTIER':
            raise models.ValidationError('La présence doit être validée par un chef de chantier.')

    class Meta:
        verbose_name = 'Présence'
        verbose_name_plural = 'Présences'


class RapportChantier(models.Model):
    chantier = models.ForeignKey(Chantier, on_delete=models.CASCADE, related_name='rapports_chantier')
    chef_chantier = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='rapports_chantier')
    date = models.DateField()
    avancement = models.IntegerField(default=0)
    problemes = models.TextField(blank=True)
    commentaires = models.TextField(blank=True)

    def clean(self):
        if self.chef_chantier and self.chef_chantier.role != 'CHEF_CHANTIER':
            raise models.ValidationError('Le rapport doit être rédigé par un chef de chantier.')

    class Meta:
        verbose_name = 'Rapport de chantier'
        verbose_name_plural = 'Rapports de chantier'


class Personnel(models.Model):
    ROLE_CHOICES = [
        ('chef_chantier', 'Chef de Chantier'),
        ('maitre_ouvrier', 'Maître Ouvrier'),
        ('ouvrier', 'Ouvrier'),
        ('apprenti', 'Apprenti'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='ouvrier')
    # Rémunération: taux journalier (ouvrier/maître/apprenti), ou salaire mensuel (chef)
    taux_journalier = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    adresse = models.CharField(max_length=300, blank=True)
    date_embauche = models.DateField()
    chantier_actuel = models.ForeignKey(Chantier, on_delete=models.SET_NULL, null=True, blank=True, related_name='personnel_actuel')
    est_actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    salaire_mensuel = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    # Champs spécifiques selon le rôle
    # Ouvrier / Maître ouvrier
    metier = models.CharField(max_length=100, blank=True)
    specialite = models.CharField(max_length=100, blank=True)
    # Chef de chantier
    zone = models.CharField(max_length=100, blank=True)
    prime_responsabilite = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, default=0)
    # Apprenti
    tuteur = models.CharField(max_length=150, blank=True)
    formation = models.CharField(max_length=150, blank=True)

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

    @property
    def total_payments(self):
        from django.db.models import Sum
        total = self.payments.aggregate(s=Sum('montant'))['s'] if hasattr(self, 'payments') else 0
        return total or 0

    @property
    def reste_a_payer(self):
        try:
            return max(self.total - self.total_payments, 0)
        except Exception:
            return self.total


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


class Payment(models.Model):
    MODE_CHOICES = [
        ('espece', 'Espèces'),
        ('virement', 'Virement'),
        ('cheque', 'Chèque'),
        ('carte', 'Carte'),
        ('autre', 'Autre'),
    ]

    facture = models.ForeignKey(Facture, on_delete=models.CASCADE, related_name='payments')
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default='virement')
    reference = models.CharField(max_length=200, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments_created')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Paiement {self.montant} - {self.facture.numero}"

    class Meta:
        verbose_name = 'Paiement'
        verbose_name_plural = 'Paiements'


class FactureActionLog(models.Model):
    ACTION_CHOICES = [
        ('mark_paid', 'Marqué payé'),
        ('mark_unpaid', 'Marqué impayé'),
        ('cancel', 'Annulée'),
        ('reopen', 'Rouverte'),
        ('partial_payment', 'Paiement partiel'),
    ]

    facture = models.ForeignKey(Facture, on_delete=models.CASCADE, related_name='action_logs')
    action = models.CharField(max_length=40, choices=ACTION_CHOICES)
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Facture {self.facture_id} - {self.action} by {self.user} at {self.created_at}"

    class Meta:
        verbose_name = 'Journal action facture'
        verbose_name_plural = 'Journaux actions facture'

class PersonnelPayment(models.Model):
    MODE_CHOICES = [
        ('espece', 'Espèces'),
        ('virement', 'Virement'),
        ('cheque', 'Chèque'),
        ('carte', 'Carte'),
        ('autre', 'Autre'),
    ]

    personnel = models.ForeignKey(Personnel, on_delete=models.CASCADE, related_name='paiements')
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default='virement')
    reference = models.CharField(max_length=200, blank=True)
    periode = models.CharField(max_length=32, blank=True, help_text='Période payée (ex: 2026-01)')
    note = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='personnel_payments_created')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Paiement {self.montant} - {self.personnel.user.get_full_name()} ({self.date})"

    class Meta:
        verbose_name = 'Paiement Personnel'
        verbose_name_plural = 'Paiements Personnel'


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
