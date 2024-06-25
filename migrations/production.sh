#!/bin/bash

declare -a production_volumes
declare -a monitoring_volumes
declare -a production_paths
declare -a monitoring_paths

production_volumes=(
  mongodb_data_container
  rmq_data_container
  neo4j_data
  neo4j_import
  neo4j_plugins
  neo4j_conf
)

monitoring_volumes=(
  grafana_volume
  prometheus_volume
  loki_volume
)

production_paths=(
  /data/db/
  /var/lib/rabbitmq/
  /data/
  /import/
  /plugins/
)

monitoring_paths=(
  /var/lib/grafana/
  /prometheus/
  /data/loki/
)

run() {
  volumes=$1
  paths=$2
  prepend=$3

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

      echo Migrating...
      docker run --rm -v $prepend_$volume:$path -v compose_$volume:/backup ubuntu cp -a $path /backup
      echo Completed
    done
  fi
}

run $monitoring_volumes $monitoring_paths monitoring

echo Finished