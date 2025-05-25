# Docker Deployment Guide

## Overview

This guide explains how to deploy the Ocean Hiring Agent application using Docker Compose, which includes both the backend API and frontend UI services.

## Prerequisites

- Docker and Docker Compose installed
- API keys for Mistral AI and/or OpenAI
- Data files in the `data/` directory

## Quick Start

1. **Clone the repository and navigate to the project directory:**
   ```bash
   cd ocean-hiring-agent
   ```

2. **Set up environment variables:**
   Create a `.env` file in the root directory:
   ```bash
   # API Keys (required)
   MISTRAL_API_KEY=your_mistral_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   
   # Rate Limiting (optional)
   MISTRAL_REQUESTS_PER_SECOND=1.0
   ```

3. **Ensure data files exist:**
   ```
   data/
   ├── team.json
   ├── candidate_1.json
   ├── candidate_2.json
   └── ...
   ```

4. **Build and start the services:**
   ```bash
   docker-compose up --build
   ```

5. **Access the application:**
   - **Home Page**: http://localhost:5005
   - **Dashboard**: http://localhost:5005/dashboard
   - **Interview Portal**: http://localhost:5005/interview
   - **Backend API**: http://localhost:8000
   - **API Documentation**: http://localhost:8000/docs

## Architecture

### Services

#### Backend (`ocean-hiring-backend`)
- **Port**: 8000
- **Technology**: FastAPI + uvicorn
- **Purpose**: AI analysis, interview management, compatibility scoring
- **Health Check**: `/health` endpoint
- **Data Access**: Read/write to `./data` volume

#### UI (`ocean-hiring-ui`)
- **Port**: 5005
- **Technology**: Flask
- **Purpose**: Web interface, dashboards, interview portal
- **Data Access**: Read-only to `./data` volume
- **API Connection**: Connects to backend via internal Docker network

### Networking
- Both services communicate via a shared Docker network (`compatibility-network`)
- UI connects to backend using service name: `http://backend:8000`
- External access via exposed ports

### Data Persistence
- Host `./data` directory mounted to both containers
- Backend has read/write access for saving analysis results
- UI has read-only access for displaying data

## Environment Variables

### Backend Environment Variables
- `MISTRAL_API_KEY`: Required for AI analysis
- `OPENAI_API_KEY`: Required for interview management
- `MISTRAL_REQUESTS_PER_SECOND`: Rate limiting (default: 1.0)
- `PYTHONPATH`: Set to `/app` automatically

### UI Environment Variables
- `FLASK_ENV`: Set to `production`
- `FLASK_DEBUG`: Set to `0`
- `API_BASE_URL`: Automatically set to `http://backend:8000`

## Commands

### Development
```bash
# Build and start services
docker-compose up --build

# Start services in background
docker-compose up -d

# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f backend
docker-compose logs -f ui
```

### Production
```bash
# Start services in production mode
docker-compose up -d --build

# Update services
docker-compose pull
docker-compose up -d --build

# Stop services
docker-compose down
```

### Maintenance
```bash
# Restart specific service
docker-compose restart backend
docker-compose restart ui

# Check service status
docker-compose ps

# View resource usage
docker stats ocean-hiring-backend ocean-hiring-ui

# Clean up
docker-compose down --volumes --remove-orphans
docker system prune -f
```

## Health Checks

Both services include health checks:

- **Backend**: `curl -f http://localhost:8000/health`
- **UI**: `python healthcheck.py`

Health check configuration:
- Interval: 30 seconds
- Timeout: 10 seconds
- Retries: 3
- Start period: 40 seconds (backend), 5 seconds (UI)

## Data Directory Structure

```
data/
├── team.json                    # Team configuration
├── candidate_*.json            # Individual candidate files
├── compatibility_scores.json   # Generated analysis results
└── interview_transcripts/      # Interview data (optional)
```

## Troubleshooting

### Common Issues

1. **Backend fails to start**
   - Check if API keys are set in `.env` file
   - Verify data files exist and are valid JSON
   - Check logs: `docker-compose logs backend`

2. **UI cannot connect to backend**
   - Ensure backend service is healthy
   - Check if `API_BASE_URL` is correctly set
   - Verify network connectivity: `docker-compose exec ui ping backend`

3. **Permission issues with data directory**
   ```bash
   # Fix permissions if needed
   sudo chown -R $USER:$USER ./data
   chmod -R 755 ./data
   ```

4. **Port conflicts**
   - Change ports in `docker-compose.yml` if 5005 or 8000 are in use
   - Update `API_BASE_URL` if backend port changes

### Debug Commands

```bash
# Enter container shell
docker-compose exec backend bash
docker-compose exec ui bash

# Check container logs
docker-compose logs -f --tail=100 backend

# Test API directly
curl http://localhost:8000/health
curl http://localhost:8000/status

# Test UI health
curl http://localhost:5005/health
```

## Security Considerations

- API keys are passed as environment variables (keep `.env` file secure)
- Data directory is mounted with appropriate permissions
- CORS is configured for development (adjust for production)
- Consider using Docker secrets for production deployments

## Performance Tuning

- Adjust `MISTRAL_REQUESTS_PER_SECOND` based on your API limits
- Monitor resource usage with `docker stats`
- Consider adding resource limits in docker-compose.yml for production

## Backup and Recovery

```bash
# Backup data directory
tar -czf backup-$(date +%Y%m%d).tar.gz data/

# Restore from backup
tar -xzf backup-YYYYMMDD.tar.gz
```

## Updating

1. Pull latest changes from repository
2. Rebuild containers: `docker-compose up --build`
3. Check logs to ensure services start correctly

This deployment setup provides a complete, production-ready environment for the Ocean Hiring Agent application. 