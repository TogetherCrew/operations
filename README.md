# operations
This repository houses a collection of code artifacts, including Github actions, Github workflows, and essential docker-compose files. These resources are instrumental in facilitating efficient and automated staging and production deployments.

## Running on docker

## Localhost

1. Install [mkcert](https://github.com/FiloSottile/mkcert)
2. If its the first mkcert install, run `mkcert -install`
3. `mkdir certs`
4. `mkcert -cert-file certs/local-cert.pem -key-file certs/local-key.pem "docker.localhost" "*.docker.localhost"`

## Server