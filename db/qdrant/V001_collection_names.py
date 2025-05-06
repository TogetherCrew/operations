from qdrant_client import QdrantClient
from pymongo import MongoClient
from bson import ObjectId
import os
import re
from tqdm import tqdm
import logging
from dotenv import load_dotenv
from qdrant_client.http import models as rest


load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def run_migration():
    # Connect to Qdrant
    qdrant_host = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    qdrant_https = os.getenv("QDRANT_USE_HTTPS", False)
    # Get batch size from environment variable or use a smaller default (32 instead of 128)
    batch_size = int(os.getenv("QDRANT_MIGRATION_BATCH_SIZE", "32"))

    # Connect to Qdrant
    qdrant_client = QdrantClient(
        host=qdrant_host,
        port=qdrant_port,
        https=qdrant_https,
        api_key=qdrant_api_key,
    )

    # Connect to MongoDB
    mongo_uri = os.getenv("MONGODB_URI")
    if not mongo_uri:
        raise ValueError("MONGODB_URI environment variable is not set")
    mongo_client = MongoClient(mongo_uri)
    core_db = mongo_client["Core"]
    platforms_collection = core_db["platforms"]

    # Get all Qdrant collection names
    collections = qdrant_client.get_collections().collections
    collection_names = [collection.name for collection in collections]

    # Regular expression to identify and parse collection names
    pattern = r"^([^_]+)_([^_]+)(?:_summary)?$"

    # Dictionary to store the mappings
    mappings = {}

    # Find collections matching the pattern and extract communityId and platformName
    for name in collection_names:
        match = re.match(pattern, name)
        if match:
            community_id = match.group(1)
            platform_name = match.group(2)
            is_summary = name.endswith("_summary")

            # Find the platform in MongoDB
            platform = platforms_collection.find_one(
                {"community": ObjectId(community_id), "name": platform_name}
            )

            if platform:
                platform_id = str(platform["_id"])

                # Create the new collection name
                new_name = f"{community_id}_{platform_id}"
                if is_summary:
                    new_name += "_summary"

                mappings[name] = new_name
                logger.info(f"Will rename: {name} -> {new_name}")
            else:
                logger.warning(
                    f"Could not find platform with communityId={community_id} and name={platform_name}"
                )

    # Perform the migration for each collection
    for old_name, new_name in tqdm(mappings.items(), desc="Migrating collections"):
        try:
            # Check if the collection exists
            if old_name in collection_names:
                # Get collection info to recreate with same parameters
                collection_info = None
                for collection in collections:
                    if collection.name == old_name:
                        collection_info = collection
                        break

                if collection_info:
                    # Get detailed collection information including configuration
                    detailed_info = qdrant_client.get_collection(
                        collection_name=old_name
                    )

                    if new_name in collection_names:
                        logger.info(f"Collection {new_name} already exists - skipping the process.")
                        continue

                    # Create the new collection with the same parameters
                    qdrant_client.create_collection(
                        collection_name=new_name,
                        vectors_config=detailed_info.config.params.vectors,
                        hnsw_config=detailed_info.config.hnsw_config.__dict__,
                        optimizers_config=detailed_info.config.optimizer_config.__dict__,
                        wal_config=detailed_info.config.wal_config.__dict__,
                        quantization_config=detailed_info.config.quantization_config,
                    )

                    # Get all data from the old collection in batches
                    # Using a smaller batch size to prevent "413 Payload Too Large" errors
                    
                    # scroll returns (records, next_offset)
                    next_offset = None

                    while True:
                        records, next_offset = qdrant_client.scroll(
                            collection_name=old_name,
                            limit=batch_size,
                            offset=next_offset,
                            with_payload=True,
                            with_vectors=True,
                        )

                        if not records:
                            break

                        points = [
                            rest.PointStruct(
                                id=rec.id, vector=rec.vector, payload=rec.payload
                            )
                            for rec in records
                        ]

                        try:
                            qdrant_client.upsert(
                                collection_name=new_name,
                                points=points,
                                wait=True,
                            )
                        except Exception as upsert_error:
                            if "413" in str(upsert_error):
                                # If we hit a payload too large error, try with a smaller batch
                                logger.warning(f"Payload too large with batch size {len(points)}, attempting with smaller batches")
                                # Split the batch in half and retry each half
                                mid = len(points) // 2
                                for sub_batch in [points[:mid], points[mid:]]:
                                    if sub_batch:
                                        qdrant_client.upsert(
                                            collection_name=new_name,
                                            points=sub_batch,
                                            wait=True,
                                        )
                                logger.info(f"Successfully inserted with smaller sub-batches")
                            else:
                                # Re-raise other errors
                                raise upsert_error

                        # no more pages
                        if next_offset is None:
                            break
                    logger.info(
                        f"Successfully migrated collection: {old_name} -> {new_name}"
                    )
                else:
                    logger.error(f"Could not get collection info for {old_name}")
        except Exception as e:
            logger.error(
                f"Error migrating collection {old_name} to {new_name}: {str(e)}"
            )


if __name__ == "__main__":
    run_migration()
