# Docker Setup for Team Compatibility Dashboard UI

This directory contains Docker configuration files to run the Team Compatibility Dashboard UI using Docker and Docker Compose.

## Prerequisites

- Docker
- Docker Compose
- Data files in the `./data` directory

## Quick Start

### 1. Build and Run with Docker Compose

```bash
# Build and start the UI service
docker-compose up --build

# Or run in detached mode
docker-compose up --build -d
```

### 2. Access the Dashboard

Open your browser and navigate to:
```
http://localhost:5005
```

### 3. Stop the Services

```bash
# Stop and remove containers
docker-compose down

# Stop and remove containers, networks, and volumes
docker-compose down -v
```

## Configuration

### Data Volume

The `./data` directory is mounted as a read-only volume at `/app/data` inside the container. This allows the UI to access:

- `compatibility_scores.json` - Cached analysis results
- `team.json` - Team member data
- `candidate_*.json` - Candidate data files

### Environment Variables

The following environment variables are set in the container:

- `FLASK_ENV=production` - Run Flask in production mode
- `FLASK_DEBUG=0` - Disable debug mode
- `PYTHONUNBUFFERED=1` - Ensure Python output is not buffered
- `PYTHONDONTWRITEBYTECODE=1` - Prevent Python from writing .pyc files

### Port Mapping

- Host port `5005` is mapped to container port `5005`
- The Flask application listens on `0.0.0.0:5005` inside the container

## Development

### Local Development vs Docker

The application automatically detects the environment and adjusts file paths:

- **Docker**: Looks for data files in `/app/data/` (mounted volume)
- **Local**: Looks for data files in `../data/` (relative path)

### Building Only the UI Image

```bash
# Build just the UI image
docker build -t compatibility-ui ./ui

# Run the UI container manually
docker run -p 5005:5005 -v $(pwd)/data:/app/data:ro compatibility-ui
```

## API Integration

If the local `compatibility_scores.json` file is not found, the UI will attempt to call the API at `http://localhost:8000/analysis/compatibility` to generate fresh data.

For full functionality with the API:

1. Uncomment the `api` service in `docker-compose.yml`
2. Create a `Dockerfile.api` for the API service
3. Update the API URL if running both services in Docker

## Troubleshooting

### Common Issues

1. **Data files not found**
   - Ensure the `./data` directory exists and contains the required JSON files
   - Check file permissions (Docker needs read access)

2. **Port already in use**
   - Change the host port in `docker-compose.yml`: `"5006:5005"`
   - Or stop the conflicting service

3. **Build failures**
   - Ensure you have a stable internet connection for downloading dependencies
   - Try cleaning Docker cache: `docker system prune`

### Logs

View application logs:
```bash
# View logs from all services
docker-compose logs

# View logs from UI service only
docker-compose logs ui

# Follow logs in real-time
docker-compose logs -f ui
```

## File Structure

```
.
├── docker-compose.yml          # Multi-service orchestration
├── ui/
│   ├── Dockerfile             # UI application container
│   ├── .dockerignore          # Files to exclude from build
│   ├── app.py                 # Flask application
│   ├── pyproject.toml         # Python dependencies (uv)
│   └── ...                    # Other UI files
└── data/                      # Data files (mounted as volume)
    ├── team.json
    ├── candidate_*.json
    └── compatibility_scores.json
``` 