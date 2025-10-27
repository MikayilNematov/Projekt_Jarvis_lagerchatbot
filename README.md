# 🛠️ Jarvis Lagerbot - AI-Assistent

**Jarvis Lagerbot** är ett desktopbaserat system byggt i **Python** med **CustomTkinter** för GUI och **SQLite** som databas. Den fungerar som en AI-assistent för lagerhantering, med stöd för att:

- Söka produkter via namn eller artikelnummer.
- Uppdatera lagersaldo.
- Lägga till, ta bort och byta namn på produkter.
- Ändra lagerplats för produkter.
- Visa historik över lagersaldo.
- Visa produkter med låg lagerstatus och toppförsäljning.
- Skapa en enkel admin-roll med lösenord.

Projektet är färdigt att kompileras till en `.exe` med **PyInstaller**.

---

## 🧩 Funktioner

1. **Rollhantering:**  
   - Pop-up vid start som frågar efter användarroll (`user` eller `admin`).  
   - Admin kräver lösenord (`admin123` som standard).

2. **Produktinteraktion:**  
   - Sök efter produkter med `get_product_info`.
   - Uppdatera saldo med `update_product_stock`.
   - Flytta produkter med `change_product_location`.
   - Lägg till nya produkter med `add_new_product_and_stock`.
   - Ta bort produkter med `remove_product`.
   - Byt namn på produkter med `rename_product`.

3. **Historik och analys:**  
   - Få historik över lagersaldo (`get_product_history`).  
   - Lista produkter med låg lagerstatus (`get_low_stock_products`).  
   - Visa toppförsäljande produkter (`get_top_selling_products`).  

4. **GUI-funktioner:**  
   - Chattfönster med Jarvis som avsändare.  
   - Inputfält med Enter och Skicka-knapp.  
   - Trådhantering för respons utan att frysa GUI.  

5. **Loggning:**  
   - Alla aktiviteter loggas i `logs/elfirman.log`.  
   - Stöd för PyInstaller så att loggar sparas korrekt i `logs`-mappen.  

---

## ⚙️ Krav

- Python 3.11+  
- Bibliotek:  
  ```bash
  pip install customtkinter
  pip install numpy
  pip install pandas
  pip install sentence-transformers
  ```

## 🔑 Miljövariabler
```bash
Projektet använder en `.env`-fil för känslig information som API-nycklar. Skapa en fil i projektets rot med följande innehåll:
```
API KEY=din nyckel

## 🐍 Skapa virtuell miljö och installera dependencies
Kör Jarvis Lagerbot exakt som på utvecklingsmaskinen, följ dessa steg för att skapa en virtuell miljö och installera alla Python-paket:

# 🛠️ Jarvis Lagerbot - AI-Assistent

**Jarvis Lagerbot** är ett desktopbaserat system byggt i **Python** med **CustomTkinter** för GUI och **SQLite** som databas. Den fungerar som en AI-assistent för lagerhantering, med stöd för att:

- Söka produkter via namn eller artikelnummer.
- Uppdatera lagersaldo.
- Lägga till, ta bort och byta namn på produkter.
- Ändra lagerplats för produkter.
- Visa historik över lagersaldo.
- Visa produkter med låg lagerstatus och toppförsäljning.
- Skapa en enkel admin-roll med lösenord.

Projektet är färdigt att kompileras till en `.exe` med **PyInstaller**.

---

## 🧩 Funktioner

1. **Rollhantering:**  
   - Pop-up vid start som frågar efter användarroll (`user` eller `admin`).  
   - Admin kräver lösenord (`admin123` som standard).

2. **Produktinteraktion:**  
   - Sök efter produkter med `get_product_info`.
   - Uppdatera saldo med `update_product_stock`.
   - Flytta produkter med `change_product_location`.
   - Lägg till nya produkter med `add_new_product_and_stock`.
   - Ta bort produkter med `remove_product`.
   - Byt namn på produkter med `rename_product`.

3. **Historik och analys:**  
   - Få historik över lagersaldo (`get_product_history`).  
   - Lista produkter med låg lagerstatus (`get_low_stock_products`).  
   - Visa toppförsäljande produkter (`get_top_selling_products`).  

4. **GUI-funktioner:**  
   - Chattfönster med Jarvis som avsändare.  
   - Inputfält med Enter och Skicka-knapp.  
   - Trådhantering för respons utan att frysa GUI.  

5. **Loggning:**  
   - Alla aktiviteter loggas i `logs/elfirman.log`.  
   - Stöd för PyInstaller så att loggar sparas korrekt i `logs`-mappen.  

---

## ⚙️ Krav

- Python 3.11+  
- Bibliotek:  
  ```bash
  pip install customtkinter
  pip install numpy
  pip install pandas
  pip install sentence-transformers
  ```

## 🔑 Miljövariabler
```
Projektet använder en `.env`-fil för känslig information som API-nycklar. Skapa en fil i projektets rot med följande innehåll:
```
API KEY = din nyckel
(Glöm inte att döpa om .env.exemple till .env)
## 💻 Installation, virtuell miljö och körning

1️⃣ **Kloning av repo**

```bash
git clone <repo-url>
cd DEMO10
```

