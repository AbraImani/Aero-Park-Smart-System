/* ========================================
   AeroPark Admin - JavaScript
   ======================================== */

// Configuration Admin par défaut
const DEFAULT_ADMIN = {
    username: 'Abraham',
    password: '123456',
    name: 'Administrateur'
};

// Authentification Admin
const AdminAuth = {
    storageKey: 'aeropark_admin_session',
    adminsKey: 'aeropark_admins',

    // Initialiser les admins
    init() {
        if (!localStorage.getItem(this.adminsKey)) {
            localStorage.setItem(this.adminsKey, JSON.stringify([DEFAULT_ADMIN]));
        }
    },

    // Connexion admin
    login(username, password) {
        this.init();
        const admins = JSON.parse(localStorage.getItem(this.adminsKey));
        const admin = admins.find(a => a.username === username && a.password === password);

        if (admin) {
            const session = {
                username: admin.username,
                name: admin.name,
                loginAt: new Date().toISOString()
            };
            localStorage.setItem(this.storageKey, JSON.stringify(session));
            return { success: true, message: 'Connexion réussie' };
        }

        return { success: false, message: 'Identifiant ou mot de passe incorrect' };
    },

    // Déconnexion
    logout() {
        localStorage.removeItem(this.storageKey);
    },

    // Vérifier si connecté
    isLoggedIn() {
        return localStorage.getItem(this.storageKey) !== null;
    },

    // Obtenir l'admin actuel
    getCurrentAdmin() {
        const session = localStorage.getItem(this.storageKey);
        return session ? JSON.parse(session) : null;
    },

    // Changer le mot de passe
    changePassword(oldPassword, newPassword) {
        const admins = JSON.parse(localStorage.getItem(this.adminsKey));
        const currentAdmin = this.getCurrentAdmin();
        
        if (!currentAdmin) return { success: false, message: 'Non connecté' };

        const adminIndex = admins.findIndex(a => a.username === currentAdmin.username);
        
        if (adminIndex === -1) return { success: false, message: 'Admin non trouvé' };
        
        if (admins[adminIndex].password !== oldPassword) {
            return { success: false, message: 'Ancien mot de passe incorrect' };
        }

        admins[adminIndex].password = newPassword;
        localStorage.setItem(this.adminsKey, JSON.stringify(admins));
        
        return { success: true, message: 'Mot de passe modifié avec succès' };
    }
};

// Gestion des utilisateurs
const UserManager = {
    getAll() {
        return JSON.parse(localStorage.getItem('aeropark_users') || '[]');
    },

    getById(userId) {
        const users = this.getAll();
        return users.find(u => u.id === userId);
    },

    update(userId, updates) {
        const users = this.getAll();
        const index = users.findIndex(u => u.id === userId);
        if (index !== -1) {
            users[index] = { ...users[index], ...updates };
            localStorage.setItem('aeropark_users', JSON.stringify(users));
            return true;
        }
        return false;
    },

    delete(userId) {
        const users = this.getAll();
        const filtered = users.filter(u => u.id !== userId);
        localStorage.setItem('aeropark_users', JSON.stringify(filtered));
        return true;
    },

    block(userId) {
        return this.update(userId, { blocked: true });
    },

    unblock(userId) {
        return this.update(userId, { blocked: false });
    },

    getStats() {
        const users = this.getAll();
        return {
            total: users.length,
            blocked: users.filter(u => u.blocked).length,
            active: users.filter(u => !u.blocked).length
        };
    }
};

