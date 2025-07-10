# operations
This repository houses a collection of code artifacts, including Github actions, Github workflows, and essential docker-compose files. These resources are instrumental in facilitating efficient and automated staging and production deployments.

## Running on docker

1. `cd compose`
2. In the `/redis` folder, create a random password for each redis service (replace `PASSWORD`). See `/redis/example.*.conf` files for required inputs.
3. Configure the environments for each service by creating your `.env.*` files. See `example.env.*` files for required inputs.
4. Create replica.key for mongodb:
```sh
openssl rand -base64 756 > mongo/replica.key # create replica.key
chmod 400 mongo/replica.key # read-only
sudo chown 999:999 mongo/replica.key # change ownership
```
5. On Github generate a app and get the private key, place it in a file `github/githubapp.private-key.pem`.
6. Create an origin certificate on Cloudflare. Place both the .pem and .key files in the `/nginx/ssl` (make sure their name is the same as the `DOMAIN` in `.env.nginx`).
7. Allocate memswap:
```bash
free -h                           # Check Existing Swap Space

sudo fallocate -l 32G /swapfile   # Create a 32GB swap file
sudo chmod 600 /swapfile          # Set the correct permissions
sudo mkswap /swapfile             # Set up the swap file
sudo swapon /swapfile             # Enable the swap file

# Verify Swap Space
swapon --show
free -h

# Persist the Swap File
echo '/swapfile swap swap defaults 0 0' | sudo tee -a /etc/fstab
```
6. Run `docker compose up -d`


<!-- ## Localhost

- Create a `.env` file with `HOST_NAME=docker.localhost`. See [.env.example](/.env.example).
- Generate a basic auth for a user using: `echo $(htpasswd -nB user)`
- Create a `userFile` file and paste the basic auth you generated. See [userFile.example](/userFile.example).
- Install [mkcert](https://github.com/FiloSottile/mkcert).
- If its the first mkcert install, run `mkcert -install`.
- Create the `/certs` folder using `mkdir certs`.
- Generate your origin certificates: `mkcert -cert-file certs/origin-cert.pem -key-file certs/origin-key.pem "docker.localhost" "*.docker.localhost"`
- Start docker: `docker compose up -d`
- Head over to [traefik.docker.localhost](https://traefik.docker.localhost)
- Enter the user and password from the basic auth.
- You should see your traefik dashboard. -->

<!-- ## Server w/ Cloudflare Origin Certificates

- Login to your server
- [Install Docker Engine with Ubuntu](https://docs.docker.com/engine/install/ubuntu/)
- Clone the repository. `git clone https://github.com/TogetherCrew/operations`
- Go into the folder: `cd operations`
- Create a `.env` file with `HOST_NAME=yourdomain.com`. See [.env.example](/.env.example).
- Generate a basic auth for a user using: `echo $(htpasswd -nB user)`. See [userFile.example](/userFile.example).
- Create a `userFile` file and paste the basic auth you generated. You can add multiple.
- Go to Cloudflare -> Your Domain -> SSL/TLS -> Origin Server, and Create Certificates.
- Create the `/certs` folder using `mkdir certs`.
- Create a file named `origin-cert.pem` and paste the Origin Certificate from Cloudflare.
- Create a file named `origin-key.pem` and paste the Origin Key from Cloudflare.
- Configure your DNS. For example:
|Type|Name|Content|Proxy status|TTL|
|-|-|-|-|-|
|A|yourdomain.com|123.456.789|True|Auto|
|CNAME|traefik|@|True|Auto|
- Start docker: `docker compose up -d`
- Head over to traefik.*yourdomain.com*
- Enter the user and password from the basic auth.
- You should see your traefik dashboard. -->

## Running Neo4j migrations

- Install [neo4j-migrations](https://michael-simons.github.io/neo4j-migrations/2.2.2/#cli) tool
- Create a file `.migrations.properties` under the db folder for neo4j based on `.migrations.properties.example`
- run the `neo4j-migrations apply` within `db` directory (the directory containing the `.migrations.properties`) to run neo4j migrations

## Running MongoDB migrations

- Install [mongodb-migrations](https://pypi.org/project/mongodb-migrations/) tool
- Change directory to `db/mongo`
- Create a `config.ini` file based on the `config.ini.example`
- run the command `mongodb-migrate` within the directory you are in

## Running Qdrant migrations

Qdrant migration scripts handle various data migration tasks including renaming collections and transferring data between different storage systems.

### V001: Collection rename migration

This migration renames Qdrant collections from `[communityId]_[platformName]` format to `[communityId]_[platformId]` format.

1. Install the required dependencies:

   ```bash
   cd db/qdrant
   pip install -r v001_requirements.txt
   ```

2. Set up environment variables by creating a `.env` file based on `.env.v001.example` file

3. Run the migration script:

   ```bash
   cd db/qdrant
   python V001_collection_names.py
   ```

The script will:

- Identify collections that match the pattern `[communityId]_[platformName]`
- Look up the corresponding platformId in MongoDB
- Create new collections with names in the format `[communityId]_[platformId]`
- Transfer all data from the old collections to the new ones

### V002: Discord PostgreSQL to Qdrant migration

This migration moves Discord data from PostgreSQL vector storage to Qdrant vector storage, including both regular Discord messages and Discord summaries.

1. Install the required dependencies:

   ```bash
   cd db/qdrant
   pip install -r v002_requirements.txt
   ```

2. Set up environment variables by creating a `.env` file based on `.env.v002.example` file

3. Run the migration script:

   ```bash
   cd db/qdrant
   python V002_migrate_discord_pgvector.py --community-id COMMUNITY_ID --platform-id PLATFORM_ID
   ```

   Optional flags:
   - `--dry-run`: Run in dry-run mode to preview the migration without actually transferring data

The script will:

- Connect to the PostgreSQL database for the specified community
- Retrieve Discord messages and summaries with their embeddings
- Transfer all data to Qdrant collections using the specified platform ID
- Create separate collections for regular messages and summaries (`platform_id` and `platform_id_summary`)

## Creating a .htpasswd file

```bash
cd /nginx/htpasswd/
htpasswd -c .htpasswd username
```
