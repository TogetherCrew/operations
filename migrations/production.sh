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
  volume=$1
  prepend=$2
  echo "######################################"
  echo $volume
  echo docker run --rm -v "${prepend}_${volume}":/source -v compose_$volume:/target ubuntu cp -av source/. target
  echo "######################################"

  echo Migrating...
  docker run --rm -v "${prepend}_${volume}":/source -v compose_$volume:/target ubuntu cp -av source/. target
  echo Completed
}

length=${#monitoring_volumes[@]}
for ((i=1; i<=length; i++)); do
  j=i-1
  run ${volumes[$j]} "monitoring"
end

echo Finished