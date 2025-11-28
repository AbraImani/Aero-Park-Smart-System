/* ========================================
   AeroPark Smart System - Data Management
   Gestion des données simulées
   ======================================== */

const ParkingData = {
    // Configuration du parking
    config: {
        totalSpots: 50,
        rows: 5,
        spotsPerRow: 10
    },

    // Initialiser les données de parking
    init() {
        if (!localStorage.getItem('parkingSpots')) {
            this.generateParkingSpots();
        }
        if (!localStorage.getItem('reservations')) {
            localStorage.setItem('reservations', JSON.stringify([]));
        }
    },

    // Générer les places de parking avec état aléatoire
    generateParkingSpots() {
        const spots = [];
        const letters = ['A', 'B', 'C', 'D', 'E'];
        
        for (let row = 0; row < this.config.rows; row++) {
            for (let spot = 1; spot <= this.config.spotsPerRow; spot++) {
                const id = `${letters[row]}${spot}`;
                // 60% disponible, 30% occupé, 10% réservé (simulation)
                const rand = Math.random();
                let status = 'available';
                if (rand > 0.6 && rand <= 0.9) {
                    status = 'occupied';
                } else if (rand > 0.9) {
                    status = 'reserved';
                }
                
                spots.push({
                    id: id,
                    row: letters[row],
                    number: spot,
                    status: status,
                    reservedBy: null,
                    reservedAt: null
                });
            }
        }
        
        localStorage.setItem('parkingSpots', JSON.stringify(spots));
        return spots;
    },

    // Obtenir toutes les places
    getAllSpots() {
        const spots = localStorage.getItem('parkingSpots');
        return spots ? JSON.parse(spots) : this.generateParkingSpots();
    },

    // Obtenir une place par ID
    getSpotById(id) {
        const spots = this.getAllSpots();
        return spots.find(spot => spot.id === id);
    },

    // Mettre à jour une place
    updateSpot(id, updates) {
        const spots = this.getAllSpots();
        const index = spots.findIndex(spot => spot.id === id);
        if (index !== -1) {
            spots[index] = { ...spots[index], ...updates };
            localStorage.setItem('parkingSpots', JSON.stringify(spots));
            return spots[index];
        }
        return null;
    },

    // Obtenir les statistiques
    getStats() {
        const spots = this.getAllSpots();
        const total = spots.length;
        const available = spots.filter(s => s.status === 'available').length;
        const occupied = spots.filter(s => s.status === 'occupied').length;
        const reserved = spots.filter(s => s.status === 'reserved').length;
        const rate = Math.round(((occupied + reserved) / total) * 100);
        
        return {
            total,
            available,
            occupied,
            reserved,
            occupationRate: rate
        };
    },

    // Simuler des changements en temps réel
    simulateRealTimeChanges() {
        const spots = this.getAllSpots();
        const availableSpots = spots.filter(s => s.status === 'available');
        const occupiedSpots = spots.filter(s => s.status === 'occupied');
        
        // 10% de chance de changer une place
        if (Math.random() < 0.1 && availableSpots.length > 0) {
            const randomAvailable = availableSpots[Math.floor(Math.random() * availableSpots.length)];
            this.updateSpot(randomAvailable.id, { status: 'occupied' });
        }
        
        if (Math.random() < 0.08 && occupiedSpots.length > 0) {
            const randomOccupied = occupiedSpots[Math.floor(Math.random() * occupiedSpots.length)];
            this.updateSpot(randomOccupied.id, { status: 'available' });
        }
    },

    // Réserver une place
    reserveSpot(spotId, userId) {
        const spot = this.getSpotById(spotId);
        if (spot && spot.status === 'available') {
            this.updateSpot(spotId, {
                status: 'reserved',
                reservedBy: userId,
                reservedAt: new Date().toISOString()
            });
            
            // Ajouter à l'historique des réservations
            this.addReservation({
                spotId: spotId,
                userId: userId,
                createdAt: new Date().toISOString(),
                status: 'active'
            });
            
            return true;
        }
        return false;
    },

    // Annuler une réservation
    cancelReservation(spotId, userId) {
        const spot = this.getSpotById(spotId);
        if (spot && spot.status === 'reserved' && spot.reservedBy === userId) {
            this.updateSpot(spotId, {
                status: 'available',
                reservedBy: null,
                reservedAt: null
            });
            
            // Mettre à jour l'historique
            this.updateReservationStatus(spotId, userId, 'cancelled');
            
            return true;
        }
        return false;
    },

    // Ajouter une réservation à l'historique
    addReservation(reservation) {
        const reservations = this.getReservations();
        reservation.id = Date.now().toString();
        reservations.push(reservation);
        localStorage.setItem('reservations', JSON.stringify(reservations));
        return reservation;
    },

    // Obtenir toutes les réservations
    getReservations() {
        const reservations = localStorage.getItem('reservations');
        return reservations ? JSON.parse(reservations) : [];
    },

    // Obtenir les réservations d'un utilisateur
    getUserReservations(userId) {
        const reservations = this.getReservations();
        return reservations.filter(r => r.userId === userId && r.status === 'active');
    },

    // Mettre à jour le statut d'une réservation
    updateReservationStatus(spotId, userId, status) {
        const reservations = this.getReservations();
        const index = reservations.findIndex(r => r.spotId === spotId && r.userId === userId && r.status === 'active');
        if (index !== -1) {
            reservations[index].status = status;
            localStorage.setItem('reservations', JSON.stringify(reservations));
        }
    },

    // Réinitialiser les données (pour les tests)
    reset() {
        localStorage.removeItem('parkingSpots');
        localStorage.removeItem('reservations');
        this.init();
    }
};

// Initialiser les données au chargement
ParkingData.init();
