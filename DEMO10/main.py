# main.py
import customtkinter as ctk
from src.chatbot.gui import ChatbotGUI 
import os 
import sys 

if __name__ == "__main__":
    #Ställer in utseendet
    ctk.set_appearance_mode("System") 
    ctk.set_default_color_theme("blue")

    #Skapar huvudfönstret
    app = ctk.CTk()
    app.title("Jarvis Lagerbot - AI-Assistent")
    app.geometry("800x600")

    try:
        if getattr(sys, 'frozen', False):
            icon_path = os.path.join(sys._MEIPASS, "assets", "Jarvis.ico")
        else:
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "Jarvis.ico")
            
        if os.path.exists(icon_path):
            app.iconbitmap(icon_path)
        else:
            print(f"VARNING: Ikonfilen hittades inte på {icon_path}")
    except Exception as e:
        print(f"Kunde inte sätta fönsterikon: {e}")

    #Initierar den grafiska applikationen
    chatbot_gui = ChatbotGUI(app)
    
    #Startar applikationens huvudloop
    app.mainloop()