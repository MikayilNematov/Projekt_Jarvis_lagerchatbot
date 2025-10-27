from src.database.db import (
    get_product_info, 
    update_product_stock, 
    get_low_stock_products, 
    get_product_history,
    get_top_selling_products,    
    add_new_product_and_stock,
    change_product_location,
    remove_product,
    rename_product,
)
from src.utils.logger import log_info, log_error, log_warning 
from src.ai.forecast import forecast_next_week 

#NY IMPORT KRÄVS FÖR PROGNOSBERÄKNINGEN
import pandas as pd 

#Saldo Kommando
def saldo(product_name, role):
    """Hämtar lagersaldo och plats för en specifik produkt."""
    log_info(f"Kommando 'saldo' initierat av {role} för produkt: {product_name}")
    
    try:
        product = get_product_info(product_name)
        #Använder de nya kolumnnamnen från get_product_info
        name = product['name']
        stock = product['stock']
        location = product['location']
        return f"Produkten {name} finns i lager ({stock} st) på plats: {location}."
    except ValueError as e:
        #Fångar fel som "Produkt hittades inte" eller "Tvetydig sökning"
        log_warning(f"Sökfel vid saldo: {e}")
        return f"Fel: {e}"
    except Exception as e:
        log_error(f"Oväntat fel vid saldo: {e}")
        return f"Ett oväntat fel inträffade vid saldo: {e}"


#Uppdatera Kommando (Admin)
def uppdatera(product_name, stock_amount, role):
    """Uppdaterar lagersaldo för en specifik produkt. Anropar db.update_product_stock."""
    if role != 'admin':
        return "Åtkomst nekad: Du måste vara administratör för att uppdatera lagersaldo."
        
    try:
        #Försöker konvertera till heltal och validera
        new_stock = int(stock_amount)
        if new_stock < 0:
            return "Lagersaldo kan inte vara negativt."
        
        #Anropar den kritiska funktionen i db.py som uppdaterar LAGER OCH loggar HISTORIK
        exact_name = update_product_stock(product_name, new_stock)
        
        return f"Lagersaldo för **{exact_name}** är uppdaterat till **{new_stock}** st."
    except ValueError as e:
        #Fångar fel från databasen (produkt hittades inte/tvetydig) eller int()-konvertering
        log_error(f"Uppdateringsfel (ValueError): {e}") 
        return f"Fel: {e}"
    except Exception as e:
        log_error(f"Oväntat fel vid uppdatering: {e}") 
        return f"Ett oväntat fel inträffade vid uppdatering: {e}"

#Lågtsaldo Kommando (Admin)
def lågtsaldo(role):
    """Hämtar produkter med lågt lagersaldo (under tröskelvärdet)."""
    if role != 'admin':
        return "Åtkomst nekad: Du måste vara administratör för att se lågt saldo."

    products = get_low_stock_products(threshold=10)
    
    if not products:
        return "Inga produkter har lågt saldo (under 10 st)."
        
    message = "Följande produkter har lågt saldo (≤10 st):\n"
    for p in products:
        message += f"- {p['name']}: {p['stock']} st (Plats: {p['location']})\n"
        
    return message
    
#Historik Kommando
def historik(product_name, role):
    """Hämtar historik (datum och saldon) för en specifik produkt."""
    log_info(f"Kommando 'historik' initierat av {role} för produkt: {product_name}")
    
    try:
        history = get_product_history(product_name)
    except ValueError as e:
        log_warning(f"Historikfel: {e}")
        return f"Fel: {e}"
    
    if not history:
        return f"Ingen historik hittades för produkten '{product_name}'."
        
    message = f"Historik för **{product_name}** (Saldon vid uppdatering):\n"
    for item in history:
        message += f"- {item['date']}: {item['quantity']} st\n"
        
    return message

#Prognos Kommando (Admin)
def prognos(product_name, role):
    """
    Beräknar och returnerar en lagersaldoprognos för nästa vecka baserat på historik.
    Kräver minst två historiska datapunkter för att fungera.
    """
    if role != 'admin':
        return "Åtkomst nekad: Du måste vara administratör för att skapa prognoser."

    try:
        #Hämtar rå historikdata
        history = get_product_history(product_name)
        
        if len(history) < 2:
            return f"Kan inte skapa prognos. Minst 2 historikposter (saldoändringar) krävs för '{product_name}'. Hittade {len(history)}."
            
        #Skapar DataFrame
        df = pd.DataFrame(history)
            
        #Anropar prognosmodellen
        #Använder både produktnamn och DataFrame som argument
        predicted_consumption = forecast_next_week(product_name, df)
        
        #Avrundar till heltal
        rounded_consumption = int(predicted_consumption)

        return (f"Prognos för **{product_name}** nästa vecka:\n"
                f"Baserat på historiska data förutspås ett uttag på **{rounded_consumption}** st.")

    except ValueError as e:
        #Fångar fel som "Produkt hittades inte"
        log_error(f"Fel vid prognos: {e}")
        return f"Ett fel inträffade vid prognos: {e}"

    except Exception as e:
        log_error(f"Kritiskt fel vid skapande av prognos för {product_name}: {e}")
        return f"Ett fel inträffade vid prognos: {e}"

