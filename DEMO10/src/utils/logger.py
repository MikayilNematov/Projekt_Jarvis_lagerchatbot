import logging
import sys
import os 
from pathlib import Path

#Hittar basmapp 
if getattr(sys, 'frozen', False):
#Använder sys.executable för att få sökvägen till EXE-filen
#Detta pekar på den mapp där .exe-filen ligger 
    BASE_DIR = Path(os.path.dirname(sys.executable)) 
else: 
#Körs som vanlig Python-kod 
    BASE_DIR = Path(__file__).resolve().parent.parent.parent

#Logs-mapp 
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True) #Skapar logs-mappen om den inte finns

#Loggfil
LOG_FILE = LOG_DIR / "elfirman.log"

#Konfigurera loggning
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO, #INFO loggar kommandon, ERROR loggar fel
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

#Enkel funktion för loggning
def log_info(message: str):
    logging.info(message)

def log_error(message: str):
    logging.error(message)

def log_warning(message: str):
    logging.warning(message)
