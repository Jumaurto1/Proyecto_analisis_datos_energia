#!/bin/bash
# Levanta el notebook con Voila usando template gridstack y configuración de recursos

# Definir puerto, por si no está en $PORT
PORT=${PORT:-8888}

# Ejecutar Voila con template gridstack y theme dark
exec voila Proyecto_Bootcamp.ipynb \
     --template=gridstack \
     --VoilaConfiguration.resources="{'gridstack': {'show_handles': True}}" \
     --Voila.theme=dark \
     --port=$PORT \
     --no-browser \
     --Voila.ip=0.0.0.0
