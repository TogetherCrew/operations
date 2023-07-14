1. Launch a Ubuntu instance
2. Install Docker Engine on Ubuntu: https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository
3. Manage Docker as a non-root user: https://docs.docker.com/engine/install/linux-postinstall/
4. Install Grafana Loki Docker driver: https://grafana.com/docs/loki/latest/clients/docker-driver/
5. Clone this repository: `git clone https://github.com/TogetherCrew/operations/`
6. Go to directory: `cd operations/deployment`
7. Launch services: `docker compose -f docker-compose.monitoring.yml up -d`

Notes
- Make sure port 4000 is available on the instances