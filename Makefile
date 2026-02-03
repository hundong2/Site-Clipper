.PHONY: help install install-backend install-frontend dev dev-backend dev-frontend build build-frontend clean docker docker-up docker-down

# Default target
help:
	@echo "Site Clipper - Available Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install          Install all dependencies (backend + frontend)"
	@echo "  make install-backend  Install backend Python dependencies"
	@echo "  make install-frontend Install frontend npm dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make dev              Run backend and frontend in dev mode (parallel)"
	@echo "  make dev-backend      Run backend only (uvicorn with reload)"
	@echo "  make dev-frontend     Run frontend only (vite dev server)"
	@echo ""
	@echo "Build:"
	@echo "  make build            Build frontend for production"
	@echo "  make build-frontend   Same as 'make build'"
	@echo ""
	@echo "Docker:"
	@echo "  make docker           Build and run backend with Docker Compose"
	@echo "  make docker-up        Start Docker containers"
	@echo "  make docker-down      Stop Docker containers"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean            Remove build artifacts and caches"
	@echo "  make health           Check if backend is running"

# =============================================================================
# Installation
# =============================================================================

install: install-backend install-frontend
	@echo "✓ All dependencies installed"

install-backend:
	@echo "Installing backend dependencies..."
	cd backend && python -m venv venv || true
	cd backend && . venv/bin/activate && pip install -r requirements.txt
	cd backend && . venv/bin/activate && playwright install chromium
	@echo "✓ Backend dependencies installed"

install-frontend:
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "✓ Frontend dependencies installed"

# =============================================================================
# Development
# =============================================================================

dev:
	@echo "Starting backend and frontend in dev mode..."
	@echo "Backend:  http://localhost:8000"
	@echo "Frontend: http://localhost:5173"
	@echo ""
	@make -j2 dev-backend dev-frontend

dev-backend:
	cd backend && . venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

dev-frontend:
	cd frontend && npm run dev

# =============================================================================
# Build
# =============================================================================

build: build-frontend
	@echo "✓ Build complete"

build-frontend:
	@echo "Building frontend for production..."
	cd frontend && npm run build
	@echo "✓ Frontend built to frontend/dist/"

# =============================================================================
# Docker
# =============================================================================

docker: docker-up

docker-up:
	@echo "Starting backend with Docker Compose..."
	cd backend && docker compose up --build

docker-down:
	cd backend && docker compose down

# =============================================================================
# Utilities
# =============================================================================

clean:
	@echo "Cleaning build artifacts..."
	rm -rf frontend/dist
	rm -rf frontend/node_modules/.vite
	rm -rf backend/__pycache__
	rm -rf backend/app/__pycache__
	rm -rf backend/app/**/__pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✓ Clean complete"

health:
	@curl -s http://localhost:8000/api/v1/health | python3 -m json.tool || echo "Backend is not running"
