from mongodb_migrations.base import BaseMigration

# requirement lib: mongodb-migrations


class Migration(BaseMigration):
    def upgrade(self):
        client = self.db.client

        db_saga = client["Saga"]
        collection_saga = db_saga["sagas"]

        db_core = client["Core"]
        collection_platforms = db_core["platforms"]

        for saga_document in collection_saga.find():
            if "guildId" in saga_document["data"]:
                print(f"Updating saga document to CC with _id: {saga_document['_id']}")
                guild_id = saga_document["data"]["guildId"]

                platform_document = collection_platforms.find_one(
                    {"metadata.id": guild_id}, {"_id": 1}
                )

                if platform_document:
                    platform_id = str(platform_document["_id"])
                    saga_document["data"]["platformId"] = platform_id
                    del saga_document["data"]["guildId"]
                    collection_saga.update_one(
                        {"_id": saga_document["_id"]}, {"$set": saga_document}
                    )
                else:
                    print(f"Warning: No platforms for guildId: {guild_id}")
            else:
                print(
                    f"document is already updated with CC. _id: {saga_document['_id']}"
                )

        client.close()

    def downgrade(self):
        pass
