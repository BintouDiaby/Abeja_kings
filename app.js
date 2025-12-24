// Vérifier si l'utilisateur est connecté
function checkAuthentication() {
    const currentUser = JSON.parse(localStorage.getItem('currentUser'));
    
    if (!currentUser) {
        window.location.href = '/login/';
        return false;
    }
    
    return true;
}

// Rapports management
class ReportsManager {
    static loadRapportsPage(container) {
        const rapports = DataManager.getRapports();

        container.innerHTML = `
            <div class="content-section">
                <div class="section-header">
                    <h3>Rapports Journaliers</h3>
                    <div class="section-actions">
                        <button class="btn btn-outline" onclick="window.app.showPage('rapports')">
                            <i class="fas fa-sync"></i> Rafraîchir
                        </button>
                        <button class="btn btn-primary" onclick="openModal('modal-new-rapport')">
                            <i class="fas fa-plus"></i> Nouveau Rapport
                        </button>
                    </div>
                </div>
                <div class="report-list">
                    ${rapports.map(r => `
                        <div class="report-item">
                            <div class="report-header">
                                <h4>${r.titre}</h4>
                                <small>${formatDate(r.date)} — ${DataManager.getChantierById(r.chantierId)?.nom || r.chantierId}</small>
                            </div>
                            <div class="report-meta">Par ${r.auteur}</div>
                            <p class="report-summary">${r.resume}</p>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
}


// Fonction de déconnexion
function logout() {
    if (confirm('Êtes-vous sûr de vouloir vous déconnecter ?')) {
        localStorage.removeItem('currentUser');
        window.location.href = '/login/';
    }
}

// Utility functions
function formatDate(dateString) {
    const options = { day: '2-digit', month: '2-digit', year: 'numeric' };
    return new Date(dateString).toLocaleDateString('fr-FR', options);
}

function formatCurrency(amount) {
    // Afficher les montants en FCFA sans décimales
    try {
        const n = Number(amount) || 0;
        const formatted = new Intl.NumberFormat('fr-FR', {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(n);
        return `${formatted} FCFA`;
    } catch (e) {
        return amount + ' FCFA';
    }
}

// Récupérer cookie (utilitaire CSRF)
function getCookie(name) {
    const matches = document.cookie.match(new RegExp('(?:^|; )' + name.replace(/([.$?*|{}()\[\]\\\/\+^])/g, '\\$1') + '=([^;]*)'));
    return matches ? decodeURIComponent(matches[1]) : undefined;
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

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
        // If opening the facture modal, initialize its selects dynamically
        try {
            if (modalId === 'modal-new-facture' && window.app && typeof window.app.initializeFactureModal === 'function') {
                window.app.initializeFactureModal();
            }
            if (modalId === 'modal-new-rapport' && window.app && typeof window.app.initializeRapportModal === 'function') {
                window.app.initializeRapportModal();
            }
        } catch (e) {
            console.warn('initializeFactureModal failed', e);
        }
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            <span>${message}</span>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => notification.classList.add('show'), 100);
    
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

// Sample data for the application
class DataManager {
    static getChantiers() {
        return JSON.parse(localStorage.getItem('chantiers')) || [
            {
                id: 'CH001',
                nom: 'Rénovation Appartement Cocody',
                client: 'Kouassi Traoré',
                dateDebut: '2024-03-15',
                dateFinPrevue: '2024-04-30',
                budget: 85000,
                statut: 'active',
                avancement: 75
            },
            {
                id: 'CH002',
                nom: 'Construction Maison Marcory',
                client: 'Aïssata Koné',
                dateDebut: '2024-02-01',
                dateFinPrevue: '2024-05-15',
                budget: 120000,
                statut: 'active',
                avancement: 45
            },
            {
                id: 'CH003',
                nom: 'Aménagement Bureau Plateau',
                client: 'Abidjan Constructions SARL',
                dateDebut: '2024-04-01',
                dateFinPrevue: '2024-06-30',
                budget: 75000,
                statut: 'pending',
                avancement: 30
            }
        ];
    }

    static getPersonnel() {
        return JSON.parse(localStorage.getItem('personnel')) || [
            {
                id: 'EMP001',
                nom: 'Yao Kouassi',
                role: 'Chef de Chantier',
                contact: 'yao.kouassi@abeja.ci',
                tauxHoraire: 45,
                chantierAffecte: 'CH001'
            },
            {
                id: 'EMP002',
                nom: 'Aïcha Coulibaly',
                role: 'Ouvrier Professionnel',
                contact: 'aicha.coulibaly@gmail.com',
                tauxHoraire: 35,
                chantierAffecte: 'CH001'
            },
            {
                id: 'EMP003',
                nom: 'Kouame N\'Dri',
                role: 'Électricien',
                contact: 'kouame.ndri@ouvrier.ci',
                tauxHoraire: 40,
                chantierAffecte: 'CH002'
            }
        ];
    }

    static getMateriaux() {
        return JSON.parse(localStorage.getItem('materiaux')) || [
            {
                id: 'MAT001',
                nom: 'Ciment',
                quantiteStock: 150,
                unite: 'Sac',
                prixUnitaire: 8.50,
                seuilAlerte: 20
            },
            {
                id: 'MAT002',
                nom: 'Briques',
                quantiteStock: 5,
                unite: 'Palette',
                prixUnitaire: 120,
                seuilAlerte: 10
            },
            {
                id: 'MAT003',
                nom: 'Sable',
                quantiteStock: 80,
                unite: 'm³',
                prixUnitaire: 45,
                seuilAlerte: 15
            }
        ];
    }

    static getClients() {
        return JSON.parse(localStorage.getItem('clients')) || [
            {
                id: 'CL001',
                nom: 'Kouassi Traoré',
                email: 'kouassi.traore@traoreci.ci',
                telephone: '+225 21 23 45 67'
            },
            {
                id: 'CL002',
                nom: 'Aïssata Koné',
                email: 'aissata.kone@koneci.ci',
                telephone: '+225 27 89 01 23'
            },
            {
                id: 'CL003',
                nom: 'Abidjan Constructions SARL',
                email: 'contact@abidjanconstructions.ci',
                telephone: '+225 21 23 45 68'
            },
            {
                id: 'CL004',
                nom: 'Société Ivoire BTP',
                email: 'contact@societebtp.ci',
                telephone: '+225 21 45 67 89'
            },
            {
                id: 'CL005',
                nom: 'Kone & Frères SARL',
                email: 'info@konefreres.ci',
                telephone: '+225 27 12 34 56'
            },
            {
                id: 'CL006',
                nom: 'Sika CI',
                email: 'sales@sikaci.ci',
                telephone: '+225 21 98 76 54'
            }
        ];
    }

    static getRapports() {
        return JSON.parse(localStorage.getItem('rapports')) || [
            {
                id: 'RPT001',
                titre: 'Rapport d’avancement - Cocody',
                date: '2024-04-02',
                chantierId: 'CH001',
                auteur: 'Yao Kouassi',
                resume: 'Travaux de plomberie terminés, peinture en cours. Aucun incident signalé.'
            },
            {
                id: 'RPT002',
                titre: 'Rapport sécurité - Marcory',
                date: '2024-04-05',
                chantierId: 'CH002',
                auteur: 'Aïcha Coulibaly',
                resume: 'Formation sécurité effectuée pour 12 ouvriers; équipements conformes.'
            },
            {
                id: 'RPT003',
                titre: 'Rapport matériel - Plateau',
                date: '2024-04-10',
                chantierId: 'CH003',
                auteur: 'Kouame N\'Dri',
                resume: 'Approvisionnement sable prévu demain; livraison de briques en retard.'
            }
        ];
    }

    static addRapport(rapport) {
        const rapports = this.getRapports();
        rapport.id = 'RPT' + String(rapports.length + 1).padStart(3, '0');
        rapports.unshift(rapport); // ajouter au début
        localStorage.setItem('rapports', JSON.stringify(rapports));
        return rapport;
    }

    static getFournisseurs() {
        return JSON.parse(localStorage.getItem('fournisseurs')) || [
            {
                id: 'FOU001',
                nom: 'Fournitures BTP Abidjan',
                contact: '+225 27 33 44 55',
                email: 'contact@fournituresbtp.ci',
                adresse: 'Zone 4, Abidjan'
            },
            {
                id: 'FOU002',
                nom: 'Matériaux Ivoire SARL',
                contact: '+225 21 44 33 22',
                email: 'vente@materiauxivoire.ci',
                adresse: 'Marcory, Abidjan'
            },
            {
                id: 'FOU003',
                nom: 'TechniBat CI',
                contact: '+225 27 55 66 77',
                email: 'contact@technibat.ci',
                adresse: 'Cocody, Abidjan'
            }
        ];
    }

    static getFactures() {
        return JSON.parse(localStorage.getItem('factures')) || [
            {
                id: 'FAC001',
                numero: '2024-FAC-001',
                date: '2024-03-20',
                clientId: 'CL001',
                chantierId: 'CH001',
                montant: 25000,
                statut: 'pending'
            },
            {
                id: 'FAC002',
                numero: '2024-FAC-002',
                date: '2024-04-02',
                clientId: 'CL002',
                chantierId: 'CH002',
                montant: 48000,
                statut: 'active'
            },
            {
                id: 'FAC003',
                numero: '2024-FAC-003',
                date: '2024-04-10',
                clientId: 'CL003',
                chantierId: 'CH003',
                montant: 15000,
                statut: 'completed'
            }
        ];
    }

    static getDashboardStats() {
        const chantiers = this.getChantiers();
        const personnel = this.getPersonnel();
        const materiaux = this.getMateriaux();
        
        return {
            chantiersActifs: chantiers.filter(c => c.statut === 'active').length,
            totalPersonnel: personnel.length,
            totalMateriaux: materiaux.reduce((sum, mat) => sum + mat.quantiteStock, 0),
            chiffreAffaires: chantiers.reduce((sum, c) => sum + c.budget, 0)
        };
    }

    static getChantierById(id) {
        return this.getChantiers().find(c => c.id === id);
    }

    static addChantier(chantier) {
        const chantiers = this.getChantiers();
        chantier.id = 'CH' + String(chantiers.length + 1).padStart(3, '0');
        chantiers.push(chantier);
        localStorage.setItem('chantiers', JSON.stringify(chantiers));
        return chantier;
    }

    static deleteChantier(id) {
        const chantiers = this.getChantiers().filter(c => c.id !== id);
        localStorage.setItem('chantiers', JSON.stringify(chantiers));
    }

    static addPersonnel(employe) {
        const personnel = this.getPersonnel();
        employe.id = 'EMP' + String(personnel.length + 1).padStart(3, '0');
        personnel.push(employe);
        localStorage.setItem('personnel', JSON.stringify(personnel));
        return employe;
    }

    static addMateriau(materiau) {
        const materiaux = this.getMateriaux();
        materiau.id = 'MAT' + String(materiaux.length + 1).padStart(3, '0');
        materiaux.push(materiau);
        localStorage.setItem('materiaux', JSON.stringify(materiaux));
        return materiau;
    }

    static addClient(client) {
        const clients = this.getClients();
        client.id = 'CL' + String(clients.length + 1).padStart(3, '0');
        clients.push(client);
        localStorage.setItem('clients', JSON.stringify(clients));
        return client;
    }

    static addFacture(facture) {
        const factures = this.getFactures();
        facture.id = 'FAC' + String(factures.length + 1).padStart(3, '0');
        // Générer un numéro si absent
        if (!facture.numero) {
            const year = new Date().getFullYear();
            facture.numero = `${year}-FAC-${String(factures.length + 1).padStart(3, '0')}`;
        }
        factures.push(facture);
        localStorage.setItem('factures', JSON.stringify(factures));
        return facture;
    }
}

// Chantiers management
class ChantiersManager {
    static loadChantiersPage(container) {
        const chantiers = DataManager.getChantiers();
        
        container.innerHTML = `
            <div class="content-section">
                <div class="section-header">
                    <h3>Tous les Chantiers</h3>
                    <div class="section-actions">
                        <button class="btn btn-outline">
                            <i class="fas fa-filter"></i> Filtrer
                        </button>
                        <button class="btn btn-primary" onclick="openModal('modal-new-chantier')">
                            <i class="fas fa-plus"></i> Nouveau Chantier
                        </button>
                    </div>
                </div>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Nom</th>
                                <th>Client</th>
                                <th>Date Début</th>
                                <th>Budget</th>
                                <th>Avancement</th>
                                <th>Statut</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${chantiers.map(chantier => `
                                <tr>
                                    <td>
                                        <div class="chantier-info">
                                            <strong>${chantier.nom}</strong>
                                            <small>${chantier.id}</small>
                                        </div>
                                    </td>
                                    <td>${chantier.client}</td>
                                    <td>${formatDate(chantier.dateDebut)}</td>
                                    <td>${formatCurrency(chantier.budget)}</td>
                                    <td>
                                        <div class="progress-container">
                                            <div class="progress-bar">
                                                <div class="progress-fill" style="width: ${chantier.avancement}%"></div>
                                            </div>
                                            <div class="progress-text">${chantier.avancement}%</div>
                                        </div>
                                    </td>
                                    <td><span class="status-badge status-${chantier.statut}">${getStatusText(chantier.statut)}</span></td>
                                    <td>
                                        <div class="action-buttons">
                                            <button class="btn btn-outline btn-sm" onclick="ChantiersManager.editChantier('${chantier.id}')">
                                                <i class="fas fa-edit"></i>
                                            </button>
                                            <button class="btn btn-outline btn-sm" onclick="ChantiersManager.deleteChantier('${chantier.id}')">
                                                <i class="fas fa-trash"></i>
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }

    static editChantier(id) {
        const chantier = DataManager.getChantierById(id);
        if (chantier) {
            showNotification(`Modification du chantier: ${chantier.nom}`, 'info');
        }
    }

    static deleteChantier(id) {
        const chantier = DataManager.getChantierById(id);
        if (chantier && confirm(`Êtes-vous sûr de vouloir supprimer le chantier "${chantier.nom}" ?`)) {
            DataManager.deleteChantier(id);
            showNotification('Chantier supprimé avec succès', 'success');
            window.app.showPage('chantiers');
        }
    }
}

// Personnel management
class PersonnelManager {
    static loadPersonnelPage(container) {
        const personnel = DataManager.getPersonnel();
        
        container.innerHTML = `
            <div class="content-section">
                <div class="section-header">
                    <h3>Gestion du Personnel</h3>
                    <div class="section-actions">
                        <button class="btn btn-outline">
                            <i class="fas fa-filter"></i> Filtrer
                        </button>
                        <button class="btn btn-primary">
                            <i class="fas fa-plus"></i> Nouvel Employé
                        </button>
                    </div>
                </div>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Employé</th>
                                <th>Rôle</th>
                                <th>Contact</th>
                                <th>Taux Horaire</th>
                                <th>Chantier Affecté</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${personnel.map(emp => `
                                <tr>
                                    <td>
                                        <div class="employee-info">
                                            <strong>${emp.nom}</strong>
                                            <small>${emp.id}</small>
                                        </div>
                                    </td>
                                    <td>${emp.role}</td>
                                    <td>${emp.contact}</td>
                                    <td>${formatCurrency(emp.tauxHoraire)}/h</td>
                                    <td>${emp.chantierAffecte || 'Non affecté'}</td>
                                    <td>
                                        <div class="action-buttons">
                                            <button class="btn btn-outline btn-sm">
                                                <i class="fas fa-edit"></i>
                                            </button>
                                            <button class="btn btn-outline btn-sm">
                                                <i class="fas fa-trash"></i>
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }
}

// Materiaux management
class MateriauxManager {
    static loadMateriauxPage(container) {
        const materiaux = DataManager.getMateriaux();
        
        container.innerHTML = `
            <div class="content-section">
                <div class="section-header">
                    <h3>Stock des Matériaux</h3>
                    <div class="section-actions">
                        <button class="btn btn-outline">
                            <i class="fas fa-filter"></i> Filtrer
                        </button>
                        <button class="btn btn-primary">
                            <i class="fas fa-plus"></i> Nouveau Matériau
                        </button>
                    </div>
                </div>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Matériau</th>
                                <th>Quantité</th>
                                <th>Unité</th>
                                <th>Prix Unitaire</th>
                                <th>Seuil d'Alerte</th>
                                <th>Statut</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${materiaux.map(mat => `
                                <tr>
                                    <td>
                                        <div class="materiau-info">
                                            <strong>${mat.nom}</strong>
                                            <small>${mat.id}</small>
                                        </div>
                                    </td>
                                    <td>${mat.quantiteStock}</td>
                                    <td>${mat.unite}</td>
                                    <td>${formatCurrency(mat.prixUnitaire)}</td>
                                    <td>${mat.seuilAlerte}</td>
                                    <td>
                                        <span class="status-badge ${mat.quantiteStock <= mat.seuilAlerte ? 'status-pending' : 'status-active'}">
                                            ${mat.quantiteStock <= mat.seuilAlerte ? 'Stock Bas' : 'Disponible'}
                                        </span>
                                    </td>
                                    <td>
                                        <div class="action-buttons">
                                            <button class="btn btn-outline btn-sm">
                                                <i class="fas fa-edit"></i>
                                            </button>
                                            <button class="btn btn-outline btn-sm">
                                                <i class="fas fa-trash"></i>
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }
}

// Fournisseurs management
class FournisseursManager {
    static loadFournisseursPage(container) {
        const fournisseurs = DataManager.getFournisseurs();

        container.innerHTML = `
            <div class="content-section">
                <div class="section-header">
                    <h3>Gestion des Fournisseurs</h3>
                    <div class="section-actions">
                        <button class="btn btn-primary" onclick="showNotification('Fonction ajouter fournisseur temporaire', 'info')">
                            <i class="fas fa-plus"></i> Nouveau Fournisseur
                        </button>
                    </div>
                </div>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Fournisseur</th>
                                <th>Contact</th>
                                <th>Email</th>
                                <th>Adresse</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${fournisseurs.map(f => `
                                <tr>
                                    <td>
                                        <div class="fournisseur-info">
                                            <strong>${f.nom}</strong>
                                            <small>${f.id}</small>
                                        </div>
                                    </td>
                                    <td>${f.contact}</td>
                                    <td>${f.email}</td>
                                    <td>${f.adresse}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }
}

// Factures management
class FacturesManager {
    static loadFacturesPage(container) {
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
                                <th>Chantier</th>
                                <th>Montant</th>
                                <th>Statut</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${factures.map(f => `
                                <tr>
                                    <td>${f.numero}</td>
                                    <td>${formatDate(f.date)}</td>
                                    <td>${DataManager.getClients().find(c => c.id === f.clientId)?.nom || f.clientId}</td>
                                    <td>${DataManager.getChantierById(f.chantierId)?.nom || f.chantierId}</td>
                                    <td>${formatCurrency(f.montant)}</td>
                                    <td><span class="status-badge status-${f.statut}">${getStatusText(f.statut)}</span></td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }
}

// Clients management
class ClientsManager {
    static loadClientsPage(container) {
        const clients = DataManager.getClients();

        container.innerHTML = `
            <div class="content-section">
                <div class="section-header">
                    <h3>Gestion des Clients</h3>
                    <div class="section-actions">
                        <button class="btn btn-primary" onclick="openModal('modal-new-client')">
                            <i class="fas fa-plus"></i> Nouveau Client
                        </button>
                    </div>
                </div>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Client</th>
                                <th>Email</th>
                                <th>Téléphone</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${clients.map(c => `
                                <tr>
                                    <td>
                                        <div class="client-info">
                                            <strong>${c.nom}</strong>
                                            <small>${c.id}</small>
                                        </div>
                                    </td>
                                    <td>${c.email || '-'}</td>
                                    <td>${c.telephone || '-'}</td>
                                    <td>
                                        <div class="action-buttons">
                                            <button class="btn btn-outline btn-sm" onclick="showNotification('Edition client non implémentée', 'info')">
                                                <i class="fas fa-edit"></i>
                                            </button>
                                            <button class="btn btn-outline btn-sm" onclick="ClientsManager.deleteClient('${c.id}')">
                                                <i class="fas fa-trash"></i>
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }

    static deleteClient(id) {
        if (!confirm('Supprimer ce client ?')) return;
        const clients = DataManager.getClients().filter(c => c.id !== id);
        localStorage.setItem('clients', JSON.stringify(clients));
        showNotification('Client supprimé', 'success');
        window.app.showPage('clients');
    }
}

// Fonctions globales pour clients
function saveNewClient() {
    const nom = document.getElementById('client-nom').value.trim();
    const email = document.getElementById('client-email').value.trim();
    const telephone = document.getElementById('client-telephone').value.trim();
    const adresse = document.getElementById('client-adresse').value.trim();

    if (!nom) {
        showNotification('Le nom du client est requis', 'error');
        return;
    }

    const newClient = {
        nom: nom,
        email: email,
        telephone: telephone,
        adresse: adresse
    };

    DataManager.addClient(newClient);
    closeModal('modal-new-client');
    showNotification('Nouveau client ajouté', 'success');
    window.app.showPage('clients');
}

function saveNewFacture() {
    const clientId = document.getElementById('facture-client').value;
    const chantierId = document.getElementById('facture-chantier').value;
    const date = document.getElementById('facture-date').value;
    const statut = document.getElementById('facture-statut').value;
    const tvaPct = parseFloat(document.getElementById('facture-tva').value) || 0;

    if (!clientId || !chantierId || !date) {
        showNotification('Veuillez remplir tous les champs obligatoires (client, chantier, date).', 'error');
        return;
    }

    // Collecter les lignes
    const lignes = collectFactureLines();
    if (!lignes.length) {
        showNotification('Ajoutez au moins une ligne à la facture.', 'error');
        return;
    }

    const subtotal = lignes.reduce((s, l) => s + l.total, 0);
    const tvaMontant = +(subtotal * (tvaPct / 100));
    const totalTTC = +(subtotal + tvaMontant);

    const newFacture = {
        numero: '',
        date: date,
        clientId: clientId,
        chantierId: chantierId,
        lignes: lignes,
        subtotal: subtotal,
        tvaPct: tvaPct,
        tvaMontant: tvaMontant,
        montant: totalTTC,
        statut: statut || 'pending'
    };

    // Préparer l'envoi au backend Django via POST (FormData)
    const clientName = (DataManager.getClients().find(c => c.id === clientId) || {}).nom || clientId;
    const formData = new FormData();
    formData.append('client_nom', clientName);
    formData.append('date', date);
    formData.append('subtotal', subtotal);
    formData.append('tva_pct', tvaPct);
    formData.append('tva_amount', tvaMontant);
    formData.append('total', totalTTC);
    formData.append('statut', statut || 'pending');
    formData.append('lines_json', JSON.stringify(lignes));

    // Determine CSRF token: prefer token returned by /set-csrf/ (window._csrftoken)
    const csrftoken = window._csrftoken || getCookie('csrftoken');

    const backend = window.BACKEND_ORIGIN || 'http://127.0.0.1:8000';
    fetch(`${backend}/factures/new/`, {
        method: 'POST',
        credentials: 'include',
        headers: csrftoken ? { 'X-CSRFToken': csrftoken, 'X-Requested-With': 'XMLHttpRequest' } : { 'X-Requested-With': 'XMLHttpRequest' },
        body: formData
    }).then(r => r.json()).then(resp => {
        if (resp && resp.success) {
            closeModal('modal-new-facture');
            showNotification('Facture enregistrée côté serveur', 'success');
            // rediriger vers la liste Django
            window.location.href = resp.redirect || '/factures/';
        } else {
            // fallback local
            DataManager.addFacture(newFacture);
            closeModal('modal-new-facture');
            showNotification('Facture enregistrée en local (fallback)', 'info');
            window.app.showPage('devis-factures');
        }
    }).catch(err => {
        console.error('Erreur en sauvegardant la facture:', err);
        // fallback local
        DataManager.addFacture(newFacture);
        closeModal('modal-new-facture');
        showNotification('Facture enregistrée en local (offline)', 'info');
        window.app.showPage('devis-factures');
    });
}

function saveNewRapport() {
    const chantierId = document.getElementById('rapport-chantier').value;
    const date = document.getElementById('rapport-date').value;
    const auteur = document.getElementById('rapport-auteur').value.trim();
    const titre = document.getElementById('rapport-titre').value.trim();
    const resume = document.getElementById('rapport-resume').value.trim();

    if (!chantierId || !date || !auteur || !titre) {
        showNotification('Veuillez remplir les champs obligatoires (chantier, date, auteur, titre).', 'error');
        return;
    }

    const newRapport = {
        titre: titre,
        date: date,
        chantierId: chantierId,
        auteur: auteur,
        resume: resume
    };

    DataManager.addRapport(newRapport);
    closeModal('modal-new-rapport');
    showNotification('Rapport enregistré', 'success');
    window.app.showPage('rapports');
}

function collectFactureLines() {
    const rows = Array.from(document.querySelectorAll('#facture-lines-body tr'));
    const lignes = rows.map(row => {
        const desc = row.querySelector('.line-desc')?.value.trim() || '';
        const qty = parseFloat(row.querySelector('.line-qty')?.value) || 0;
        const pu = parseFloat(row.querySelector('.line-pu')?.value) || 0;
        return { description: desc, quantite: qty, pu: pu, total: +(qty * pu) };
    }).filter(l => l.description || l.quantite);
    return lignes;
}

function addFactureLineRow(desc = '', qty = 1, pu = 0) {
    const tbody = document.getElementById('facture-lines-body');
    if (!tbody) return;

    const tr = document.createElement('tr');
    tr.innerHTML = `
        <td><input class="line-desc" type="text" value="${escapeHtml(desc)}" placeholder="Description"></td>
        <td><input class="line-qty" type="number" min="0" step="0.01" value="${qty}"></td>
        <td><input class="line-pu" type="number" min="0" step="0.01" value="${pu}"></td>
        <td class="line-total">${formatCurrency(qty * pu)}</td>
        <td><button type="button" class="btn btn-outline btn-sm" onclick="removeFactureLineRow(this)"><i class="fas fa-trash"></i></button></td>
    `;

    tbody.appendChild(tr);

    // attacher événements
    tr.querySelectorAll('.line-qty, .line-pu, .line-desc').forEach(inp => {
        inp.addEventListener('input', updateFactureTotals);
    });

    updateFactureTotals();
}

function removeFactureLineRow(button) {
    const tr = button.closest('tr');
    if (tr) tr.remove();
    updateFactureTotals();
}

function updateFactureTotals() {
    const lignes = collectFactureLines();
    const subtotal = lignes.reduce((s, l) => s + l.total, 0);
    const tvaPct = parseFloat(document.getElementById('facture-tva')?.value) || 0;
    const tvaMontant = +(subtotal * (tvaPct / 100));
    const totalTTC = +(subtotal + tvaMontant);

    const subtotalEl = document.getElementById('facture-subtotal');
    const tvaEl = document.getElementById('facture-tva-montant');
    const totalEl = document.getElementById('facture-total-ttc');

    if (subtotalEl) subtotalEl.textContent = formatCurrency(subtotal);
    if (tvaEl) tvaEl.textContent = formatCurrency(tvaMontant);
    if (totalEl) totalEl.textContent = formatCurrency(totalTTC);

    // mettre à jour les montants par ligne dans la table
    const rows = Array.from(document.querySelectorAll('#facture-lines-body tr'));
    rows.forEach(row => {
        const qty = parseFloat(row.querySelector('.line-qty')?.value) || 0;
        const pu = parseFloat(row.querySelector('.line-pu')?.value) || 0;
        const montant = qty * pu;
        const montantTd = row.querySelector('.line-total');
        if (montantTd) montantTd.textContent = formatCurrency(montant);
    });
}

function escapeHtml(text) {
    return String(text).replace(/[&<>"']/g, function (s) {
        return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":"&#39;"})[s];
    });
}



// Main application logic
class AbejaKingsApp {
    constructor() {
        this.currentPage = 'dashboard';
        
        // Vérifier l'authentification avant d'initialiser
        if (checkAuthentication()) {
            this.init();
        }
    }

    init() {
        // Bind UI events first
        this.bindEvents();

        // Mettre à jour l'interface utilisateur (nom/role)
        this.updateUserInterface();

        // Appliquer les permissions en fonction du rôle
        this.applyRolePermissions();

        // Déterminer la page d'atterrissage selon le rôle
        const currentUser = JSON.parse(localStorage.getItem('currentUser')) || {};
        const roleLanding = {
            'directeur': 'dashboard',
            'chef': 'chantiers',
            'ouvrier': 'rapports'
        };
        const landing = roleLanding[currentUser.role] || 'dashboard';

        // Charger les données du dashboard (utile si landing === 'dashboard')
        this.loadDashboardData();

        // Afficher la page d'atterrissage
        this.showPage(landing);

        this.initializeModals();
        this.initializeMobileMenu();
    }

    /**
     * Applique les permissions de navigation et affiche/masque
     * les éléments de l'interface selon le rôle courant.
     */
    applyRolePermissions() {
        const currentUser = JSON.parse(localStorage.getItem('currentUser')) || {};
        const role = currentUser.role;

        const allowedPagesByRole = {
            'directeur': ['dashboard','chantiers','personnel','materiaux','devis-factures','rapports','fournisseurs','clients'],
            'chef': ['dashboard','chantiers','materiaux','rapports','clients'],
            'ouvrier': ['rapports','chantiers']
        };

        const allowed = allowedPagesByRole[role] || ['dashboard'];

        // Masquer les items de la sidebar non autorisés
        document.querySelectorAll('.nav-item').forEach(item => {
            const page = item.getAttribute('data-page');
            if (!allowed.includes(page)) {
                item.style.display = 'none';
            } else {
                item.style.display = '';
            }
        });

        // Stocker pour vérification rapide
        this._allowedPages = allowed;

        // Masquer la carte "Chiffre d'Affaires" pour les chefs de chantier
        try {
            const caEl = document.getElementById('ca-montant');
            if (caEl) {
                const caCard = caEl.closest('.stat-card');
                if (caCard) {
                    if (role === 'chef') {
                        caCard.style.display = 'none';
                    } else {
                        caCard.style.display = '';
                    }
                }
            }
        } catch (e) {
            // si erreur, ne pas bloquer l'application
            console.warn('Erreur en appliquant visibilité CA:', e);
        }
    }

    /**
     * Affiche un message d'accès refusé dans la zone other-content
     */
    showAccessDenied(page) {
        const content = document.getElementById('other-content');
        if (!content) return;
        content.innerHTML = `\n            <div class="content-section">\n                <div class="section-header">\n                    <h3>Accès refusé</h3>\n                </div>\n                <div style="padding: 40px; text-align: center;">\n                    <i class="fas fa-lock" style="font-size:48px;color:#cbd5e1;margin-bottom:12px"></i>\n                    <h4>Vous n'avez pas la permission d'accéder à la page <strong>${page}</strong>.</h4>\n                    <p>Si vous pensez que c'est une erreur, contactez l'administrateur.</p>\n                </div>\n            </div>\n        `;
    }
    
    updateUserInterface() {
        const currentUser = JSON.parse(localStorage.getItem('currentUser'));
        if (currentUser) {
            const userNames = document.querySelectorAll('.user-name');
            const userRoles = document.querySelectorAll('.user-role');
            
            userNames.forEach(element => {
                element.textContent = currentUser.nom;
            });
            
            userRoles.forEach(element => {
                element.textContent = this.getRoleText(currentUser.role);
            });
        }
    }
    
    getRoleText(role) {
        const roles = {
            'directeur': 'Direction',
            'chef': 'Chef de Chantier',
            'ouvrier': 'Ouvrier'
        };
        return roles[role] || role;
    }

    bindEvents() {
        // Navigation events
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const page = e.currentTarget.getAttribute('data-page');
                this.showPage(page);
                this.closeMobileMenu();
            });
        });
    }

    initializeMobileMenu() {
        const menuToggle = document.getElementById('menuToggle');
        const sidebar = document.querySelector('.sidebar');
        
        if (menuToggle && sidebar) {
            menuToggle.addEventListener('click', () => {
                sidebar.classList.toggle('active');
            });
        }

        // Close menu when clicking outside on mobile
        document.addEventListener('click', (e) => {
            if (window.innerWidth <= 768 && sidebar && sidebar.classList.contains('active')) {
                if (!sidebar.contains(e.target) && !e.target.closest('.menu-toggle')) {
                    sidebar.classList.remove('active');
                }
            }
        });
    }

    closeMobileMenu() {
        const sidebar = document.querySelector('.sidebar');
        if (window.innerWidth <= 768 && sidebar) {
            sidebar.classList.remove('active');
        }
    }

    initializeModals() {
        this.initializeChantierModal();
        // prepare facture modal population (called on open as well)
        if (typeof this.initializeFactureModal === 'function') {
            this.initializeFactureModal();
        }
    }

    initializeFactureModal() {
        const clients = DataManager.getClients();
        const chantiers = DataManager.getChantiers();

        const clientSelect = document.getElementById('facture-client');
        const chantierSelect = document.getElementById('facture-chantier');
        const dateInput = document.getElementById('facture-date');

        if (clientSelect) {
            clientSelect.innerHTML = '<option value="">Sélectionner un client</option>' +
                clients.map(c => `<option value="${c.id}">${c.nom} (${c.id})</option>`).join('');
        }

        if (chantierSelect) {
            chantierSelect.innerHTML = '<option value="">Sélectionner un chantier</option>' +
                chantiers.map(ch => `<option value="${ch.id}">${ch.nom} (${ch.id})</option>`).join('');
        }

        if (dateInput) {
            const today = new Date().toISOString().split('T')[0];
            dateInput.value = today;
        }
    }

    initializeRapportModal() {
        const clients = DataManager.getClients();
        const chantiers = DataManager.getChantiers();

        const chantierSelect = document.getElementById('rapport-chantier');
        const dateInput = document.getElementById('rapport-date');
        const auteurInput = document.getElementById('rapport-auteur');

        if (chantierSelect) {
            chantierSelect.innerHTML = '<option value="">Sélectionner un chantier</option>' +
                chantiers.map(ch => `<option value="${ch.id}">${ch.nom} (${ch.id})</option>`).join('');
        }

        if (dateInput) {
            const today = new Date().toISOString().split('T')[0];
            dateInput.value = today;
        }

        if (auteurInput) {
            const currentUser = JSON.parse(localStorage.getItem('currentUser')) || {};
            auteurInput.value = currentUser.nom || '';
        }
    }

    initializeChantierModal() {
        const clients = DataManager.getClients();
        const clientSelect = document.getElementById('chantier-client');
        if (clientSelect) {
            clientSelect.innerHTML = '<option value="">Sélectionner un client</option>' +
                clients.map(client => 
                    `<option value="${client.nom}">${client.nom}</option>`
                ).join('');
        }
    }

    showPage(page) {
        this.currentPage = page;

        // Vérifier les permissions avant d'afficher la page
        const allowed = this._allowedPages || [];
        if (allowed.length && !allowed.includes(page)) {
            // Afficher message d'accès refusé et quitter
            this.showAccessDenied(page);
            showNotification("Accès refusé : vous n'avez pas la permission.", 'error');
            return;
        }

        // Update active nav item
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        const navEl = document.querySelector(`[data-page="${page}"]`);
        if (navEl) navEl.classList.add('active');
        
        // Update page title
        const titles = {
            'dashboard': 'Tableau de Bord',
            'chantiers': 'Gestion des Chantiers',
            'personnel': 'Gestion du Personnel',
            'materiaux': 'Gestion des Matériaux',
            'devis-factures': 'Devis & Factures',
            'rapports': 'Rapports Journaliers',
            'fournisseurs': 'Gestion des Fournisseurs',
            'clients': 'Gestion des Clients'
        };
        
        document.getElementById('page-title').textContent = titles[page] || 'Abeja Kings';
        
        // Show/hide content
        if (page === 'dashboard') {
            document.getElementById('dashboard-content').style.display = 'block';
            document.getElementById('other-content').style.display = 'none';
            this.loadDashboardData();
        } else {
            document.getElementById('dashboard-content').style.display = 'none';
            document.getElementById('other-content').style.display = 'block';
            this.loadPageContent(page);
        }
    }

    loadDashboardData() {
        const stats = DataManager.getDashboardStats();
        
        // Update statistics cards
        document.getElementById('chantiers-count').textContent = stats.chantiersActifs;
        document.getElementById('personnel-count').textContent = stats.totalPersonnel;
        document.getElementById('materiaux-count').textContent = stats.totalMateriaux;
        document.getElementById('ca-montant').textContent = `${formatCurrency(stats.chiffreAffaires)}`;
        
        // Load recent chantiers
        this.loadRecentChantiers();
        
        // Load critical materials
        this.loadCriticalMaterials();
    }

    loadRecentChantiers() {
        const chantiers = DataManager.getChantiers().slice(0, 3);
        const tbody = document.querySelector('#recent-chantiers-table tbody');
        
        if (tbody) {
            tbody.innerHTML = chantiers.map(chantier => `
                <tr>
                    <td>${chantier.nom}</td>
                    <td>${chantier.client}</td>
                    <td>${formatDate(chantier.dateFinPrevue)}</td>
                    <td>
                        <div class="progress-container">
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${chantier.avancement}%"></div>
                            </div>
                            <div class="progress-text">${chantier.avancement}%</div>
                        </div>
                    </td>
                    <td><span class="status-badge status-${chantier.statut}">${getStatusText(chantier.statut)}</span></td>
                </tr>
            `).join('');
        }
    }

    loadCriticalMaterials() {
        const materiaux = DataManager.getMateriaux().filter(mat => mat.quantiteStock <= mat.seuilAlerte);
        const container = document.querySelector('.materiaux-list');
        
        if (container) {
            container.innerHTML = materiaux.map(mat => `
                <div class="materiau-item">
                    <div class="materiau-info">
                        <h4>${mat.nom}</h4>
                        <span>Stock: ${mat.quantiteStock} ${mat.unite}</span>
                    </div>
                    <div class="materiau-alert">
                        Seuil: ${mat.seuilAlerte}
                    </div>
                </div>
            `).join('');
            
            if (materiaux.length === 0) {
                container.innerHTML = '<p style="padding: 20px; text-align: center; color: var(--gray);">Aucun matériau critique</p>';
            }
        }
    }

    loadPageContent(page) {
        const content = document.getElementById('other-content');
        
        switch(page) {
            case 'chantiers':
                ChantiersManager.loadChantiersPage(content);
                this.initializeChantierModal();
                break;
            case 'personnel':
                PersonnelManager.loadPersonnelPage(content);
                break;
            case 'materiaux':
                MateriauxManager.loadMateriauxPage(content);
                break;
            case 'fournisseurs':
                FournisseursManager.loadFournisseursPage(content);
                break;
            case 'devis-factures':
                FacturesManager.loadFacturesPage(content);
                break;
            case 'clients':
                ClientsManager.loadClientsPage(content);
                break;
            case 'rapports':
                ReportsManager.loadRapportsPage(content);
                break;
            default:
                content.innerHTML = `
                    <div class="content-section">
                        <div class="section-header">
                            <h3>${page.charAt(0).toUpperCase() + page.slice(1).replace('-', ' ')}</h3>
                        </div>
                        <div style="padding: 40px; text-align: center;">
                            <i class="fas fa-tools" style="font-size: 48px; color: var(--gray-light); margin-bottom: 16px;"></i>
                            <h3 style="color: var(--gray); margin-bottom: 8px;">Page en développement</h3>
                            <p style="color: var(--gray);">Cette fonctionnalité sera disponible prochainement.</p>
                        </div>
                    </div>
                `;
        }
    }
}

// Global functions for modal actions
function saveNewChantier() {
    const nom = document.getElementById('chantier-nom').value;
    const client = document.getElementById('chantier-client').value;
    const budget = parseFloat(document.getElementById('chantier-budget').value);
    const duree = parseInt(document.getElementById('chantier-duree').value) || 60;
    const description = document.getElementById('chantier-description').value;

    if (!nom || !client || !budget) {
        showNotification('Veuillez remplir tous les champs obligatoires', 'error');
        return;
    }

    const newChantier = {
        nom: nom,
        client: client,
        budget: budget,
        dateDebut: new Date().toISOString().split('T')[0],
        dateFinPrevue: new Date(Date.now() + duree * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        statut: 'pending',
        avancement: 0,
        description: description
    };
    
    DataManager.addChantier(newChantier);
    closeModal('modal-new-chantier');
    showNotification('Nouveau chantier créé avec succès', 'success');
    window.app.showPage('chantiers');
}

// Initialize app when DOM is loaded
// Ensure CSRF cookie is set by calling backend endpoint (useful when serving SPA from Django static)
function requestCsrf() {
    // Try same-origin first (when front served by Django). If that fails
    // (e.g. front served with Live Server on another port), fall back to
    // calling the backend explicitly and include credentials so cookies
    // / CSRF headers can be set/used.
    try {
        // Try same-origin and read token from JSON if returned
        fetch('/set-csrf/', { credentials: 'same-origin' })
            .then(r => r.json().catch(() => ({})))
            .then(data => {
                if (data && data.csrftoken) {
                    window._csrftoken = data.csrftoken;
                }
            })
            .catch(() => {
                // fallback to known backend origin used in dev
                const backend = window.BACKEND_ORIGIN || 'http://127.0.0.1:8000';
                fetch(`${backend}/set-csrf/`, { credentials: 'include' })
                    .then(r => r.json().catch(() => ({})))
                    .then(data => {
                        if (data && data.csrftoken) {
                            window._csrftoken = data.csrftoken;
                        }
                    })
                    .catch(() => {});
            });
    } catch (e) {
        console.warn('CSRF request failed', e);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // Request CSRF cookie first (no-op if not served from same origin)
    requestCsrf();
    window.app = new AbejaKingsApp();
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
window.saveNewChantier = saveNewChantier;