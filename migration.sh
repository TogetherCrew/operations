#!/bin/bash

# call file using the following:
# ./migration.sh YOUR_PEM_PATH SOURCE_SERVER_URI

# Load env vars
pem=$1
source=$2

echo pem: $pem
echo source: $source

# Declare arrays
declare -a volumes
declare -a paths

# source volume
volumes=(
  mongodb_data_container
  rmq_data_container
  neo4j_data
  neo4j_import
  neo4j_plugins
  grafana_volume
  prometheus_volume
  loki_volume
  # pgvector_data
  airflow_config
  airflow_logs
  airflow_plugins
  airflow_sources
  tempo_data
  qdrant_data
  qdrant_snapshots
)

# target path
paths=(
  /data/db/
  /var/lib/rabbitmq/
  /data/
  /import/
  /plugins/
  /var/lib/grafana/
  /prometheus/
  /data/loki/
  # /var/lib/postgresql/data/
  /opt/airflow/config/
  /opt/airflow/logs/
  /opt/airflow/plugins/
  /sources/
  /tmp/tempo/
  /qdrant/storage/
  /qdrant/snapshots/
)

# Get the length of the arrays
volume_length=${#volumes[@]}
paths_length=${#paths[@]}

# Compare the lengths
if [ $volume_length -ne $paths_length ]; then
  echo "diff length! $volume_length $paths_length"
else
  # Loop x times
  for ((i=1; i<=volume_length; i++)); do
    j=i-1
    volume=${volumes[$j]}
    path=${paths[$j]}
    echo "######################################"
    echo "######################################"
    echo "######################################"
    echo $volume, $path
    echo "######################################"
    echo "######################################"
    echo "######################################"

    echo 1. Downloading...
    ssh -i "$pem" $source "sudo docker run --rm -v development_$volume:$path ubuntu tar -cvf - -C $path ." > ./backup/$volume.tar
    
    # echo 2. Migrating...
    # docker run --rm -v compose_$volume:$path -v ./backup:/backup ubuntu bash -c "cd $path && tar -xvf ../../backup/$volume.tar --strip 1"
    
    # echo 3. Deleting .tar
    # rm ./backup/$volume.tar

    echo 4. Completed
  done
fi