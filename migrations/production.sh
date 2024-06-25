#!/bin/bash

declare -a production_volumes
declare -a monitoring_volumes

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

run() {
  volumes=$1
  prepend=$3

  echo $volumes
  echo $prepend

  volume_length=${#volumes[@]}
  echo $volume_length

  # Loop x times
  for ((i=1; i<=volume_length; i++)); do
    j=i-1
    volume=${volumes[$j]}
    echo "######################################"
    echo "######################################"
    echo "######################################"
    echo $volume
    echo "######################################"
    echo "######################################"
    echo "######################################"

    echo docker run --rm -v "${prepend}_${volume}":/source -v compose_$volume:/target ubuntu cp -av source/. target

    echo Migrating...
    docker run --rm -v "${prepend}_${volume}":/source -v compose_$volume:/target ubuntu cp -av source/. target
    echo Completed
  done
}

run $monitoring_volumes "monitoring"

echo Finished