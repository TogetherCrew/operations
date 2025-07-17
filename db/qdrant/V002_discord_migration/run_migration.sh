#!/bin/bash

# Discord PostgreSQL to Qdrant Migration Runner
# This script simplifies running the Discord migration in Docker

set -e

COMPOSE_FILES="-f compose/docker-compose.yml -f db/qdrant/V002_discord_migration/docker-compose.migration.yml"
SERVICE_NAME="discord-migration"

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

# Function to check if Docker and Docker Compose are available
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed or not in PATH"
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Function to check if required services are running
check_services() {
    print_status "Checking if required services are running..."
    
    services=("mongodb" "pgvector" "qdrant" "temporal")
    for service in "${services[@]}"; do
        if docker-compose ps | grep -q "$service.*Up"; then
            print_success "$service is running"
        else
            print_error "$service is not running. Please start your services first."
            exit 1
        fi
    done
}

# Function to build the migration image
build_image() {
    print_status "Building migration Docker image..."
    docker-compose $COMPOSE_FILES build $SERVICE_NAME
    print_success "Migration image built successfully"
}

# Function to run dry-run
run_dry_run() {
    print_status "Running migration dry-run..."
    print_warning "This will show what would be migrated without actually moving data"
    docker-compose $COMPOSE_FILES run --rm $SERVICE_NAME --dry-run
    print_success "Dry-run completed"
}

# Function to run actual migration
run_migration() {
    print_warning "This will perform the actual migration!"
    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Running actual migration..."
        docker-compose $COMPOSE_FILES run --rm $SERVICE_NAME
        print_success "Migration completed"
    else
        print_status "Migration cancelled"
        exit 0
    fi
}

# Function to run verification
run_verification() {
    print_status "Running migration verification..."
    docker-compose $COMPOSE_FILES run --rm $SERVICE_NAME python V002_verify_migration.py
    print_success "Verification completed"
}

# Function to show help
show_help() {
    echo "Discord PostgreSQL to Qdrant Migration Runner"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  build       Build the migration Docker image"
    echo "  dry-run     Run migration in dry-run mode (recommended first step)"
    echo "  migrate     Run the actual migration"
    echo "  verify      Run migration verification"
    echo "  full        Run the complete migration process (build, dry-run, migrate, verify)"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 dry-run    # Test the migration without moving data"
    echo "  $0 migrate    # Run the actual migration"
    echo "  $0 full       # Run the complete process"
}

# Main script logic
main() {
    case "${1:-help}" in
        "build")
            check_prerequisites
            build_image
            ;;
        "dry-run")
            check_prerequisites
            check_services
            build_image
            run_dry_run
            ;;
        "migrate")
            check_prerequisites
            check_services
            build_image
            run_migration
            ;;
        "verify")
            check_prerequisites
            check_services
            run_verification
            ;;
        "full")
            check_prerequisites
            check_services
            build_image
            run_dry_run
            echo ""
            print_status "Dry-run completed. Review the output above."
            read -p "Do you want to proceed with the actual migration? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                run_migration
                run_verification
            else
                print_status "Full migration process cancelled"
            fi
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# Check if we're in the correct directory
if [[ ! -f "compose/docker-compose.yml" ]]; then
    print_error "Please run this script from the project root directory (where compose/docker-compose.yml is located)"
    exit 1
fi

# Run main function with all arguments
main "$@" 