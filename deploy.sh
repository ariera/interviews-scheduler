#!/bin/bash

# Interview Scheduler Deployment Script
# Usage: ./deploy.sh [dev|prod] [build|up|down|logs|restart]

set -e

ENVIRONMENT=${1:-prod}
ACTION=${2:-up}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Function to create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    mkdir -p logs/nginx
    mkdir -p uploads
    chmod 755 logs logs/nginx uploads
}

# Function to check environment files
check_env_files() {
    if [ "$ENVIRONMENT" = "prod" ]; then
        if [ ! -f "production.env" ]; then
            print_warning "production.env not found. Creating from template..."
            cp production.env.example production.env
            print_warning "Please edit production.env with your production settings!"
        fi
    else
        if [ ! -f "development.env" ]; then
            print_warning "development.env not found. Creating from template..."
            cp development.env.example development.env
        fi
    fi
}

# Function to deploy
deploy() {
    local compose_file="docker-compose.yaml"
    if [ "$ENVIRONMENT" = "dev" ]; then
        compose_file="docker-compose.dev.yaml"
    fi

    case $ACTION in
        "build")
            print_status "Building Docker images for $ENVIRONMENT environment..."
            docker-compose -f $compose_file build
            print_success "Build completed successfully!"
            ;;
        "up")
            print_status "Starting services for $ENVIRONMENT environment..."
            if [ "$ENVIRONMENT" = "prod" ]; then
                docker-compose -f $compose_file up -d
                print_success "Services started in background!"
                print_status "Access the application at: http://localhost:8080"
            else
                docker-compose -f $compose_file up
            fi
            ;;
        "down")
            print_status "Stopping services..."
            docker-compose -f $compose_file down
            print_success "Services stopped!"
            ;;
        "restart")
            print_status "Restarting services..."
            docker-compose -f $compose_file down
            docker-compose -f $compose_file up -d
            print_success "Services restarted!"
            ;;
        "logs")
            print_status "Showing logs for $ENVIRONMENT environment..."
            docker-compose -f $compose_file logs -f
            ;;
        "clean")
            print_status "Cleaning up Docker resources..."
            docker-compose -f $compose_file down -v
            docker system prune -f
            print_success "Cleanup completed!"
            ;;
        "status")
            print_status "Checking service status..."
            docker-compose -f $compose_file ps
            ;;
        *)
            print_error "Unknown action: $ACTION"
            print_status "Available actions: build, up, down, restart, logs, clean, status"
            exit 1
            ;;
    esac
}

# Main execution
main() {
    print_status "Interview Scheduler Deployment Script"
    print_status "Environment: $ENVIRONMENT"
    print_status "Action: $ACTION"
    echo

    check_docker
    create_directories
    check_env_files
    deploy
}

# Show usage if no arguments provided
if [ $# -eq 0 ]; then
    echo "Interview Scheduler Deployment Script"
    echo ""
    echo "Usage: $0 [dev|prod] [build|up|down|logs|restart|clean|status]"
    echo ""
    echo "Environments:"
    echo "  dev   - Development environment with live reload"
    echo "  prod  - Production environment (default)"
    echo ""
    echo "Actions:"
    echo "  build   - Build Docker images"
    echo "  up      - Start services"
    echo "  down    - Stop services"
    echo "  restart - Restart services"
    echo "  logs    - Show service logs"
    echo "  clean   - Clean up Docker resources"
    echo "  status  - Show service status"
    echo ""
    echo "Examples:"
    echo "  $0 prod up      # Start production services"
    echo "  $0 dev up       # Start development services"
    echo "  $0 prod logs    # Show production logs"
    echo "  $0 dev restart  # Restart development services"
    exit 1
fi

main