from src.chatbot import commands
from src.utils.logger import log_info, log_error, log_warning
from src.ai.rag import RAGChatbot
from src.utils.config import CHAT_CONFIG 

from google import genai
from google.genai.errors import APIError 
from dotenv import load_dotenv
import json
import pandas as pd 

#Laddar miljövariabler (som din GEMINI_API_KEY)
load_dotenv()

#LLM-baserad Kommando-Tolkning (Behålls som extern funktion) ---

def tolka_kommando_med_llm(cmd_input: str, role: str) -> dict:
    """
    Använder Gemini för att tolka naturligt språk till ett strukturerat kommando (JSON).
    """
    try:
        #Säkerställer att klienten kan initieras
        client = genai.Client()
    except Exception as e:
        log_error(f"Kunde inte initiera Gemini Client för tolkning: {e}")
        return {"action": "okänd", "error": "LLM-klient ej tillgänglig"}

    #NY PROMPT FÖR BÄTTRE KOMMANDOTOLKNING
    system_prompt = (
        "Du är Lagerbot, en tolk för en lagerhanteringsassistent. Din uppgift är att konvertera "
        "användarens naturliga språk till ett strukturerat JSON-kommando. "
        "Du får INTE svara med text, endast JSON.\n\n"
        "Tillgängliga roller: 'user' (kan söka) och 'admin' (kan söka och uppdatera/se lågt saldo/prognos). "
        "Användarens nuvarande roll är: {role}\n\n"
        "Tillgängliga åtgärder (action) och deras argument (args):\n"
        "1. saldo: Hämta lagersaldo. Kräver ett sökord för produkten i args[0].\n"
        "2. uppdatera: Uppdatera lagersaldo. Kräver 'admin' roll. Kräver produktnamn i args[0] och nytt saldo (tal) i args[1].\n"
        "3. lågtsaldo: Lista produkter med lågt saldo (≤10). Kräver 'admin' roll. Kräver inga args.\n"
        "4. historik: Hämta historiska saldon. Kräver ett sökord för produkten i args[0].\n"
        "5. prognos: Förutsäga försäljning/uttag för nästa vecka. Kräver 'admin' roll. Kräver ett sökord för produkten i args[0].\n"
        "6. läggtill: Lägger till en ny produkt. Kräver 'admin' roll. Kräver produktnamn i args[0], initialt saldo (tal) i args[1], plats/hylla i args[2], specifikationer/beskrivning i args[3], och artikelnummer i args[4].\n" 
        "7. topplista: Hämta topplistan över mest förbrukade produkter. Kräver 'admin' roll. Kräver inga args.\n"
        "8. flyttaplats: Ändrar lagringsplats. Kräver 'admin' roll. Kräver produktnamn i args[0] och ny plats/hylla i args[1].\n"
        "9. tabort: Tar bort en produkt permanent från lagret. Kräver 'admin' roll. Kräver produktnamn i args[0].\n"
        "10. bytnamn: Ändrar namnet på en produkt. Kräver 'admin' roll. Kräver gammalt produktnamn i args[0] och nytt produktnamn i args[1].\n"
        "11. rag: Fråga kunskapsdatabasen. Används om frågan inte matchar något av ovanstående kommandon (t.ex. 'Vad är en Dimmerspärr?'). Kräver hela frågan som args[0].\n" 
        "12. okänd: Om frågan inte kan tolkas som någon av de andra åtgärderna.\n\n" 
        "Returnera ALLTID en JSON med strukturen: {{ \"action\": <action>, \"args\": [<arg1>, <arg2>, ...] }}"
    ).format(role=role)
    
    response_schema = {
        "type": "OBJECT",
        "properties": {
            "action": {"type": "STRING", "description": "Det identifierade kommandot."},
            "args": {"type": "ARRAY", "items": {"type": "STRING"}, "description": "Argument till kommandot."},
        },
        "required": ["action", "args"]
    }

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=cmd_input,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_schema=response_schema,
                temperature=0.0
            ),
        )
        
        json_response = json.loads(response.text)
        log_info(f"LLM-tolkning: {json_response}")
        return json_response
        
    except APIError as e:
        log_error(f"LLM-API-fel (t.ex. timeout) inträffade vid tolkning: {e}")
        return {"action": "okänd", "error": "LLM-timeout."}
    except Exception as e:
        log_error(f"Ett LLM-relaterat fel inträffade vid tolkning: {e}")
        return {"action": "okänd", "error": f"LLM-tolkningsfel: {e}"}

#Huvudklasser

