import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from src.database.db import get_product_history

def forecast_next_week(product_name: str, df: pd.DataFrame) -> int:
    """
    Använder ARIMA-modellering för att förutsäga efterfrågan för nästa vecka baserat på historik.
    
    Args:
        product_name: Namn på produkten (för loggning/felrapportering).
        df: DataFrame som innehåller historisk data ('date', 'quantity').
        
    Returns:
        Heltal som representerar förväntad försäljning/uttag nästa vecka.
    """
    
    if df.empty:
        return 0 

    #Förbereder data
    try:
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date').sort_index()
        ts = df['quantity'].astype(float)
    
        if len(ts) < 7:
            return round(ts.mean()) if not ts.empty else 0
            
    except Exception as e:
        return round(df['quantity'].mean()) if not df.empty else 0


    #Modellering (ARIMA)
    try:
        model = ARIMA(ts, order=(1, 0, 0))
        model_fit = model.fit()

        forecast = model_fit.forecast(steps=1)[0]
        return max(0, int(round(forecast)))

    except Exception as e:
        return max(0, int(round(ts.mean()))) if not ts.empty else 0
