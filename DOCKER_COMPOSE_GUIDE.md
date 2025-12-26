# Docker Compose Setup Guide

## Overview

This project uses Docker Compose to orchestrate multi-service deployments across development, staging, and production environments.

### Services

1. **PostgreSQL 16-Alpine** – Main relational database
2. **Redis 7-Alpine** – Caching & session storage
3. **PgAdmin** – PostgreSQL administration UI (optional)
4. **CAMP Backend App** – FastAPI/Uvicorn application
5. **Nginx** – Reverse proxy (production only)

---

## Quick Start

### Development Environment

```bash
# Clone environment configuration
cp .env.example .env

# Start all services (PostgreSQL, Redis, PgAdmin, App)
docker-compose up -d

# View logs
docker-compose logs -f app

# Access application
# API:      http://localhost:8000
# Swagger:  http://localhost:8000/docs
# PgAdmin:  http://localhost:5050 (admin@example.com / admin)
# Redis:    localhost:6379 (localhost)

# Stop services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v
```

### Staging Environment

```bash
# Start with staging-specific overrides (2 workers, production logging)
docker-compose -f docker-compose.yml -f docker-compose.staging.yml up -d

# View logs
docker-compose -f docker-compose.yml -f docker-compose.staging.yml logs -f app

# Stop services
docker-compose -f docker-compose.yml -f docker-compose.staging.yml down
```

### Production Environment

```bash
# Configure environment file for production
cp .env.example .env.prod
# Edit .env.prod with production settings

# Start with production-specific overrides (multi-worker, SSL, Nginx)
docker-compose -f docker-compose.yml -f docker-compose.prod.yml \
  --env-file .env.prod up -d

# View logs
docker-compose -f docker-compose.yml -f docker-compose.prod.yml \
  --env-file .env.prod logs -f app

# Stop services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml down
```

---

## Common Commands

### View Service Status

```bash
# List all services and their status
docker-compose ps

# Check health of a specific service
docker-compose ps postgres
```

### Execute Commands in Container

```bash
# Run Alembic migrations in the app container
docker-compose exec app alembic upgrade head

# Access PostgreSQL via psql
docker-compose exec postgres psql -U postgres -d camp_backend_db

# Run Python shell
docker-compose exec app python -c "import app; print(app.__version__)"

# Run tests inside container
docker-compose exec app pytest tests/
```

### View Logs

```bash
# Tail all service logs
docker-compose logs -f

# Tail app logs only
docker-compose logs -f app

# View logs from a specific service
docker-compose logs postgres

# View last 100 lines
docker-compose logs --tail=100 app
```

### Rebuild & Restart

```bash
# Rebuild the app image (after code changes)
docker-compose build app

# Rebuild and restart
docker-compose up -d --build app

# Rebuild all services
docker-compose build

# Restart a service without rebuilding
docker-compose restart app
```

### Clean Up

```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune

# Remove unused volumes (WARNING: deletes data)
docker volume prune

# Full cleanup (containers, images, volumes, networks)
docker system prune -a --volumes
```

---

## Environment Variables

### Minimum Required (.env)

```ini
ENVIRONMENT=development
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=camp_backend_db
SECRET_KEY=dev-secret-key-min-32-characters-long
```

### Common Customizations

```ini
# Change app port
APP_PORT=8001

# Change database port
POSTGRES_PORT=5433

# Change Redis port
REDIS_PORT=6380

# Production environment
ENVIRONMENT=production
DEBUG=false

# LLM API keys
ANTHROPIC_API_KEY=sk-ant-...
```

See `.env.example` for all available options.

---

## Troubleshooting

### PostgreSQL Health Check Fails

```bash
# Check PostgreSQL container logs
docker-compose logs postgres

# Verify PostgreSQL is listening
docker-compose exec postgres pg_isready -U postgres

# Restart PostgreSQL
docker-compose restart postgres
```

### App Cannot Connect to Database

```bash
# Verify network connectivity
docker-compose exec app ping postgres

# Check DATABASE_URL in app container
docker-compose exec app env | grep DATABASE_URL

# View app logs
docker-compose logs app
```

### Redis Connection Issues

```bash
# Test Redis connectivity
docker-compose exec app redis-cli -h redis ping

# View Redis logs
docker-compose logs redis

# Restart Redis
docker-compose restart redis
```

### Port Already in Use

```bash
# Find what's using port 5432
lsof -i :5432
# or on Windows:
netstat -ano | findstr :5432

# Change port in .env
POSTGRES_PORT=5433

# Restart services
docker-compose up -d
```

### Rebuild After Dependency Changes

```bash
# Update Python dependencies
docker-compose build --no-cache app

# Restart with new image
docker-compose up -d app
```

---

## Data Persistence

All services use named volumes to persist data:

- **postgres_data** – PostgreSQL databases
- **redis_data** – Redis snapshots
- **pgadmin_data** – PgAdmin configuration
- **uploads** – User file uploads
- **logs** – Application logs

Volumes survive container restarts but are removed with `docker-compose down -v`.

### Backup PostgreSQL Data

```bash
# Create a backup
docker-compose exec postgres pg_dump -U postgres camp_backend_db > backup.sql

# Restore from backup
docker-compose exec -T postgres psql -U postgres camp_backend_db < backup.sql
```

---

## Production Considerations

### SSL/TLS Configuration

Update `nginx.conf` and mount certificates:

```bash
mkdir -p ssl
# Copy your certificates to ssl/
cp /path/to/cert.pem ssl/
cp /path/to/key.pem ssl/
```

### Resource Limits

Production compose file includes:

- **App**: 2 CPU, 1 GB RAM
- **PostgreSQL**: 2 CPU, 2 GB RAM
- **Redis**: 1 CPU, 512 MB RAM
- **Nginx**: 1 CPU, 256 MB RAM

Adjust in `docker-compose.prod.yml` for your infrastructure.

### Monitoring & Logging

- All services log to JSON files with rotation (max 10 MB, 3 files)
- Use container orchestration (Kubernetes, Docker Swarm) for advanced monitoring
- Integrate with Application Insights (Azure) via environment variables

### Multi-Region / Multi-Cloud

For Azure deployments, consider:

- Azure Container Instances (single container)
- Azure Container Apps (multi-container, serverless)
- Azure Kubernetes Service (AKS) for enterprise scale

---

## Documentation Links

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL Docker Image](https://hub.docker.com/_/postgres)
- [Redis Docker Image](https://hub.docker.com/_/redis)
- [PgAdmin Docker Image](https://hub.docker.com/r/dpage/pgadmin4/)
- [Nginx Docker Image](https://hub.docker.com/_/nginx)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/docker/)

---

## Support

For issues or questions:

1. Check service logs: `docker-compose logs <service>`
2. Verify environment configuration: `docker-compose config`
3. Rebuild images: `docker-compose build --no-cache`
4. Consult project documentation in `docs/`