class ChatBot:
    def __init__(self):
        self.role = 'user' 
        self.admin_password = CHAT_CONFIG["admin_password"]
        self.rag = RAGChatbot() 
        log_info(f"ChatBot initierad. Standardroll: {self.role}.")
        
    def set_role(self, new_role, password=""):
        """Sätter användarens roll."""
        new_role = new_role.lower()
        
        if new_role not in ['user', 'admin']:
            return f"Ogiltig roll: '{new_role}'. Välj 'user' eller 'admin'."

        if new_role == 'admin':
            if password == self.admin_password:
                self.role = 'admin'
                log_info("Roll satt till ADMIN.")
                return f"Rollen är satt till **ADMIN**."
            else:
                log_warning("Försök till administratörsåtkomst misslyckades.")
                return "Felaktigt lösenord för administratörsroll."
        
        #Om rollen är 'user'
        self.role = 'user'
        log_info("Roll satt till USER.")
        return f"Rollen är satt till **USER**."
        
    def get_response(self, user_input: str) -> str:
        """
        Tar emot användarinmatning, tolkar den via LLM och exekverar kommandot.
        """
        user_input = user_input.strip()
        
        if not user_input:
            return ""

        #Hämtar LLM-tolkat kommando
        parsed_cmd = tolka_kommando_med_llm(user_input, self.role)
        
        action = parsed_cmd.get("action", "okänd").lower()
        args = parsed_cmd.get("args", [])
        
        log_info(f"Tolkad handling: '{action}' med argument: {args}")

        try:
            #Exekvera handlingen
            if action == "saldo" and len(args) >= 1:
                return commands.saldo(args[0], self.role)
                
            elif action == "historik" and len(args) >= 1:
                return commands.historik(args[0], self.role)
                
            elif action == "prognos" and len(args) >= 1:
                #Prognoslogiken flyttades till commands.prognos för renhet
                return commands.prognos(args[0], self.role)
                
            #Administratörskommandon
            elif action == "uppdatera" and self.role == "admin" and len(args) == 2:
                produkt = args[0] 
                antal = args[1]
                return commands.uppdatera(produkt, antal, self.role)
                
            elif action == "lågtsaldo" and self.role == "admin":
                return commands.lågtsaldo(self.role)
            
            elif action == "läggtill" and self.role == "admin" and len(args) == 5:
                produkt = args[0]
                saldo = args[1]
                plats = args[2]
                specifikation = args[3]
                artikelnummer = args[4]
                return commands.läggtill(produkt, saldo, plats, specifikation, artikelnummer, self.role)
                
            elif action == "topplista" and self.role == "admin":
                return commands.topplista(self.role)
            
            elif action == "flyttaplats" and self.role == "admin" and len(args) == 2:
                produkt = args[0]
                ny_plats = args[1]
                return commands.flyttaplats(produkt, ny_plats, self.role)
                
            elif action == "tabort" and self.role == "admin" and len(args) == 1:
                produkt = args[0]
                return commands.tabort(produkt, self.role)
                
            elif action == "bytnamn" and self.role == "admin" and len(args) == 2:
                gammalt_namn = args[0]
                nytt_namn = args[1]
                return commands.bytnamn(gammalt_namn, nytt_namn, self.role)
            
            #RAG-fråga
            elif action == "rag" and len(args) >= 1:
                fråga = args[0]
                svar, hits = self.rag.query(fråga)
                #Formaterar utdata för GUI
                kontext = "\n\n--- Kontext som användes ---\n" + "\n".join(f" - {h}" for h in hits)
                return f"Svar: {svar}{kontext}"

            #Felhantering
            elif action == "okänd" and "LLM-timeout" in parsed_cmd.get("error", ""):
                return "Jag är ledsen, men AI-tjänsten tog för lång tid. Försök igen."
                
            elif action == "okänd":
                #Om LLM inte kunde tolka till ett känt kommando
                return "Jag förstår inte kommandot. Skriv 'help' för lista på tillgängliga operationer."
            
            #Fångar ALLA admin-kommandon om rollen INTE är admin
            elif action in ["uppdatera", "lågtsaldo", "prognos", "läggtill", "topplista", "flyttaplats", "tabort", "bytnamn"] and self.role != "admin":
                 return "Åtkomst nekad: Du måste vara administratör för att utföra den åtgärden."
            
            else:
                return "Okänt kommando eller felaktig syntax. Skriv 'help' för lista."

        except ValueError as ve:
            #Fångar fel från commands/db (t.ex. produkt hittades inte)
            return f"Inmatningsfel: {ve}"
        except Exception as e:
            log_error(f"Kritiskt fel vid kommandoexekvering: {e}")
            return f"Ett oväntat fel inträffade. Kontrollera loggarna."
        
