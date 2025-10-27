import customtkinter as ctk
import threading
from src.chatbot.bot import ChatBot 
from src.utils.config import CHAT_CONFIG

#Pop-up Fönster för Rollval
class RoleSelectionWindow(ctk.CTkToplevel):
    """Ett pop-up fönster för att välja användarroll vid start."""
    def __init__(self, master, callback, initial_role):
        super().__init__(master)
        self.title("Välj Användarroll")
        self.geometry("300x200")
        self.resizable(False, False)
        self.transient(master) 
        self.protocol("WM_DELETE_WINDOW", self.destroy) 
        
        self.callback = callback
        
        #Roll-val
        self.role_label = ctk.CTkLabel(self, text="Välj din roll:")
        self.role_label.pack(pady=10)
        
        self.role_var = ctk.StringVar(value=initial_role)
        self.role_optionmenu = ctk.CTkOptionMenu(
            self, 
            values=["user", "admin"], 
            variable=self.role_var,
            command=self.show_hide_password
        )
        self.role_optionmenu.pack(pady=5)
        
        #Lösenordsfält (Dolt initialt)
        self.password_entry = ctk.CTkEntry(self, placeholder_text="Admin Lösenord", show="*")
        self.show_hide_password(initial_role) # Visa/dölj initialt
        
        #Bekräfta-knapp
        self.confirm_button = ctk.CTkButton(self, text="Bekräfta", command=self.confirm)
        self.confirm_button.pack(pady=15)
        
        #Centrerar fönstret
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = master.winfo_x() + (master.winfo_width() // 2) - (width // 2)
        y = master.winfo_y() + (master.winfo_height() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def show_hide_password(self, role):
        """Visar/döljer lösenordsfältet beroende på roll."""
        role_str = role if isinstance(role, str) else self.role_var.get()

        if role_str == "admin":
            self.password_entry.pack(pady=5)
        else:
            self.password_entry.pack_forget()

    def confirm(self):
        """Anropar callback-funktionen med vald roll och lösenord."""
        role = self.role_var.get()
        password = self.password_entry.get() if role == "admin" else ""
        self.callback(role, password)
        self.destroy()

#Huvudklass: ChatbotGUI
class ChatbotGUI:
    def __init__(self, master):
        self.master = master
        #ChatBot initieras med standardroll 'user'
        self.chatbot = ChatBot() 
        
        self.create_widgets()

        #Visa pop-up för rollval efter att GUI:t har renderats
        self.master.after(100, self.show_role_selector) 
        
        #Ange initial placeholder text
        self.update_placeholder()

    def create_widgets(self):
        #Konfigurera grid-layout
        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_columnconfigure(0, weight=1)
        
        #1. Chattfönster (CTkTextbox)
        self.chat_history = ctk.CTkTextbox(self.master, state="disabled", wrap="word")
        self.chat_history.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="nsew")

        #2. Inputfält (CTkEntry)
        self.input_entry = ctk.CTkEntry(
            self.master,
            placeholder_text="" 
        )
        self.input_entry.grid(row=1, column=0, padx=(10, 5), pady=(0, 10), sticky="ew")
        self.input_entry.bind("<Return>", self.send_message)

        #Skicka-knapp (CTkButton)
        self.send_button = ctk.CTkButton(self.master, text="Skicka", command=self.send_message)
        self.send_button.grid(row=1, column=1, padx=(5, 10), pady=(0, 10), sticky="e")

    def append_message(self, sender, message, is_bot=True):
        """Lägger till ett meddelande i chatthistoriken. Uppdaterad för att visa 'Jarvis'."""
        self.chat_history.configure(state="normal")
        
        tag = "bot_tag" if is_bot else "user_tag"
        color = "green" if is_bot else "blue"
        
        self.chat_history.tag_config(tag, foreground=color)
        
        #Använd "Jarvis" istället för "Bot" om det är ett botmeddelande
        sender_display = "Jarvis" if is_bot else sender
        
        self.chat_history.insert(ctk.END, f"{sender_display}: ", tag)
        self.chat_history.insert(ctk.END, f"{message}\n\n")
        self.chat_history.configure(state="disabled")
        self.chat_history.see(ctk.END)

    def disable_input(self):
        self.input_entry.configure(state="disabled")
        self.send_button.configure(state="disabled")

    def enable_input(self):
        self.input_entry.configure(state="normal")
        self.send_button.configure(state="normal")
        self.input_entry.focus_set()

    def update_placeholder(self):
        self.input_entry.configure(
            placeholder_text=f"Roll: {self.chatbot.role.upper()}. Ställ en fråga eller skriv 'help'..."
        )

    #Pop-up Relaterade Metoder
    def show_role_selector(self):
        """Visar pop-up fönstret för rollval och initierar välkomstmeddelande."""
        RoleSelectionWindow(
            self.master, 
            self.handle_role_selection,
            self.chatbot.role 
        )
        
    def handle_role_selection(self, role, password):
        """Callback som hanterar det valda rollen från pop-upen. Uppdaterad för välkomstmeddelande."""
        
        #1. Hantera lösenord och sätt roll
        if role == 'admin' and password != CHAT_CONFIG["admin_password"]:
            response = "Fel lösenord. Rollen är satt till USER."
            self.chatbot.set_role('user', '') # Tvinga till USER vid fel
        else:
            response = self.chatbot.set_role(role, password)
            
        #2. Uppdatera GUI (placeholder text)
        self.update_placeholder()
        
        self.append_message("Du", response, is_bot=True)
        
        #Lägg till det nya välkomstmeddelandet
        welcome_message = "Hej!\nJag heter Jarvis, hur kan jag hjälpa till?"
        
        #4. Skicka ut välkomstmeddelandet med en liten fördröjning
        self.master.after(100, lambda: self.append_message("Du", welcome_message, is_bot=True))

    #Skicka Meddelande Logik
    def run_response_in_thread(self, cmd_input):
        """Körs i en separat tråd för att undvika frysning."""
        try:
            response = self.chatbot.get_response(cmd_input)
            #Uppdaterar GUI:t på huvudtråden (använder Jarvis som avsändare)
            self.master.after(0, lambda: self.append_message("Du", response, is_bot=True))
        
        #Fångar de specifika databasfelen från db.py
        except (FileNotFoundError, ConnectionError) as db_error:
            error_msg = f"KRITISKT DATABASFEL: {db_error}"
            #Loggar felet och visa det för användaren (använder Jarvis som avsändare)
            self.master.after(0, lambda: self.append_message("Du", error_msg, is_bot=True))
        
        except Exception as e:
            #Fångar alla andra fel (använder Jarvis som avsändare)
            error_msg = f"Ett oväntat fel inträffade vid hantering av svar: {e}"
            self.master.after(0, lambda: self.append_message("Du", error_msg, is_bot=True))
        finally:
            #Detta garanterar att inmatningsfältet ALLTID låses upp.
            self.master.after(0, self.enable_input)

    def send_message(self, event=None):
        cmd_input = self.input_entry.get().strip()
        if not cmd_input:
            return

        self.input_entry.delete(0, ctk.END)
        self.append_message("Du", cmd_input, is_bot=False)
        self.disable_input()
        
        #Startar tråden för att hämta svar
        threading.Thread(target=self.run_response_in_thread, args=(cmd_input,)).start()
