# Docker Deployment Guide

This directory contains Docker configurations for deploying the Interview Scheduler application in both development and production environments.

## Architecture

The application uses a two-container setup:
- **interview-scheduler**: Python Flask application with Gunicorn
- **nginx**: Reverse proxy with load balancing and security headers

## Quick Start

### Development Environment

1. **Copy environment file:**
   ```bash
   cp development.env.example development.env
   ```

2. **Start development environment:**
   ```bash
   docker-compose -f docker-compose.dev.yaml up --build
   ```

3. **Access the application:**
   - Web interface: http://localhost:8080
   - Direct Flask app: http://localhost:5001

### Production Environment

1. **Copy environment file:**
   ```bash
   cp production.env.example production.env
   ```

2. **Edit production.env with your settings:**
   ```bash
   # Change the secret key and other production values
   nano production.env
   ```

3. **Start production environment:**
   ```bash
   docker-compose up --build -d
   ```

4. **Access the application:**
   - Web interface: http://localhost:8080

## Configuration

### Environment Variables

#### Development (`development.env`)
- `FLASK_ENV=development`: Enables debug mode
- `FLASK_DEBUG=1`: Enables auto-reload
- `SECRET_KEY`: Flask secret key (change in production)

#### Production (`production.env`)
- `FLASK_ENV=production`: Production mode
- `SECRET_KEY`: Strong secret key (required)
- `MAX_SOLVER_TIME`: Maximum solver time in seconds
- `MAX_SOLUTIONS`: Maximum number of solutions to generate
- `WORKERS`: Number of Gunicorn workers

### Volumes

- `./examples:/app/examples:ro`: Example configuration files (read-only)
- `./logs:/app/logs`: Application logs
- `./logs/nginx:/var/log/nginx`: Nginx logs

### Ports

- **8080**: Nginx reverse proxy (external access)
- **5001**: Flask application (internal only)

## Docker Commands

### Build Images
```bash
# Production
docker-compose build

# Development
docker-compose -f docker-compose.dev.yaml build
```

### Start Services
```bash
# Production (detached)
docker-compose up -d

# Development (with logs)
docker-compose -f docker-compose.dev.yaml up
```

### Stop Services
```bash
# Production
docker-compose down

# Development
docker-compose -f docker-compose.dev.yaml down
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f interview-scheduler
docker-compose logs -f nginx
```

### Shell Access
```bash
# Flask application
docker-compose exec interview-scheduler bash

# Nginx
docker-compose exec nginx sh
```

## Security Features

### Production Security
- Non-root user in Python container
- Security headers in Nginx
- CSRF protection enabled
- Request size limits
- Health checks

### Nginx Security Headers
- X-Frame-Options: SAMEORIGIN
- X-XSS-Protection: 1; mode=block
- X-Content-Type-Options: nosniff
- Referrer-Policy: no-referrer-when-downgrade
- Content-Security-Policy

## Monitoring

### Health Checks
- Application: `http://localhost:8080/health`
- Container health checks configured
- Nginx health check endpoint

### Logs
- Application logs: `./logs/app.log`
- Nginx access logs: `./logs/nginx/access.log`
- Nginx error logs: `./logs/nginx/error.log`

## Troubleshooting

### Common Issues

1. **Port already in use:**
   ```bash
   # Check what's using the port
   lsof -i :8080

   # Change port in docker-compose.yaml
   ports:
     - "127.0.0.1:8081:80"  # Change 8080 to 8081
   ```

2. **Permission denied:**
   ```bash
   # Create logs directory with proper permissions
   mkdir -p logs/nginx
   chmod 755 logs logs/nginx
   ```

3. **Build fails:**
   ```bash
   # Clean and rebuild
   docker-compose down
   docker system prune -f
   docker-compose build --no-cache
   ```

### Debug Mode
```bash
# Run with debug output
docker-compose -f docker-compose.dev.yaml up --build
```

## Production Deployment

### Prerequisites
- Docker and Docker Compose installed
- Proper firewall configuration
- SSL certificate (recommended)

### SSL Configuration
For production, add SSL configuration to nginx.conf:
```nginx
server {
    listen 443 ssl;
    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;
    # ... rest of configuration
}
```

### Backup Strategy
- Configuration files: Version controlled
- Logs: Mounted volumes
- Uploads: Consider persistent storage

### Scaling
```bash
# Scale the application
docker-compose up -d --scale interview-scheduler=3
```

## Maintenance

### Update Application
```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose up --build -d
```

### Clean Up
```bash
# Remove unused containers and images
docker system prune -f

# Remove all containers and volumes
docker-compose down -v
```