// Gestion des paiements
const PaymentManager = {
    getAll() {
        return JSON.parse(localStorage.getItem('aeropark_payments') || '[]');
    },

    getByDateRange(startDate, endDate) {
        const payments = this.getAll();
        return payments.filter(p => {
            const date = new Date(p.paidAt);
            return date >= startDate && date <= endDate;
        });
    },

    getByMethod(method) {
        const payments = this.getAll();
        return payments.filter(p => p.paymentMethod === method);
    },

    getTotalRevenue() {
        const payments = this.getAll();
        return payments.reduce((sum, p) => sum + (p.amount || 0), 0);
    },

    getRevenueByMethod() {
        const payments = this.getAll();
        const byMethod = {};
        
        payments.forEach(p => {
            if (!byMethod[p.paymentMethod]) {
                byMethod[p.paymentMethod] = 0;
            }
            byMethod[p.paymentMethod] += p.amount || 0;
        });
        
        return byMethod;
    },

    getStats() {
        const payments = this.getAll();
        return {
            total: payments.length,
            completed: payments.filter(p => p.status === 'completed').length,
            failed: payments.filter(p => p.status === 'failed').length,
            revenue: this.getTotalRevenue()
        };
    }
};

// Gestion des réservations
const ReservationManager = {
    getAll() {
        return ParkingData.getReservations();
    },

    getActive() {
        return this.getAll().filter(r => r.status === 'active');
    },

    cancel(reservationId) {
        const reservations = this.getAll();
        const index = reservations.findIndex(r => r.id === reservationId);
        
        if (index !== -1) {
            const reservation = reservations[index];
            reservations[index].status = 'cancelled';
            localStorage.setItem('reservations', JSON.stringify(reservations));
            
            // Libérer la place
            ParkingData.updateSpot(reservation.spotId, {
                status: 'available',
                reservedBy: null,
                reservedAt: null
            });
            
            return true;
        }
        return false;
    },

    getStats() {
        const reservations = this.getAll();
        return {
            total: reservations.length,
            active: reservations.filter(r => r.status === 'active').length,
            cancelled: reservations.filter(r => r.status === 'cancelled').length,
            completed: reservations.filter(r => r.status === 'completed').length
        };
    }
};

// Paramètres du parking
const ParkingSettings = {
    storageKey: 'aeropark_settings',

    getDefaults() {
        return {
            parkingName: 'AeroPark GOMA',
            totalSpots: 50,
            ratePerHour: 1000,
            currency: 'FC',
            maxDuration: 168,
            address: 'Aéroport de Goma, RDC',
            phone: '+243 XXX XXX XXX',
            email: 'contact@aeroparkgoma.com'
        };
    },

    get() {
        const settings = localStorage.getItem(this.storageKey);
        return settings ? JSON.parse(settings) : this.getDefaults();
    },

    update(newSettings) {
        const current = this.get();
        const updated = { ...current, ...newSettings };
        localStorage.setItem(this.storageKey, JSON.stringify(updated));
        return updated;
    },

    reset() {
        localStorage.setItem(this.storageKey, JSON.stringify(this.getDefaults()));
        return this.getDefaults();
    }
};

// Utilitaires
const AdminUtils = {
    formatDate(dateString) {
        return new Date(dateString).toLocaleDateString('fr-FR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    formatMoney(amount) {
        return amount.toLocaleString('fr-FR') + ' FC';
    },

    exportToCSV(data, filename) {
        if (data.length === 0) return;

        const headers = Object.keys(data[0]);
        const csvContent = [
            headers.join(','),
            ...data.map(row => headers.map(h => `"${row[h] || ''}"`).join(','))
        ].join('\n');

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = filename;
        link.click();
    },

    showNotification(message, type = 'success') {
        const existing = document.querySelector('.admin-notification');
        if (existing) existing.remove();

        const notification = document.createElement('div');
        notification.className = `admin-notification ${type}`;
        notification.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
            <span>${message}</span>
        `;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 1.5rem;
            background: ${type === 'success' ? 'var(--secondary-color)' : 'var(--danger-color)'};
            color: white;
            border-radius: var(--radius-md);
            box-shadow: var(--shadow-lg);
            display: flex;
            align-items: center;
            gap: 0.75rem;
            z-index: 100000;
            animation: slideIn 0.3s ease;
        `;

        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 3000);
    }
};

// Initialiser AdminAuth
AdminAuth.init();
