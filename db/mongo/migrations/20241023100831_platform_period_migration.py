import logging
from datetime import datetime, timedelta

from mongodb_migrations.base import BaseMigration


class Migration(BaseMigration):
    def upgrade(self):
        client = self.db.client

        core_db = client["Core"]
        platforms_collection = core_db["platforms"]

        for platform_document in platforms_collection.find(
            {
                "metadata.period": {"$lte": datetime.now() - timedelta(days=90)}
            }
        ):
            platform_id = platform_document["_id"]
            logging.info(f"Migrating platform _id: {platform_id}")
            try:
                # update the `metadata.period` to be just 90 days ago
                platforms_collection.update_one(
                    {"_id": platform_id},
                    {
                        "$set": {
                            "metadata.period": datetime.now() - timedelta(days=90)
                        }
                    }
                )
            except Exception:
                logging.error(f"Exception raised during handling platform id: {platform_id}")


    def downgrade(self):
        pass
