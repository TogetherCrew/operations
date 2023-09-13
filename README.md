# operations
This repository houses a collection of code artifacts, including Github actions, Github workflows, and essential docker-compose files. These resources are instrumental in facilitating efficient and automated staging and production deployments.

## Running on docker

## Localhost

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
- You should see your traefik dashboard.

## Server w/ Cloudflare Origin Certificates

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
- You should see your traefik dashboard.