2️⃣ Skapa en virtuell miljö
```bash
python -m venv venv_311  # skapa virtual environment
```

3️⃣ Aktivera den virtuella miljön

Windows (CMD):
```bash
.\venv_311\Scripts\activate
```
4️⃣ Installera dependencies

Om du har en requirements.txt i projektet, kör:
```bash
pip install -r requirements.txt
```

5️⃣ Kompilera till exe med PyInstaller:

```bash
pyinstaller --onefile --windowed --icon=assets/Jarvis.ico main.py
```

## 🛠️ Bygga exe med PyInstaller med spec-fil
**OBS!**  
   - Byt namn på "main.spec" till "lagerbot.spec"

Om du vill bygga exe själv kan du använda den medföljande lagerbot.spec:
```bash
pyinstaller lagerbot.spec
```

## 📂 Projektstruktur
```
DEMO10/
│
├── assets/
│   └── Jarvis.ico
│
├── data/
│   ├── docs.txt
│   └── index.faiss
│
├── logs/
│   └── elfirman.log
│
├── src/
│   ├── ai/
│   │   ├── forecast.py
│   │   ├── rag.py
│   │   └── __init__.py
│   │
│   ├── chatbot/
│   │   ├── bot.py
│   │   ├── commands.py
│   │   ├── gui.py
│   │   └── __init__.py
│   │
│   ├── database/
│   │   ├── db.py
│   │   └── __init__.py
│   │
│   ├── utils/
│   │   ├── config.py
│   │   ├── logger.py
│   │   └── __init__.py
│   │  
│   └── __init__.py
│
├── Elfirman.db
├── main.py
├── lagerbot.spec
└── venv_311/
```

## 🔐 Standardlösenord

Admin: admin123

OBS: Byt lösenord i src/utils/config.py innan produktion.

## 📝 Exempel på användning

Sök produkt:

```python
from src.database.db import get_product_info
info = get_product_info("Produktnamn")
print(info)
```

Uppdatera lager:

```python
from src.database.db import update_product_stock
update_product_stock("Produktnamn", 25)
```

Lägg till produkt:

```python
from src.database.db import add_new_product_and_stock
add_new_product_and_stock("Ny Produkt", 50, "Hyllplats A")
```

Visa historik:

```python
from src.database.db import get_product_history
history = get_product_history("Produktnamn")
print(history)
```


1️⃣ Skapa en virtuell miljö
```bash
cd /sökväg/till/DEMO10   # byt till projektets huvudmapp
python -m venv venv_311  # skapa virtual environment
```
2️⃣ Aktivera den virtuella miljön

Windows (CMD):
```bash
.\venv_311\Scripts\activate
```
3️⃣ Installera dependencies

Om du har en requirements.txt i projektet, kör:
```bash
pip install -r requirements.txt
```

## 💻 Installation & Körning

Kloning av repo:

```bash 
git clone <repo-url>
cd DEMO10
```



Kompilera till exe med PyInstaller:

```bash
pyinstaller --onefile --windowed --icon=assets/Jarvis.ico main.py
```

## 🛠️ Bygga exe med PyInstaller med spec-fil
**OBS!**  
   - Byt namn på "main.spec" till "lagerbot.spec"

Om du vill bygga exe själv kan du använda den medföljande lagerbot.spec:
```bash
pyinstaller lagerbot.spec
```

## 📂 Projektstruktur
```
DEMO10/
│
├── assets/
│   └── Jarvis.ico
│
├── data/
│   ├── docs.txt
│   └── index.faiss
│
├── logs/
│   └── elfirman.log
│
├── src/
│   ├── ai/
│   │   ├── forecast.py
│   │   ├── rag.py
│   │   └── __init__.py
│   │
│   ├── chatbot/
│   │   ├── bot.py
│   │   ├── commands.py
│   │   ├── gui.py
│   │   └── __init__.py
│   │
│   ├── database/
│   │   ├── db.py
│   │   └── __init__.py
│   │
│   ├── utils/
│   │   ├── config.py
│   │   ├── logger.py
│   │   └── __init__.py
│   │  
│   └── __init__.py
│
├── Elfirman.db
├── main.py
├── lagerbot.spec
└── venv_311/
```

## 🔐 Standardlösenord

Admin: admin123

OBS: Byt lösenord i src/utils/config.py innan produktion.

## 📝 Exempel på användning

Sök produkt:

```python
from src.database.db import get_product_info
info = get_product_info("Produktnamn")
print(info)
```

Uppdatera lager:

```python
from src.database.db import update_product_stock
update_product_stock("Produktnamn", 25)
```

Lägg till produkt:

```python
from src.database.db import add_new_product_and_stock
add_new_product_and_stock("Ny Produkt", 50, "Hyllplats A")
```

Visa historik:

```python
from src.database.db import get_product_history
history = get_product_history("Produktnamn")
print(history)
```
---

### 💾 Ladda ner färdig .exe
Om du bara vill testa programmet direkt utan att kompilera:
[Ladda ner Jarvis.exe här](https://drive.google.com/file/d/1kk0Hc0PvQsHqtieGmwdeLLR1wX68Mfmc/view?usp=drive_link)
