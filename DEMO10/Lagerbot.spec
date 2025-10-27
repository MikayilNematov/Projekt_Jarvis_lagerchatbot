# -*- mode: python ; coding: utf-8 -*-
#
# DENNA FIL ÄR GENERAD AV PYINSTALLER OCH REDIGERAD FÖR RAG-PROJEKTET.

import sys
import os

# Den exakta sökvägen till din SentenceTransformer-modell i Python 3.11-cachen.
# PyInstaller kommer att använda denna väg för att baka in alla modellfiler.
s_t_path = "C:\\Users\\Admin\\.cache\\huggingface\\hub\\models--sentence-transformers--all-MiniLM-L6-v2"


a = Analysis(
    ['main.py'], # Programstartpunkt
    pathex=['.'], # Lägger till den nuvarande mappen i sökvägen
    binaries=[],
    datas=[
        # 1. Lägg till hela din SRC-mapp så att alla moduler hittas
        ('src', 'src'),
        
        # 2. Databasfilen (SQLite)
        # OBS: PyInstaller packar den i roten av 'dist'
        ('Elfirman.db', '.'),
        
        # 3. RAG Index/Data
        ('data', 'data'),
        
        # 4. Den inbäddade SentenceTransformer-modellen (Kritisk länk!)
        (s_t_path, 'sentence_transformers/all-MiniLM-L6-v2'),
        
        # NY RAD: Lägg till ICON-filen och dess mapp (assets)
        # Detta matchar den sökväg vi specificerade i main.py (assets/icon.ico)
        ('assets/Jarvis.ico', 'assets'),
        
        # Lägg till din befintliga ikonfil (om den används någon annanstans)
        ('Jarvis.ico', '.'),
        
    ],
    # Lägg till dolda beroenden som PyInstaller missar
    hiddenimports=[
        'sklearn.utils._cython_blas', 
        'sklearn.neighbors.typedefs',
        'src.chatbot.bot',         
        'src.chatbot.commands',
        'src.ai.rag',
        'src.database.db',
        'threading', # För multitrådning i GUI
        
        # FIX FÖR STATSMODELS/ARIMA
        'statsmodels.tsa.tsatools', 
        'statsmodels.nonparametric._reweighted_ls',
        'statsmodels.nonparametric.bandwidths',
        
        # Pandas-beroenden som ofta krävs av statsmodels
        'pandas._libs.tslibs.timedeltas', 
        'pandas._libs.tslibs.np_datetime',
        
        # *** KRITISK NY RAD FÖR GENAI-FELET (DeadlineExceeded) ***
        'google.genai.errors'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pyodbc'], # Exkluderar den gamla MSSQL-beroendet
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Jarvis',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False, # Håller CMD-fönstret dolt (Bra!)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # IKONKONTROLL: Säkerställ att ikonen sätts här också för Windows
    icon='Jarvis.ico' # Använd det filnamn du vill ha som fönsterikon
)