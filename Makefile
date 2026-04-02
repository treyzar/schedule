# Makefile for Schedule Monorepo

.PHONY: build up down logs restart shell-backend shell-frontend clean

# Default: Build and start all services in detached mode
up:
	docker-compose up -d --build

# Start services and show logs
up-logs:
	docker-compose up --build

# Stop and remove all containers
down:
	docker-compose down

# View logs for all containers
logs:
	docker-compose logs -f

# Restart all services
restart:
	docker-compose restart

# Enter the backend container shell
shell-backend:
	docker-compose exec backend bash

# Enter the frontend container shell
shell-frontend:
	docker-compose exec frontend sh

# Remove unused Docker images and volumes
clean:
	docker system prune -f
	docker volume prune -f

# Run Django migrations manually inside the container
migrate:
	docker-compose exec backend python manage.py migrate

# Create a Django superuser
createsuperuser:
	docker-compose exec backend python manage.py createsuperuser

makemigrations:
	docker-compose exec backend python manage.py makemigrations