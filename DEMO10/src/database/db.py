import sqlite3
import os
import sys
from src.utils.logger import log_info, log_error, log_warning
from datetime import datetime 

#Kolumnnamn
COL_NAME = "Namn" 
COL_STOCK = "Antal" 
COL_LOCATION = "Lagerplats" 
COL_PRODID = "ProduktID" 
COL_ARTICLENUMBER = "Artikelnummer" 
COL_TIME = "timestamp" 

#Tabellnamn
PRODUCTS_TABLE = "Produkter"
STOCK_TABLE = "Lager"
HISTORY_TABLE = "Produkt_historik" 

#Beräknar sökvägen till projektets rotmapp
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATABASE_PATH_DEV = os.path.join(PROJECT_ROOT, 'Elfirman.db')

def _initialize_database(conn):
    """
    Kritisk funktion: Säkerställer att alla nödvändiga tabeller existerar.
    Lägger även till initial historik om tabellen är tom (behövs för prognos).
    """
    cursor = conn.cursor()
    
    #Skapar Produkt_historik-tabellen om den inte finns
    try:
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {HISTORY_TABLE} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                date TEXT NOT NULL,
                quantity INTEGER NOT NULL
            );
        """)
        conn.commit()
        log_info(f"Säkerställde att tabellen '{HISTORY_TABLE}' existerar.")
    except sqlite3.Error as e:
        log_error(f"Kritiskt SQLite fel vid initiering av {HISTORY_TABLE}: {e}")
        return 

    #Kontrollera om historiktabellen är tom
    cursor.execute(f"SELECT COUNT(*) FROM {HISTORY_TABLE}")
    count = cursor.fetchone()[0]
    
    if count == 0:
        log_warning("Produkt_historik är tom. Fyller med initiala saldon från Lager.")
        
        #Hämtar alla produkter och deras nuvarande lagerstatus
        cursor.execute(f"""
            SELECT p.{COL_NAME}, l.{COL_STOCK} 
            FROM {PRODUCTS_TABLE} p
            INNER JOIN {STOCK_TABLE} l ON p.{COL_PRODID} = l.{COL_PRODID}
        """)
        initial_products = cursor.fetchall()

        #Lägger till varje produkt i historiken med dagens datum
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        #Använder p.product_name och l.stock_count som alias (ROW[0], ROW[1] i SQL-resultatet)
        insert_data = [(row[0], current_date, row[1]) for row in initial_products] 
        
        try:
            cursor.executemany(f"""
                INSERT INTO {HISTORY_TABLE} (product_name, date, quantity) 
                VALUES (?, ?, ?)
            """, insert_data)
            conn.commit()
            log_info(f"Initiala {len(initial_products)} produkter lades till i historiken.")
        except sqlite3.Error as e:
            log_error(f"Fel vid fyllning av initial historik: {e}")
    else:
        log_info(f"Produkt_historik har redan {count} poster. Ingen initial fyllning behövs.")


def get_db_connection():
    """
    Hanterar databasanslutning för både utveckling och PyInstaller (.exe).
    """
    if getattr(sys, 'frozen', False):
        #Ansluter till originalfilen
        db_path = r'C:\Users\Admin\Desktop\DEMO10\Elfirman.db'
    else:
        #Använder relativ sökväg i projektet
        db_path = DATABASE_PATH_DEV

    log_info(f"Försöker ansluta till databas: {db_path}") 
    
    if not os.path.exists(db_path):
        log_error(f"FATAL: Databasfilen hittades INTE på förväntad sökväg: {db_path}")
        raise FileNotFoundError(f"Databasfilen hittades inte. Sökväg: {db_path}")
        
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row 
        
        #Initierar databasstrukturen (inklusive initial fyllning)
        _initialize_database(conn)
        
        return conn
    except sqlite3.Error as e:
        log_error(f"Kritiskt SQLite fel vid anslutning: {e}")
        raise ConnectionError(f"Kunde inte ansluta till databasen: {e}")

def get_product_info(product_name):
    """
    Hämtar produktinformation (Namn, Antal, Lagerplats) baserat på produktnamn eller artikelnummer.
    """
    try:
        conn = get_db_connection()
    except Exception as e:
        log_error(f"Anslutning misslyckades vid get_product_info: {e}")
        raise ConnectionError(f"Kunde inte ansluta till databasen: {e}")
    
    cursor = conn.cursor()
    p_lower = product_name.lower()
    
    #Använder INNER JOIN och söker i både namn och artikelnummer
    cursor.execute(f"""
        SELECT 
            p.{COL_NAME} AS name, 
            l.{COL_STOCK} AS stock, 
            l.{COL_LOCATION} AS location
        FROM {PRODUCTS_TABLE} p
        INNER JOIN {STOCK_TABLE} l ON p.{COL_PRODID} = l.{COL_PRODID}
        WHERE LOWER(p.{COL_NAME}) = LOWER(?)
        OR LOWER(p.{COL_NAME}) LIKE ?
        OR p.{COL_ARTICLENUMBER} = ?  -- NY SÖKNING PÅ ARTIKELNUMMER
    """, (p_lower, '%' + p_lower + '%', product_name)) 
    
    matched_products = cursor.fetchall()
    conn.close()

    if len(matched_products) == 1:
        return matched_products[0]
    elif len(matched_products) > 1:
        raise ValueError(f"Tvetydig sökning efter '{product_name}'. Vänligen specificera.") 
    else:
        raise ValueError(f"Produkt '{product_name}' hittades inte i lagret.")
    
def get_product_history(product_name):
    """Hämtar historik (datum och lagersaldo) för en specifik produkt."""
    try:
        conn = get_db_connection()
    except Exception:
        return []
        
    cursor = conn.cursor()
    
    #Hittar exakt namn från Produkter baserat på användarens inmatning
    cursor.execute(f"""
        SELECT {COL_NAME} 
        FROM {PRODUCTS_TABLE} 
        WHERE LOWER({COL_NAME}) = LOWER(?) 
        OR LOWER({COL_NAME}) LIKE ?
        OR {COL_ARTICLENUMBER} = ?
    """, (product_name.lower(), '%' + product_name.lower() + '%', product_name))
    
    matched_products = cursor.fetchall()

    if not matched_products or len(matched_products) > 1:
        #Stoppar om ingen match eller tvetydig match (returnerar tom lista)
        conn.close()
        return []
        
    #Använder det exakta namnet för sökning i historiktabellen
    exact_name = matched_products[0][COL_NAME]

    #Hämtar historik baserat på det exakta produktnamnet, sorterat efter datum (senaste sist)
    cursor.execute(f"""
        SELECT date, quantity 
        FROM {HISTORY_TABLE} 
        WHERE product_name = ? 
        ORDER BY date ASC
    """, (exact_name,))
    
    history = cursor.fetchall()
    conn.close()
    return [dict(row) for row in history] #Konverterar till lista av dicts för enkel användning
    
def update_product_stock(product_name, new_stock):
    """
    KRITISK FUNKTION: 
    1. Uppdaterar lagersaldo i Lager-tabellen.
    2. Loggar transaktionen (det nya saldot) i Produkt_historik-tabellen.
    """
    log_info(f"Försöker uppdatera '{product_name}' till {new_stock} st.")
    try:
        conn = get_db_connection()
    except Exception as e:
        log_error(f"Databasanslutning misslyckades: {e}")
        raise ValueError(f"Kunde inte ansluta till databasen för uppdatering: {e}")
        
    cursor = conn.cursor()
    
    #Hitta ProduktID och exakt namn
    cursor.execute(f"""
        SELECT {COL_PRODID}, {COL_NAME} 
        FROM {PRODUCTS_TABLE} 
        WHERE LOWER({COL_NAME}) = LOWER(?) 
        OR LOWER({COL_NAME}) LIKE ?
        OR {COL_ARTICLENUMBER} = ?
    """, (product_name.lower(), '%' + product_name.lower() + '%', product_name))
    matched_products = cursor.fetchall()

    if len(matched_products) == 1:
        product_id = matched_products[0][COL_PRODID]
        exact_name = matched_products[0][COL_NAME]
        
        #Uppdatera Antal i tabellen Lager, kopplat till ProduktID
        cursor.execute(f"UPDATE {STOCK_TABLE} SET {COL_STOCK} = ? WHERE {COL_PRODID} = ?", (new_stock, product_id))
        
        #Logga transaktion i Produkt_historik
        cursor.execute(f"INSERT INTO {HISTORY_TABLE} (product_name, date, quantity) VALUES (?, DATE('now'), ?)", (exact_name, new_stock))
        
        conn.commit()
        conn.close()
        log_info(f"Uppdatering lyckades för '{exact_name}'. Nytt saldo: {new_stock}. Historik loggad.")
        return exact_name
    elif len(matched_products) > 1:
        conn.close()
        log_warning(f"Tvetydig sökning för: {product_name}")
        raise ValueError("Tvetydig produkt. Uppdateringen avbröts. Var vänlig specificera produktnamnet mer exakt.")
    else:
        conn.close()
        log_warning(f"Produkt hittades inte: {product_name}")
        raise ValueError(f"Produkt '{product_name}' hittades inte.")


def add_new_product_and_stock(product_name, initial_stock, location, specifications="", article_number="", category_id=1, supplier_id=1, unit="st"):
    """
    Lägger till en ny produkt i Produkter-tabellen och skapar en motsvarande
    rad i Lager-tabellen.
    """
    log_info(f"Försöker lägga till ny produkt: {product_name} med {initial_stock} st på {location}.")

    if initial_stock < 0:
        raise ValueError("Initialt saldo måste vara noll (0) eller positivt.")

    try:
        conn = get_db_connection()
    except Exception as e:
        log_error(f"Databasanslutning misslyckades vid tillägg av produkt: {e}")
        raise ValueError("Kunde inte ansluta till databasen för att lägga till produkt.")

    cursor = conn.cursor()

    try:
        #Kontrollerar om produkten redan finns ELLER om artikelnumret redan används
        cursor.execute(f"SELECT {COL_NAME} FROM {PRODUCTS_TABLE} WHERE LOWER({COL_NAME}) = LOWER(?) OR {COL_ARTICLENUMBER} = ?", 
                       (product_name, article_number))
        if cursor.fetchone():
            conn.close()
            raise ValueError(f"Produktnamn '{product_name}' eller Artikelnummer '{article_number}' existerar redan i databasen.")

        #INSERT i Produkter-tabellen 
        cursor.execute(f"""
            INSERT INTO {PRODUCTS_TABLE} ({COL_NAME}, Specifikationer, Artikelnummer, KategoriID, LeverantorID, Enhet) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (product_name, specifications, article_number, category_id, supplier_id, unit))

        #Hämtar det senast infogade ProduktID
        new_product_id = cursor.lastrowid
        if not new_product_id:
            raise Exception("Kunde inte hämta det nya ProduktID:t efter infogning i Produkter.")

        #INSERT i Lager-tabellen, med det nya ProduktID:t
        cursor.execute(f"""
            INSERT INTO {STOCK_TABLE} ({COL_PRODID}, {COL_STOCK}, {COL_LOCATION}) 
            VALUES (?, ?, ?)
        """, (new_product_id, initial_stock, location))

        #Logga initialt saldo i Produkt_historik
        cursor.execute(f"""
            INSERT INTO {HISTORY_TABLE} (product_name, date, quantity) 
            VALUES (?, DATE('now'), ?)
        """, (product_name, initial_stock))

        #Slutför transaktionen (MÅSTE ske efter alla inserts)
        conn.commit()
        log_info(f"Produkten {product_name} (ID: {new_product_id}) lades till framgångsrikt i Lager och Historik.")
        return product_name

    except sqlite3.Error as e:
        conn.rollback()
        log_error(f"SQLite fel vid tillägg av produkt: {e}")
        raise ValueError(f"Databasfel: Kunde inte lägga till produkten ({e}).")
    finally:
        conn.close()


