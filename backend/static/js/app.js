// Abeja Kings Application Class
class AbejaKingsApp {
    constructor() {
        this.currentPage = 'dashboard';
        this.init();
    }

    async init() {
        this.setupNavigation();
        await this.loadUserData();
        // Appliquer les permissions AVANT d'afficher la page
        const userData = JSON.parse(localStorage.getItem('currentUser'));
        if (userData) {
            this.applyRolePermissions(userData.role);
        }
        await this.showPage('dashboard');
    }

    setupNavigation() {
        const navItems = document.querySelectorAll('.nav-item');
        navItems.forEach(item => {
            item.addEventListener('click', async () => {
                const page = item.getAttribute('data-page');
                await this.showPage(page);
            });
        });
    }

    async showPage(pageName) {
        // Bloquer l'accès aux pages interdites pour le chef de chantier
        const userData = JSON.parse(localStorage.getItem('currentUser'));
        if (userData && userData.role === 'chef') {
            const forbiddenPages = ['personnel', 'devis-factures', 'fournisseurs'];
            if (forbiddenPages.includes(pageName)) {
                // Affiche un message d'accès refusé
                const otherContent = document.getElementById('other-content');
                if (otherContent) {
                    otherContent.style.display = 'block';
                    otherContent.innerHTML = '<div class="content-section"><div class="error-message" style="color:red;font-weight:bold;font-size:1.2em;"><i class="fas fa-ban"></i> Accès interdit pour ce rôle</div></div>';
                }
                // Masque le dashboard si besoin
                const dashboardContent = document.getElementById('dashboard-content');
                if (dashboardContent) dashboardContent.style.display = 'none';
                // Met à jour le titre
                const pageTitle = document.getElementById('page-title');
                if (pageTitle) pageTitle.textContent = 'Accès interdit';
                this.currentPage = pageName;
                return;
            }
        }

        // Update navigation active state
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        const activeNavItem = document.querySelector(`[data-page="${pageName}"]`);
        if (activeNavItem) {
            activeNavItem.classList.add('active');
        }

        // Hide all content sections
        document.querySelectorAll('.page-content').forEach(content => {
            content.style.display = 'none';
        });

        // Appliquer les permissions AVANT d'afficher la page
        if (userData) {
            this.applyRolePermissions(userData.role);
        }

        // Show the selected page content
        if (pageName === 'dashboard') {
            const dashboardContent = document.getElementById('dashboard-content');
            if (dashboardContent) {
                dashboardContent.style.display = 'block';
            }
        } else {
            // For other pages, show the other-content and load content dynamically
            const otherContent = document.getElementById('other-content');
            if (otherContent) {
                otherContent.style.display = 'block';
                await this.showSpecificPage(pageName);
                // Réappliquer le masquage après chargement dynamique
                if (userData) {
                    this.applyRolePermissions(userData.role);
                }
            }
        }

        // Update page title
        const pageTitle = document.getElementById('page-title');
        if (pageTitle) {
            const titles = {
                'dashboard': 'Tableau de Bord',
                'chantiers': 'Gestion Chantiers',
                'personnel': 'Gestion Personnel',
                'materiaux': 'Gestion Matériaux',
                'devis-factures': 'Devis & Factures',
                'rapports': 'Rapports Journaliers',
                'fournisseurs': 'Fournisseurs',
                'clients': 'Clients'
            };
            pageTitle.textContent = titles[pageName] || 'Page';
        }

        this.currentPage = pageName;
    }

    async showSpecificPage(pageName) {
        const otherContent = document.getElementById('other-content');
        if (!otherContent) return;

        // Clear current content
        otherContent.innerHTML = '<div class="loading">Chargement...</div>';

        try {
            // Load content based on page
            switch(pageName) {
                case 'chantiers':
                    await ChantiersManager.loadChantiersPage(otherContent);
                    break;
                case 'personnel':
                    await PersonnelManager.loadPersonnelPage(otherContent);
                    break;
                case 'materiaux':
                    await MateriauxManager.loadMateriauxPage(otherContent);
                    break;
                case 'devis-factures':
                    FacturesManager.loadFacturesPage(otherContent);
                    break;
                case 'rapports':
                    await ReportsManager.loadRapportsPage(otherContent);
                    break;
                case 'fournisseurs':
                    await FournisseursManager.loadFournisseursPage(otherContent);
                    break;
                case 'clients':
                    await ClientsManager.loadClientsPage(otherContent);
                    break;
                default:
                    otherContent.innerHTML = '<div class="content-section"><h3>Page en développement</h3></div>';
            }
        } catch (error) {
            console.error('Erreur lors du chargement de la page:', error);
            otherContent.innerHTML = `
                <div class="content-section">
                    <div class="error-message">
                        <i class="fas fa-exclamation-triangle"></i>
                        Erreur lors du chargement de la page. Veuillez réessayer.
                    </div>
                </div>
            `;
        }
    }

