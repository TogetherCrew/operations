#!/usr/bin/env python3
"""
Verification script to check Discord data migration from PostgreSQL to Qdrant.

This script compares document counts and sample data between PostgreSQL 
and Qdrant to verify migration completeness.

Usage:
    python verify_discord_migration.py --community-id COMMUNITY_ID --platform-id PLATFORM_ID [--detailed]
"""

import argparse
import logging
import sys
from typing import Dict, List

from tc_hivemind_backend.db.postgresql import PostgresSingleton
from tc_hivemind_backend.ingest_qdrant import CustomIngestionPipeline
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()


class DiscordMigrationVerifier:
    def __init__(self):
        self.verification_results = []

    def get_pg_counts(self, dbname: str) -> Dict[str, int]:
        """Get document counts from PostgreSQL."""
        try:
            postgres = PostgresSingleton(dbname=dbname)
            conn = postgres.get_connection()
            cursor = conn.cursor()
            
            counts = {}
            
            # Check discord table
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'data_discord'
                );
            """)
            
            result = cursor.fetchone()
            if result and result[0]:
                cursor.execute("SELECT COUNT(*) FROM data_discord;")
                result = cursor.fetchone()
                counts['discord'] = result[0] if result else 0
            else:
                counts['discord'] = 0
            
            # Check discord_summary table
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'data_discord_summary'
                );
            """)
            
            result = cursor.fetchone()
            if result and result[0]:
                cursor.execute("SELECT COUNT(*) FROM data_discord_summary;")
                result = cursor.fetchone()
                counts['discord_summary'] = result[0] if result else 0
            else:
                counts['discord_summary'] = 0
            
            cursor.close()
            postgres.close_connection()
            
            return counts
            
        except Exception as e:
            logger.error(f"Error getting PostgreSQL counts for {dbname}: {e}")
            return {}

    def list_qdrant_collections(self, community_id: str) -> List[str]:
        """List all available Qdrant collections."""
        try:
            # Create a dummy pipeline just to get the client
            ingestion_pipeline = CustomIngestionPipeline(
                community_id=community_id,
                collection_name="dummy",
                use_cache=False,
            )
            
            collections = ingestion_pipeline.qdrant_client.get_collections()
            collection_names = [col.name for col in collections.collections]
            logger.info(f"Available Qdrant collections: {collection_names}")
            return collection_names
            
        except Exception as e:
            logger.error(f"Error listing Qdrant collections: {e}")
            return []

    def get_qdrant_counts(self, community_id: str, platform_id: str) -> Dict[str, int]:
        """Get document counts from Qdrant."""
        counts = {}
        
        # First, list all available collections
        self.list_qdrant_collections(community_id)
        
        try:
            # Count regular Discord documents
            collection_name = f"{community_id}_{platform_id}"
            logger.info(f"Checking Qdrant collection: {collection_name}")
            
            ingestion_pipeline = CustomIngestionPipeline(
                community_id=community_id,
                collection_name=collection_name,
                use_cache=False,
            )
            
            # Try to get collection info
            try:
                collection_info = ingestion_pipeline.qdrant_client.get_collection(collection_name)
                counts['discord'] = collection_info.points_count
                logger.info(f"Collection {collection_name} has {collection_info.points_count} documents")
            except Exception as e:
                logger.warning(f"Collection {collection_name} not found or error: {e}")
                counts['discord'] = 0
            
            # Count Discord summary documents
            try:
                summary_collection_name = f"{community_id}_{platform_id}_summary"
                logger.info(f"Checking Qdrant summary collection: {summary_collection_name}")
                
                summary_pipeline = CustomIngestionPipeline(
                    community_id=community_id,
                    collection_name=summary_collection_name,
                    use_cache=False,
                )
                collection_info = summary_pipeline.qdrant_client.get_collection(summary_collection_name)
                counts['discord_summary'] = collection_info.points_count
                logger.info(f"Summary collection {summary_collection_name} has {collection_info.points_count} documents")
            except Exception as e:
                logger.warning(f"Summary collection {summary_collection_name} not found or error: {e}")
                counts['discord_summary'] = 0
                
        except Exception as e:
            logger.error(f"Error getting Qdrant counts for platform {platform_id}: {e}")
            counts['discord'] = 0
            counts['discord_summary'] = 0
        
        return counts

    def verify_community(self, community_id: str, platform_id: str, detailed: bool = False) -> Dict:
        """Verify migration for a single community."""
        logger.info(f"Verifying migration for community {community_id}, platform {platform_id}")
        
        dbname = f"community_{community_id}"
        
        # Get counts from PostgreSQL
        pg_counts = self.get_pg_counts(dbname)
        
        # Get counts from Qdrant
        qdrant_counts = self.get_qdrant_counts(community_id, platform_id)
        
        # Extract counts
        pg_discord_count = pg_counts.get('discord', 0)
        pg_summary_count = pg_counts.get('discord_summary', 0)
        qdrant_discord_count = qdrant_counts.get('discord', 0)
        qdrant_summary_count = qdrant_counts.get('discord_summary', 0)
        
        # Verification results
        result = {
            'community_id': community_id,
            'platform_id': platform_id,
            'pg_discord_count': pg_discord_count,
            'pg_summary_count': pg_summary_count,
            'qdrant_discord_count': qdrant_discord_count,
            'qdrant_summary_count': qdrant_summary_count,
            'discord_match': pg_discord_count == qdrant_discord_count,
            'summary_match': pg_summary_count == qdrant_summary_count,
            'success': pg_discord_count == qdrant_discord_count and pg_summary_count == qdrant_summary_count
        }
        
        if detailed:
            result['detailed_pg_counts'] = pg_counts
            result['detailed_qdrant_counts'] = qdrant_counts
        
        return result

    def run_verification(self, community_id: str, platform_id: str, detailed: bool = False):
        """Run verification for specific community and platform."""
        logger.info("Starting Discord migration verification")
        
        try:
            result = self.verify_community(community_id, platform_id, detailed)
            self.verification_results.append(result)
            
            # Log result
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            logger.info(
                f"{status} Community {result['community_id']}, Platform {result['platform_id']}: "
                f"Discord {result['pg_discord_count']}→{result['qdrant_discord_count']}, "
                f"Summaries {result['pg_summary_count']}→{result['qdrant_summary_count']}"
            )
            
        except Exception as e:
            logger.error(f"Failed to verify community {community_id}, platform {platform_id}: {e}")
            return False
        
        # Print summary
        logger.info("=" * 80)
        logger.info("VERIFICATION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Community: {result['community_id']}")
        logger.info(f"Platform: {result['platform_id']}")
        logger.info(f"Discord documents: PG={result['pg_discord_count']}, Qdrant={result['qdrant_discord_count']}")
        logger.info(f"Summary documents: PG={result['pg_summary_count']}, Qdrant={result['qdrant_summary_count']}")
        
        discord_match = result['discord_match']
        summary_match = result['summary_match']
        
        logger.info(f"Discord migration: {'✅ SUCCESS' if discord_match else '❌ MISMATCH'}")
        logger.info(f"Summary migration: {'✅ SUCCESS' if summary_match else '❌ MISMATCH'}")
        
        if result['success']:
            logger.info("🎉 Migration verified successfully!")
            return True
        else:
            logger.error("❌ Migration verification failed!")
            return False


def main():
    parser = argparse.ArgumentParser(
        description="Verify Discord data migration from PostgreSQL to Qdrant"
    )
    parser.add_argument(
        "--community-id",
        type=str,
        required=True,
        help="Community ID to verify"
    )
    parser.add_argument(
        "--platform-id",
        type=str,
        required=True,
        help="Platform ID for the Discord platform"
    )
    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Show detailed counts per platform"
    )
    
    args = parser.parse_args()
    
    verifier = DiscordMigrationVerifier()
    
    try:
        success = verifier.run_verification(args.community_id, args.platform_id, args.detailed)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Verification interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 