def get_low_stock_products(threshold=10):
    """Hämtar en lista över alla produkter med lagersaldo under en given tröskel."""
    try:
        conn = get_db_connection()
    except Exception:
        return []

    cursor = conn.cursor()
    
    #Använder INNER JOIN mellan Produkter (p) och Lager (l) på ProduktID
    cursor.execute(f"""
        SELECT 
            p.{COL_NAME} AS name, 
            l.{COL_STOCK} AS stock, 
            l.{COL_LOCATION} AS location
        FROM {PRODUCTS_TABLE} p
        INNER JOIN {STOCK_TABLE} l ON p.{COL_PRODID} = l.{COL_PRODID}
        WHERE l.{COL_STOCK} <= ?
    """, (threshold,))
    
    products = cursor.fetchall()
    conn.close()
    
    #Returnerar en lista av dicts för enkel hantering i commands.py
    return [dict(p) for p in products]

def get_top_selling_products(limit=5):
    """
    Beräknar och returnerar de N (limit) produkter som haft störst nettouttag 
    (minskat saldo) över hela den tillgängliga historiken.
    """
    try:
        conn = get_db_connection()
    except Exception:
        return []

    cursor = conn.cursor()
    
    #Kärnlogik SQL-fråga beräknar den totala minskningen i saldo per produkt.
    cursor.execute(f"""
        WITH StockChanges AS (
            SELECT
                product_name,
                quantity,
                -- Hämta föregående saldo för samma produkt, sorterat efter datum
                LAG(quantity, 1, quantity) OVER (
                    PARTITION BY product_name 
                    ORDER BY date
                ) AS previous_quantity
            FROM {HISTORY_TABLE}
        )
        -- Summera den totala förbrukningen (endast när saldot har minskat)
        SELECT
            product_name AS name,
            SUM(CASE 
                WHEN quantity < previous_quantity THEN previous_quantity - quantity 
                ELSE 0 
            END) AS total_consumption
        FROM StockChanges
        GROUP BY product_name
        HAVING total_consumption > 0 -- Filtrera bort produkter som aldrig har förbrukats
        ORDER BY total_consumption DESC -- Störst förbrukning först
        LIMIT ?
    """, (limit,))
    
    top_products = cursor.fetchall()
    conn.close()
    
    #Returnerar en lista av dicts
    return [dict(p) for p in top_products]