    loadUserData() {
        // Load user data from API
        checkAuthentication().then(isAuthenticated => {
            if (isAuthenticated) {
                this.updateUserInterface();
            }
        });
    }

    updateUserInterface() {
        const userData = JSON.parse(localStorage.getItem('currentUser'));
        if (userData) {
            // Update user info in header and sidebar
            const elements = [
                'headerUserName', 'sidebarUserName',
                'headerUserRole', 'sidebarUserRole'
            ];

            elements.forEach(id => {
                const element = document.getElementById(id);
                if (element) {
                    if (id.includes('Name')) {
                        element.textContent = userData.first_name || userData.username || 'Utilisateur';
                    } else if (id.includes('Role')) {
                        element.textContent = this.getRoleDisplayName(userData.role);
                    }
                }
            });

            // Update initials
            const initialsElements = ['headerUserInitials', 'userInitials'];
            initialsElements.forEach(id => {
                const element = document.getElementById(id);
                if (element) {
                    const name = userData.first_name || userData.username || 'U';
                    element.textContent = name.charAt(0).toUpperCase();
                }
            });

            // Update role badge
            const roleBadge = document.getElementById('currentRole');
            if (roleBadge) {
                roleBadge.textContent = this.getRoleDisplayName(userData.role);
            }

            // Appliquer les permissions selon le rôle
            this.applyRolePermissions(userData.role);
        }
    }

    applyRolePermissions(role) {
        // Restrictions pour les chefs de chantier
        if (role === 'chef') {
            // Supprimer du DOM les éléments non autorisés pour le chef
            // Navigation
            ['devis-factures', 'fournisseurs', 'personnel'].forEach(page => {
                const item = document.querySelector(`.nav-item[data-page="${page}"]`);
                if (item) item.remove();
            });

            // Actions rapides et modales
            document.querySelectorAll('.btn-nouveau-chantier, .modal-hide-chef, .btn-nouvelle-facture, .btn-gerer-fournisseurs, .section-fournisseurs').forEach(el => el.remove());

            // Profil utilisateur sidebar/header
            document.querySelectorAll('.user-profile-section').forEach(el => el.remove());
        }
    }

    getRoleDisplayName(role) {
        const roleNames = {
            'admin': 'Administrateur',
            'chef': 'Chef de Chantier',
            'ouvrier': 'Ouvrier'
        };
        return roleNames[role] || role;
    }

    async loadDashboardData() {
        try {
            const stats = await DataManager.getDashboardStats();

            // Mettre à jour les statistiques principales
            document.getElementById('chantiers-count').textContent = stats.chantiers.actifs;
            document.getElementById('personnel-count').textContent = stats.personnel.total;
            document.getElementById('materiaux-count').textContent = stats.materiaux.total;

            // Calculer le CA (factures du mois)
            const caElement = document.getElementById('ca-montant');
            caElement.textContent = formatCurrency(stats.finances.factures_mois) + ' FCFA';

            // Charger les chantiers récents
            await this.loadRecentChantiers();

        } catch (error) {
            console.error('Erreur lors du chargement des données du dashboard:', error);
            // Afficher des valeurs par défaut en cas d'erreur
            document.getElementById('chantiers-count').textContent = '0';
            document.getElementById('personnel-count').textContent = '0';
            document.getElementById('materiaux-count').textContent = '0';
            document.getElementById('ca-montant').textContent = '0 FCFA';
        }
    }

