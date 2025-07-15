#!/usr/bin/env python3
"""
Migration script to move Discord data from PostgreSQL to Qdrant.

This script migrates both regular Discord messages and Discord summaries
from PostgreSQL vector storage to Qdrant vector storage for all Discord platforms.

Usage:
    python V002_migrate_discord_pgvector.py [--dry-run]
"""
import asyncio
import argparse
import logging
import sys
from datetime import datetime

from llama_index.core import Document
from tc_hivemind_backend.db.postgresql import PostgresSingleton
from tc_hivemind_backend.ingest_qdrant import CustomIngestionPipeline
from tc_hivemind_backend.db.mongo import MongoSingleton
from dotenv import load_dotenv
from tc_temporal_backend.client import TemporalClient
from pydantic import BaseModel


class BatchDocument(BaseModel):
    """A model representing a document for batch ingestion.
    
    """
    docId: str
    text: str
    metadata: dict
    excludedEmbedMetadataKeys: list[str] = []
    excludedLlmMetadataKeys: list[str] = []


class BatchIngestionRequest(BaseModel):
    """A model representing a batch of ingestion requests for document processing.

    Parameters
    ----------
    ingestion_requests : list[IngestionRequest]
        A list of ingestion requests.
    """
    communityId: str
    platformId: str
    collectionName: str | None = None
    document: list[BatchDocument]


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