def change_product_location(product_name, new_location):
    """Ändrar lagerplats för en befintlig produkt."""
    try:
        conn = get_db_connection()
    except Exception as e:
        raise ValueError(f"Kunde inte ansluta till databasen för platsändring: {e}")

    cursor = conn.cursor()

    #Hittar ProduktID och exakt namn (Sök på Namn OCH Artikelnummer)
    cursor.execute(f"""
        SELECT {COL_PRODID}, {COL_NAME} 
        FROM {PRODUCTS_TABLE} 
        WHERE LOWER({COL_NAME}) = LOWER(?) 
        OR LOWER({COL_NAME}) LIKE ? 
        OR {COL_ARTICLENUMBER} = ?
    """, (product_name.lower(), '%' + product_name.lower() + '%', product_name))
    matched_products = cursor.fetchall()

    if len(matched_products) == 1:
        product_id = matched_products[0][COL_PRODID]
        exact_name = matched_products[0][COL_NAME]

        #Uppdaterar Lagerplats i tabellen Lager
        cursor.execute(f"UPDATE {STOCK_TABLE} SET {COL_LOCATION} = ? WHERE {COL_PRODID} = ?", (new_location, product_id))
        
        conn.commit()
        conn.close()
        log_info(f"Lagerplats lyckades ändras för '{exact_name}' till {new_location}.")
        return exact_name
    elif len(matched_products) > 1:
        conn.close()
        raise ValueError("Tvetydig produkt. Platsändring avbröts. Var vänlig specificera produktnamnet mer exakt.")
    else:
        conn.close()
        raise ValueError(f"Produkt '{product_name}' hittades inte.")

