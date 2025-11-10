# config.py
# === CONFIGURACIÓN DEL PROYECTO BIBLIOMETRÍA-IA-GRAFOS-UQ-2025 ===

import platform
from pathlib import Path

# === 1. DETECTAR SISTEMA OPERATIVO ===
SO = platform.system()

# === 2.  DEFINIR RUTA BASE DEL PROYECTO ===
if SO == "Windows":
    # 🧩 Ruta base del proyecto (ajustar según el usuario en Windows)
    BASE_DIR = Path(
        r"C:\Users\USER\Desktop\YAN\Carpeta Universidad\decimo-semestre\Analisis-de-algoritmos\Proyecto-final-algoritmos"
    )
else:
    # 🧩 Ruta base del proyecto en Linux (tu caso actual)
    BASE_DIR = Path("/home/ycmejia/Escritorio/PROYECTO_ALGORITMOS")

# === 3. CONFIGURAR CHROMEDRIVER ===
if SO == "Windows":
    CHROMEDRIVER_PATH = BASE_DIR / "chromedriver.exe"
else:
    # En Linux se suele instalar con: sudo apt install chromium-chromedriver
    CHROMEDRIVER_PATH = Path("/usr/bin/chromedriver")

# === 4. RUTAS DE DESCARGAS Y SALIDAS ===
DOWNLOAD_DIR_SAGE = BASE_DIR / "bases_de_datos" / "Sage_Journals"
DOWNLOAD_DIR_SCIENCEDIRECT = BASE_DIR / "bases_de_datos" / "Science_Direct"
OUTPUT_DIR_BIBLIO = BASE_DIR / "salidas"

# Crear directorios si no existen
for path in [DOWNLOAD_DIR_SAGE, DOWNLOAD_DIR_SCIENCEDIRECT, OUTPUT_DIR_BIBLIO]:
    path.mkdir(parents=True, exist_ok=True)

# === 5. URLS IMPORTANTES ===
URL_LOGIN = "https://library.uniquindio.edu.co/databases"
SCIENCEDIRECT_URL = "https://www-sciencedirect-com.crai.referencistas.com/"

# === 6. CREDENCIALES DE ACCESO (UQ) ===
USUARIO = "yarleyc.mejiab@uqvirtual.edu.co"
CONTRASENA = "Familia967vfg15a"
