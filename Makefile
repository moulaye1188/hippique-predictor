.PHONY: help build up down logs shell restart clean init test

help:
	@echo "🐴 Hippique Predictor - Commandes disponibles"
	@echo ""
	@echo "Démarrage:"
	@echo "  make up          - Lancer l'application (docker-compose up -d)"
	@echo "  make build       - Construire l'image Docker"
	@echo ""
	@echo "Gestion:"
	@echo "  make down        - Arrêter l'application"
	@echo "  make restart     - Redémarrer l'application"
	@echo "  make logs        - Voir les logs en temps réel"
	@echo "  make shell       - Accéder au shell du conteneur"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean       - Arrêter et supprimer les conteneurs"
	@echo "  make init        - Initialiser la base de données"
	@echo ""
	@echo "Exemple d'utilisation:"
	@echo "  make build && make up"
	@echo "  Puis ouvrir: http://localhost:5000"

build:
	docker-compose build --no-cache

up:
	@echo "🚀 Lancement de l'application..."
	docker-compose up -d
	@echo "✅ Application lancée"
	@echo "📍 Accédez à: http://localhost:5000"
	@echo "⏳ Attendez 30-40 secondes pour l'entraînement du modèle..."

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f app

shell:
	docker exec -it hippique-predictor bash

clean:
	docker-compose down -v
	rm -rf data/hippique.db models/*.h5
	@echo "✅ Nettoyage complet effectué"

status:
	docker-compose ps

health:
	@echo "🏥 Vérification de la santé de l'application..."
	curl -s http://localhost:5000/api/health | python -m json.tool || echo "❌ L'application ne répond pas"

test-predict:
	@echo "🧪 Test de prédiction..."
	curl -X POST http://localhost:5000/api/predict \
	  -H "Content-Type: application/json" \
	  -d '{"race_date":"2026-06-03","hippodrome":"LAVAL","distance":2850,"horses":[{"number":1,"name":"TEST","description":"Test horse","odds":"5/1"}]}'