def remove_product(product_name):
    """Tar bort en produkt från Lager och Produkt-tabellerna (avveckling)."""
    try:
        conn = get_db_connection()
    except Exception as e:
        raise ValueError(f"Kunde inte ansluta till databasen för borttagning: {e}")

    cursor = conn.cursor()

    #Hittar ProduktID och exakt namn (Sök på Namn OCH Artikelnummer)
    cursor.execute(f"""
        SELECT {COL_PRODID}, {COL_NAME} 
        FROM {PRODUCTS_TABLE} 
        WHERE LOWER({COL_NAME}) = LOWER(?) 
        OR LOWER({COL_NAME}) LIKE ? 
        OR {COL_ARTICLENUMBER} = ?
    """, (product_name.lower(), '%' + product_name.lower() + '%', product_name))
    matched_products = cursor.fetchall()

    if len(matched_products) == 1:
        product_id = matched_products[0][COL_PRODID]
        exact_name = matched_products[0][COL_NAME]

        #Transaktionell borttagning
        try:
            #Ta bort från Lager-tabellen
            cursor.execute(f"DELETE FROM {STOCK_TABLE} WHERE {COL_PRODID} = ?", (product_id,))
            
            #Ta bort från Produkter-tabellen
            cursor.execute(f"DELETE FROM {PRODUCTS_TABLE} WHERE {COL_PRODID} = ?", (product_id,))
            
            conn.commit()
            log_info(f"Produkten '{exact_name}' (ID: {product_id}) togs bort permanent från Lager och Produkter.")
            return exact_name
        except sqlite3.Error as e:
            conn.rollback()
            raise ValueError(f"Databasfel vid borttagning av produkt: {e}")
        finally:
            conn.close()
    elif len(matched_products) > 1:
        conn.close()
        raise ValueError("Tvetydig produkt. Borttagning avbröts. Var vänlig specificera produktnamnet mer exakt.")
    else:
        conn.close()
        raise ValueError(f"Produkt '{product_name}' hittades inte.")

