#!/bin/bash
# Levanta el notebook con Voila usando template gridstack y configuración de recursos
voila --template=gridstack Proyecto_Bootcamp.ipynb \
      --VoilaConfiguration.resources="{'gridstack': {'show_handles': True}}" \
      --port $PORT --no-browser --Voila.ip=0.0.0.0
