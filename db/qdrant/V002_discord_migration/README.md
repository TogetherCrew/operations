# Discord PostgreSQL to Qdrant Migration (V002)

This directory contains the Docker setup for migrating Discord data from PostgreSQL to Qdrant vector storage.

## Files

- `V002_migrate_discord_pgvector.py` - Main migration script
- `V002_verify_migration.py` - Verification script to check migration results
- `v002_requirements.txt` - Python dependencies
- `Dockerfile` - Docker image definition for the migration
- `docker-compose.migration.yml` - Docker Compose service definition

## Prerequisites

1. Ensure your main services are running:
   - MongoDB
   - PostgreSQL (pgvector)
   - Qdrant
   - Temporal

2. Make sure you have the required environment variables set in your `.env` file:
   ```env
    POSTGRES_HOST=
    POSTGRES_PASS=
    POSTGRES_USER=
    POSTGRES_PORT=
    POSTGRES_DBNAME=

    QDRANT_HOST=
    QDRANT_PORT=
    QDRANT_API_KEY=
    QDRANT_USE_HTTPS=

    MONGODB_HOST=
    MONGODB_USER=
    MONGODB_PASS=
    MONGODB_PORT=

    COHERE_API_KEY=
    CHUNK_SIZE=
    EMBEDDING_DIM=

    TEMPORAL_HOST=
    TEMPORAL_API_KEY=
    TEMPORAL_PORT=
   ```

## Usage

### 1. Build the Migration Image

From the project root directory:

```bash
docker compose -f compose/docker-compose.yml -f db/qdrant/V002_discord_migration/docker-compose.migration.yml build discord-migration
```

### 2. Run a Dry Run (Recommended)

Test the migration without actually moving data:

```bash
docker compose -f compose/docker-compose.yml -f db/qdrant/V002_discord_migration/docker-compose.migration.yml run --rm discord-migration --dry-run
```

### 3. Run the Actual Migration

Once you're satisfied with the dry run results:

```bash
docker compose -f compose/docker-compose.yml -f db/qdrant/V002_discord_migration/docker-compose.migration.yml run --rm discord-migration
```

### 4. Verify the Migration (Optional)

Run the verification script to check that data was migrated correctly:

```bash
docker compose -f compose/docker-compose.yml -f db/qdrant/V002_discord_migration/docker-compose.migration.yml run --rm discord-migration python V002_verify_migration.py
```

## What the Migration Does

1. **Discovers Discord Platforms**: Queries MongoDB to find all active Discord platforms
2. **Migrates Regular Documents**: Moves Discord messages from PostgreSQL to Qdrant using Temporal workflows
3. **Migrates Summary Documents**: Moves Discord summaries to separate Qdrant collections using Temporal workflows
4. **Preserves Metadata**: Converts date metadata to timestamps and maintains all other metadata
5. **Handles Embeddings**: Transfers existing vector embeddings from PostgreSQL to Qdrant

## Troubleshooting

### Check Service Health

```bash
# Check if all required services are running
docker-compose ps

# Check specific service logs
docker-compose logs mongodb
docker-compose logs pgvector
docker-compose logs qdrant
docker-compose logs temporal
```

### Test Network Connectivity

```bash
# Test connectivity from within the network
docker-compose run --rm discord-migration ping mongodb
docker-compose run --rm discord-migration ping pgvector
docker-compose run --rm discord-migration ping qdrant
docker-compose run --rm discord-migration ping temporal
```

### View Migration Logs

```bash
# Run with verbose logging
docker compose -f docker-compose.yml -f db/qdrant/V002_discord_migration/docker-compose.migration.yml run --rm discord-migration --dry-run 2>&1 | tee migration.log
```

## Important Notes

- **Always run a dry run first** to understand what will be migrated
- **Backup your data** before running the actual migration
- The migration uses Temporal workflows for reliability and can be monitored through the Temporal UI
- Each Discord platform gets its own collection in Qdrant
- Summary documents are stored in separate collections with the suffix `_summary`
- The migration preserves all existing metadata and embeddings