def rename_product(old_name, new_name):
    """Ändrar namnet på en produkt i Produkter-tabellen och uppdaterar historiktabellen."""
    try:
        conn = get_db_connection()
    except Exception as e:
        raise ValueError(f"Kunde inte ansluta till databasen för namnbyte: {e}")

    cursor = conn.cursor()

    #Hittar ProduktID och exakt gammalt namn (Sök på Namn OCH Artikelnummer)
    cursor.execute(f"""
        SELECT {COL_PRODID}, {COL_NAME} 
        FROM {PRODUCTS_TABLE} 
        WHERE LOWER({COL_NAME}) = LOWER(?) 
        OR LOWER({COL_NAME}) LIKE ? 
        OR {COL_ARTICLENUMBER} = ?
    """, (old_name.lower(), '%' + old_name.lower() + '%', old_name))
    matched_products = cursor.fetchall()

    if len(matched_products) == 1:
        product_id = matched_products[0][COL_PRODID]
        exact_old_name = matched_products[0][COL_NAME]

        #Transaktionellt namnbyte
        try:
            #Steg 2: Uppdatera namnet i Produkter-tabellen
            cursor.execute(f"UPDATE {PRODUCTS_TABLE} SET {COL_NAME} = ? WHERE {COL_PRODID} = ?", (new_name, product_id))

            #Uppdatera namnet i Historik-tabellen (för att bevara historisk data)
            cursor.execute(f"UPDATE {HISTORY_TABLE} SET product_name = ? WHERE product_name = ?", (new_name, exact_old_name))

            conn.commit()
            log_info(f"Produktnamn ändrat från '{exact_old_name}' till '{new_name}'. Historik uppdaterad.")
            return exact_old_name, new_name
        except sqlite3.Error as e:
            conn.rollback()
            raise ValueError(f"Databasfel vid namnbyte av produkt: {e}")
        finally:
            conn.close()

    elif len(matched_products) > 1:
        conn.close()
        raise ValueError("Tvetydig produkt. Namnbyte avbröts. Var vänlig specificera det gamla produktnamnet mer exakt.")
    else:
        conn.close()
        raise ValueError(f"Produkt '{old_name}' hittades inte.")
