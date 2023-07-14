1. Add code to `/etc/docker/daemon.json`.

```json
{
  "metrics-addr": "127.0.0.1:9323"
}
```

2. Add Grafana Loki Docker driver:

https://grafana.com/docs/loki/latest/clients/docker-driver/

3. Restart docker