class DiscordPGToQdrantMigrator:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.processed_documents = 0
        self.processed_summaries = 0

    def convert_date_to_timestamp(self, metadata):
        """Convert date string in metadata to float timestamp."""
        if metadata and isinstance(metadata, dict) and 'date' in metadata:
            try:
                date_str = metadata['date']
                if isinstance(date_str, str):
                    # Try parsing with time first (regular Discord documents)
                    try:
                        dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        # Try parsing date only (summaries)
                        dt = datetime.strptime(date_str, '%Y-%m-%d')
                    
                    metadata['date'] = dt.timestamp()
            except (ValueError, TypeError) as e:
                logger.warning(f"Could not parse date '{metadata.get('date', 'N/A')}': {e}")
        return metadata

    def get_discord_platforms(self):
        """Get all Discord platforms from MongoDB."""
        try:
            mongo_instance = MongoSingleton.get_instance()
            db = mongo_instance.get_client()["Core"]
            platforms_collection = db["platforms"]
            
            # Query for all Discord platforms
            discord_platforms = platforms_collection.find(
                {
                    "name": "discord",
                    "disconnectedAt": None,
                }
            )
            
            platforms = []
            for platform in discord_platforms:
                community_id = str(platform["community"])
                platform_id = str(platform["_id"])
                platforms.append({
                    "community_id": community_id,
                    "platform_id": platform_id
                })
            
            logger.info(f"Found {len(platforms)} Discord platforms")
            return platforms
            
        except Exception as e:
            logger.error(f"Error getting Discord platforms from MongoDB: {e}")
            return []

    def get_discord_document_count(self, dbname: str) -> int:
        """Get count of Discord documents from a community database."""
        try:
            postgres_instance = PostgresSingleton(dbname=dbname)
            conn = postgres_instance.get_connection()
            cursor = conn.cursor()
            
            # Check if discord table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'data_discord'
                );
            """)
            
            result = cursor.fetchone()
            has_discord_table = result[0] if result else False
            
            if has_discord_table:
                cursor.execute("SELECT COUNT(*) FROM data_discord;")
                result = cursor.fetchone()
                count = result[0] if result else 0
                logger.info(f"Found {count} Discord documents in {dbname}")
            else:
                count = 0
                logger.info(f"No Discord table found in {dbname}")
            
            cursor.close()
            postgres_instance.close_connection()
            
            return count
            
        except Exception as e:
            logger.error(f"Error getting document count from {dbname}: {e}")
            return 0

    def migrate_discord_documents(self, dbname: str, platform_id: str) -> bool:
        """Migrate Discord documents from PostgreSQL to Qdrant."""
        try:
            community_id = dbname.replace("community_", "")
            
            logger.info(f"Migrating Discord documents for community {community_id}, platform {platform_id}")
            
            # Connect to PostgreSQL
            postgres_instance = PostgresSingleton(dbname=dbname)
            conn = postgres_instance.get_connection()
            cursor = conn.cursor()
            
            # Get documents from PostgreSQL (no platform_id filter since it's not stored)
            cursor.execute("""
                SELECT node_id, text, metadata_, embedding
                FROM data_discord 
                ORDER BY (metadata_->>'date')::timestamp;
            """)
            
            documents: list[Document] = []
            for row in cursor.fetchall():
                node_id, text, metadata, embedding = row

                # Convert date in metadata to timestamp
                metadata = self.convert_date_to_timestamp(metadata)

                # Create Document object
                doc = Document(
                    text=text,
                    doc_id=node_id,
                    metadata=metadata
                )
                
                # Add the embedding if it exists
                if embedding is not None:
                    try:
                        # Convert embedding from PostgreSQL format to list
                        if isinstance(embedding, str):
                            # If it's a string representation, parse it
                            import ast
                            embedding_vector = ast.literal_eval(embedding)
                        elif hasattr(embedding, 'tolist'):
                            # If it's a numpy array or similar, convert to list
                            embedding_vector = embedding.tolist()
                        else:
                            # If it's already a list/sequence, use as is
                            embedding_vector = list(embedding)
                        
                        doc.embedding = embedding_vector
                    except Exception as e:
                        logger.warning(f"Could not parse embedding for document {node_id}: {e}")
                    
                documents.append(doc)
            
            cursor.close()
            postgres_instance.close_connection()
            
            logger.info(f"Retrieved {len(documents)} Discord documents")

            client = asyncio.run(TemporalClient().get_client())

            batch_documents: list[BatchDocument] = []
            if not self.dry_run and documents:                
                # Migrate in batches of 50
                batch_size = 50
                for i in range(0, len(documents), batch_size):
                    batch = documents[i:i+batch_size]
                    logger.info(f"Processing Discord batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}")
                    # batch_documents.extend(batch)
                    batch_documents.extend(
                        [
                            BatchDocument(
                                docId=doc.doc_id, 
                                text=doc.text, 
                                metadata=doc.metadata, 
                                excludedEmbedMetadataKeys=doc.metadata.get("excludedEmbedMetadataKeys", []), 
                                excludedLlmMetadataKeys=doc.metadata.get("excludedLlmMetadataKeys", [])
                            ) for doc in batch
                        ]
                    )


                payload = BatchIngestionRequest(
                    communityId=community_id,
                    platformId=platform_id,
                    document=batch_documents,
                )

                asyncio.run(client.execute_workflow(
                    "BatchVectorIngestionWorkflow",
                    payload,
                    id=f"migrations:IngestDiscord:{datetime.now().timestamp()}",
                    task_queue="TEMPORAL_QUEUE_PYTHON_HEAVY",
                ))

                logger.info(f"Successfully migrated {len(documents)} Discord documents")
            
            self.processed_documents += len(documents)
            return True
            
        except Exception as e:
            logger.error(f"Error migrating Discord documents: {e}")
            return False

    def migrate_discord_summaries(self, dbname: str, platform_id: str) -> bool:
        """Migrate Discord summaries from PostgreSQL to Qdrant."""
        try:
            community_id = dbname.replace("community_", "")
            
            logger.info(f"Migrating Discord summaries for community {community_id}, platform {platform_id}")
            
            # Connect to PostgreSQL
            postgres_instance = PostgresSingleton(dbname=dbname)
            conn = postgres_instance.get_connection()
            cursor = conn.cursor()
            
            # Check if discord_summary table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'data_discord_summary'
                );
            """)
            
            result = cursor.fetchone()
            has_summary_table = result[0] if result else False
            
            if not has_summary_table:
                logger.info(f"No Discord summary table found in {dbname}")
                cursor.close()
                postgres_instance.close_connection()
                return True
            
            # Get summary documents from PostgreSQL
            cursor.execute("""
                SELECT node_id, text, metadata_, embedding
                FROM data_discord_summary 
                ORDER BY (metadata_->>'date')::timestamp;
            """)
            
            documents = []
            for row in cursor.fetchall():
                node_id, text, metadata, embedding = row
                
                # Convert date in metadata to timestamp
                metadata = self.convert_date_to_timestamp(metadata)

                # Create Document object
                doc = Document(
                    text=text,
                    doc_id=node_id,
                    metadata=metadata
                )
                
                # Add the embedding if it exists
                if embedding is not None:
                    try:
                        # Convert embedding from PostgreSQL format to list
                        if isinstance(embedding, str):
                            # If it's a string representation, parse it
                            import ast
                            embedding_vector = ast.literal_eval(embedding)
                        elif hasattr(embedding, 'tolist'):
                            # If it's a numpy array or similar, convert to list
                            embedding_vector = embedding.tolist()
                        else:
                            # If it's already a list/sequence, use as is
                            embedding_vector = list(embedding)
                        
                        doc.embedding = embedding_vector
                    except Exception as e:
                        logger.warning(f"Could not parse embedding for summary document {node_id}: {e}")
                    
                documents.append(doc)
            
            cursor.close()
            postgres_instance.close_connection()
            
            logger.info(f"Retrieved {len(documents)} Discord summary documents")
            
            if not self.dry_run and documents:
                # Set up Qdrant ingestion pipeline for summaries
                ingestion_pipeline = CustomIngestionPipeline(
                    community_id=community_id,
                    collection_name=f"{platform_id}_summary",
                    use_cache=False,
                )
                
                # Migrate in batches of 50
                batch_size = 50
                for i in range(0, len(documents), batch_size):
                    batch = documents[i:i+batch_size]
                    logger.info(f"Processing summary batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}")
                    ingestion_pipeline.run_pipeline(docs=batch)
                
                logger.info(f"Successfully migrated {len(documents)} Discord summary documents")
            
            self.processed_summaries += len(documents)
            return True
            
        except Exception as e:
            logger.error(f"Error migrating Discord summaries: {e}")
            return False

    def run_migration(self):
        """Run the complete migration process for all Discord platforms."""
        logger.info("Starting Discord PostgreSQL to Qdrant migration for all platforms")
        
        if self.dry_run:
            logger.info("DRY RUN MODE - No data will be actually migrated")
        
        # Get all Discord platforms
        platforms = self.get_discord_platforms()
        
        if not platforms:
            logger.info("No Discord platforms found")
            return True
        
        overall_success = True
        
        for platform in platforms:
            community_id = platform["community_id"]
            platform_id = platform["platform_id"]
            
            logger.info(f"Processing community: {community_id}, platform: {platform_id}")
            
            dbname = f"community_{community_id}"
            
            # Check if community database has Discord data
            doc_count = self.get_discord_document_count(dbname)
            if doc_count == 0:
                logger.info(f"No Discord documents found in community {community_id}")
                continue
            
            success = True
            
            # Migrate Discord documents
            if not self.migrate_discord_documents(dbname, platform_id):
                success = False
                overall_success = False
            
            # Migrate Discord summaries
            if not self.migrate_discord_summaries(dbname, platform_id):
                success = False
                overall_success = False
            
            if success:
                logger.info(f"Successfully migrated community {community_id}")
            else:
                logger.error(f"Failed to migrate community {community_id}")
        
        # Summary
        logger.info("=" * 60)
        logger.info("MIGRATION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total platforms processed: {len(platforms)}")
        logger.info(f"Total documents migrated: {self.processed_documents}")
        logger.info(f"Total summaries migrated: {self.processed_summaries}")
        
        if overall_success:
            logger.info("Migration completed successfully!")
        else:
            logger.error("Migration failed for one or more platforms!")
        
        return overall_success


def main():
    parser = argparse.ArgumentParser(
        description="Migrate Discord data from PostgreSQL to Qdrant for all platforms"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run in dry-run mode (don't actually migrate data)"
    )
    
    args = parser.parse_args()
    
    migrator = DiscordPGToQdrantMigrator(dry_run=args.dry_run)
    
    try:
        success = migrator.run_migration()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 