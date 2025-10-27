import os
import faiss
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
from src.utils.config import RAG_CONFIG 
import sys 
from google import genai
from google.genai.errors import APIError

#För att hantera API-nyckel säkert från miljövariabel
from dotenv import load_dotenv 

#Laddar miljövariabler (som din GEMINI_API_KEY)
load_dotenv()

class RAGChatbot:
    def __init__(self):
        """
        Initierar SentenceTransformer för embeddings och Gemini-klienten.
        """
        
        model_name = RAG_CONFIG["embedding_model"]
        
        if getattr(sys, 'frozen', False):
            base_dir = sys._MEIPASS
            
            self.index_path = os.path.join(base_dir, RAG_CONFIG["index_path"])
            self.docs_path = os.path.join(base_dir, RAG_CONFIG["docs_path"])
        else:
            self.index_path = RAG_CONFIG["index_path"]
            self.docs_path = RAG_CONFIG["docs_path"]
        
        try:
            self.client = genai.Client()
            self.llm_model = 'gemini-2.5-flash'
            print("INFO: Gemini API-klient initierad.")
        except Exception as e:
            self.client = None
            print(f"VARNING: Kunde inte initiera Gemini Client (fel: {e}). Svar genereras lokalt.")

        self.embedder = SentenceTransformer(model_name)
        
        self.index = None
        self.docs = [] 
    
    def build_index(self, texts):
        Path(os.path.dirname(self.index_path)).mkdir(exist_ok=True, parents=True)

        embeddings = self.embedder.encode(texts, convert_to_numpy=True)
        d = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(d)
        self.index.add(embeddings)
        self.docs = texts
        faiss.write_index(self.index, self.index_path)
        with open(self.docs_path, "w", encoding="utf-8") as f:
            for t in texts:
                f.write(t + "\n")

    def load_index(self):
        if not os.path.exists(self.index_path):
            raise FileNotFoundError(f"Inget FAISS-index hittades på sökväg: {self.index_path}. Kör build_index först.")
        self.index = faiss.read_index(self.index_path)
        with open(self.docs_path, "r", encoding="utf-8") as f:
            self.docs = [line.strip() for line in f.readlines()]

    def _generate_response_dummy(self, prompt):
        """
        Dummy-funktion som simulerar ett svar när inget LLM är konfigurerat.
        """
        if "huvudbrytare" in prompt.lower():
            return "En huvudbrytare används för att säkert bryta strömmen i huvudkretsen enligt de dokument jag hittade."
        elif "jordfelsbrytare" in prompt.lower():
            return "Jordfelsbrytare skyddar mot strömgenomgång genom att snabbt bryta strömmen vid fel."
        return "Jag kan svara baserat på kontexten, men just nu har jag ingen aktiv språkmodell (LLM) ansluten."


    def query(self, question, top_k=3):
        """
        Hämtar relevanta textbitar (R) och genererar svar (G) via Gemini API.
        """
        if self.index is None:
            raise ValueError("Index är inte laddat. Kör build_index() eller load_index().")

        q_emb = self.embedder.encode([question], convert_to_numpy=True)
        D, I = self.index.search(np.array(q_emb), k=top_k)
        hits = [self.docs[i] for i in I[0]]

        context = "\n".join(hits)
        prompt = (
            "Du är Elfirman Lagerbot, en expert på elmaterial. "
            "Använd endast den 'Relevant information' som tillhandahålls nedan för att svara på 'Fråga'. "
            "Om informationen inte är tillgänglig, svara att du inte vet och hänvisa till att du sökte i dokumentationen."
            f"\n\nRelevant information:\n{context}\n\nFråga: {question}\n\nSvar:"
        )

        if self.client:
            try:
                response = self.client.models.generate_content(
                    model=self.llm_model,
                    contents=prompt,
                    config=genai.types.GenerateContentConfig(temperature=0.1) 
                )
                svar = response.text
            except APIError as e:
                svar = f"Ett API-fel uppstod vid generering: {e}"
            except Exception as e:
                svar = f"Ett oväntat fel uppstod: {e}"
        else:
            svar = self._generate_response_dummy(question)
        
        return svar, hits