#Topplista Kommando (Admin)
def topplista(role):
    """Hämtar de N mest förbrukade produkterna baserat på historik."""
    if role != 'admin':
        return "Åtkomst nekad: Du måste vara administratör för att se topplistan."

    #Anropar den nya databasfunktionen
    try:
        top_products = get_top_selling_products(limit=5)
    except Exception as e:
        log_error(f"Fel vid hämtning av topplista: {e}")
        return "Fel vid hämtning av topplista från databasen."
        
    if not top_products:
        return "Ingen historik hittades för att beräkna topplistan."
        
    message = "**Topp 5 Mest Förbrukade Produkter (Netto Uttag):**\n"
    for i, p in enumerate(top_products):
        #Visar uttaget som ett positivt tal, men det var en minskning i lager.
        consumption = int(p['total_consumption'])
        message += f"{i+1}. **{p['name']}**: {consumption} st\n"
        
    return message

#Läggtill Kommando (Admin)
def läggtill(product_name, initial_stock, location, specification, article_number, role):
    """Lägger till en helt ny produkt i lagret, inklusive artikelnummer och specifikationer."""
    if role != 'admin':
        return "Åtkomst nekad: Du måste vara administratör för att lägga till produkter."

    try:
        stock = int(initial_stock)
        if stock < 0:
             return "Initialt saldo måste vara noll eller positivt."
        
        add_new_product_and_stock(
            product_name=product_name, 
            initial_stock=stock, 
            location=location, 
            specifications=specification,    
            article_number=article_number    
        )
        
        return (f"Produkt **{product_name}** har lagts till i lagret!\n"
                f"Detaljer:\n"
                f"- **Saldo:** {stock} st på plats: {location}\n"
                f"- **Artikelnummer:** {article_number if article_number else 'Saknas'}\n"
                f"- **Specifikation:** {specification if specification else 'Saknas'}")
                
    except ValueError as e:
        log_error(f"Fel vid 'läggtill' (ValueError): {e}")
        return f"Fel: {e}"
    except Exception as e:
        log_error(f"Oväntat fel vid 'läggtill': {e}")
        return f"Ett oväntat fel inträffade vid tillägg av produkt: {e}"

#Flyttar Plats Kommando (Admin)
def flyttaplats(product_name, new_location, role):
    """Ändrar lagerplats för en produkt."""
    if role != 'admin':
        return "Åtkomst nekad: Du måste vara administratör för att byta lagerplats."
        
    try:
        exact_name = change_product_location(product_name, new_location)
        return f"Lagerplats för **{exact_name}** är uppdaterad till **{new_location}**."
    except ValueError as e:
        log_error(f"Platsändringsfel: {e}") 
        return f"Fel: {e}"
    except Exception as e:
        log_error(f"Oväntat fel vid platsändring: {e}") 
        return f"Ett oväntat fel inträffade: {e}"

#Ta Bort Kommando (Admin)
def tabort(product_name, role):
    """Tar bort en produkt permanent från lagret."""
    if role != 'admin':
        return "Åtkomst nekad: Du måste vara administratör för att ta bort produkter."
        
    try:
        exact_name = remove_product(product_name)
        return f"Produkten **{exact_name}** har permanent tagits bort från lagret och databasen."
    except ValueError as e:
        log_error(f"Borttagningsfel: {e}") 
        return f"Fel: {e}"
    except Exception as e:
        log_error(f"Oväntat fel vid borttagning: {e}") 
        return f"Ett oväntat fel inträffade: {e}"

#Byt Namn Kommando (Admin)
def bytnamn(old_name, new_name, role):
    """Ändrar namnet på en befintlig produkt och uppdaterar historiken."""
    if role != 'admin':
        return "Åtkomst nekad: Du måste vara administratör för att ändra produktnamn."

    try:
        exact_old_name, exact_new_name = rename_product(old_name, new_name)
        return (f"Produktnamnet har uppdaterats.\n"
                f"Tidigare: **{exact_old_name}**\n"
                f"Nuvarande: **{exact_new_name}**")
    except ValueError as e:
        log_error(f"Namnbytesfel: {e}") 
        return f"Fel: {e}"
    except Exception as e:
        log_error(f"Oväntat fel vid namnbyte: {e}") 
        return f"Ett oväntat fel inträffade: {e}"