    async loadRecentChantiers() {
        try {
            const chantiers = await DataManager.getChantiers();
            const recentChantiers = chantiers.slice(0, 5); // Les 5 plus récents

            const tbody = document.querySelector('#recent-chantiers-table tbody');
            tbody.innerHTML = recentChantiers.map(chantier => `
                <tr>
                    <td><strong>${chantier.nom}</strong></td>
                    <td>${chantier.client.nom}</td>
                    <td>${formatDate(chantier.date_fin_prevue)}</td>
                    <td>${chantier.avancement}%</td>
                    <td><span class="status-badge status-${chantier.statut}">${chantier.statut_display}</span></td>
                </tr>
            `).join('');

        } catch (error) {
            console.error('Erreur lors du chargement des chantiers récents:', error);
        }
    }
}

// Utility functions
function formatDate(dateString) {
    const options = { day: '2-digit', month: '2-digit', year: 'numeric' };
    return new Date(dateString).toLocaleDateString('fr-FR', options);
}

function formatCurrency(amount) {
    try {
        const n = Number(amount) || 0;
        const formatted = new Intl.NumberFormat('fr-FR', {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(n);
        return formatted + ' FCFA';
    } catch (e) {
        return amount + ' FCFA';
    }
}

function getStatusText(status) {
    const statusMap = {
        'active': 'En Cours',
        'pending': 'En Attente',
        'completed': 'Terminé',
        'cancelled': 'Annulé'
    };
    return statusMap[status] || status;
}

// DataManager class
class DataManager {
    // Cache pour éviter les appels répétés
    static cache = {};
    static cacheTimeout = 5 * 60 * 1000; // 5 minutes

    static async getChantiers() {
        return await this.fetchFromAPI('/api/chantiers/', 'chantiers');
    }

    static async getPersonnel() {
        return await this.fetchFromAPI('/api/personnel/', 'personnel');
    }

    static async getMateriaux() {
        return await this.fetchFromAPI('/api/materiaux/', 'materiaux');
    }

    static async getClients() {
        return await this.fetchFromAPI('/api/clients/', 'clients');
    }

    static async getFournisseurs() {
        return await this.fetchFromAPI('/api/fournisseurs/', 'fournisseurs');
    }

    static async getFactures() {
        return await this.fetchFromAPI('/api/factures/', 'factures');
    }

    static async getRapports() {
        return await this.fetchFromAPI('/api/rapports/', 'rapports');
    }

    static async getDashboardStats() {
        return await this.fetchFromAPI('/api/dashboard/', null);
    }

    // Méthode générique pour récupérer des données depuis l'API
    static async fetchFromAPI(endpoint, cacheKey) {
        const now = Date.now();
        const cached = this.cache[cacheKey];

        // Vérifier si les données sont en cache et valides
        if (cached && (now - cached.timestamp) < this.cacheTimeout) {
            return cached.data;
        }

        try {
            const response = await fetch(endpoint, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin'
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            // Transformer les données selon le cacheKey
            let transformedData = [];
            switch(cacheKey) {
                case 'chantiers':
                    transformedData = data.chantiers.map(chantier => ({
                        id: chantier.id,
                        nom: chantier.nom,
                        client: chantier.client.nom,
                        dateDebut: chantier.date_debut,
                        dateFinPrevue: chantier.date_fin_prevue,
                        budget: chantier.budget,
                        statut: chantier.statut,
                        avancement: chantier.avancement,
                        chef_chantier: chantier.chef_chantier ? chantier.chef_chantier.nom : null
                    }));
                    break;
                case 'personnel':
                    transformedData = data.personnel.map(personne => ({
                        id: personne.id,
                        nom: personne.user.full_name,
                        role: personne.role_display,
                        contact: personne.user.email,
                        tauxHoraire: personne.taux_horaire,
                        chantierAffecte: personne.chantier_actuel ? personne.chantier_actuel.nom : null,
                        est_actif: personne.est_actif
                    }));
                    break;
                case 'materiaux':
                    transformedData = data.materiaux.map(materiau => ({
                        id: materiau.id,
                        nom: materiau.nom,
                        categorie: materiau.categorie_display,
                        quantiteStock: materiau.quantite_stock,
                        unite: materiau.unite,
                        seuilMinimum: materiau.seuil_minimum,
                        prix_unitaire: materiau.prix_unitaire,
                        fournisseur: materiau.fournisseur ? materiau.fournisseur.nom : null,
                        est_en_rupture: materiau.est_en_rupture
                    }));
                    break;
                case 'clients':
                    transformedData = data.clients.map(client => ({
                        id: client.id,
                        nom: client.nom,
                        email: client.email,
                        telephone: client.telephone
                    }));
                    break;
                case 'fournisseurs':
                    transformedData = data.fournisseurs.map(fournisseur => ({
                        id: fournisseur.id,
                        nom: fournisseur.nom,
                        email: fournisseur.email,
                        telephone: fournisseur.telephone,
                        specialite: fournisseur.specialite
                    }));
                    break;
                case 'rapports':
                    transformedData = (data.rapports || []).map(r => ({
                        id: r.id,
                        titre: r.titre,
                        date: r.date,
                        auteur: r.auteur ? r.auteur.full_name : null,
                        resume: (r.contenu || '').substring(0, 200),
                        chantier: r.chantier ? r.chantier.nom : null,
                        created_at: r.created_at
                    }));
                    break;
                default:
                    transformedData = data;
            }

            // Mettre en cache
            this.cache[cacheKey] = {
                data: transformedData,
                timestamp: now
            };

            return transformedData;

        } catch (error) {
            console.error(`Erreur lors de la récupération des données ${cacheKey}:`, error);
            // En cas d'erreur, retourner les données mockées depuis localStorage
            return this.getMockData(cacheKey);
        }
    }

    // Données mockées en cas d'erreur API
    static getMockData(key) {
        const mockData = {
            chantiers: [
                {
                    id: 'CH001',
                    nom: 'Rénovation Villa Cocody',
                    client: 'Mme Marie Dupont',
                    dateDebut: '2024-01-15',
                    dateFinPrevue: '2024-04-30',
                    budget: 85000,
                    statut: 'active',
                    avancement: 75
                }
            ],
            personnel: [
                {
                    id: 'EMP001',
                    nom: 'Yao Kouassi',
                    role: 'Chef de Chantier',
                    contact: 'yao.kouassi@abeja.ci',
                    tauxHoraire: 45,
                    chantierAffecte: 'CH001'
                }
            ],
            materiaux: [
                {
                    id: 'MAT001',
                    nom: 'Briques',
                    categorie: 'Matériaux de construction',
                    quantiteStock: 1500,
                    unite: 'unités',
                    seuilMinimum: 200
                }
            ],
            clients: [
                {
                    id: 'CL001',
                    nom: 'Mme Marie Dupont',
                    email: 'marie.dupont@email.ci',
                    telephone: '+225 01 02 03 04'
                }
            ],
            fournisseurs: [
                {
                    id: 'FOU001',
                    nom: 'Matériaux Plus SARL',
                    email: 'contact@materiauxplus.ci',
                    telephone: '+225 21 23 45 67',
                    specialite: 'Matériaux de construction'
                }
            ]
        };
        return mockData[key] || [];
    }

    static searchChantiers(query, statut = null) {
        return this.getChantiers().then(chantiers => {
            return chantiers.filter(chantier => {
                const matchesQuery = !query ||
                    chantier.nom.toLowerCase().includes(query.toLowerCase()) ||
                    chantier.client.nom.toLowerCase().includes(query.toLowerCase()) ||
                    chantier.description.toLowerCase().includes(query.toLowerCase());

                const matchesStatut = !statut || chantier.statut === statut;

                return matchesQuery && matchesStatut;
            });
        });
    }

    static searchPersonnel(query, role = null) {
        return this.getPersonnel().then(personnel => {
            return personnel.filter(personne => {
                const matchesQuery = !query ||
                    personne.user.full_name.toLowerCase().includes(query.toLowerCase()) ||
                    personne.user.username.toLowerCase().includes(query.toLowerCase()) ||
                    personne.role_display.toLowerCase().includes(query.toLowerCase());

                const matchesRole = !role || personne.role === role;

                return matchesQuery && matchesRole;
            });
        });
    }

    static searchMateriaux(query, categorie = null) {
        return this.getMateriaux().then(materiaux => {
            return materiaux.filter(materiau => {
                const matchesQuery = !query ||
                    materiau.nom.toLowerCase().includes(query.toLowerCase()) ||
                    materiau.categorie_display.toLowerCase().includes(query.toLowerCase()) ||
                    materiau.description.toLowerCase().includes(query.toLowerCase());

                const matchesCategorie = !categorie || materiau.categorie === categorie;

                return matchesQuery && matchesCategorie;
            });
        });
    }

    static searchFournisseurs(query) {
        return this.getFournisseurs().then(fournisseurs => {
            return fournisseurs.filter(fournisseur => {
                return !query ||
                    fournisseur.nom.toLowerCase().includes(query.toLowerCase()) ||
                    fournisseur.specialite.toLowerCase().includes(query.toLowerCase()) ||
                    fournisseur.contact.toLowerCase().includes(query.toLowerCase());
            });
        });
    }

    static searchFactures(query, statut = null) {
        return this.getFactures().then(factures => {
            return factures.filter(facture => {
                const matchesQuery = !query ||
                    facture.numero.toLowerCase().includes(query.toLowerCase()) ||
                    facture.client.nom.toLowerCase().includes(query.toLowerCase());

                const matchesStatut = !statut || facture.statut === statut;

                return matchesQuery && matchesStatut;
            });
        });
    }

    // Méthodes utilitaires pour l'UX
    static showNotification(message, type = 'info', duration = 3000) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            <span>${message}</span>
            <button class="notification-close" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;

        document.body.appendChild(notification);

        // Animation d'entrée
        setTimeout(() => notification.classList.add('show'), 10);

        // Auto-suppression
        if (duration > 0) {
            setTimeout(() => {
                notification.classList.remove('show');
                setTimeout(() => notification.remove(), 300);
            }, duration);
        }

        return notification;
    }

    static async confirmAction(message, title = 'Confirmation') {
        return new Promise((resolve) => {
            const modal = document.createElement('div');
            modal.className = 'modal-overlay';
            modal.innerHTML = `
                <div class="modal confirm-modal">
                    <div class="modal-header">
                        <h3>${title}</h3>
                    </div>
                    <div class="modal-body">
                        <p>${message}</p>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-outline" onclick="this.closest('.modal-overlay').remove(); resolve(false)">
                            Annuler
                        </button>
                        <button class="btn btn-danger" onclick="this.closest('.modal-overlay').remove(); resolve(true)">
                            Confirmer
                        </button>
                    </div>
                </div>
            `;

            document.body.appendChild(modal);
            setTimeout(() => modal.classList.add('show'), 10);
        });
    }

    static showLoadingSpinner(container, message = 'Chargement...') {
        const spinner = document.createElement('div');
        spinner.className = 'loading-spinner';
        spinner.innerHTML = `
            <div class="spinner"></div>
            <p>${message}</p>
        `;
        container.innerHTML = '';
        container.appendChild(spinner);
        return spinner;
    }

    static hideLoadingSpinner(container) {
        const spinner = container.querySelector('.loading-spinner');
        if (spinner) {
            spinner.remove();
        }
    }
}

// ChantiersManager class
class ChantiersManager {
    static async loadChantiersPage(container) {
        try {
            const chantiers = await DataManager.getChantiers();

            container.innerHTML = `
                <div class="content-section">
                    <div class="section-header">
                        <h3>Tous les Chantiers</h3>
                        <div class="section-actions">
                            <div class="search-filters">
                                <input type="text" id="chantiers-search" placeholder="Rechercher par nom, client..." class="search-input">
                                <select id="chantiers-statut-filter" class="filter-select">
                                    <option value="">Tous les statuts</option>
                                    <option value="planifie">Planifié</option>
                                    <option value="en_cours">En cours</option>
                                    <option value="suspendu">Suspendu</option>
                                    <option value="termine">Terminé</option>
                                    <option value="annule">Annulé</option>
                                </select>
                            </div>
                            <a href="/chantiers/new/" class="btn btn-primary">
                                <i class="fas fa-plus"></i> Nouveau Chantier
                            </a>
                        </div>
                    </div>
                    <div class="table-container">
                        <table id="chantiers-table">
                            <thead>
                                <tr>
                                    <th>Nom</th>
                                    <th>Client</th>
                                    <th>Date Début</th>
                                    <th>Budget</th>
                                    <th>Avancement</th>
                                    <th>Statut</th>
                                </tr>
                            </thead>
                            <tbody id="chantiers-tbody">
                                ${this.renderChantiersTable(chantiers)}
                            </tbody>
                        </table>
                    </div>
                </div>
            `;

            // Ajouter les event listeners pour la recherche
            this.setupChantiersSearch();

        } catch (error) {
            console.error('Erreur lors du chargement des chantiers:', error);
            container.innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-triangle"></i>
                    Erreur lors du chargement des chantiers: ${error.message}
                </div>
            `;
        }
    }

    static renderChantiersTable(chantiers) {
        return chantiers.map(chantier => `
            <tr>
                <td><strong>${chantier.nom}</strong></td>
                <td>${chantier.client.nom}</td>
                <td>${formatDate(chantier.date_debut)}</td>
                <td>${formatCurrency(chantier.budget)}</td>
                <td>${chantier.avancement}%</td>
                <td><span class="status-badge status-${chantier.statut}">${chantier.statut_display}</span></td>
            </tr>
        `).join('');
    }

    static setupChantiersSearch() {
        const searchInput = document.getElementById('chantiers-search');
        const statutFilter = document.getElementById('chantiers-statut-filter');
        const tbody = document.getElementById('chantiers-tbody');

        const performSearch = async () => {
            const query = searchInput.value.trim();
            const statut = statutFilter.value;

            try {
                const filteredChantiers = await DataManager.searchChantiers(query, statut);
                tbody.innerHTML = this.renderChantiersTable(filteredChantiers);
            } catch (error) {
                console.error('Erreur lors de la recherche:', error);
            }
        };

        searchInput.addEventListener('input', performSearch);
        statutFilter.addEventListener('change', performSearch);
    }
}

// PersonnelManager class
class PersonnelManager {
    static async loadPersonnelPage(container) {
        try {
            const personnel = await DataManager.getPersonnel();

            container.innerHTML = `
                <div class="content-section">
                    <div class="section-header">
                        <h3>Gestion du Personnel</h3>
                        <div class="section-actions">
                            <a href="/api/personnel/" class="btn btn-primary" target="_blank">
                                <i class="fas fa-plus"></i> Nouveau Employé
                            </a>
                        </div>
                    </div>
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>Nom</th>
                                    <th>Rôle</th>
                                    <th>Contact</th>
                                    <th>Taux Horaire</th>
                                    <th>Chantier Affecté</th>
                                    <th>Statut</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${personnel.map(emp => `
                                    <tr>
                                        <td><strong>${emp.nom}</strong></td>
                                        <td>${emp.role}</td>
                                        <td>${emp.contact}</td>
                                        <td>${formatCurrency(emp.tauxHoraire)}/h</td>
                                        <td>${emp.chantierAffecte || 'Aucun'}</td>
                                        <td><span class="status-badge ${emp.est_actif ? 'status-active' : 'status-inactive'}">${emp.est_actif ? 'Actif' : 'Inactif'}</span></td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        } catch (error) {
            console.error('Erreur lors du chargement du personnel:', error);
            container.innerHTML = `
                <div class="content-section">
                    <div class="error-message">
                        <i class="fas fa-exclamation-triangle"></i>
                        Erreur lors du chargement du personnel. Veuillez réessayer.
                    </div>
                </div>
            `;
        }
    }
}

// MateriauxManager class
class MateriauxManager {
    static async loadMateriauxPage(container) {
        try {
            const materiaux = await DataManager.getMateriaux();

            container.innerHTML = `
                <div class="content-section">
                    <div class="section-header">
                        <h3>Gestion des Matériaux</h3>
                        <div class="section-actions">
                            <a href="/api/materiaux/" class="btn btn-primary" target="_blank">
                                <i class="fas fa-plus"></i> Nouveau Matériau
                            </a>
                        </div>
                    </div>
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>Nom</th>
                                    <th>Catégorie</th>
                                    <th>Stock</th>
                                    <th>Unité</th>
                                    <th>Seuil Min</th>
                                    <th>Prix Unitaire</th>
                                    <th>Fournisseur</th>
                                    <th>Statut</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${materiaux.map(mat => `
                                    <tr class="${mat.est_en_rupture ? 'rupture-stock' : ''}">
                                        <td><strong>${mat.nom}</strong></td>
                                        <td>${mat.categorie}</td>
                                        <td>${mat.quantiteStock}</td>
                                        <td>${mat.unite}</td>
                                        <td>${mat.seuilMinimum}</td>
                                        <td>${formatCurrency(mat.prix_unitaire)}</td>
                                        <td>${mat.fournisseur || 'Non défini'}</td>
                                        <td>
                                            <span class="status-badge ${mat.est_en_rupture ? 'status-rupture' : 'status-ok'}">
                                                ${mat.est_en_rupture ? 'Rupture' : 'OK'}
                                            </span>
                                        </td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        } catch (error) {
            console.error('Erreur lors du chargement des matériaux:', error);
            container.innerHTML = `
                <div class="content-section">
                    <div class="error-message">
                        <i class="fas fa-exclamation-triangle"></i>
                        Erreur lors du chargement des matériaux. Veuillez réessayer.
                    </div>
                </div>
            `;
        }
    }
}

// ClientsManager class
class ClientsManager {
    static async loadClientsPage(container) {
        try {
            const clients = await DataManager.getClients();

            container.innerHTML = `
                <div class="content-section">
                    <div class="section-header">
                        <h3>Gestion des Clients</h3>
                        <div class="section-actions">
                            <a href="/api/clients/" class="btn btn-primary" target="_blank">
                                <i class="fas fa-plus"></i> Nouveau Client
                            </a>
                        </div>
                    </div>
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>Nom</th>
                                    <th>Email</th>
                                    <th>Téléphone</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${clients.map(client => `
                                    <tr>
                                        <td><strong>${client.nom}</strong></td>
                                        <td>${client.email || '-'}</td>
                                        <td>${client.telephone || '-'}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        } catch (error) {
            console.error('Erreur lors du chargement des clients:', error);
            container.innerHTML = `
                <div class="content-section">
                    <div class="error-message">
                        <i class="fas fa-exclamation-triangle"></i>
                        Erreur lors du chargement des clients. Veuillez réessayer.
                    </div>
                </div>
            `;
        }
    }
}

// FacturesManager class
class FacturesManager {
    static loadFacturesPage(container) {
        const role = (JSON.parse(localStorage.getItem('currentUser')) || {}).role;
        if (role === 'chef') {
            container.innerHTML = `
                <div class="content-section">
                    <div class="section-header">
                        <h3>Devis & Factures</h3>
                    </div>
                    <div class="info-box warning">
                        <i class="fas fa-lock"></i>
                        Accès réservé à l'administrateur.
                    </div>
                </div>`;
            return;
        }

        const factures = DataManager.getFactures();

        container.innerHTML = `
            <div class="content-section">
                <div class="section-header">
                    <h3>Devis & Factures</h3>
                    <div class="section-actions">
                        <button class="btn btn-primary" onclick="openModal('modal-new-facture')">
                            <i class="fas fa-plus"></i> Nouvelle Facture
                        </button>
                    </div>
                </div>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Numéro</th>
                                <th>Date</th>
                                <th>Client</th>
                                <th>Montant</th>
                                <th>Statut</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${factures.map(facture => `
                                <tr>
                                    <td><strong>${facture.numero}</strong></td>
                                    <td>${formatDate(facture.date)}</td>
                                    <td>${DataManager.getClientById(facture.clientId)?.nom || facture.clientId}</td>
                                    <td>${formatCurrency(facture.montant)}</td>
                                    <td><span class="status-badge status-${facture.statut}">${getStatusText(facture.statut)}</span></td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }
}

// FournisseursManager class
class FournisseursManager {
    static async loadFournisseursPage(container) {
        const role = (JSON.parse(localStorage.getItem('currentUser')) || {}).role;
        if (role === 'chef') {
            container.innerHTML = `
                <div class="content-section">
                    <div class="section-header">
                        <h3>Fournisseurs</h3>
                    </div>
                    <div class="info-box warning">
                        <i class="fas fa-lock"></i>
                        Accès réservé à l'administrateur.
                    </div>
                </div>`;
            return;
        }

        try {
            const fournisseurs = await DataManager.getFournisseurs();

            container.innerHTML = `
                <div class="content-section">
                    <div class="section-header">
                        <h3>Fournisseurs</h3>
                        <div class="section-actions">
                            <a href="/api/fournisseurs/" class="btn btn-primary" target="_blank">
                                <i class="fas fa-plus"></i> Nouveau Fournisseur
                            </a>
                        </div>
                    </div>
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>Nom</th>
                                    <th>Email</th>
                                    <th>Téléphone</th>
                                    <th>Spécialité</th>
                            </tr>
                            </thead>
                            <tbody>
                                ${fournisseurs.map(fournisseur => `
                                    <tr>
                                        <td><strong>${fournisseur.nom}</strong></td>
                                        <td>${fournisseur.email || '-'}</td>
                                        <td>${fournisseur.telephone || '-'}</td>
                                        <td>${fournisseur.specialite || '-'}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        } catch (error) {
            console.error('Erreur lors du chargement des fournisseurs:', error);
            container.innerHTML = `
                <div class="content-section">
                    <div class="error-message">
                        <i class="fas fa-exclamation-triangle"></i>
                        Erreur lors du chargement des fournisseurs. Veuillez réessayer.
                    </div>
                </div>
            `;
        }
    }
}

// ReportsManager class
class ReportsManager {
    static async loadRapportsPage(container) {
        const rapports = await DataManager.getRapports();

        container.innerHTML = `
            <div class="content-section">
                <div class="section-header">
                    <h3>Rapports Journaliers</h3>
                    <div class="section-actions">
                        <button class="btn btn-primary" onclick="openModal('modal-new-rapport')">
                            <i class="fas fa-plus"></i> Nouveau Rapport
                        </button>
                    </div>
                </div>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Titre</th>
                                <th>Date</th>
                                <th>Auteur</th>
                                <th>Résumé</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${rapports.map(rapport => `
                                <tr>
                                    <td><strong>${rapport.titre}</strong></td>
                                    <td>${formatDate(rapport.date)}</td>
                                    <td>${rapport.auteur}</td>
                                    <td>${rapport.resume}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }
}

// Vérifier si l'utilisateur est connecté
async function checkAuthentication() {
    try {
        const response = await fetch('/api/user/', {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            },
            credentials: 'same-origin'
        });

        if (response.ok) {
            const userData = await response.json();
            // Stocker les informations utilisateur
            localStorage.setItem('currentUser', JSON.stringify(userData));
            return true;
        } else if (response.status === 401 || response.status === 403) {
            // Utilisateur non connecté
            localStorage.removeItem('currentUser');
            window.location.href = '/accounts/login/';
            return false;
        }
    } catch (error) {
        console.warn('Erreur lors de la vérification d\'authentification:', error);
        localStorage.removeItem('currentUser');
        window.location.href = '/accounts/login/';
        return false;
    }

    return false;
}

// Fonction de déconnexion
function logout() {
    if (confirm('Êtes-vous sûr de vouloir vous déconnecter ?')) {
        localStorage.removeItem('currentUser');
        window.location.href = '/accounts/login/';
    }
}

// Modal functions
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Request CSRF cookie first (no-op if not served from same origin)
    requestCsrf();
    window.app = new AbejaKingsApp();
});

// Ensure action-card / quick-action anchors always navigate (fallback for SPA interception)
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('a.action-card, a.btn.btn-primary').forEach(a => {
        a.addEventListener('click', (e) => {
            // If anchor has a real href (absolute or root-relative), force navigation
            const href = a.getAttribute('href');
            if (href && href.startsWith('/')) {
                // Let browser navigate normally; but also force in case other handlers prevented it
                window.location.href = href;
            }
        });
    });
});

// Close modal when clicking outside
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal')) {
        closeModal(e.target.id);
    }
});

// Close modal with Escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            if (modal.style.display === 'flex') {
                closeModal(modal.id);
            }
        });
    }
});

// Make functions globally available
window.showPage = (page) => window.app.showPage(page);
window.openModal = openModal;
window.closeModal = closeModal;
window.logout = logout;

// CSRF token handling
function requestCsrf() {
    try {
        fetch('/set-csrf/', {
            method: 'GET',
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            if (data && data.csrfToken) {
                window._csrftoken = data.csrfToken;
            }
        })
        .catch(() => {});
    } catch (e) {
        console.warn('CSRF request failed', e);
    }
}