## EC2 Instance Setup

Currently we are running the complete service on one EC2 instance (bad practice, but cheap). As we move forward, we will need to distribute the application components across severall instances in order to meet the requirements of a true production system.

This tutorial show you how to launch an EC2 instance and run the complete service on it.

1. Launch an instance

https://eu-central-1.console.aws.amazon.com/ec2

Recommendation:

| Characteristic | Value |
|-|-|
| AMI | Ubuntu |
| Instance | r5.large |
| Key pair | generate or use existing |
| Network | Create security group |
| Allow SSH traffic from | Anywhere |
| Allow HTTPS traffic | true |
| Allow HTTP traffic | true |
| Storage | 15 GiB gp3 |

2. Install docker

We will be running the services using docker compose. For this, we need to install .

You will need to connect to your instance using SSH.

Use these instructions: https://docs.docker.com/engine/install/ubuntu/

3. Manage docker as a non-root user

```bash
sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker
```

3. Clone repositories

```bash
cd ~
git clone https://github.com/RnDAO/tc-operation.git
git clone https://github.com/RnDAO/tc-serverComm.git
git clone https://github.com/RnDAO/tc-discordBot.git
```

4. Create environment variables

Using the *.sample file in: 

- https://github.com/RnDAO/tc-operation/tree/main/production
- https://github.com/RnDAO/tc-operation/tree/main/production/redis

Create the files with the production values in the following directory.

```bash
# development
cd tc-operations/development
# production
cd tc-operations/production
```

5. Start services

```bash
docker compose up -d
```

6. Restart services

It takes a minute or two for Neo4J to start, you will need to restart the discord-analyzer-worker once this is done.

```bash
docker compose restart server-comm-prod discord-analyzer-worker-prod
```

Now our services are running internally, but they are not available externally. For this, we need nginx.

7. Install nginx

https://www.digitalocean.com/community/tutorials/how-to-install-nginx-on-ubuntu-22-04

8. Install certbot

https://www.digitalocean.com/community/tutorials/how-to-secure-nginx-with-let-s-encrypt-on-ubuntu-22-04

9. Service Access (optional)

If you want to have access to MongoDB, Neo4J, or RabbitMQ, you will need to go into your instance security group and edit it. You will need to make the ports available (see docker-compose.yml for ports).