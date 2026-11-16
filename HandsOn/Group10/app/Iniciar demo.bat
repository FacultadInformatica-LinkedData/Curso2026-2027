@echo off
cd /d "%~dp0"
echo Abriendo Meteo Madrid KG en http://localhost:8000
echo Deja esta ventana abierta durante la demo. Para cerrar: Ctrl+C
start "" http://localhost:8000/index.html
py -m http.server 8000
