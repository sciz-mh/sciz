#!/bin/bash

if [ "$#" -eq 0 ]; then
  echo "Donner la version !"
  exit
fi
set -x
mv /sciz/logs/sciz_updater.log /sciz/logs/sciz_updater.log.$1
mv /sciz/logs/sciz_walker.log  /sciz/logs/sciz_walker.log.$1
mv /sciz/logs/sciz.log         /sciz/logs/sciz.log.$1
mv /sciz/logs/sciz_server.log  /sciz/logs/sciz_server.log.$1
mv /sciz/logs/maintenance.log  /sciz/logs/maintenance.log.$1

