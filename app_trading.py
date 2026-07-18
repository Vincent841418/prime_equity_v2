#----------------------------------------LIBRARIES----------------------------------
#These are ESSENTIAL for the program to run properly. Without them, the code won't be shown. 
#If you're logged in at a new device, install these BEFORE trying to execute the code lines below.

#To install these libraries, use the code: pip install (name of the library) on the terminal.
#To make it simpler, next to each library, is the code you need to copy on the terminal.

import streamlit as st  #pip install streamlit
import streamlit_authenticator as stauth #pip install streamlit-authenticator
import yaml # Para cargar configuraciones
from yaml.loader import SafeLoader
import yfinance as yf
from google import genai #pip install 
import pandas as pd #already comes with python
from google.genai import types #Herramienta de búsqueda de internet
import time #Comes with python
import plotly.graph_objects as go #pip install plotly
import datetime #already comes with python
from datetime import datetime #Dentro de la libreria datetime, hay una funcion especifica q tmb se llama Datetime, esa es la q buscamos llamar en esta linea.
import json #pip install json
import os
import pytz
import PyPDF2
import numpy as np
import plotly.express as px
import re
from fredapi import Fred #pip install fredapi
from pypdf import PdfReader #pip install pypdf

#PARA BORRAR Y LIBERAR LA MEMORIA
#pip uninstall 'library_name'

#----------------------------------------------------------------------------------

#-----------------------------CONFIGURACION DE USUARIO Y CONTRASEÑA-------------------------------
names = ["User 1", "Admin", "User 2"]
usernames = ["user1", "admin", "user2"]
passwords = ["2015", "2011", "2026"]

credentials = {
    'usernames': {
        usernames[0]: {'name': names[0], 'password': passwords[0]},
        usernames[1]: {'name': names[1], 'password': passwords[1]},
        usernames[2]: {'name': names[2], 'password': passwords[2]}
    }
}
#Hasher hace q la contraseña 2006 se guarde con un código único (tipo a7f8g9h2....). 
#Esto es para en caso de hackeos no puedan conseguir la contraseña real. Solo el programa sabe relacionar el código con la clave real.

# 1. Hashear las contraseñas de forma directa
# Nota: Ahora se usa el método estático directamente sobre la clase
stauth.Hasher.hash_passwords(credentials)
# 3. Inicializar el autenticador
# En las versiones nuevas, solo pasamos el diccionario de credenciales primero

#FUNCIONAMIENTO:
#El usuario entra por un navegador (Chrome, Safari, Edge, Firefox). Cuando ingresa sus datos, el programa le genera una cookie.
#Esta cookie que seria la prime_equity_cookie se graba en el disco duro del navegador dentro de la PC.
#Este disco luego le envia la info al servidor y si coincide, se graba y dura por 30 dias esa cookie.
#Si inicias el programa en distintos navegadores, no te reconoceria y tendrias que iniciar sesion de nuevo. Solo se graba por navegador.
authenticator = stauth.Authenticate(
    credentials,
    'prime_equity_cookie', 
    'signature_key',       
    30                     
)



# 4. Renderizar el login
# Esto dibuja el cuadro sin causar el error rojo
authenticator.login()
#Streamlit dibuja el cuadro de inicio de sesion automaticamente.
# Obtenemos los valores de la memoria interna de la app
authentication_status = st.session_state.get("authentication_status")
name = st.session_state.get("name")
username = st.session_state.get("username")

#--------------------------------------------------------------------------------------------------------------------------------------------------

#INICIO DEL PROGRAMA---------------------------------------------------------------------------------

if authentication_status:
     # ---------------------------------- CONFIGURACIÓN DE PÁGINA ----------------------------------
    st.set_page_config(page_title="Prime Equity v2", layout="wide")
    st.title("💸 Prime Equity v2")

    #SI EL LOGIN ES CORRECTO, CORRE TODA TU APP AQUÍ
    with st.sidebar:
        st.write(f"Welcome, **{name}**")
        authenticator.logout('Log Out', 'sidebar')

        ny_time = datetime.now(pytz.timezone('America/New_York'))
        st.write(f"🔔 NYSE Time: **{ny_time.strftime('%H:%M:%S')}**")
        
        #-----------------------------------MEMORIA INTERNA---------------------------
        #Aca se le avisa a Streamlit que estas variables SI EXISTEN, aunque esten vacias.
        #Mejor dicho, creamos las variables dandoles valor 0, vacio, nada.
        #Esto es para cuando dependemos de que la variable sea creada a partir de un boton.

        #DEL BOTON DE NOTICIAS
        if 'puntos_noticias' not in st.session_state:
            st.session_state['puntos_noticias'] = None

        #DEL REPORTE DEL AI EDGE FINDER AGENT
        if 'resultado_ia' not in st.session_state:
            st.session_state['resultado_ia'] = None

        #Financial Snapshot del Earnings Report
        if 'resultado' not in st.session_state:
            st.session_state.resultado = None

        variables_tokens = ['total_input', 'total_output', 'total_combined', 'intentos_diarios']
        for var in variables_tokens:
            if var not in st.session_state:
                st.session_state[var] = 0
                
        if 'ultimo_consumo' not in st.session_state:
            st.session_state['ultimo_consumo'] = {'input': 0, 'output': 0, 'total': 0}
        #........................................................................................................................
    # ---------------------------------------------------------------------------------------------
    
    # --- BARRA LATERAL (Conexión) ---
    with st.sidebar:
        st.image("logo.png", use_container_width=True)
        st.divider()

        st.header("Settings")

        #NOTA IMPORTANTE: 
        #Dado que Gemini es el motor de la app para varias cosas (análisis técnico, búsqueda de ticker, análisis de noticias, sentiment scoring, Google Search tool)
        #Google AI Studio impone un límite diario o por minuto a las llamadas a su servidor, por lo que la API Key esta pensada para solo UN USUARIO, por temas de desgaste.
        #Ademas que puede ser usada malintencionadamente y esta ligada a mi cuenta personal de Google.

        api_key = st.text_input("Insert your Google AI Studio API Key:", type="password")
        #Esto SOLO si tuviera pro, pero como no lo tengo, en INICIALIZACIÓN, python escoje por su cuenta el modelo flash.
        #Es decir, en la app sale debajo de la apikey una caja de opciones, pero da igual la q escojas.
        modelo_seleccionado = st.selectbox("Model", ["gemini-2.5-flash", "gemini-2.5-pro"]) 
        st.info("This app is powered by Gemini AI, Yahoo Finance and others' APIs to gather and digest the data.")
        st.info("Tools: Gemini's DeepSearch")

    #-------------------------------------------------APARTADO DE FUNCIONES---------------------------------------------------
    def scanner_oportunidades(tickers):
        oportunidades = []
        if not tickers:
            return oportunidades

        # 1. DESCARGA MASIVA: Bajamos todas las acciones de golpe
        # Esto reduce el tiempo de espera de 30s a unos 3-5s
        data = yf.download(tickers, period="1mo", interval="1d", group_by='ticker', progress=False)
        
        for t in tickers:
            try:
                # Seleccionamos la data de este ticker específico
                df = data[t] if len(tickers) > 1 else data
                df = df.dropna()
                
                if len(df) < 11: continue
                
                # 2. Cálculo de rendimiento 2 semanas (10 sesiones)
                precio_actual = float(df['Close'].iloc[-1])
                precio_hace_2w = float(df['Close'].iloc[-10])
                rendimiento = ((precio_actual - precio_hace_2w) / precio_hace_2w) * 100
                
                # 3. Cálculo de RSI (14 sesiones)
                delta = df['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi_val = 100 - (100 / (1 + rs))
                actual_rsi = rsi_val.iloc[-1]
                
                # FILTRO ESTRATÉGICO
                if rendimiento < -6 and actual_rsi < 38:
                    oportunidades.append({
                        "Ticker": t,
                        "Caída %": f"{rendimiento:.1f}%",
                        "RSI": f"{actual_rsi:.1f}",
                        "Precio": f"${precio_actual:.2f}"
                    })
            except:
                continue # Si un ticker falla, pasamos al siguiente
                
        return oportunidades  
    
    def actualizar_consumo_tokens(response):
        """Extrae los metadatos de uso y actualiza los contadores globales."""
        try:
            usage = response.usage_metadata
            
            # 1. Sumar al acumulado total de la sesión
            st.session_state['total_input'] += usage.prompt_token_count #+= significa agregar al valor existente.
            st.session_state['total_output'] += usage.candidates_token_count
            st.session_state['total_combined'] += usage.total_token_count
            
            # 2. Sumar 1 al contador de peticiones diarias (RPD)
            st.session_state['intentos_diarios'] += 1
            
            # 3. Guardar el "último consumo" para mostrarlo individualmente si quieres
            st.session_state['ultimo_consumo'] = {
                'input': usage.prompt_token_count,
                'output': usage.candidates_token_count,
                'total': usage.total_token_count
            }
        except Exception as e:
            print(f"Error tracking tokens: {e}")
    
    def calcular_rsi(data, periodos=14):
        delta = data['Close'].diff()
        ganancia = delta.where(delta > 0, 0)
        perdida = -delta.where(delta < 0, 0)
        avg_ganancia = ganancia.ewm(com=periodos - 1, adjust=False).mean()
        avg_perdida = perdida.ewm(com=periodos - 1, adjust=False).mean()
        rs = avg_ganancia / avg_perdida
        return 100 - (100 / (1 + rs))

    def calcular_sma(data, ventana=100):
        return data['Close'].rolling(window=ventana).mean()

    def calcular_sma50(data, ventana=50):
        return data['Close'].rolling(window=ventana).mean()

    def calcular_macd(data, slow=26, fast=12, sign=9):
        # 1. Calcular las EMAs (Medias Móviles Exponenciales)
        ema_fast = data['Close'].ewm(span=fast, adjust=False).mean()
        ema_slow = data['Close'].ewm(span=slow, adjust=False).mean()
    
        # 2. Calcular la línea MACD
        macd_line = ema_fast - ema_slow
        
        # 3. Calcular la línea de Señal (Signal Line)
        signal_line = macd_line.ewm(span=sign, adjust=False).mean()
        
        # 4. Calcular el Histograma
        histograma = macd_line - signal_line
        
        return macd_line, signal_line, histograma

    def macd_divergencias(data, macd_line):
        recents = macd_line.tail(30)
        last_prices = data['Close'].tail(30)
            
        if macd_line.iloc[-2] > signal_line.iloc[-2] and macd_line.iloc[-1] < signal_line.iloc[-1]:
            cruce_status = "RECENT BEARISH CROSS (Death Cross)"
        elif macd_line.iloc[-2] < signal_line.iloc[-2] and macd_line.iloc[-1] > signal_line.iloc[-1]:
            cruce_status = "RECENT BULLISH CROSS (Golden Cross)"
        else:
            cruce_status = "NO RECENT CROSS"
            

        mitad = len(recents) // 2 #Dividir el periodo en grupo A (30-15 dias) y B (ultimos 15 dias)

        #BULLISH DIVERGENCE DATA
        min_1 = recents.iloc[:mitad].min()
        min_2 = recents.iloc[mitad:].min()
        p_min_1 = last_prices.iloc[:mitad].min()
        p_min_2 = last_prices.iloc[mitad:].min()
        
        if p_min_2 < p_min_1 and min_2 > min_1:
            return "POSSIBLE BULLISH DIVERGENCE"
        
        #BEARISH DIVERGENCE DATA
        max_1 = recents.iloc[:mitad].max()
        max_2 = recents.iloc[mitad:].max()
        p_max_1 = last_prices.iloc[:mitad].max()
        p_max_2 = last_prices.iloc[mitad:].max()

        if p_max_2 > p_max_1 and max_2 < max_1:
            return "POSSIBLE BEARISH DIVERGENCE"
            
        return cruce_status

    def adx_indicator(data, period=14):
        df = data.copy()
        
        # 1. TR (True Range)
        df['h-l'] = df['High'] - df['Low']
        df['h-pc'] = abs(df['High'] - df['Close'].shift(1))
        df['l-pc'] = abs(df['Low'] - df['Close'].shift(1))
        df['TR'] = df[['h-l', 'h-pc', 'l-pc']].max(axis=1)

        # 2. DM (+DM y -DM)
        df['up'] = df['High'] - df['High'].shift(1)
        df['down'] = df['Low'].shift(1) - df['Low']
        
        df['+DM'] = 0.0
        df.loc[(df['up'] > df['down']) & (df['up'] > 0), '+DM'] = df['up']
        
        df['-DM'] = 0.0
        df.loc[(df['down'] > df['up']) & (df['down'] > 0), '-DM'] = df['down']
        
        # 3. Suavizado de Wilder (Punto clave para TradingView)
        # TradingView usa alpha = 1/periodo para el suavizado de Wilder
        alpha = 1 / period
        df['TR_smooth'] = df['TR'].ewm(alpha=alpha, adjust=False).mean()
        df['+DM_smooth'] = df['+DM'].ewm(alpha=alpha, adjust=False).mean()
        df['-DM_smooth'] = df['-DM'].ewm(alpha=alpha, adjust=False).mean()
        
        # 4. Calcular +DI y -DI
        df['+DI'] = 100 * (df['+DM_smooth'] / df['TR_smooth'])
        df['-DI'] = 100 * (df['-DM_smooth'] / df['TR_smooth'])
        
        # 5. Calcular DX y ADX
        df['DX'] = 100 * (abs(df['+DI'] - df['-DI']) / (df['+DI'] + df['-DI']))
        df['ADX'] = df['DX'].ewm(alpha=alpha, adjust=False).mean()
        
        return df['+DI'], df['-DI'], df['ADX']

    def calcular_atr(df, period=14):
        high = df['High']
        low = df['Low']
        close = df['Close'].shift(1)

        tr1 = high - low
        tr2 = abs(high - close)
        tr3 = abs(low - close)
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr_serie = tr.rolling(window=period).mean() #rolling y no ewm pq es swing trading, no scalping
        
        return atr_serie

    def puntuacion_noticias(text_analysis):
        prompt_news = f"""
        Vas a actuar como un analista de Wall Street. 
        Analiza el sentimiento financiero e impacto esperado en el precio de la acción del siguiente texto: '{text_analysis}'.
        Para ello debes considerar los siguientes aspectos:
        -Cambios en incertidumbre
        -Tono de la noticia
        -Sorpresas 
        -Actualizaciones en la calificación de la acción (upgrade/downgrade: buy/hold/sell)
        -Eventos extremos o revisiones de proyecciones negativas.

        Lo que sí debes ignorar:
        -Narrativa periodística
        -Opiniones sin respaldo por datos
    
        Devuelve un número entre -1.0 (pánico/muy bajista) y 1.0 (euforia/muy alcista).
        Si la noticia tuviera un verdadero impacto, evita responder con 0.0
        Responde ÚNICAMENTE con el número.
        """

        try:
            res = client.models.generate_content(model=nombre_real, contents=prompt_news)
            return float(res.text.strip()) #Strip = Elimina cualquier tipo de texto aparte del número. Bota el número solo (limpio)
        except Exception as e:
            print(f"Error en puntuación: {e}")
            return 0.0
        
    def obtener_win_rate(df, rsi_actual, adx_actual, macd_h_actual, precio_actual, sma50_actual, sma100_actual, direccion, mult_atr, ratio):    
        # 1. LIMPIEZA TOTAL: Eliminamos filas con datos faltantes para que las columnas midan lo mismo
        df_f = df.dropna(subset=['RSI', 'SMA_50', 'SMA_100', 'MACD_Hist', 'ADX']).copy()
        
        # 2. EXTRAEMOS LOS VALORES PUROS (Aquí está el truco)
        # Convertimos las columnas en arrays de numpy para que no tengan "etiquetas"
        rsi_vals = df_f['RSI'].values
        close_vals = df_f['Close'].values
        sma50_vals = df_f['SMA_50'].values
        sma100_vals = df_f['SMA_100'].values
        macd_vals = df_f['MACD_Hist'].values
        adx_vals = df_f['ADX'].values

        # --- LÓGICA DE FILTRO DE FRONTERA (RSI) ---
            # Si estamos cerca de zonas de reversión (70 o 30), reducimos el margen a +/- 2
            # Si estamos en zona neutral, mantenemos +/- 4
        if rsi_actual >= 65 or rsi_actual <= 35:
            margen_rsi = 2
            metodo_usado = "Strict Frontier (Critical Zone)"
        else:
            margen_rsi = 4
            metodo_usado = "Standard (Neutral Zone)"

        # 3. CREAMOS LA MÁSCARA USANDO LOS VALORES PUROS
        # Esto ya no puede fallar porque son solo listas de números
        mask = (
            (rsi_vals >= (rsi_actual - margen_rsi)) & (rsi_vals <= (rsi_actual + margen_rsi)) &
            ((macd_vals > 0) == (macd_h_actual > 0)) &
            (adx_vals > 20) &
            ((close_vals > sma50_vals) == (precio_actual > sma50_actual)) & #IZQUIERDA (PASADO) | DERECHA (PRESENTE)
            ((close_vals > sma100_vals) == (precio_actual > sma100_actual)) #Si en el presente, precio>sma50, bota True y busca q otros dias en el pasado tambien boto True.
                                                                            #Caso contrario, botaria False y buscaria en el pasado cuando marco False
        )

        eventos = df_f[mask].copy()

        # Si el filtro es demasiado estricto y no hay casos, relajamos un poco
        if len(eventos) < 10:
            mask_relax = (
                (rsi_vals >= (rsi_actual - 7)) & (rsi_vals <= (rsi_actual + 7)) &
                ((close_vals > sma50_vals) == (precio_actual > sma50_actual))
            )
            eventos = df_f[mask_relax].copy()

        resultados = []
        dias_duracion = []
        
        # 2. Simulación de los eventos encontrados
        for idx in eventos.index: #IDX = FECHA
            pos = df.index.get_loc(idx)
            if pos + 90 >= len(df): continue # Necesitamos ver el futuro
            
            futuro = df.iloc[pos + 1 : pos + 91] #MIRA LOS SIGUIENTES 90 DIAS. 
                                                 #Para hacerse la idea, 22 dias = 1 mes de mercado de acciones
                                                 #Lo configuramos para 90 dias, pq ganancias de casi 30% son dificiles de q ocurran en poco tiempo. 3 meses deberian de ser suficientes
            
            # AQUÍ ESTÁ EL TRUCO: Replicamos la lógica del usuario en cada día del pasado
            # Usamos el ATR que había EN ESE DÍA del pasado
            atr_pasado = df.loc[idx, 'ATR']
            distancia_sl_pasado = atr_pasado * mult_atr
            distancia_tp_pasado = distancia_sl_pasado * ratio
            precio_entrada_pasado = df.loc[idx, 'Close']

            if direccion == "Long":
                sl = precio_entrada_pasado - distancia_sl_pasado
                tp = precio_entrada_pasado + distancia_tp_pasado
                for i in range(len(futuro)):
                    if futuro['Low'].iloc[i] <= sl:
                        resultados.append(0)
                        dias_duracion.append(i + 1)
                        break
                    if futuro['High'].iloc[i] >= tp:
                        resultados.append(1)
                        dias_duracion.append(i + 1)
                        break

            elif direccion == "Short":
                sl = precio_entrada_pasado + distancia_sl_pasado
                tp = precio_entrada_pasado - distancia_tp_pasado
                for i in range(len(futuro)):
                    if futuro['High'].iloc[i] >= sl: # En Short el SL está arriba
                        resultados.append(0)
                        dias_duracion.append(i + 1)
                        break
                    if futuro['Low'].iloc[i] <= tp: # En Short el TP está abajo
                        resultados.append(1)
                        dias_duracion.append(i + 1)
                        break #Break sirve para detener bucles
                
        win_rate = np.mean(resultados) if resultados else 0.50
        avg_days = np.mean(dias_duracion) if dias_duracion else 0

        if len(resultados) == len(eventos):
                eventos['Resultado'] = resultados
        else:
            # Rellenar con ceros si hubo eventos sin futuro suficiente
            eventos['Resultado'] = (resultados + [0] * (len(eventos) - len(resultados)))[:len(eventos)]
        
        if len(dias_duracion) == len(eventos):
            eventos['Days_to_Close'] = dias_duracion

        # IMPORTANTE: Devolvemos las 3 cosas
        return win_rate, eventos, metodo_usado, avg_days
    
    MEMORY_FILE = "trading_memory.json"

    def guardar_trading_strategy_memoria(ticker, direccion, entrada, sl, tp, confianza):
        memoria = {}
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, 'r') as f:
                memoria = json.load(f)
        
        ahora = datetime.now()
        id_unico = f"{ticker}_{ahora.strftime('%Y%m%d_%H%M%S')}"
        #Esto creara un ID unico para cada ticker, independientemente si se trata de la misma accion.
        #(Ejemplo: "AXP_20260213_1945")

        # Guardamos el nuevo análisis con la fecha de hoy
        memoria[id_unico] = {
            "ticker": ticker,
            "direccion": direccion,
            "precio_entrada": entrada,
            "stop_loss": sl,
            "take_profit": tp,
            "confianza": confianza,
            "fecha": datetime.now().strftime("%Y-%m-%d")
        }
        
        #SI HAY MAS DE 20 ACCIONES EN MEMORIA, BORRAMOS EL MAS ANTIGUO
        if len(memoria) > 20:
            primer_ticker = list(memoria.keys())[0]
            del memoria[primer_ticker]

        with open(MEMORY_FILE, 'w') as f:
            json.dump(memoria, f, indent=4)
    
    def obtener_memoria_ticker(ticker):
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, 'r') as f:
                memoria = json.load(f)
                
                # 1. Filtramos todas las entradas que correspondan a ese ticker
                # Buscamos claves que empiecen con "AXP_"
                registros_ticker = [v for k, v in memoria.items() if k.startswith(f"{ticker}_")]
                
                if not registros_ticker:
                    return None
                
                # 2. Ordenamos por fecha (la más reciente primero)
                # Como guardamos la fecha en formato YYYY-MM-DD, nos sirve para ordenar
                registros_ordenados = sorted(registros_ticker, key=lambda x: x['fecha'], reverse=True)
                
                # 3. Retornamos el análisis más nuevo para que la IA lo compare
                return registros_ordenados[0]
        return None
    
    def calcular_monte_carlo(ticker, dias_proyectar=60, simulaciones=1000, precio_inicio=None):
        try:
            data = yf.download(ticker, period="1y", interval="1d", progress=False)
            if isinstance(data.columns, pd.MultiIndex):
                data = data.xs('Close', axis=1, level=0, drop_level=True)
            else:
                data = data['Close']
                
            if data.empty or len(data) < 30: return None

            # 1. Calculamos retornos porcentuales REALES del pasado
            precios = data.values.flatten()
            returns = precios[1:] / precios[:-1] # Esto nos da factores como 0.98, 1.02, etc.
            
            last_price = float(precios[-1])

            # ✅ usar precio entrada si existe
            if precio_inicio is not None:
                last_price = float(precio_inicio)
            
            # 2. SIMULACIÓN POR BOOTSTRAPPING (Muestreo real)
            # En lugar de normal distribution, elegimos retornos que ya pasaron
            simulaciones_retornos = np.random.choice(returns, size=(dias_proyectar, simulaciones))
            
            # 3. Creamos las trayectorias
            price_paths = np.zeros((dias_proyectar, simulaciones))

            # primer día = precio entrada
            price_paths[0, :] = last_price

            # construir trayectoria
            for t in range(1, dias_proyectar):
                price_paths[t, :] = price_paths[t-1, :] * simulaciones_retornos[t, :]
                
            return price_paths
            
        except Exception as e:
            print(f"Error en MC Bootstrapping: {e}")
            return None
    
    def validar_probabilidades_monte_carlo(paths, sl, tp):
        if paths is None: return 0, 0
        ex, fr = 0, 0
        tp, sl = float(tp), float(sl)
        precio_inicial = paths[0, 0] # El precio de hoy (donde empiezan las líneas)
        
        # LA REGLA DE ORO: Si el TP está por debajo del inicio, ¡es un Short!
        es_short = tp < precio_inicial 

        for i in range(paths.shape[1]):
            trayectoria = paths[:, i]
            
            if es_short:
                # En SHORT se gana si CAE
                d_tp = np.where(trayectoria <= tp)[0] # Éxito: choca el TP abajo
                d_sl = np.where(trayectoria >= sl)[0] # Fracaso: choca el SL arriba
            else:
                # En LONG se gana si SUBE
                d_tp = np.where(trayectoria >= tp)[0]
                d_sl = np.where(trayectoria <= sl)[0]
                
            p_tp = d_tp[0] if len(d_tp) > 0 else 99999
            p_sl = d_sl[0] if len(d_sl) > 0 else 99999
            
            if p_tp < p_sl: ex += 1 # Ganó el TP
            elif p_sl < p_tp: fr += 1 # Ganó el SL
                
        return ex, fr
    
    
    #-----------------------------------------------------------------------------------------------------------------------------------------

    # --- INICIALIZACIÓN DE CLIENTE ---
    if api_key:
        try:
            client = genai.Client(api_key=api_key)
            modelos = client.models.list()
            nombre_real = next((m.name for m in modelos if "flash" in m.name.lower()), "gemini-2.5-flash")
            st.sidebar.success(f"Connected to: {nombre_real}")
        except Exception as e:
            st.sidebar.error(f"Error de conexión: {e}")
            st.stop()

        # Buscador GLOBAL
        st.subheader("Buscador de Tickers o Empresas")
        st.info("Para evitar interrupciones en la conexión con los servidores de Yahoo Finance, le recomendamos realizar sus búsquedas de activos de forma pausada. " \
        "Así aseguramos que su acceso permanezca activo y sin bloqueos.")
        user_entry = st.text_input("Escribe el Ticker o el nombre de la empresa (ej: AAPL, TSLA):").upper()
    
        if user_entry:
            with st.spinner(f"Buscando información de: '{user_entry}'..."):
                try:
                    prompt_ticker = f"""
                    Instrucciones: 
                    Estamos analizando acciones de la bolsa de Nueva York (NYSE). 
                    En caso recibas el nombre de la empresa procede a darme el ticker oficial, RESPONDIENDO SOLO EL TICKER, SEGUN EL FORMATO DE YAHOO FINANCE. 
                    En caso recibas el ticker, limitate a simplemente a decirme el ticker de nuevo (copiar el prompt que recibes, RESPONDE SOLO EL TICKER).

                    Orden: 
                    Dime el ticker oficial de {user_entry}. Responde SOLO el ticker.
                    """
                    res_ticker = client.models.generate_content(model=nombre_real, contents=prompt_ticker)
                    actualizar_consumo_tokens(res_ticker) #<--------RASTREADOR DE TOKENS
                    ticker_input = res_ticker.text.strip().upper()

                    st.success(f"Empresa identificada, su ticker es: '{ticker_input}'.")
                
                    #-------------------CODIGO DE LIMPIEZA DE MEMORIA PARA VARIABLES ALMACENADAS EN LA MEMORIA DE STREAMLIT-------------------------
                    if 'ultimo_ticker' not in st.session_state:
                        st.session_state['ultimo_ticker'] = ticker_input

                    if st.session_state['ultimo_ticker'] != ticker_input:
                        # 1. Lista de llaves a fulminar
                        llaves_a_borrar = ['resultado_ia', 'analisis_final', 'puntos_noticias']
                        
                        for llave in llaves_a_borrar:
                            if llave in st.session_state:
                                st.session_state[llave] = None # Primero las hacemos None
                                del st.session_state[llave]    # Luego las borramos

                        # 2. Actualizamos el ticker de control
                        st.session_state['ultimo_ticker'] = ticker_input
                        
                        # 3. FORZAMOS EL REINICIO
                        st.rerun()
                        
                        if 'total_input' not in st.session_state:
                            st.session_state['total_input'] = 0
                        if 'total_output' not in st.session_state:
                            st.session_state['total_output'] = 0
                        if 'total_combined' not in st.session_state:
                            st.session_state['total_combined'] = 0
                        if 'intentos_diarios' not in st.session_state:
                            st.session_state['intentos_diarios'] = 0
                    #-------------------CODIGO DE LIMPIEZA DE MEMORIA DEL PUNTAJE DE NOTICIAS-------------------------

                except Exception as e:
            
                    st.error("No se pudo identificar la empresa.")
                    ticker_input = None           
        
        
            if ticker_input:
                try:
                    # 1. Obtenemos los datos de Yahoo Finance
                    ticker = yf.Ticker(ticker_input)
                    # 2. Obtén la información (esto es lo que te faltaba)
                    info = ticker.info
                    hist = ticker.history(period="1y")
                    time.sleep(3)
                    
                    if hist.empty:
                        st.error(f"❌ El ticker '{ticker_input}' no existe o no tiene datos.")
                    else:
                        # 2. Cálculos base
                        precio_actual = hist['Close'].iloc[-1]
                        precio_ayer = hist['Close'].iloc[-2]
                        rsi_serie = calcular_rsi(hist)
                        last_rsi = rsi_serie.iloc[-1]

                    variacion_absoluta = precio_actual - precio_ayer
                    variacion_porcentual = (variacion_absoluta / precio_ayer) * 100

                    st.sidebar.markdown("---")
                    modo_app = "🚀 Trading"  # Archivo separado: esta version SOLO contiene el Modo Trading
                    
                    tab_market = tab_about = tab_tech = tab_edge = tab_ai = tab_lab = None
                    
                    if modo_app == "🚀 Trading":
                        # MODO TRADING: Muestra Market, About, Technicals, Edge Finder, AI, Stats
                        # (Omitimos Portfolio y Earnings)
                        
                        tabs = st.tabs([
                            "🎥 Market Dashboard",   # Común
                            "🧬 About the Stock",    # Común
                            "📊 Technicals",         # Trading
                            "👨‍💻 Edge Finder Agent",  # Trading
                            "🤖 AIs",                # Trading 
                            "🔬 Trade Lab",           #Trading
                            "📒 Corporate Hub"
                                      
                        ])
                        tab_market, tab_about, tab_tech, tab_edge, tab_ai, tab_lab, tab_corp = tabs
                        
                        # Desempaquetamos en orden
                        


                    
                    with tab_market:
                        st.subheader("Live Market 🔴")
                        st.write("Here you'll find information about the current market status. There may be some minimum delays with the data.")

                        st.subheader("Standard & Poor's 500 Index (S&P500)")
                        with st.expander("What is the S&P500?"):
                            st.write("""
                                        Arguably the best benchmark for the Stock Market, the S&P500 Index tracks the 500 biggest public companies in the US, though 'biggest' might be a little ambiguous." 
                                        There's a special committee that decides which stock may enter the index. The main requirements are high liquidity, great market cap, and profitability.
                                        Indeed, only common stocks are allowed.                    
                                        """)
                        
                        with st.expander("Measurement:"):
                            st.write(f"""
                                    It's a market cap weighted index adjusted by free float (only shares that can be traded). This can create trouble such as giving a false lecture of the market. 
                                    Indeed, big names like Apple, Google, Nvidia account over 30% of the index. That's why some rather use the SP500 Equal Weight, where each stock has the same relevance (1/500).
                                    """)
                            st.latex(r"\text{S\&P 500} = \frac{\sum_{i=1}^{500} (\text{Price}_i \times \text{Q}_i)}{\text{Divider}}")
                            st.write(r"""
                                    **Where:**
                                    * $P_i$: Current price of the stock $i$.
                                    * $Q_i$: Number of shares available for the public (floating shares) $i$.
                                    * $\sum$: Summation of the index companies' market cap.
                                    * **Divider**: A number (in constant change) that ensures special events, such as *splits* or rotation of companies in the index, does not affect the index value.
                                    """)

                            st.latex(r"\text{Company's weight}_i = \frac{\text{Market Cap Float}_i}{\sum_{j=1}^{500} \text{Market Cap Float}_j}")

                        st.subheader(f"S&P500 vs {ticker_input}")
                        with st.expander("INFO:"):
                            st.write("""
                                        Here you can compare how your stock did during 1Y against the overall index.
                                        We take day 0 = 100 base, in order to be able to compare both items, considering SP500 levels are over 6000, while common stocks rarely get that price
                                        """)
                            
                        with st.expander("Calculation:"):
                            st.latex(r'''
                                    \text{Normalized Price} = \left( \frac{\text{Last Price}}{\text{Base Price (Day 0)}} \right) \times 100
                                    ''')
                            st.write("The calculation just requires the last price and initial price (day 0) of the asset in question. This allows to compare how well the asset did since day 0.")

                        sp500 = yf.Ticker("^GSPC")
                        sp500_hist = sp500.history(period="1y")

                        #CONVERSION A NUMEROS INDICE. EL "AÑO BASE=100" ES EL PRIMER DIA DEL AÑO.
                        stock_norm = hist['Close'] / hist['Close'].iloc[0] * 100
                        sp500_norm = sp500_hist['Close'] / sp500_hist['Close'].iloc[0] * 100

                        rendimiento_stock = (hist['Close'].iloc[-1] / hist['Close'].iloc[0]) - 1
                        rendimiento_sp500 = (sp500_hist['Close'].iloc[-1] / sp500_hist['Close'].iloc[0]) - 1

                        col_sp1, col_sp2 = st.columns(2)

                        with col_sp1:
                            st.metric(
                                label=f"Performance {ticker_input}", 
                                value=f"{stock_norm.iloc[-1]:.2f} pts", 
                                delta=f"{rendimiento_stock:.2%}"
                            )

                        with col_sp2:
                            st.metric(
                                label="Performance S&P 500", 
                                value=f"{sp500_norm.iloc[-1]:.2f} pts", 
                                delta=f"{rendimiento_sp500:.2%}"
                            )

                        # 5. Comparison Chart
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(x=hist.index, y=stock_norm, name=ticker_input, line=dict(color='#00CC96')))
                        fig.add_trace(go.Scatter(x=sp500_hist.index, y=sp500_norm, name="S&P 500", line=dict(color='white', dash='dash')))

                        fig.update_layout(
                            title="Relative Performance (Base 100 Index)",
                            template="plotly_dark",
                            yaxis_title="Index Value (Base 100)"
                        )

                        st.plotly_chart(fig, use_container_width=True)

                        st.divider()
                            
                        st.subheader("Dow Jones Industrial Average")
                        with st.expander("What is the DJ30?"):
                            st.write("""
                                    The Dow Jones Industrial Average (DJIA), often referred to as the Dow 30 or simply the Dow, once held the same symbolic importance for investors as the S&P 500 does today. It is composed of 30 major U.S. companies, selected to represent the backbone of the American economy and its evolving structure.
                                    Founded by Charles Dow in the late 19th century, the index originally began as a 12‑stock average. Over time, it expanded to 30 components and became one of the most widely followed benchmarks in global finance. Historically, Dow stocks were known for offering dividend yields higher than the overall market, although this trend has diminished in recent decades.
                                    Unlike the S&P 500, which is weighted by market capitalization, the Dow is a price‑weighted index. This means that companies with higher share prices exert a disproportionately greater influence on the index’s movements, regardless of their actual size or market value. While this methodology has often been criticized as outdated, the Dow remains a powerful market indicator and a symbol of U.S. economic strength.
                                     """)
                        with st.expander("Calculation:"):
                            st.latex(r"DJIA = \frac{\sum_{i=1}^{30} P_i}{D}")
                            st.write(":blue[$P_i$]: **Price** of each stock that makes up the index.")
                            st.write(":blue[$D$]: It's the **Dow Divider**, that adjusts the index when a company makes a stock split or leaves the index.")
                            

                        # Diccionario con sectores y empresas del Dow Jones (2026)
                        dow_components = {
                            "Technology": [
                                "Apple (AAPL)", "Microsoft (MSFT)", "NVIDIA (NVDA)",
                                "Amazon (AMZN)", "Intel (INTC)", "Cisco Systems (CSCO)", "Salesforce (CRM)", "International Business Machines (IBM)"
                            ],
                            "Financials": [
                                "JPMorgan Chase (JPM)", "Goldman Sachs (GS)",
                                "American Express (AXP)", "Visa (V)"
                            ],
                            "Healthcare": [
                                "Johnson & Johnson (JNJ)", "Amgen (AMGN)",
                                "UnitedHealth Group (UNH)", "Merck (MRK)"
                            ],
                            "Consumer & Retail": [
                                "Walmart (WMT)", "Home Depot (HD)", "McDonald’s (MCD)",
                                "Nike (NKE)", "Procter & Gamble (PG)",
                                "Coca-Cola (KO)", "PepsiCo (PEP)"
                            ],
                            "Industrials & Energy": [
                                "Boeing (BA)", "Caterpillar (CAT)", "Chevron (CVX)",
                                "3M (MMM)", "Honeywell (HON)"
                            ],
                            "Communication & Entertainment": [
                                "Verizon (VZ)", "Walt Disney (DIS)"
                            ],

                        }

                        df_dow = pd.DataFrame([ {"Sector": sector, "Company": company} for sector, companies in dow_components.items() for company in companies ])
                        st.markdown("### Dow Jones Components")
                        with st.expander("Here's the list of the 30 components of the Dow Jones Average"):
                            st.table(df_dow)
                        
                        st.markdown(f"### DJI vs {ticker_input}")
                        
                        dowjones30 = yf.Ticker("^DJI")
                        dowjones30_hist = dowjones30.history(period="1y")

                        dow30_norm = dowjones30_hist['Close']/dowjones30_hist['Close'].iloc[0]*100

                        rendimiento_dow30 = (dowjones30_hist['Close'].iloc[-1] / dowjones30_hist['Close'].iloc[0]) - 1
                        rendimiento_stock = (hist['Close'].iloc[-1] / hist['Close'].iloc[0]) - 1

                        col1_dow, col2_dow = st.columns(2)

                        with col1_dow:
                            st.metric(
                                label=f"Performance {ticker_input}", 
                                value=f"{stock_norm.iloc[-1]:.2f} pts", 
                                delta=f"{rendimiento_stock:.2%}"
                            )
                        
                        with col2_dow:
                            st.metric(
                                label="Performance S&P 500", 
                                value=f"{dow30_norm.iloc[-1]:.2f} pts", 
                                delta=f"{rendimiento_dow30:.2%}"
                            )
                        
                        st.divider()

                        st.subheader("Volatility Index (VIX)")
                        with st.expander("What is the VIX?"):
                            st.write("The VIX is the best metric to track Market's volatility and high risk periods.")
                            st.write("The CBOE Volatility Index measures the expected volatility for the S&P 500 the following 30 days, using options' prices as basis. As the VIX tries to predict the next 30 days, it uses options that expire in 23-37 days. If traders believe there will be a trigger soon, they buy options to protect their equity stake. VIX considers hundreds of calls and puts on the index with strikes around the index level, this way, options work as an implied volatility.")
                            st.write("In finance theory, if you have all the options for different strikes, you can reconstruct the expected variance of the index.")
                            st.write("VIX is calculated following this formula: ")
                            st.latex(r"""
                            \sigma^2 = \frac{2}{T} \sum_{i} \frac{\Delta K_i}{K_i^2} e^{rT} Q(K_i)
                            - \frac{1}{T} \left(\frac{F}{K_0} - 1\right)^2
                            """)
                            st.latex(r"""
                            VIX = 100 \times \sqrt{\sigma^2}
                            """)
                            st.markdown(r"""
                            **Where:**

                            - \(T\) = expiration date 
                            - \(K_i\) = strike 
                            - \(\Delta K_i\) = distancia between strikes  
                            - \(Q(K_i)\) = price of the option (put o call)  
                            - \(F\) = forward of the index
                            - \(K_0\) = strike closest to the forward  
                            - \(r\) = free risk rate
                            """)

                        vix_data = yf.download("^VIX", period="2y")
                        close_col = vix_data['Close']
                        if isinstance(close_col, pd.DataFrame):
                            vix_series = close_col.iloc[:, 0].dropna()
                        else:
                            vix_series = close_col.dropna()                        
                        ultimo_vix = float(vix_series.iloc[-1])
                        vix_previo = float(vix_series.iloc[-2])
                        delta_vix = ultimo_vix - vix_previo
                        percentil_vix = (vix_series < ultimo_vix).mean() * 100

                        col_vix, col_info = st.columns([1, 2])

                        with col_vix:
                            # El delta aquí es inverso: si sube el VIX, es "malo" (rojo)
                            st.metric("VIX Index", f"{ultimo_vix:.2f}", f"{delta_vix:.2f}", delta_color="inverse")

                        with col_info:
                            if ultimo_vix < 15:
                                st.success("✅ **Low volatility:**")
                            elif 15 <= ultimo_vix <= 25:
                                st.warning("🟡 **Medium volatility:**")
                            else:
                                st.error("🔥 **High Volatility:**")

                        st.line_chart(vix_series)
                        
                        st.write(f"VIX is at **{percentil_vix:.1f} percentile**")
                        st.caption(f"This means that the VIX is higher than on {percentil_vix:.1f}% of the days in the period you are measuring (in this case 2 years).")

                        st.divider()

                        st.subheader("Market Summary:")
                        st.info("Daily market recap: price action, news flow, and main catalysts.")

                        st.subheader("Oversold stocks tracker")
                        st.write("Upload your watchlist and the script will identify stocks with significant moves.")

                        @st.cache_data(ttl=600) # Guarda los resultados por 1 hora
                        def ejecutar_analisis_cached(lista_tickers):
                            # Aquí llamamos a tu función matemática
                            return scanner_oportunidades(lista_tickers)
                    
                        # --- EN LA INTERFAZ DE STREAMLIT ---
                        # --- SECCIÓN DE WATCHLIST ---
                        input_raw = st.text_area("Paste your watchlist:") 
                        st.write("Please insert it into excel format. The program assumes each ticker is a row in your watchlist.")                        
                        
                        # --- REEMPLAZO DE LA IA POR LÓGICA PURA ---
                        if input_raw:
                            # .split() sin argumentos separa automáticamente por cualquier espacio en blanco o salto de línea
                            # .strip() quita espacios basura y .upper() asegura que Yahoo Finance lo entienda
                            lista_final = [t.strip().upper() for t in input_raw.split() if t.strip()]

                            if lista_final:
                                st.success(f"✅ {len(lista_final)} tickers detected from your column.")

                            if lista_final:
                                
                                #El scanner de Python hace el trabajo pesado con los datos
                                with st.spinner("Calculating punished stocks"):
                                    resultados = scanner_oportunidades(lista_final)
                                if resultados:
                                    st.markdown(f"### 🚨 Found {len(resultados)} Rebounce Opportunities")
                                    
                                    # Creamos columnas para que no sea una lista larga hacia abajo
                                    cols = st.columns(2) 
                                    
                                    for idx, op in enumerate(resultados):
                                        # Usamos el operador % 2 para repartir entre la col 1 y col 2
                                        with cols[idx % 2]:
                                            with st.container(border=True):
                                                st.error(f"**Ticker: {op['Ticker']}**")
                                                
                                                # Mostramos los datos que calculó tu función
                                                m1, m2 = st.columns(2)
                                                try:
                                                    val_rsi = float(op['RSI'])
                                                    m1.metric("RSI", f"{val_rsi:.2f}")
                                                except:
                                                    m1.metric("RSI", str(op['RSI']))
                                                
                                                # --- Formateo seguro de Caída ---
                                                try:
                                                    # Limpiamos el texto por si ya trae el %
                                                    clean_drop = str(op['Caída %']).replace('%', '').strip()
                                                    val_drop = float(clean_drop)
                                                    m2.metric("2W Drop", f"{val_drop:.1f}%")
                                                except:
                                                    m2.metric("2W Drop", str(op['Caída %']))
                                                
                                else:
                                    # Si la función devolvió una lista vacía []
                                    st.info(f"No stocks found with RSI < 35 and Drop > 10% in your watchlist.")

                    with tab_about:
                        col1, col2 = st.columns([1, 2])
                        with col1:
                            st.metric(
                            label="Last Price", 
                            value=f"${precio_actual:.2f}",
                            delta=f"{variacion_absoluta:.2f} ({variacion_porcentual:.2f}%)"
                            )
                        with col2:
                            st.line_chart(hist['Close'])
                        
                        st.divider()

                        st.subheader(f"Key Fundamentals of {ticker_input}")

                        m1, m2, m3, m4 = st.columns(4)

                        with m1:
                            pe_ratio = info.get('trailingPE', 'N/A')
                            st.metric("P/E Ratio", f"{pe_ratio:.2f}" if isinstance(pe_ratio, (int, float)) else "N/A")

                        with m2:
                            eps = info.get('trailingEps', 'N/A')
                            val_eps = f"${eps:.2f}" if isinstance(eps, (int, float)) else "N/A"
                            st.metric("Diluted EPS (TTM)", val_eps) #Diluted EPS = Suma acciones comunes + acciones potenciales (opciones, warrants, preferentes, bonos convertibles)

                        with m3:
                            # El EBITDA suele ser un número muy grande, lo simplificamos
                            ebitda = info.get('ebitda', 0)
                            if isinstance(ebitda, (int, float)) and ebitda > 0:
                                ebitda_fmt = f"${ebitda/1e9:.2f}B" if ebitda >= 1e9 else f"${ebitda/1e6:.2f}M"
                            else:
                                ebitda_fmt = "N/A"
                            st.metric("EBITDA", ebitda_fmt)

                        with m4:
                            div_rate = info.get('dividendRate', 0)
                            val_div = f"${div_rate:.2f}" if isinstance(div_rate, (int, float)) else "0.00"
                            st.metric("Dividend Rate", val_div)
                        
                        n5, n6, n7, n8 = st.columns(4)

                        with n5:
                            fwd_pe_ratio = info.get('forwardPE', 'N/A')
                            st.metric("Forward P/E Ratio", f"{fwd_pe_ratio:.2f}" if isinstance(fwd_pe_ratio, (int, float)) else "N/A")

                        with n6:
                            roe = info.get('returnOnEquity', 'N/A')
                            if isinstance(roe, (int, float)):
                                val_roe = f"{roe * 100:.2f}%"
                            else:
                                val_roe = "N/A"
                            st.metric("ROE (Return On Equity)", val_roe)

                        with n7:
                            pb_ratio = info.get('priceToBook', 'N/A')
                            val_pb = f"{pb_ratio:.2f}x" if isinstance(pb_ratio, (int, float)) else "N/A"
                            st.metric("P/B Ratio", val_pb)

                        with n8:
                            earnings_growth_yoy = info.get('earningsQuarterlyGrowth', 'N/A')

                            if isinstance(earnings_growth_yoy, (int, float)):
                                val_growth = f"{earnings_growth_yoy * 100:.2f}%"
                                # Opcional: Mostrar en verde si es positivo, rojo si es negativo
                                delta_color = "normal" if earnings_growth_yoy >= 0 else "inverse"
                            else:
                                val_growth = "N/A"
                                delta_color = "off"
                                
                            st.metric("Earnings Growth (YoY)", val_growth)

                        st.caption("Source: Yahoo Finance")    

                        st.divider()

                        st.subheader("Fundamentals Guide 📜")
                        
                        with st.expander("What is EPS?"):
                            st.write("""
                                    Earnings per Share is the Total Income divided by the Outstanding Shares. It shows how much the firm earns for each stock. 
                                    Net Income = 1000
                                    Outstanding Shares = 100
                                    EPS = 10, in theory, each stock receives 10 dollars of the earnings. 
                                    Generally speaking, the higher the EPS, the more profitable is considered the firm.
                                    As there're other types of shares besides common shares, we add the term diluted. Stock options, warrants or convertible bonds are those convertible instruments that expand the number of outstanding shares.

                                    **Note that a company can game its EPS by buying back stock, which reduces the amount of Outstanding Shares (Denominator).** As wel as changes in the accounting policy of the company, that could distort the EPS. 
                                    EPS doesn't use the stock's price in its calculation so it is not used to judge if the price is over/undervalued.
                                """)
                            st.write("Basic EPS Formula:")
                            st.latex(r"\text{Basic EPS} = \frac{\text{Net Income} - \text{Preferred Dividends}}{\text{Weighted Average Common Shares}}")
                            st.write("Basic EPS doesn't take into account the convertible instruments. Preferred Dividends are subtracted because they don't go to common shareholders, these dividends have priority. ")
                            st.write("We use the Weighted Average because during the year, new shares can be (and oftenly are) issued.")
                            st.write("Diluted EPS Formula: ")
                            st.latex(r"EPS Diluted = \frac{Net\ Income - Preferred\ Dividends \pm Nonrecurring\ Items}{Weighted\ Average\ Common\ Shares\ Outstanding}")

                            st.write("""
                                    Nonrecurring Items:
                                     
                                    It is the calculus of the EPS excluding rare and allegedly unique events that could distort the EPS image.
                                    A company that builds computer screens has 2 factories, but sells one. That will modify the Income Statement and increase the Net Income, but not due to a better performance from the firm. 
                                    The same way happens with negative events like a fire or extraordinary demand.
                                """)
                            
                            st.write("Dividends and Capital:")
                            st.write("""
                                    Unfortunately for the shareholder, you don't have direct access to those earnings. Some portion may be distributed through dividends, but it is not mandatory.
                                    The firm has total freedom to retain those earnings to keep growing or buy-back programs.

                                    Another problem that few ask themselves is where did the earnings (Net Income) come from? It could be possible that one company obtained those earnings with little assets, but has the same EPS as another company that invested much more. 
                                    Simply looking at their EPS could give the wrong idea that both are equally good.
                                """)

                        with st.expander("What is P/E Ratio?"):
                            st.write("""
                                    The Price/Earnings Ratio is mainly used for 2 reasons. First, it indicates how many times the market is paying for what the stock is actually earning. It's a basic but powerful tool to see if the stock might be overvalued. 
                                    Historically, a P/E > 20 has been considered too high, but valuations tend to go up over time, so it shouldn't be a fixed condition. 
                                    It should always be compared to the industry average and your own history to get an accurate diagnosis.
                                """)

                        with st.expander("What is P/B Ratio?"):
                            st.write("Price-to-Book Ratio is a metric that compares the company's Market Value against its Book Value (Total Assets - Total Liabilities) that would be the same as the shareholders' equity.")
                            st.write("This ratio is often used to find potential undervalued stocks. It shows the value given by the market for the company's net worth.")
                            st.write("Formula: ")
                            st.latex(r"\text{P/B} = \frac{\text{Price per Share}}{\text{Book Value per Share}}")
                            st.write("Book Value Formula:")
                            st.latex(r"\text{Book Value} = \text{Total Assets} - \text{Total Liabilities}")
                            st.write("Book Value per Share = (Total assets - total liabilities) ÷ number of outstanding shares")
                            st.write("Though almost every site shows the firm's book value, you could also calculate it manually by looking at the Balance Sheet of the firm.")
                            st.write("Tangible Book Value (TBV) is another metric closely watched and that is used in the Price/TBV. TBV consists on the total book value less intangible assets. It's also called hard book value and is used when intangible assets such as patterns are hard to value.")
                            st.write("""
                                    Limitations:
                                     
                                    P/B can be really useful when a firm reports negative earnings, because the P/E will turn negative and give a false alarm. Instead, the P/B could remain positive, due to positive book value (it's rare for a company to report negative books.)
                                    
                                    However, P/B has limitations. For instance, if accounting standards vary, Book Value could be calculated different while comparing companies.
                                    P/B does not take into account intangible assets, which in tech companies in particular, have great value. Intangible assets refers to human capital, brand, software and intellectual property.
                                    Buyback programs also reduce equity, which translates into a higher P/B. Other artificial variations to the ratio could be recent acquisitions or write-offs (punishments).
                                     """)
                            st.write("Good P/B range:"
                                     
                            "The P/B ratio has been favored by value investors for decades and is widely used by market analysts. Traditionally, any value under 1.0 is considered desirable for value investors, indicating an undervalued stock may have been identified. However, some value investors may often consider stocks with a less stringent P/B value of less than 3.0 as their benchmark.")
                            
                        with st.expander("What is Fwd. P/E?"):
                            st.write("")
                        
                        with st.expander("What is EBITDA?"):
                            st.write("EBITDA stands for Earnings Before Interest, Taxes, Depreciation and Amortization. It's a key metric because it shows the company's core profitability from its main operation. It's mainly used to compare the performance of the firm across its sector.")
                            st.write("Formula: ")
                            
                        
                        st.caption("Sources: Investopedia, Banco Santander")
                        st.divider()

                        st.subheader(f"📚 Get to know more about {ticker_input}")

                        st.write("With the following button, you'll be able to learn a bit more about the business. It's history, sector and business model.")

                        #BOTON PARA CONOCER SOBRE LA EMPRESA:
                        if st.button(f"Learn from {ticker_input}"):
                                with st.spinner("Gemini is investigating..."):
                                    system_prompt = "Estamos analizando acciones del NYSE." \
                                    "Cuando te pida información de una empresa, responde con Nombre, Descripción, Historia, Sector y Modelo de negocio."
                                    prompt = f"Analiza la empresa {ticker_input}."
                                    res = client.models.generate_content(model=nombre_real, contents=prompt, config={"system_instruction": system_prompt})
                                    actualizar_consumo_tokens(res) #<------RASTREADOR DE TOKENS
                                    st.info(res.text)
                
                    #-------------------------------SEPARADOR DE MODOS----------------------------------------
                    
                    if modo_app == "🚀 Trading":
                        
                        with tab_tech:
                            st.subheader(f"Technical Indicators of {ticker_input}")
                            st.info("Analyze the potential of a firm through technical analysis")
                            st.warning("Using only one indicator to operate is highly tricky and unlikely to work effectively.")
                            st.divider()

                            st.subheader("Trend & Structure")
                            st.write("Indicators that reflect the current 'health' of the asset.")

                            st.subheader("Simple Moving Average")
                            
                            with st.expander("What is the SMA?"):
                                    st.write(f"""
                                            Simple moving averages (SMAs) are a way to smooth out data by calculating the average of values over a specific time period, with that period constantly 'moving' forward. 
                                            It's important to note that SMAs won't eliminate noise, but soften it. 
                                            Random fluctuations (noise) tend to go both up and down. When you average them together, the ups and downs partially cancel each other out, leaving the genuine directional movement more visible.
                                            In finance, and in this app, they're used to track possible buy/sell signals, as well as support/resistance levels.
                                            """)

                            st.markdown("### Simple Moving Average (SMA) 100")
                            
                            sma_100 = calcular_sma(hist, 100)
                            ultimo_sma = sma_100.iloc[-1]
                            precio_actual = hist['Close'].iloc[-1]

                            col_sma1, col_sma2 = st.columns([1, 2])

                            with col_sma1:
                            # Mostramos el valor del SMA y si el precio está por encima o debajo
                                diferencia = precio_actual - ultimo_sma
                                st.metric(
                                label="SMA 100 Days", 
                                value=f"${ultimo_sma:.2f}", 
                                delta=f"{diferencia:.2f} vs Price"
                                )

                                with st.expander("Formula:"):
                                    st.latex(r"\text{SMA}_n(t) = \frac{1}{n}\sum_{i=0}^{n-1} P_{t-i}")
                
                                if precio_actual > ultimo_sma:
                                    st.success("Bullish Trend (Price > SMA 100)")
                                else:
                                    st.warning("Bearish Trend (Price < SMA 100)")

                            with col_sma2:
                                # Gráfico comparando Precio vs SMA
                                st.write("Price vs Moving Average 100 Days")
                                # Creamos un dataframe solo para el gráfico
                                comparativa = pd.DataFrame({
                                'Price': hist['Close'],
                                'SMA 100': sma_100
                                })
                                st.line_chart(comparativa)

                            st.markdown("### Simple Moving Average (SMA) 50")

                            sma_50 = calcular_sma50(hist, 50)
                            ultimo_sma50 = sma_50.iloc[-1]
                            precio_actual = hist['Close'].iloc[-1]

                            col_sma50a, col_sma50b = st.columns([1, 2])

                            with col_sma50a:
                                diferencia50 = precio_actual - ultimo_sma50
                                st.metric(
                                label="SMA 50 Days", 
                                value=f"${ultimo_sma50:.2f}", 
                                delta=f"{diferencia50:.2f} vs Precio"
                                )

                                if precio_actual > ultimo_sma50:
                                    st.success("Tendencia Alcista (Precio > SMA 50)")
                                else:
                                    st.warning("Tendencia Bajista (Precio < SMA 50)")

                            with col_sma50b:
                                # Gráfico comparando Precio vs SMA
                                st.write("Precio vs Media Móvil 50 días")
                                # Creamos un dataframe solo para el gráfico
                                comparativa = pd.DataFrame({
                                'Precio': hist['Close'],
                                'SMA 50': sma_50
                                })
                                st.line_chart(comparativa)


                            st.divider()

                            st.subheader("Momentum & Velocity")
                            st.write("These won't tell you the direction, but the strenght of the , the dominant bullish/bearish trend, and how fast is it moving.")
                            st.write("Usually try to predict the market, so the trader can act before the price. They're also helpful to determine if the trend is sustained or running out of steam.")

                            st.subheader("RSI")

                            col_rsi1, col_rsi2 = st.columns([1, 2])

                            with col_rsi1:
        
                                distancia = last_rsi - 50
                                st.write("Fórmula aplicada:")
                                st.latex(r"RSI = 100 - \left( \frac{100}{1 + RS} \right)")
                                
                                with st.expander("What is RSI?"):
                                    st.write("The Relative Strength Index measures the speed and change of price movements. " \
                                    "RSI does not tell you whether the stock is actually overvalued or undervalued, but how fast it's moving, hence you can tell if people are over buying/selling the stock. " \
                                    "It can help with the entry/exit timing of the trade. However, it does not work well for long term or extraordinary market conditions.")

                                with st.expander("Guide"):
                                    st.error("RSI < 30 is normally a sign of an oversold asset. It means that there could be potential room for rebounds.")
                                    st.success("RSI > 70 is normally a sign of an overbought asset. It means that there could be potential room for drops.")

                                if last_rsi > 70: 
                                    st.error("OVERBOUGHT")
                                
                                elif last_rsi < 30: 
                                    st.success("OVERSOLD")
                                
                                else: 
                                    st.info("HOLD/WAIT")

                                st.write("OVERBOUGHT = Price has risen too sharply and fast in the last 14 days.")
                                st.write("OVERSOLD = Price has dropped too sharply and fast in the last 14 days.")

                            with col_rsi2:
                                color_rsi = "inverse" if last_rsi > 70 else "normal" if last_rsi < 30 else "off"
                                st.metric("RSI (14D)", f"{last_rsi:.2f}", delta=f"{distancia:.2f} vs 50", delta_color=color_rsi)
                                st.line_chart(rsi_serie)
                                                
                            st.subheader("MACD")
                            
                            macd_line, signal_line, hist_macd = calcular_macd(hist)

                            # 2. Preparamos los datos más recientes para las métricas
                            ultimo_macd = macd_line.iloc[-1]
                            ultima_signal = signal_line.iloc[-1]
                            ultimo_hist = hist_macd.iloc[-1]

                            col_macd1, col_macd2 = st.columns([1, 2])

                            
                            # Métrica principal
                            st.metric(label="MACD Line", value=f"{ultimo_macd:.2f}", delta=f"{ultimo_hist:.2f} (Hist)")
            
                                # Interpretación simple
                            if ultimo_macd > ultima_signal:
                                st.success("Bullish signal")
                            else:
                                st.error("Bearish signal")
            
                            st.write("Intersections between both the MACD and Signal Lines suggests changes in the trend of the asset.")

                            st.write("THOUGH, simple intersections can give false alarms. Hence, it's better to check above, for divergencies")
                            
                            with col_macd1:

                                divergence_message = macd_divergencias(hist, macd_line)
                                with st.expander("What is MACD?"):
                                    st.write("The Moving Average Convergence Divergence is an indicator that reflects momentum and trend's direction of the stock.")

                                if "BULLISH" in divergence_message:
                                    st.success(f"🚀 {divergence_message}: Price keeps dropping but it might be close to it's local min. Pay attention for rebounds!")
                                
                                elif "BEARISH" in divergence_message:
                                    st.error(f"⚠️ {divergence_message}: Price could be running out of steam. Careful for possible drops!")
                                
                                else:
                                    st.info(divergence_message)

                            with col_macd2:
                                # Gráfico de las líneas MACD y Signal
                                # 1. Gráfico de las líneas MACD y Signal (Líneas de Streamlit)
                                st.write("MACD & Signal Lines")
                                df_lineas_macd = pd.DataFrame({
                                'MACD': macd_line,
                                'Signal': signal_line
                                })
                                st.line_chart(df_lineas_macd)


                                colors_macd = ['#00ff00' if x > 0 else '#ff0000' for x in hist_macd]
                                #Llama a Plotly 
                                fig_hist = go.Figure()

                                #Definimos el tipo de gráfico que queremos q haga
                                fig_hist.add_trace(go.Bar(
                                x=hist.index, 
                                y=hist_macd,
                                marker_color=colors_macd, # Aplicamos la lista de colores
                                name='Histogram'
                                ))

                                #Configuracion del diseño
                                fig_hist.update_layout(
                                template='plotly_dark',
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                margin=dict(l=0, r=0, t=0, b=0),
                                height=250,
                                showlegend=False # No necesitamos leyenda para el histograma
                                )

                                st.plotly_chart(fig_hist, use_container_width=True)

                            st.subheader("Average Directional Index (ADX)")

                            plus_di, minus_di, adx_serie = adx_indicator(hist)
                            
                            last_adx = adx_serie.iloc[-1]
                            #+DI = PDI & -DI = MDI ----------> DIRECTION INDICATORS
                            last_pdi = plus_di.iloc[-1]
                            last_mdi = minus_di.iloc[-1]

                            col_adxa, col_adxb = st.columns([1, 2])

                            with col_adxa:

                                st.metric("ADX Strength", f"{last_adx:.2f}")
                                with st.expander("What is ADX?"):
                                    st.write("The ADX is another indicator that measures the strenght of the trend, regardless its direction." \
                                    "In other words, the index can give you a hint of how fast the asset's movement is.")

                                with st.expander("Guide"):
                                    st.error("ADX < 20: SIDE MARKET, which means there is not clear path in the moves.")
                                    st.warning("20 < ADX < 25: Weak or Sideways market. There is not a defined trend yet.")
                                    st.success("25 < ADX < 40: Strong Trend. The movements have a defined direction")
                                    st.error("40 < ADX: Extremely strong trend, possible incoming exhaustion of the move.")


                                if last_adx < 20:
                                    st.error("Side Market")
                                elif last_adx > 20 and last_adx < 25:
                                    st.warning("Weak or No Defined Trend (Sideways)")
                                elif last_adx > 25 and last_adx < 40:
                                    st.success("Strong trend")
                                else:
                                    st.warning("Very strong trend, possible Exhaustion")

                                if last_pdi > last_mdi:
                                    st.write("🟢 **Bulls in control** (+DI > -DI)")
                                else:
                                    st.write("🔴 **Bears in control** (-DI > +DI)")

                            with col_adxb:
                                # Gráfico de las 3 líneas (ADX, +DI, -DI)

                                fig_adx = go.Figure()
                                #Linea ADX BLANCA
                                fig_adx.add_trace(go.Scatter(x=hist.index, y=adx_serie, name='ADX', line=dict(color='white', width=3)))
                                # Línea +DI (Verde)
                                fig_adx.add_trace(go.Scatter(x=hist.index, y=plus_di, name='+DI (Bulls)', line=dict(color='#00ff00')))
                                # Línea -DI (Roja)
                                fig_adx.add_trace(go.Scatter(x=hist.index, y=minus_di, name='-DI (Bears)', line=dict(color='#ff0000')))

                                fig_adx.update_layout(
                                template='plotly_dark',
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                margin=dict(l=0, r=0, t=0, b=0),
                                height=350,
                                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                                )

                                st.plotly_chart(fig_adx, use_container_width=True)
                            
                            st.subheader("📊 Smart Money Tracker (Volume Analysis)")

                            # --- CÁLCULOS AVANZADOS ---
                            # Media y Desviación para detectar anomalías reales
                            vol_mean = hist['Volume'].rolling(window=20).mean()
                            vol_std = hist['Volume'].rolling(window=20).std()
                            umbral_spike = vol_mean + (vol_std * 2) # Nivel estadístico de "Smart Money"

                            vol_actual = hist['Volume'].iloc[-1]
                            avg_vol_actual = vol_mean.iloc[-1]
                            es_anomalo_pro = vol_actual > umbral_spike.iloc[-1]

                            vol_ratio = vol_actual / avg_vol_actual if avg_vol_actual != 0 else 0

                            # --- UI DE IMPACTO ---
                            v_col1, v_col2 = st.columns([1, 2])

                            with v_col1:
                                st.metric("Volume Intensity", f"{vol_ratio:.2f}x", 
                                        delta=f"{(vol_ratio-1)*100:.1f}%", help="Ratio vs 20-day average")
                                
                                if es_anomalo_pro:
                                    st.success("💎 **INSTITUTIONAL ACTIVITY**\n\nVolume exceeds 2 standard deviations. Big institutions are likely involved.")
                                elif vol_actual > vol_mean.iloc[-1]:
                                    st.info("📈 **HEALTHY PARTICIPATION**\n\nAbove average volume. Supporting current price action.")
                                else:
                                    st.warning("⚠️ **LOW CONVICTION**\n\nRetail-dominated volume. Price moves might be fragile.")

                            with v_col2:
                                hist_tail = hist.tail(30).copy()
                                
                                # --- EL FIX AQUÍ ---
                                # Si por alguna razón no hay 'Open', comparamos el Close actual con el Close anterior
                                if 'Open' in hist_tail.columns:
                                    colors = ['#00ff00' if r['Close'] >= r['Open'] else '#ff0000' for _, r in hist_tail.iterrows()]
                                else:
                                    # Si no hay Open, usamos la diferencia diaria del Close
                                    diff = hist_tail['Close'].diff().fillna(0)
                                    colors = ['#00ff00' if v >= 0 else '#ff0000' for v in diff]
                                # -------------------

                                fig_vol = go.Figure()
                                fig_vol.add_trace(go.Bar(
                                    x=hist_tail.index, 
                                    y=hist_tail['Volume'],
                                    marker_color=colors,
                                    name='Volume'
                                ))
                                
                                fig_vol.add_trace(go.Scatter(
                                    x=hist_tail.index, 
                                    y=vol_mean.tail(30),
                                    line=dict(color='white', dash='dot'),
                                    name='Avg'
                                ))
                                
                                fig_vol.update_layout(height=250, margin=dict(l=0,r=0,t=0,b=0), template="plotly_dark", showlegend=False)
                                st.plotly_chart(fig_vol, use_container_width=True)
                                st.write("RED = Bearish dominance (close price ended lower) that day")
                                st.write("GREEN = Bullish dominance that day")

                        with tab_edge:
                            
                            st.subheader("Risk-Adjusted Analysis")
                            st.write("With the gathered data, the AI Agent will now recommend how to operate with the stock. " \
                            "Whether to go short or long, search for possible price targets and formulate your order.")
                            st.write("Not that data was collected on a daily basis (D1), which is basically meant for Swing Trading, not Scalping.")                

                            def limpiar_dato(v):
                                try:
                                    # Si tiene iloc, extraemos el último y convertimos a float
                                    return float(v.iloc[-1]) if hasattr(v, 'iloc') else float(v)
                                except:
                                    return 0.0
                            
                            macd_reciente = limpiar_dato(ultimo_macd)
                            macd_anterior = limpiar_dato(macd_line.iloc[-10])

                            macd_line, signal_line, histograma = calcular_macd(hist)
                            diagnostico_div = macd_divergencias(hist, macd_line)

                            h_actual = histograma.iloc[-1]
                            h_anterior = histograma.iloc[-10]

                            # Extraemos secuencias de 3 días
                            precios_3d = hist['Close'].tail(3).tolist()
                            sma50_3d = sma_50.tail(3).tolist()   # Asegúrate de usar la serie, no solo el último valor
                            sma100_3d = sma_100.tail(3).tolist()
                            rsi_3d = rsi_serie.tail(3).tolist()
                            h_3d = histograma.tail(3).tolist()
                            adx_3d = adx_serie.tail(3).tolist()

                            # Formateamos a strings para el prompt
                            precios_str = " -> ".join([f"${x:.2f}" for x in precios_3d])
                            sma50_str = " -> ".join([f"${x:.2f}" for x in sma50_3d])
                            sma100_str = " -> ".join([f"${x:.2f}" for x in sma100_3d])
                            rsi_str = " -> ".join([f"{x:.1f}" for x in rsi_3d])
                            h_str = " -> ".join([f"{x:.4f}" for x in h_3d])

                            datos_ticker = f"""
                            [DATA FEED]
                            - TICKER: {ticker_input}
                            - 1. DINÁMICA DE PRECIO Y MEDIAS:
                                - PRECIO: {precios_str}
                                - SMA 50: {sma50_str}
                                - SMA 100: {sma100_str}
                            
                            - 2. MOMENTUM E IMPULSO:
                                - RSI (14): {rsi_str}
                                - MACD HIST: {h_str}
                                - ADX (14): {" -> ".join([f"{x:.1f}" for x in adx_3d])}
                            
                            3. ESTADO ACTUAL:
                                - VOLUME RATIO: {limpiar_dato(vol_ratio):.2f}
                                - MACD DIVERGENCIAS: {diagnostico_div}
                            """

                            def obtener_analisis_ia(datos_ticker):
                                # Si datos_ticker es un string (ej: "AAPL"), lo convertimos a diccionario
                                # 1. IDENTIFICACIÓN
                                # Como 'datos_ticker' ahora es un f-string, usamos la variable global 
                                # ticker_input para identificar la acción en la memoria.
                                ticker_nombre = ticker_input 

                                # 2. MEMORIA
                                memoria_previa = obtener_memoria_ticker(ticker_nombre)
                                
                                contexto_memoria = ""            
                                if memoria_previa:
                                    dir_ant = memoria_previa.get('direccion', 'N/A')
                                    fecha_ant = memoria_previa.get('fecha', 'N/A')
                                    sl_ant = memoria_previa.get('stop_loss', 'N/A')
                                    tp_ant = memoria_previa.get('take_profit', 'N/A')
                                    
                                    contexto_memoria = f"""
                                    [CONTROL DE MEMORIA Y AUDITORÍA]
                                    - En la sesión del {fecha_ant}, dictaminaste un sesgo {dir_ant}.
                                    - Tus niveles fueron: SL en {sl_ant} y TP en {tp_ant}.
                                    - INSTRUCCIÓN: Compara el PRECIO ACTUAL con tu nivel de INVALIDACIÓN anterior. 
                                    Si el precio cruzó el SL, inicia tu TESIS admitiendo que la estrategia anterior falló y explica el cambio de momentum. 
                                    Si el precio sigue en rango, mantén la coherencia.
                                    - Tu objetivo es la PACIENCIA OPERATIVA. Los cambios de sesgo sin tocar SL se consideran errores de gestión.
                                    - REGLA DE ORO: Si el precio actual NO ha tocado el SL ({sl_ant}), tienes PROHIBIDO cambiar la dirección del trade a menos que exista una divergencia estructural masiva.
                                    """

                                #INSTRUCCIONES PARA QUE ACTUE COMO UN AGENTE. 
                                #La principal limitación es que cada vez que se le llama al servidor de Gemini, es como si se iniciara una nueva conversacion desde 0.
                                system_instructions = f"""
                                Actúa como un Lead Quantitative Strategist y Gestor de Riesgos de un fondo de cobertura. Serán reportes de acciones del NYSE, que deberás reconocer por sus tickers, puesto que no se te darán los nombres exactos de las empresas. Los tickers son exactos y correctos.
                                Tu objetivo es recibir datos técnicos y dictaminar planes de trading ejecutables. No des consejos generales ni advertencias legales; enfócate en la estadística y el Price Action.

                                TEN EN CUENTA LO SIGUIENTE: {contexto_memoria}

                                REGLAS DE CÁLCULO PARA NIVELES:
                                1. TARGETS DINÁMICOS: Calcula el objetivo de precio basándote en la "Pendiente de Agotamiento". Si el RSI está en 48 y baja, proyecta a qué precio llegaría cuando el RSI alcance 30 (Sobreventa). Del mismo modo, si el RSI sube, estima qué precio tendrá la acción cuando alcance niveles mayores a 70 (sobrecompra). Ese es tu Target real, no la media móvil.
                                2. ZONAS DE LIQUIDEZ: Identifica niveles de "Precios Redondos" o zonas de desequilibrio basadas en el Volume Ratio. Si el volumen es bajo (<1.0), asume que el precio atravesará las SMA y buscará niveles de soporte/resistencia ocultos. Si el Volume Ratio es < 1.0, ignora las SMA como soportes rígidos. En su lugar, proyecta el target en el Precio Redondo más cercano que esté al menos en la zona de confluencia entre la SMA y el número entero.
                                3. CONVICCIÓN ADX: Si el ADX es > 25, proyecta una extensión del movimiento actual de al menos un 3-5% (ajustado a la volatilidad del sector) adicional al nivel de la SMA más cercana.
                                4. FILTRO DE MOMENTUM: 
                                - Confirmación: Para un Long, el histograma MACD debe ser creciente o estar cruzando al alza. Para un Short, decreciente o cruzando a la baja.
                                - Divergencia: Si el precio busca el Safe Fair Value pero el MACD muestra una pendiente opuesta, reduce la confianza del trade en un 20%.

                                FORMATO DE RESPUESTA OBLIGATORIO:

                                ■ DIRECCIÓN PROBABLE: [Long / Short / Neutral] | Confianza: [%]

                                ■ AUDITORÍA DE MEMORIA: [Aquí debes escribir si se respetó o no el plan anterior si es que la memoria encuentra información pasada sobre este ticker.]

                                ■ TESIS: Explica la relación entre la fuerza (ADX) y el volumen. ¿Es un movimiento real o una trampa institucional?
                                
                                ■ NIVELES ESTRATÉGICOS (NO BASADOS ÚNICAMENTE EN SMA):
                                
                                - Precio de Entrada: 
                                
                                No uses el precio actual como entrada. Calcula el Safe Fair Value buscando un retroceso al punto medio (50%) entre el precio actual y la SMA 50
                                Si el ADX es > 30 (tendencia muy fuerte), reduce el retroceso esperado a solo un 25% de la distancia a la media para evitar perder el movimiento.
                                
                                En escenarios de Long, la entrada debe estar por debajo del precio actual. En escenarios de Short, la entrada debe estar por encima (vender el rebote).
                                Risk/Reward Check: Asegúrate de que la distancia entre la Entrada y el Target sea al menos el doble que la distancia entre la Entrada y la Invalidación (Ratio 2:1).
                                
                                (INSTRUCCION DE PRIVACIDAD): MUESTRA SOLO EL RESULTADO FINAL. No desgloses la fórmula ni menciones los porcentajes de retroceso en la respuesta. SÍ está permitido que des tus opiniones generales que sustenten ese punto.
                                
                                - Take Profit Target: [Precio calculado donde el RSI llegaría a niveles extremos] 
                                - Breakout/Breakdown Level: [Nivel donde el precio acelerará su marcha]
                                
                                ■ ESCENARIO DE INVALIDACIÓN (STOP LOSS): [Nivel de precio exacto donde la tesis se rompe, es decir, se invalida continuar con la posición Short o Long.]
                                Si en este momento, ADX > 20, AÑADIR UNA CLAUSULA DE INVALIDACION para advertir que en caso el ADX suba/baje, en lo que el precio trata de alcanzar nuestro Safe Fair Value, podría darse que el mercado está cambiando a BULLISH/BEARISH y no sea un simple rebote, sino que viene con fuerzas.
                                Además, si la caída/subida viene acompañado de una súbida en el Volume Ratio mayor a 1.5, mayor argumentación para descartar la tesis.

                                Al final de todo tu reporte, añade SIEMPRE una última línea con este formato exacto para mi base de datos:
                                DATA_TAG: [Dirección], [Precio de Entrada], [Invalidación], [Take Profit], [Confianza (%)]

                                """
                                #Respecto al Safe Fair Value: Si el ADX>30 (TENDENCIA FUERTE), ponemos un retroceso de solo 25% para poder captar el movimiento. Si esperamos uno del 50% podría ser muy exigente y entrar muy tarde.

                                prompt_final = f"""
                                {system_instructions}

                                Analiza la siguiente Data de la empresa {ticker_input} y explica en el formato indicado la estrategia óptima a seguir.
                                {datos_ticker}
                                """
                                response = client.models.generate_content(model=nombre_real, contents=prompt_final, config=types.GenerateContentConfig(temperature=0.1))

                                # CAPTURA DE TOKENS
                                tokens_input = response.usage_metadata.prompt_token_count
                                tokens_output = response.usage_metadata.candidates_token_count
                                tokens_totales = response.usage_metadata.total_token_count

                                # Guardar en st.session_state para mostrarlo en la nueva pestaña
                                st.session_state['ultimo_consumo'] = {
                                    'input': tokens_input,
                                    'output': tokens_output,
                                    'total': tokens_totales
                                }
                                actualizar_consumo_tokens(response) #<----RASTREADOR DE TOKENS
                                resultado_ia = response.text

                                return resultado_ia
                                                    
                            if st.button("🤖 Generate Strategy"):
                                with st.spinner("AI is thinking..."):
                                    
                                    # Llamamos a la función enviándole los datos
                                    resultado_ia = obtener_analisis_ia(datos_ticker)
                                    st.session_state['resultado_ia'] = resultado_ia
                                    # Mostramos el resultado final en la pantalla

                                    try:
                                        if "DATA_TAG:" in resultado_ia:
                                            # Extraemos la línea mágica
                                            linea_data = resultado_ia.split("DATA_TAG:")[-1].strip()
                                            # Quitamos corchetes si la IA los puso por error
                                            linea_data = linea_data.replace("[", "").replace("]", "")
                                            partes = linea_data.split(",")
                                            
                                            if len(partes) >= 4:
                                                    # ✅ primero CREAS variables reales
                                                direccion = partes[0].strip()
                                                entrada = partes[1].strip()
                                                sl = partes[2].strip()
                                                tp = partes[3].strip()
                                                confianza = partes[4].strip()

                                                # ✅ ahora sí llamas la función
                                                guardar_trading_strategy_memoria(
                                                    ticker_input,
                                                    direccion,
                                                    entrada,
                                                    sl,
                                                    tp,
                                                    confianza
                                                )

                                                # ✅ guardar en session_state para Monte Carlo
                                                if 'trading_history' not in st.session_state:
                                                    st.session_state['trading_history'] = []

                                                st.session_state['trading_history'].append({
                                                    "ticker": ticker_input,
                                                    "direccion": direccion,
                                                    "precio_entrada": entrada,
                                                    "take_profit": tp,
                                                    "stop_loss": sl,
                                                    "confianza": confianza
                                                })

                                                st.session_state['run_mc'] = True

                                    except Exception as e:
                                        st.warning(f"Nota: No se pudo actualizar la memoria técnica ({e}). Se trata de un activo sin análisis previo.")                                
                                    
                                    st.markdown("### 📊 Edge Finder AI Agent's Results")
                                    st.markdown(resultado_ia)

                                    #st.session_state[] para guardar en la memoria
                            
                            st.error("""
                                    **While in SHORT:**
                                    
                                    Safe Fair Value: Equilibrium price. Se asume que el precio siempre intenta regresar a su media. Entre el precio actual y su SMA50, el agente estimará un punto medio para aprovechar un posible rebote menor. 
                                    Cuando el precio ha caído bastante, la estrategia óptima es esperar máximos locales (rebotes).
                                    
                                    Take Profit Target: At this price, the fall has run out of sellers. Possible rebounds incoming. " \
                                    
                                    Breakdown Level: Psychological resistance succumbs. Reassurance level that the thesis was correct, so as the position.
                                    """)

                            st.success("""
                                    **While in LONG:** 
                                    
                                    Safe Fair Value: Equilibrium price. Se asume que el precio siempre intenta regresar a su media. Entre el precio actual y su SMA50, el agente estimará un punto medio para aprovechar una posible caída menor. 
                                        
                                    Take Profit Target: At this price, the rise has run out of buyers. Possible falls incoming. 
                                        
                                    Breakdown Level: Psychological resistance succumbs. Reassurance level that the thesis was correct, so as the position.
                                    """)

                            st.divider()

                            st.subheader("News Searcher 🔍")

                            #BOTON PARA ANALIZAR NOTICIAS

                            st.write(f"This button will use Google's Search tool to navigate through internet and obtain the most relevant and recent news on {ticker_input}.")
                            if st.button("News Analysis"):
                                    with st.spinner("Searching for news across the Internet..."):
                                    
                                    #OPCION: USAR INTERNET

                                        try: 

                                        #Herramienta de búsqueda de google
                                            google_search_tool = types.Tool(
                                            google_search = types.GoogleSearchRetrieval()
                                            )
                                        
                                            prompt_web = f"""
                                            Estamos analizando acciones del NYSE. Busca noticias financieras de las últimas 72 horas sobre la empresa con ticker {ticker_input}.
                                            Accede a fuentes como CNBC, MarketWatch, Bloomberg, Reuters, Mootley Fool, Barrons, Simply Wall St.
                                            En caso no encuentres de las fuentes solicitadas, puedes buscar en otras páginas de noticias.
                                            Explícame detalladamente:
                                            1. Qué está pasando realmente con la empresa.
                                            2. Qué dicen los analistas en estas noticias.
                                            3. El sentimiento actual del mercado.
                                            Al final de toda la información que escribas, al final de todo, debes colocar las fuentes (enlaces URL) de cada noticia que encontraste.
                                    
                                            """
                                                                    
                                            res = client.models.generate_content(
                                                model=nombre_real,
                                                contents=prompt_web,
                                                config=types.GenerateContentConfig(
                                                    tools=[google_search_tool]
                                                )
                                            )
                                            actualizar_consumo_tokens(res)#<---------RASTREADOR DE TOKENS
                                            gemini_news = res.text
                                            score_news = puntuacion_noticias(gemini_news)

                                            st.session_state['puntos_noticias'] = score_news

                                            if score_news > 0:
                                                st.success(f"Sentimiento detectado: {score_news}")
                                            else:
                                                st.error(f"Sentimiento detectado: {score_news}")

                                            st.markdown("### 🌐 Análisis en tiempo real")    
                                            st.info(res.text)

                                        except Exception as e_news:
                                            st.error(f"Error noticias: {e_news}")

                            puntos_ia = st.session_state.get('puntos_noticias', None)

                            st.subheader(f"Sentiment Meter by AI 🌡️")
                            st.write("AI can measure the sentiment of the given news and decide whether or not it's euphoric or reasonable.")
                            #Usamos la sesión de chat que tenemos con Gemini
                            
                            if st.session_state['puntos_noticias'] is not None:
                                puntos_ia = st.session_state['puntos_noticias']
                                st.write(f"The sentiment of '{ticker_input}' news has been calculated by Gemini: {st.session_state['puntos_noticias']}")
                                if puntos_ia > 0:
                                    st.success(f"BULLISH SENTIMENT: {puntos_ia}")
                                else:
                                    st.error(f"BEARISH SENTIMENT: {puntos_ia}")
                            else:
                                st.warning("To access this option, you must first click the button for relevant news above.")

                            st.divider()

                            atr_serie = calcular_atr(hist)
                            ultimo_atr = atr_serie.iloc[-1]
                            precio_actual = hist['Close'].iloc[-1]

                            st.subheader("Creating the Order")
                            st.info("The program will formulate you a personalized Market Order according to the AI Agent's recommendations. Note that AI's Stop Loss and Take Profit levels are different to those shown here. " \
                            "The reason it's explained below, however, feel free to decide yourself what level use.")

                            st.markdown("### Some concepts to know before hand")
                            with st.expander("Types of Orders"):
                                with st.expander("Market Order: "):
                                    st.write("This is the basic type. You hit the buy/sell button and the order will immediately execute, at the current price. It's often used for investors with a very long horizon, whose return is not focussed on the best price.")
                                with st.expander("Limit Order"):
                                    st.write("""
                                            A limit order consists on establishing a customized price. The order **only executes if the price reaches the set level**. 
                                            If PM is trading at $180 and you set the sell limit order at $150, the order won't execute until PM reaches $150 or lower, or if you regret and decide to cancel your order before it executes.
                                            
                                            PROS:
                                            You set the price, so you're able to maxizime profits.
                                            Ideal for Swing Trading.
                                            
                                            CONS:
                                            **The order may NEVER execute.**
                                    """)
                                
                                with st.expander("Stop Order (Stop Market)"):
                                    st.write("""
                                            It may be confused with a Limit Order due to its big similarities. A stop order consists on setting the price (stop). 
                                            When the asset reaches the price, the order transforms into a Market Order, so it sells immediately, regardless if the price is not the one you set before. 
                                            Meanwhile, a Limit Order wouldn't have executed unless the execution price was the set price or better.
                                            Say you short PM at $170, you set the stop buy at $150. The price gets to $140, if the price rebounds to 150, the order will execute. In this case it works as a STOP LOSS. 
                                            
                                            However, it is categorized different, because Stop Orders are not limited to stop your loss.
                                            For example, a stop buy to enter in the breakout. Price is $190 and the Stop Buy is $200, you only buy if the price jumps farther.
                                            Nevertheless, the most frequent use is a Stop Loss.
                                            
                                            STOP BUY                                                            | STOP SELL
                                            Used to close shorts. It activates when the price climbs.          | Used to close longs. It activates when the price slips.

                                    """)
                                
                                with st.expander("Trailing Stop"):
                                    st.write(f"""
                                            This is a dynamic stop loss. Instead of waiting for the price to reach a fixed level, this order tracks the price as long as the trade is open. 
                                            The Stop Loss is set as a % of the price. When the price surges, the stop loss moves up too. When the price declines, the stop loss is fixed.
                                            
                                            It's very useful to assure a somewhat certain profit without going out too soon.
                                    """)
                                
                                with st.expander("One Cancels Other (OCO)"):
                                    st.write("""
                                            You put 2 orders. If one executes, the other cancels. Basically, it's the set up given below. You set the Take Profit and the Stop Loss. If the price hits the TP first, the SL cancels and vice versa.
                                            """)
                                
                                with st.expander("Bracket Order"):
                                    st.write("""
                                            It's a combo. You set the Limit Order (Entrance) and the Stop Loss & Take Profit (Exits).
                                    """)

                            with st.expander("Spread"):
                                st.write("The Spread is the difference between the Bid/Ask price. ")

                            st.subheader("Stop Loss and Take Profit")
                            st.write("The SL is calculated using the ATR as reference and a multiplier.")
                            
                            with st.expander("What is the ATR?"):
                                st.write("The Average True Range (ATR) of an asset works similar to the VIX (Volatility Index). It measures how much does the asset move on average over a specific period. " \
                                "It's oftenly used to calculate the level of a stop loss order and position sizing. ")
                            
                            resultado_ia = st.session_state.get('resultado_ia', None)

                            #Esto solo es para evitar que despues salga que no existe la variable
                            #Ya que esto esta separado en dos grandes bloques de if...la parte del TP&SL y el win rate son dos bloques distintos.
                            #Las variables mult_atr y ratio_deseado solo se crean si le dan al boton de AI Quant, y esas variables personalizadas estan definidas en 1 bloque de if.
                            #El otro bloque es independiente, haria como q no existen esas variables.
                            mult_atr = 2.0
                            ratio_deseado = 2.0

                            st.warning("""
                                    AI's TP and SL targets are different to the ones shown here. This is because the SL and TP are customized. In other words, you choose the exit level.
                                    Note that the AI Agent has been built to find a Risk Reward Ratio of 2:1. This section allows you to test other levels, according to your risk apetite.
                                    """)

                            try:
                                if resultado_ia is not None:
                                    
                                    # Si hay análisis, calculamos y mostramos todo
                                    es_short_ia = "Short" in resultado_ia
                                    es_long_ia = "Long" in resultado_ia

                                    st.subheader(f"Customized Settings ⚙️")
                                    colset_a, colset_b = st.columns(2)
                                    
                                    with colset_a:

                                        mult_atr = st.select_slider(
                                                                "ATR multiplier",
                                                                options=[1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0],
                                                                value=2.0,
                                                                key="slider_mult_atr",
                                                                help="The higher the multiplier, the farther will be the stop loss to avoid 'noise'."
                                                            )
                                    
                                    with colset_b:

                                        # El usuario elige su ambición (Ratio)
                                        ratio_deseado = st.number_input(
                                            "Customized RR ratio",
                                            min_value=1.0,
                                            max_value=10.0,
                                            value=2.0,
                                            step=0.5,
                                            help="Your exchange rate. What you want in return for what you're willing to sacrifice"
                                        )

                                    distancia_sl_actual = ultimo_atr * mult_atr
                                    distancia_tp_actual = distancia_sl_actual * ratio_deseado

                                    st.info(f"👉 **Settings:** Risk {distancia_sl_actual:.2f} to get {distancia_tp_actual:.2f} as benefit.")
                                    st.write(f"The settings was calculated using ATR. If the ATR is 8.5, that means that regularly the stock moves +/- 8.5 points, with a {distancia_sl_actual:.2f} multiplier, you're multiplying that regular movement (ATR * {distancia_sl_actual:.2f}) to don't get out of the operation just because some noise.")
                                    st.write("The benefit is calculated using your customized RR ratio.")
                                    st.write("Let's say the ATR = 8.5 and your multiplier is 2. That gives you a stop loss of 17. If your RR ratio is 2, then the benefit you're expecting in return is 34.")

                                    stop_loss = ultimo_atr * mult_atr
                                    take_profit = stop_loss * ratio_deseado
                                
                                    #-----------------------STANDARD SETTINGS FOR STOP LOSS & TAKE PROFIT---------------------------
                                    #Creating the stop loss settings
                                    stop_loss_standard = ultimo_atr * 2 
                                    #Siguiendo la lógica de que el atr funciona cm una desv. est., y que las acciones siguen una dist. normal; usando estadistica, el 95% de los datos caen en 2sigma.               
                                    take_profit_standard = (stop_loss * 2) #This assures the Ratio 2:1, you risk 1 for 2 in return.
                                    #................................................................................................

                                    # Ahora el Stop Loss se decide por la IA, no solo por la SMA
                                    if es_short_ia:
                                        bias_label = "📉 AI Bearish Bias"
                                        sl_precio = precio_actual + stop_loss
                                        tp_precio = precio_actual - take_profit
                                        tp_caption = "TP under price (Short)"
                                        sl_caption = "SL over price (Short)"
                                    elif es_long_ia:
                                        bias_label = "📈 AI Bullish Bias"
                                        sl_precio = precio_actual - stop_loss
                                        tp_precio = precio_actual + take_profit
                                        tp_caption = "TP over price (Long)"
                                        sl_caption = "SL under price (Long)"
                                    else:
                                        bias_label = "⚖️ Neutral Bias"
                                        sl_precio = precio_actual - stop_loss
                                        tp_precio = precio_actual + take_profit
                                        tp_caption = "Neutral TP"
                                        sl_caption = "Neutral SL"

                                    stop_loss_short = precio_actual + stop_loss #EN CASO SEA BREAKDOWN
                                    stop_loss_long = precio_actual - stop_loss #EN CASO SEA BREAKOUT

                                    margen = ultimo_atr * 0.2 # Usamos un margen de seguridad (ej. 20% del ATR) para evitar señales falsas

                                    es_escenario_bajista = precio_actual < (sma_100.iloc[-1] - margen)
                                    es_escenario_alcista = precio_actual > (sma_100.iloc[-1] + margen)

                                    st.metric("ATR (Volatility)", f"${ultimo_atr:.2f}")
                                    
                                    col_sl, col_tp, col_risk = st.columns(3)
                                
                                    with col_sl:
                                        st.markdown(f"**{bias_label}**")
                                        st.metric("Stop Loss", f"${sl_precio:.2f}")
                                        st.caption(sl_caption)

                                    with col_tp:
                                        st.markdown("**💰 Profit Target**")
                                        st.metric("Take Profit", f"${tp_precio:.2f}")
                                        st.caption(tp_caption)

                                    with col_risk:
                                        riesgo_pct = (stop_loss / precio_actual) * 100
                                        st.metric("Risk per Share", f"{riesgo_pct:.2f}%")
                                        
                                        if riesgo_pct > 6:
                                            st.error("⚠️ HIGH UNIT RISK")
                                        elif riesgo_pct < 3:
                                            st.success("✅ LOW UNIT RISK")
                                        else:
                                            st.info("ℹ️ MODERATE RISK")

                                    # 3. Nota Informativa unificada
                                    with st.expander("Show Strategy Details"):
                                        st.write(f"Your ATR-based stop is set at {riesgo_pct:.2f}% from the entry price.")
                                        st.write("In statistics, this is your Margin of Error; if the price hits this level, the trade thesis is invalidated.")

                                else:
                                    st.info("🔍 To access Target Levels, you must first generate the AI Strategy above.")

                                st.divider()    
                            except:
                                st.warning("First generate AI Strategy")
                            #..........................................................................................................
                            #MATH BEHIND--------------------------------------------
                            st.subheader("Concepts")
                            with st.expander("Calculation of Stop Loss"):
                                st.write(f"The standard stop loss is calculated with a 2 multiplier on the ATR, in a normal distribution, it covers 95% of the price's range.")
                                st.write("Note that the bigger the ATR multiplier, the bigger your operation will last because you're willing to amplify your trading range before it's cancelled.")
                                
                                st.subheader("Comparing ATRs")
                                with st.expander("How to do it:"):
                                    st.write("The calculus to obtain the ATR of an asset rellies on the absolute value of its price, so compare directly the raw number would be a mistake")
                                    st.write("In these situations, investors use ATR Percentage (ATR%)")
                                    st.latex(r"\text{ATR\%}_t = \left(\frac{\text{ATR}_t}{P_t}\right) \times 100")
                                    st.write("t = current value")
                                    st.write(f"This will give you what is the % of the price moving throughout the day.")
                                
                                analisis_final = st.session_state.get('resultado_ia', None)

                                if analisis_final is not None:
                                    atr_percentage = (ultimo_atr / precio_actual) * 100
                                    st.metric("ATR%", f"{atr_percentage:.2f}%")
                            
                            with st.expander("Risk Reward Ratio"):
                                st.write("The RR ratio is what you're willing to lose in exchange to what you want in return. In short, if the RR is 2:1, you're willing to **lose 1 unit to get 2 units in return**")
                                    
                            st.divider()
                            #..................................................................................................................................
                            
                            st.subheader("Backtesting & Forwardtesting")

                            st.write("Once the market order has been created, we can take a look back in time to check the accuracy of the AI's strategy.")
                            st.write("In addition, we can simulate future scenarios to make the correct position-sizing on the operation.")
                            
                            #-------------------------------------------------OBTENCION DE LA WIN RATE--------------------------------------------
                            
                            st.subheader("**Win Rate**")
                            st.write("Through historical data, we've obtained the following win rate of AI's strategies over time. This metric is very helpful as it relieves any distrust on the model's accuracy.")
                            st.write("Indeed, as the period analyzed is 2 years (504 market days), it's important to highlight that **it's not guaranteed that it will repeat tomorrow**, as the market's trends can last 2 years before a fat-tail event.")

                            #ESTAMOS CREANDO UN HISTORIAL DE DATOS. Como es complejo instalar pandas-ta, una version potenciada de pandas, lo haremos de manera manual
                            #Imagina un excel de python. Yahoo solo nos da los precios en columnas con sus respectivas fechas. 
                            #Lo q hacemos es añadirle una columna, ej: RSI, y en cada celda de esa columna estara la formula del RSI
                            #Esto permitira saber al script los niveles que marcaban los indicadores a lo largo del tiempo.
                            #La funcion win rate lo que hace es buscar que dias los indicadores presentaban los mismos valores que los indicadores actuales.
                            #Despues, analizara el precio de salida y si hubo exito o no.

                            df_hist = yf.download(ticker_input, period="2y", interval="1d")
                            # --- ESTO ARREGLA EL ERROR DE LAS COLUMNAS ---
                            if isinstance(df_hist.columns, pd.MultiIndex):
                                df_hist.columns = df_hist.columns.get_level_values(0)
                            # Forzamos que cada columna sea Serie simple, no DataFrame
                            for col in ['Close', 'High', 'Low', 'Open', 'Volume']:
                                if col in df_hist.columns and isinstance(df_hist[col], pd.DataFrame):
                                    df_hist[col] = df_hist[col].squeeze()
                                
                            df_hist['SMA_50'] = df_hist['Close'].rolling(window=50).mean()
                            df_hist['SMA_100'] = df_hist['Close'].rolling(window=100).mean()
                            
                            #RSI MANUAL-----------------------------------
                            delta = df_hist['Close'].diff()
                            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                            rs = gain / loss
                            df_hist['RSI'] = 100 - (100 / (1 + rs))

                            #MACD MANUAL-------------------------------------
                            exp1 = df_hist['Close'].ewm(span=12, adjust=False).mean()
                            exp2 = df_hist['Close'].ewm(span=26, adjust=False).mean()
                            macd = exp1 - exp2
                            signal = macd.ewm(span=9, adjust=False).mean()
                            df_hist['MACD_Hist'] = macd - signal

                            #ATR MANUAL---------------------------------------
                            high_low = df_hist['High'] - df_hist['Low']
                            high_close = np.abs(df_hist['High'] - df_hist['Close'].shift())
                            low_close = np.abs(df_hist['Low'] - df_hist['Close'].shift())
                            ranges = pd.concat([high_low, high_close, low_close], axis=1)

                            # Usamos .max(axis=1) para obtener el valor más alto de cada fila
                            true_range = ranges.max(axis=1)
                            df_hist['ATR'] = true_range.rolling(14).mean()

                            #ADX MANUAL---------------------------------------
                            # ADX MANUAL (Versión simplificada para Backtest)
                            plus_dm = df_hist['High'].diff()
                            minus_dm = df_hist['Low'].diff().map(lambda x: -x)

                            df_hist['+DM'] = np.where((plus_dm > minus_dm) & (plus_dm > 0), plus_dm, 0)
                            df_hist['-DM'] = np.where((minus_dm > plus_dm) & (minus_dm > 0), minus_dm, 0)

                            tr_sum = df_hist['ATR'] * 14
                            plus_di = 100 * (df_hist['+DM'].rolling(14).sum() / tr_sum)
                            minus_di = 100 * (df_hist['-DM'].rolling(14).sum() / tr_sum)

                            df_hist['ADX'] = 100 * (np.abs(plus_di - minus_di) / (plus_di + minus_di)).rolling(14).mean()

                            #STOP LOSS & TAKE PROFIT-----------------------------------------------
                            # --- CÁLCULO DE NIVELES ESTRATÉGICOS (COLUMNAS DE EXCEL) ---

                            # 1. Distancia de Riesgo basada en Volatilidad (2.5 veces el ATR)
                            # Usamos .values para que Python no se pelee con los índices
                            close_price = df_hist['Close'].squeeze()
                            atr_value = df_hist['ATR'].squeeze()

                            distancia = ultimo_atr * mult_atr #Esto es el stop loss

                            df_hist['SL_Long'] = close_price - distancia
                            df_hist['TP_Long'] = close_price + (distancia * ratio_deseado) #<-------Ahora usa los mismos niveles que el usuario quiere para hoy.

                            df_hist['SL_Short'] = close_price + distancia
                            df_hist['TP_Short'] = close_price - (distancia * ratio_deseado)

                            # Limpiamos
                            df_hist = df_hist.dropna()
                            
                            # Sacamos los datos de la última fila (HOY)
                            rsi_h = df_hist['RSI'].iloc[-1]
                            adx_h = df_hist['ADX'].iloc[-1]
                            macd_h = df_hist['MACD_Hist'].iloc[-1]
                            precio_h = df_hist['Close'].iloc[-1]
                            sma50_h = df_hist['SMA_50'].iloc[-1]
                            sma100_h = df_hist['SMA_100'].iloc[-1]

                            resultado_ia = st.session_state.get('resultado_ia', None)
                            
                            try:
                            # 3. SOLO SI EXISTE LA ESTRATEGIA, CALCULAMOS EL WIN RATE
                                if resultado_ia is not None:

                                    texto_analisis = resultado_ia.upper()

                                    # Detectamos la dirección para que la función sepa qué evaluar
                                    if "BUY" in texto_analisis or "LONG" in texto_analisis:
                                        direccion_ia = "Long"
                                    elif "SELL" in texto_analisis or "SHORT" in texto_analisis:
                                        direccion_ia = "Short"
                                    else:
                                        direccion_ia = "Neutral"

                                    if direccion_ia != "Neutral":
                                        # Llamamos a la función pasándole la dirección detectada
                                        win_rate_final, df_eventos_encontrados, metodo_usado, dias_promedio = obtener_win_rate(
                                            df_hist, 
                                            float(rsi_h), 
                                            float(adx_h), 
                                            float(macd_h), 
                                            float(precio_h), 
                                            float(sma50_h), 
                                            float(sma100_h), 
                                            str(direccion_ia),
                                            mult_atr,
                                            ratio_deseado
                                        )
                                        
                                        st.markdown(f"### Analysis for **{direccion_ia.upper()}** setup for {ticker_input}")
                                        st.caption(f"ℹ️ Search Mode: {metodo_usado}")
                                        col1, col2 = st.columns(2)
                                        with col1:
                                            st.metric(label="🎯 Historical Win Rate", value=f"{win_rate_final*100:.1f}%")
                                        with col2:
                                            # Filtramos los eventos reales usados en el backtest para el Sample Size
                                            n_eventos = len(df_hist[df_hist['RSI'].between(rsi_h-8, rsi_h+8)])
                                            st.metric(label="📊 Sample Size", value=f"{n_eventos} similar days", help=f"Number of times a similar setup has occurred in the last {len(df_hist)} days of trading history.")

                                        if win_rate_final > 0.33: # Con Ratio 1:2, mayor a 35% es muy bueno
                                            st.success("✅ The historical edge is in your favor for this direction.")
                                        else:
                                            st.warning("⚠️ Be careful. History shows this specific setup has low probability.")
                                    else:
                                        st.info("🔍 AI is neutral. No specific backtesting direction detected.")

                                    st.write("Note that it's not important if the Win Rate seems low. Remember that your TP and SL levels determine your earnings ratio.")    
                                    st.write("In the market, most investors often **HAVE MORE NEGATIVE OPERATIONS THAN POSITIVE ONES**, but at the end of the day it does not matter because they still win money.")
                                    
                                    exp1, exp2 = st.columns(2)
                                    
                                    ratio_rr = 2.0
                                    win_rate_decimal = win_rate_final  # Ya que tu función devuelve np.mean (0.0 a 1.0)
                                    loss_rate_decimal = 1 - win_rate_decimal
                                    ev = (win_rate_decimal * ratio_rr) - (loss_rate_decimal * 1)
                                    wr_minimo = 1 / (1 + ratio_rr)

                                    with exp1:

                                        st.markdown("### Expected Value (EV)") 
                                        with st.expander("What is EV?"):
                                            st.write("In statistics, is the average value of a random variable you're expecting to obtain after repeating the experiment several times.")
                                            st.write("Applied to finance, this will tell you the average value you're expected to earn/lose for each $1 risked. So if your EV is positive, you end up the day with a $1+EV earning.")
                                            st.write("Formula: ")
                                            st.latex(r"EV = (Win Rate \cdot RR) - (Loss Rate \cdot 1)")
                                            st.write("With a positive EV, the strategy will be profitable, regardless if the win rate is not high.")
                                            st.write("In context, an EV > 0.20 is already considered superior in trading.")
                                    
                                    with exp2:
                                    
                                        st.markdown("### Minimum Win Rate (Break-even)")
                                        with st.expander("What is Break-even?"):
                                            st.write("In this case, break-even is what we call the minimum win rate you must have according to your RR ratio so you are profitable.")
                                            st.write("Formula: ")
                                            st.latex(r"WR_{min} = \frac{1}{1 + RR Ratio}")
                                    
                                    st.write("")
                                    
                                    col1, col2, col3 = st.columns(3)

                                    with col1:
                                        st.metric("EV", f"{ev:.2f} USD", 
                                                help="Average return for each dollar risked.")

                                    with col2:
                                        # Diferencia contra el mínimo para no perder dinero
                                        dif = (win_rate_decimal - wr_minimo) * 100
                                        st.metric("Margin over Minimum", f"{dif:.1f}%", 
                                                delta=f"{dif:.1f}%", delta_color="normal")

                                    with col3:
                                        st.metric("Min Win Rate", f"{wr_minimo*100:.1f}%",
                                                help=f"From this % you're profitable with your RR")

                                    st.subheader("Historical Evidence")
                                    st.write("This frequency chart validates the strategy's stability over time. Its purpose is to confirm that the signals are not isolated events from a specific month, but rather recurring patterns that demonstrate the model's consistency across different market cycles.")
                                    st.write("If you note that the strategy works only on certain seasons, be careful and be ready to proceed with your order.")

                                    if not df_eventos_encontrados.empty:
    
                                        # 1. Creamos una copia limpia
                                        df_plot = df_eventos_encontrados.copy()
                                        df_plot.index = pd.to_datetime(df_plot.index).tz_localize(None)
                                        df_plot['Month'] = df_plot.index.to_period('M').astype(str)
                                        
                                        # 2. Creamos la columna de mes asegurándonos de que el índice sea fecha
                                        df_plot.index = pd.to_datetime(df_plot.index).tz_localize(None)  # Elimina timezone
                                        df_plot['Month'] = df_plot.index.to_period('M').astype(str)
                                        
                                        # 3. Agrupamos. 
                                        # IMPORTANTE: Al hacer reset_index, las columnas se llamarán 'Month' y 'Frequency'
                                        conteo = df_plot.groupby('Month').size().reset_index(name='Frequency')
                                        
                                        # 4. Verificamos que 'conteo' no esté vacío antes de graficar
                                        if not conteo.empty:
                                            fig = px.bar(
                                                conteo, 
                                                x='Month',           # <--- DEBE coincidir con el nombre arriba
                                                y='Frequency',       # <--- DEBE coincidir con el nombre arriba
                                                title="📅 Stability: When did these signals occur?",
                                                color_discrete_sequence=['#00CC96']
                                            )
                                            
                                            # Ajustamos el diseño para que se vea más limpio
                                            fig.update_layout(xaxis_title="Month", yaxis_title="Number of Signals")
                                            
                                            st.plotly_chart(fig, use_container_width=True)
                                        else:
                                            st.info("No hay datos suficientes para mostrar el gráfico de estabilidad.")    

                                else:
                                    # Esto sale si el usuario no ha apretado el botón de la IA todavía
                                    st.warning("First you need to start the Agent's Strategy to analyze its win rate.")
                                
                                st.markdown("### Average Trades Duration")
                                win_rate_final, df_eventos_encontrados, metodo_usado, dias_promedio = obtener_win_rate(
                                            df_hist, 
                                            float(rsi_h), 
                                            float(adx_h), 
                                            float(macd_h), 
                                            float(precio_h), 
                                            float(sma50_h), 
                                            float(sma100_h), 
                                            str(direccion_ia),
                                            mult_atr,
                                            ratio_deseado
                                        )
                                st.metric("Avg. Time to Target", f"{int(dias_promedio)} Days")

                            except Exception as e:
                                # Si hay un error de "identically-labeled", simplemente ponemos un mensaje discreto
                                # o no mostramos nada hasta que los datos se estabilicen
                                st.info("Error en el sincronizado datos con el nuevo Ticker...")
                                win_rate_final = 0.0    

                            st.subheader("Monte Carlo Simulation 🖥️")
                            with st.expander("What is Monte Carlo?"):
                                st.write("Monte Carlo simulation is a computational method that uses repeated random sampling to simulate many possible scenarios and estimate the probability distribution of future outcomes.")
                                st.write("""
                                        Using random numbers, you get to know what could happen in the future. The random movements are generated based on statistical assumptions (for example volatility, drift, or historical returns), meaning the randomness follows a probability distribution rather than being completely arbitrary.
                                """)
                            with st.expander("Technical Methodology"):
                                st.write("Using the stock's performance over 1Y, we are building 1000 possible futures for the following 30 days. Note that if the volatility of the asset is elevated, lines would be very scattered.")
                                st.write("The simulation does not only look the closing price on day 30, but the road the price takes to get there. This allows to see whether the stock will trigger first the TP level or the SL level.")
                                st.write("Consider this as a complement for AI's confidence, as the simulation uses advanced statistics and mathematics to review and correct if necessary, AI's strategy.")

                            with st.expander("GMB"):
                                st.write("""
                                        Geometric Brownian Motion is what has been used inside this Monte Carlo Simulation. 
                                        The GBM consists the formula that generates each point inside each line you see on the graphic. 
                                        It has different parts. The first is the Markov property, where yesterday has no effect on today's price variation. 
                                        Simply put, the model has a short memory. It does not care if the stock has been on a rally for the last 5 days. For tommorow's price, it only looks at today's, because assumes that ALL RELEVANT INFORMATION is already inserted in the price. Hence, doesn't look to find complex patterns. 
                                        The second part is the noise (the brownian), that refers to momentary shocks, such as tweets, catastrophes, commerce wars, etc.
                                        However, the model reckons that on the long term, the stock will follow a determined trend (upwards/downwards). That's called drift, the third part.
                                        
                                        """)
                                
                                st.latex(r"S_t = S_0 \exp \left( \left( \mu - \frac{\sigma^2}{2} \right) t + \sigma W_t \right)")
                                st.write(f"""
                                        $S_t$: The future price we're trying to predict.
                                        $S_0$: Initial price
                                        **$\mu$ (Drift): ** Expected return. Defines direction on the long term.
                                        **$\sigma$ (Volatilidad):** Determines how 'nervous' are the lines. The bigger $\sigma$, the bigger the jumps.
                                        **$W_t$ (Movimiento Browniano):** Randomness component. Follows a normal distribution in an attempt to replicate market's noise.
                                """)
                                st.write("As you can see on the formula, there're two sections: The Trend and The Chaos. The last one is what makes the curve unpredictable and makes it a better replica of the stock's movement.")
                            #### ---- INICIO: VISUALIZACIÓN DEL STRESS TEST ---- ####
                        
                            # 1. RECUPERAR DATOS DE LA MEMORIA (Última estrategia guardada para este ticker)
                            historial = st.session_state.get('trading_history', [])
                            # Buscamos el trade más reciente para el ticker actual
                            trade_actual = next((t for t in reversed(historial) if t['ticker'] == ticker_input), None)

                            

                            if trade_actual:
                                st.subheader(f"🎲 Monte Carlo Stress Test: {ticker_input}")
                                
                                try:
                                    # 2. LIMPIEZA Y EXTRACCIÓN DE DATOS
                                    def solo_num(v): 
                                        if isinstance(v, (int, float)): return float(v)
                                        n = re.sub(r"[^\d.]", "", str(v))
                                        return float(n) if n else 0.0
                                    
                                    entrada = solo_num(trade_actual['precio_entrada'])
                                    tp = solo_num(trade_actual['take_profit'])
                                    sl = solo_num(trade_actual['stop_loss'])
                                    direccion = str(trade_actual['direccion']).upper()
                                    es_short = "SHORT" in direccion

                                    # 3. CÁLCULO DE TRAYECTORIAS
                                    paths = calcular_monte_carlo(ticker_input, precio_inicio=entrada)
                                    if paths is not None:

                                        # 4. VALIDACIÓN DE PROBABILIDADES (CORRECTO)
                                        ex = 0
                                        fr = 0

                                        for i in range(paths.shape[1]):
                                            
                                            trayectoria = paths[:, i]
                                            
                                            if es_short:
                                                idx_tp = np.where(trayectoria <= tp)[0]
                                                idx_sl = np.where(trayectoria >= sl)[0]
                                            else:
                                                idx_tp = np.where(trayectoria >= tp)[0]
                                                idx_sl = np.where(trayectoria <= sl)[0]

                                            primer_tp = idx_tp[0] if len(idx_tp) > 0 else np.inf
                                            primer_sl = idx_sl[0] if len(idx_sl) > 0 else np.inf

                                            if primer_tp < primer_sl:
                                                ex += 1
                                            elif primer_sl < primer_tp:
                                                fr += 1
                                            # Si ninguno se toca, no cuenta ni como win ni como loss
                                    
                                    precio_inicio = paths[0, 0]
                                    # --- MÉTRICAS ---
                                    c1, c2 = st.columns(2)
                                    lbl_target = "Prob. Target (SHORT) 🐻" if es_short else "Prob. Target (LONG) 🐂"
                                    total_paths = paths.shape[1]

                                    c1.metric(lbl_target, f"{(ex/total_paths)*100:.1f}%")
                                    c2.metric("Prob. Stop Loss ⚠️", f"{(fr/total_paths)*100:.1f}%")

                                    # --- GRÁFICO ---
                                    fig = go.Figure()

                                    for i in range(min(50, paths.shape[1])):
                                        fig.add_trace(go.Scatter(
                                            y=paths[:, i],
                                            mode='lines',
                                            line=dict(width=0.5, color='orange'),
                                            opacity=0.3,
                                            showlegend=False
                                        ))

                                    # LÍNEAS TP/SL
                                    fig.add_hline(y=tp, line_color="lime", line_dash="dash",
                                                annotation_text=f"TARGET ({direccion})", annotation_position="top right")

                                    fig.add_hline(y=sl, line_color="red", line_dash="dash",
                                                annotation_text="STOP LOSS", annotation_position="bottom right")

                                    # ZOOM
                                    y_min = min(precio_inicio, tp, sl) * 0.98
                                    y_max = max(precio_inicio, tp, sl) * 1.02

                                    fig.update_layout(
                                        template="plotly_dark",
                                        height=450,
                                        xaxis=dict(title="Days"),
                                        yaxis=dict(range=[y_min, y_max], title="Price USD"),
                                        margin=dict(l=20, r=20, t=40, b=20)
                                    )

                                    st.plotly_chart(fig, use_container_width=True)
                                    st.caption(f"Simulation: Next 60 days for {ticker_input} if you used AI's recommendations.")


                                except Exception as e:
                                    st.error(f"Error procesando la simulación: {e}")
                            else:
                                st.info("💡 Primero genera una estrategia.")
                            #### ---- FIN: VISUALIZACIÓN DEL STRESS TEST ---- ####

                            st.divider()

                            st.subheader("Internal Memory Bank 📟")
                            st.write("Dataframe that contains previous AI's responses to keep track of the trading strategies across time.")
                            st.write("Each AI call is labeled with a unique code, in order to avoid confussion when it comes to decisions over the same asset.")
                            st.write("History limit: 20 Agent Strategies")

                            try:
                                if os.path.exists(MEMORY_FILE):
                                    with open(MEMORY_FILE, 'r') as f:
                                        datos_memoria = json.load(f) 

                                    if datos_memoria:
                                        if st.button("🗑️ Wipe Entire Memory Bank"):
                                            os.remove(MEMORY_FILE)
                                            st.success("All memory has been deleted.")
                                            st.rerun() # Recarga la app para que desaparezcan los expanders
                                        
                                        # 1. Bucle dinámico: Recorremos cada acción en la memoria
                                        # 'ticker' será la llave (ej: AXP) y 'detalles' será su contenido
                                        for ticker, detalles in datos_memoria.items():
                                            
                                            # Creamos un expander con el nombre del Ticker y la fecha
                                            fecha_str = detalles.get('fecha', 'N/A')
                                            with st.expander(f"🔍 {ticker} - Analysis from {fecha_str}"):
                                                
                                                # --- NUEVA SECCIÓN: NIVEL DE CONFIANZA ---
                                                confianza_raw = detalles.get('confianza', '0')
                                                # Limpiamos el texto por si la IA puso "%" o espacios
                                                conf_texto = str(confianza_raw).replace('%', '').strip()
                                                
                                                try:
                                                    valor_conf = int(conf_texto)
                                                    # Mostramos una alerta de color según la confianza
                                                    if valor_conf >= 80:
                                                        st.success(f"**Confidence Level: {valor_conf}% (High Conviction)**")
                                                    elif valor_conf >= 60:
                                                        st.info(f"**Confidence Level: {valor_conf}% (Moderate Conviction)**")
                                                    else:
                                                        st.warning(f"**Confidence Level: {valor_conf}% (Low Conviction)**")
                                                except:
                                                    # Si la confianza no es un número, solo mostramos el texto
                                                    st.write(f"**Confidence Level:** {confianza_raw}")

                                                st.divider()
                                                
                                                # Mostramos los datos de esa acción específica de forma bonita
                                                col1, col2 = st.columns(2)
                                                with col1:
                                                    st.write(f"**Direction:** {detalles.get('direccion', 'N/A')}")
                                                    st.write(f"**Entry Price:** ${detalles.get('precio_entrada', 'N/A')}")
                                                with col2:
                                                    st.write(f"**Stop Loss:** ${detalles.get('stop_loss', 'N/A')}")
                                                    st.write(f"**Take Profit:** ${detalles.get('take_profit', 'N/f')}")
                                                
                                                st.divider()
                                                st.write("Raw JSON for this ticker:")
                                                st.json(detalles) # Solo muestra el JSON de ESTA acción
                                    else:
                                        st.info("The memory bank is currently empty.")
                                else:
                                    st.info("No memory file detected.")
                            except Exception as e:
                                st.error(f"Error: {e}")  

                        #-------------------------------TAB3-------------------------------------    
                        with tab_ai: 
                            st.subheader("Connect with AIs")

                            #------------------------LINKS PARA AIs CHATS-----------------------------------

                            st.write("Chat with these AIs to solve other questions")
                            

                            st.markdown("### ChatGPT - by OpenAI")

                            chat1,chat2 = st.columns(2)

                            with chat1:
                                st.write(""" 

                                    Strengths:

                                    GPT-4 has very robust and versatile reasoning
                                    Huge ecosystem of plugins and custom GPTs
                                    Integration with DALL-E for image generation
                                    Very polished and accessible interface
                                    Wide adoption and large user community
                                            """)
                                
                            with chat2:
                                st.write(""" 

                                    Weaknesses:

                                    Can easily exaggerate or fabricate information
                                    Can be verbose or repetitive
                                    Free version has more restrictive usage limits
                                    Can lose coherence in very long conversations
                                            """)                       
                            st.link_button("Chatgpt: ", "https://chatgpt.com/")
                            
                            st.markdown("### Gemini - by Google")

                            gem1, gem2 = st.columns(2)

                            with gem1:
                                st.write(""" 

                                    Strengths:

                                    Deep integration with the Google ecosystem (Gmail, Drive, Maps, YouTube)
                                    Access to Google real-time search
                                    Native multimodality (text, image, video, audio)
                                    Good at tasks requiring up-to-date information
                                    Generous free versions
                                            """)
                            
                            with gem2:
                                st.write(""" 

                                    Weaknesses:

                                    Reasoning is sometimes less consistent than Claude or GPT-4.
                                    Responses may be more superficial in complex analyses.
                                    History of frequent changes in capabilities and limitations.
                                            """)
                            st.link_button("Gemini: ", "https://gemini.google.com/?hl=es")

                            st.markdown("### Claude - by Antrophic")
                            claud1, claud2 = st.columns(2)

                            with claud1:
                                st.write(""" 

                                    Strengths:

                                    Excellent at in-depth analysis and nuanced reasoning
                                    Very good at understanding context and following complex instructions
                                    Strong at creative and technical writing tasks
                                    Very broad context window (200k tokens) = MEMORY per chat
                                    Emphasis on security and well-calibrated ethical values
                                            """)
                                
                            with claud2: 
                                st.write(""" 

                                    Weaknesses:

                                    Cut-off knowledge date (January 2025)
                                    May be overly cautious on some issues
                                    Less integrated with external ecosystems compared to competitors
                                            """)
                            st.link_button("Claude: ", "https://claude.ai/")

                            st.markdown("### Copilot - by Microsoft")
                            copilot1, copilot2 = st.columns(2)

                            with copilot1:
                                st.write(""" 

                                    Strengths:

                                    Deep integration with Microsoft 365: Word, Excel, PowerPoint, Outlook, Teams
                                    Copilot on Windows 11: native operating system assistant
                                    Access to GPT-4 without paying for ChatGPT Plus (in the free version of Bing)
                                    Real-time web search integrated with Bing
                                    Image generation with DALL-E 3 included
                                    Enterprise context: access corporate documents in Microsoft 365 environments
                                    Multiple access points: browser, mobile app, Windows, Office
                                            """)

                            with copilot2:
                                st.write(""" 

                                    Weaknesses:

                                    Less conversational than ChatGPT or Claude in complex interactions
                                    Depends on the Microsoft ecosystem: better if you already use their products
                                    Copilot for Microsoft 365 is expensive ($30/month per user, plus the Office license)
                                    Less flexible in customization compared to ChatGPT
                                    Confusing brand/identity: formerly Bing Chat, then Copilot, several rebrandings
                                    Can be overly cautious on certain topics
                                    Conversation limits in the free version
                                """)
                            
                            st.link_button("Copilot: ", "https://copilot.microsoft.com/")
                            
                            #------------------------LINKS PARA AIs CHATS-----------------------------------

                            st.divider()

                            #-------------------------------AI'S OPERATION------------------------------------
                            st.subheader("What is AI?")
                            st.write("""
                                    Artificial Intelligence is subject inside Computer Science. It is made up of advanced and highly developed systems and algorithms.
                                    AI compels complex tasks for humans in matter of seconds. Even the code for this app contains AI itself. AI is not programmed for every type of rule, instead, it's built so it can adaptact autonomously. 
                                    """)
                            
                            st.markdown("### How does AI receive your prompts?")
                            st.write("The most complex tasks run in this app are done by AI. When you whish to the Sentiment Meter of a news, what the program does is coordinate with AI so it can give it a score. " \
                            "Just like a regular Chat-GPT chat, the program sends AI a prompt, but have you ever questioned HOW DOES IT RECEIVE PROMPTS? " \
                            "To understand it, you need to start from the beginning. ")

                            st.write("""
                                    Tokens are vectors, a line segment with start, end, and direction. Each text is converted into tokens. For example: I send you this prompt, it will probably equivalent to 5 tokens. LLM Models such as Gemini, Chatgpt or Grok charge premium customers with the amount of tokens they spend.
                                    Each token has a UNIQUE number, like an ID. The Token ID goes to the Embedding Matrix, which is made by millions of vectors. 
                                    So you can follow, each row of this matrix is a vector, and each vector is a token. 
                                    For example: 'Explícame cómo funciona la inflación'
                                        → ["Explícame", " cómo", " funciona", " la", " inflación"] is how AI sees your prompt
                                    Now each token will go to embedding matrix as its vector form. 
                                    **Self-attention**: 
                                    Through dot product, the combination of vectors that results into a higher value, means that those tokens are the ones AI must pay attention to. In the example, funciona+inflación will be the vectors with the higher product.
                                    Indeed, it's a bit more complex, because AI also uses linear combinations and other operations with Linear Algebra, but in the end, AI understands context at a ridiculous speed.
                                """)
                            st.markdown("### LAYERS")
                            st.write("""
                                    A basic look of what layers means inside the AI:
                                    
                                    1st layer: Learns the structure. Subject - Verb - Object
                                    
                                    2nd layer: Learn meaning.
                                    
                                    3rd layer: Abstract correlations between words.
                                    
                                    Repeats the cycle of layers for about 40 times, this is 'REASONING' for AI.
                                    """)
                            
                            st.markdown("### Prediction")
                            st.write("""
                                    It does not mean AI can predict what you're going to write. If you write 'the sun comes from the...' AI has already read millions of texts to know that the most likely following word is 'east'.
                                    Think of it as the autocompletition of your cellphone's keyboard, but at an absurd higher complexity.
                                    That's the reason AI's entrance in finance has exploded, because it can take into account thousands of patterns and analyze them at faster pace than a human and give possible future moments of the market.
                                    It can find structural breaks, but is not meant for telling if tomorrow's price will go up or down.
                                    """)
                            
                            st.markdown("### Temperature")
                            st.write("Note how AI models never respond you exactly the same way over and over again? This happens because they have a temperature configuration, that basically tells the creativity in AI's answers. ")
                            st.write("When it comes to technical analysis, coding or structured outputs such as JSON files, AI should be set with a low temperature (0.0-0.3). While brainstorming, business ideas, storytelling require high temperatures (0.7-1.0) for big creativity flows. ")
                            st.write("Simplified, temperature measures how much the model can 'improvise'.")

                            st.markdown("### Hallucinations")
                            st.write("""
                                    It's very common to criticize AI's reasoning capacity because it tends to hallucinate. It's true, AI is not like Google.  
                                    Though some advanced models such as ChatGPT or Gemini have a Search tool, it's an extension of their capacity. 
                            """)

                            st.markdown("### Overfitting")
                            st.write("""
                                    AI uses two types of data: Training Data and Validation Data. The first one is data that you use to TEACH AI about certain topics. Let's say you want the AI model to learn about dogs, so you send different pictures of dogs and not dogs. 
                                    As you keep sending more examples, AI begins to learn and differentiate better. Another example could be learning for an exam. While you practice the topics and example exercises, you start learning better, that would be your Training Data. 
                                    Validation Data on the other hand is a question that didn't come in your list of examples. While you test this, you can tell if AI **memorized or learned**.
                                    If the model fails, the answer is that it memorized, in other words, overfitting. At some point there is a divergence between the Training and Validation data, because the first one's accuracy will keep going up, as it keeps doing good on data you send, but the last one's accuracy will go down, because with unseen data performs worse.
                                    When this happens, engineers have to go back to the turning point and adjusts the parameters. 

                                    **This is more focussed on AI Engineers that actually train and test LLM models such as Grok, Chatgpt or Gemini.**
                                    """)
                            
                            st.divider()

                            st.subheader("Tokens Usage 🪙")
                            st.write("The main limitation of this app is its reliance on Gemini 2.5 Flash (the free model), which has a restricted daily token allowance.")
                            st.write("Advanced features such as Edge Finder or the News Searcher consume a significant number of tokens due to the complexity of their tasks.")
                            
                            st.markdown("### Google AI Studio ")
                            st.write("The most accurate way to supervise your usage is through Google AI Studio's Usage and Limits section, where you'll find every API Key's usage over the course of the day.")
                            st.link_button("Google AI Studio: ", "https://aistudio.google.com/")
                            st.write("After clicking 'Get API Key', it will take you to another section, in which the sidebar will show 'Usage Limits'. There you'll monitor the constant changes and limits into your daily use of Gemini's API Key.")


                            with st.expander("Concepts"):
                                st.write("At first sight it might be confusing, so here's a small guide to avoid panic.")
                                st.write("")
                                
                                with st.expander("RPM"):
                                    st.write("""
                                            Requests per Minute is one of the 3 limits inside Gemini. According to the last Gemini 2.5 Flash conditions, the RPM limit is 5. 
                                            Indeed, there's nothing to worry about as it would be highly unlikely to send so many requests in a matter of minutes.
                                    """)

                                with st.expander("TPM"):
                                    st.write("Tokens per Minute refers to the limit of tokens that can be processed in one minute. That includes the context, prompt and response all in one. Hence, complex agents such as the Edge Finder or the Audit Agent, consume large quantities of tokens.")
                                    st.write("Note that we don't have a direct connection with a PRE-BUILT AGENT, so everytime you call the AI, it's like starting a new chat with it, does not store previous data.")

                                with st.expander("RPD"):
                                    st.write("""
                                            Requests per Day is the most important limit from the three. As the others are just temporary limits that go for 1 minute, this one goes for one day. 
                                            Once you exceed the limit, the APP will stop functioning immediately and will require for you to change your API Key for a new one, in case you want to keep using the program. 
                                            The RPD restarts everyday, moreless in the early morning. 
                                    """)
                                
                                with st.expander("Projects"):
                                    st.write("These limits are subject to each project. If you're considering creating 4 API Keys in the SAME project, it will have the same effect. What you could do is create many projects, but obviously Google already knows this trick.")
                                    st.write("There's no specific limit for the amount of projects you can create, so in theory there could be no limit, but Google can detect if the user abuses from the free tier.")
                                    st.write("Remember that every call consumes your quota, even if the program sends a failed prompt, Gemini will mark it as one call spent.")

                        with tab_lab:
                            
                            st.subheader("Trading History")
                            st.info("This space will show you your previous operations, profits, losses and improvements ideas to boost your earnings but not reckless.")    
                            
                            st.divider()
                            
                            st.subheader("RISK MANAGEMENT")                                        
                            st.write("To protect your capital from potential losses or your account's closure, it's mandatory to manage the risks.")
                            st.subheader("Volatility-Managed Portfolios")
                            st.info("The model comes from a paper made by Alan Moreira and Tyler Muir. They use the VIX to decide the correct exposure a portfolio should have to stocks. Though the logic is quiet simple, it is the opposite to the common belief from typical investors. When VIX is high, the market is too risky, but when VIX is low, the market is calm.")
                            with st.expander("What is a Volatility-Managed Portfolio?"):
                                st.write(" ""Be greedy when others are fearful"" That's the famous quote from Warren Buffet, which means smart investors must take advantage to buy the dips and don't follow the popular panic.")
                                st.write("However, this has been wrongly interpreted that when VIX is high, you should buy because it's a sign of fear. The model is about the opposite. When VIX increases, reduce your exposure and vice versa.")
                                st.markdown("### How do the Volatility-Managed Portfolios work?")
                                st.write(f"Each month you calculate your exposure to stocks. Say you want 75% on equity and the other 25% on cash, assuming a 'normal' VIX (the historical median level has been 17). To calculate the exposure we use this formula:")
                                st.latex(r"""
                                \text{Equity Exposure}
                                =
                                \text{Target}
                                \times
                                \frac{\text{VIX}_{\text{median}}}{\text{VIX}_{\text{actual}}}
                                """)
                                st.write("The paper found that when volatility rises, expected returns don't move but risks do increase fast.")
                                st.write("But what is the fundamental behind this reasoning?")
                                st.write("For the VIX to reach high levels, the S&P500 has already fallen, so it does not work as a timing strategy. As I've explained in the VIX chart, VIX is calculated using options, and traders react buying puts and selling stocks almost simultaneously. Because of this, VIX is considered more a Coincident indicator than a leading one (like the Yield Curve).")
                                st.write("High VIX could stay like that for longer periods and the market don't see a rebound anytime soon.")
                                st.write(f"As a proof, Helbert Ratings elaborated an analysis with data from 1990, dividing trading days into quartiles using the Wilshire 5000 Index. The interesting result was that the 25% days with the lowest VIX levels had the best risk-return ratio. Indeed, the 25% group with the highest VIX levels obtained the highest average return ratio but one has to look for the best combination of return and low risks.")
                            
                            colvix1, colvix2 = st.columns(2)
                            
                            with colvix1:
                                target_equity = st.slider("Select your Equity Exposure", 0.0, 1.0, 0.75)
                            
                            vix_median = 17.59
                            with colvix2:
                                st.metric("VIX Index", f"{ultimo_vix:.2f}", f"{delta_vix:.2f}", delta_color="inverse")
                            
                            equity_exposure = target_equity * (vix_median / ultimo_vix)
                            st.write("Equity exposure:", round(equity_exposure, 3))
                            st.metric(
                                "Recommended Equity Exposure",
                                f"{equity_exposure*100:.1f}%"
                            )

                            st.divider()

                            st.markdown("### IPOs")
                            st.write("Most new issures are sold under ""favorable market conditions"" -which means favorable for the seller and less favorable for the buyer.  ")
                            st.write("-Benjamin Graham, The Intelligent Investor, 1973")

                            st.subheader("🚀 Agente de Acciones & Valoración del S&P 500")

                            # =====================================================================
                            # PARTE 1: FILTRADO DE ACCIONES INDIVIDUALES (Yahoo Finance Data)
                            # =====================================================================
                            """
                            st.header("1. Buscador y Filtro de Acciones")

                            # Lista de tickers iniciales por defecto (el usuario puede editarla)
                            tickers_input = st.text_input("Ingresa los tickers separados por coma:", "AAPL, MSFT, GOOGL, AMZN, META, NVDA")
                            tickers_list = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

                            if st.button("Analizar y Filtrar Acciones"):
                                datos_acciones = []
                                
                                with st.spinner("Extrayendo métricas de Yahoo Finance..."):
                                    for ticker in tickers_list:
                                        try:
                                            accion = yf.Ticker(ticker)
                                            info = accion.info
                                            
                                            # Extraemos estrictamente los datos reales que expone yfinance
                                            precio = info.get('currentPrice', np.nan)
                                            pe = info.get('trailingPE', np.nan)
                                            peg = info.get('pegRatio', np.nan)
                                            roe = info.get('returnOnEquity', np.nan)
                                            if roe is not None and not np.isnan(roe):
                                                roe = roe * 100 # Convertir a porcentaje (ej: 0.15 -> 15%)
                                            div_yield = info.get('dividendYield', np.nan)
                                            if div_yield is not None and not np.isnan(div_yield):
                                                div_yield = div_yield * 100

                                            datos_acciones.append({
                                                "Ticker": ticker,
                                                "Precio": precio,
                                                "P/E": pe,
                                                "PEG": peg,
                                                "ROE (%)": roe,
                                                "Div Yield (%)": div_yield
                                            })
                                        except Exception as e:
                                            st.warning(f"No se pudo obtener data para {ticker}: {e}")

                                if datos_acciones:
                                    df_acciones = pd.DataFrame(datos_acciones)
                                    st.subheader("Métricas de Mercado Extraídas")
                                    st.dataframe(df_acciones.style.format({
                                        "Precio": "${:.2f}", "P/E": "{:.2f}", "PEG": "{:.2f}", "ROE (%)": "{:.2f}%", "Div Yield (%)": "{:.2f}%"
                                    }))
                                    
                                    # Filtros Dinámicos en base a tus reglas
                                    st.subheader("Filtrar Grupo Selecto")
                                    col_f1, col_f2, col_f3 = st.columns(3)
                                    with col_f1:
                                        min_roe = st.number_input("Mínimo ROE (%)", value=15.0)
                                    with col_f2:
                                        max_pe = st.number_input("Máximo P/E", value=25.0)
                                    with col_f3:
                                        max_peg = st.number_input("Máximo PEG", value=1.5)
                                        
                                    # Aplicar filtros al DataFrame
                                    df_filtrado = df_acciones[
                                        (df_acciones["ROE (%)"] >= min_roe) & 
                                        (df_acciones["P/E"] <= max_pe) & 
                                        (df_acciones["PEG"] <= max_peg)
                                    ]
                                    
                                    st.write("**🏆 Acciones seleccionadas bajo tus criterios:**")
                                    st.dataframe(df_filtrado)
                                else:
                                    st.error("No se recolectó data de ninguna acción.")


                            # =====================================================================
                            # PARTE 2: MODELO DE VALORACIÓN SPX CON EARNINGS PROYECTADOS (Gemini)
                            # =====================================================================
                            st.header("2. Escenarios de Valoración Justa del S&P 500 (SPX)")

                            # Simulamos los Earnings Trimestrales en dólares que Gemini calcularía/repartiría de forma inteligente
                            # (Para producción, aquí mapeas el output JSON/diccionario de tu llamada a la API de Gemini)
                            
                            earnings_proyectados = {
                                "Año 1 - Q1": 75.03,
                                "Año 1 - Q2": 81.68,
                                "Año 1 - Q3": 88.59,
                                "Año 1 - Q4": 91.90,
                                "Año 2 - Q1": 59.0,
                                "Año 2 - Q2": 62.0,
                                "Año 2 - Q3": 60.5,
                                "Año 2 - Q4": 66.0,
                            }

                            # Convertir a DataFrame base
                            df_earnings = pd.DataFrame(list(earnings_proyectados.items()), columns=["Trimestre", "Earnings per Share (EPS)"])

                            # Crear la tabla de sensibilidad con múltiplos P/E arbitrarios (19, 20, 21, 22, 23)
                            multiplos_pe = [19, 20, 21, 22, 23]

                            for pe_mult in multiplos_pe:
                                # Valor Justo del SPX = EPS del trimestre * Múltiplo P/E asignado
                                df_earnings[f"SPX @ P/E {pe_mult}"] = df_earnings["Earnings per Share (EPS)"] * pe_mult

                            st.subheader("Tabla de Sensibilidad del S&P 500 según EPS por Quarter")
                            st.dataframe(df_earnings.style.format({
                                "Earnings per Share (EPS)": "${:.2f}",
                                "SPX @ P/E 19": "{:.0f} pts",
                                "SPX @ P/E 20": "{:.0f} pts",
                                "SPX @ P/E 21": "{:.0f} pts",
                                "SPX @ P/E 22": "{:.0f} pts",
                                "SPX @ P/E 23": "{:.0f} pts"
                            }))

                            st.info("💡 Con esta matriz de sensibilidad puedes contrastar el precio actual del SPX en el mercado y ver qué múltiplo implícito está pagando el mercado respecto a los trimestres adelantados.")
                        """
                            
                        with tab_corp:
                            st.subheader("Corporate Finance Hub")
                            sp100_components = {
                            "Information Technology": ["AAPL", "ACN", "ADBE", "AMD", "AVGO", "CRM", "CSCO", "IBM", "INTC", "INTU", "MSFT", "NOW", "NVDA", "ORCL", "PLTR", "QCOM", "TXN"],
                            "Health Care": ["ABBV", "ABT", "AMGN", "BMY", "CVS", "DHR", "GILD", "ISRG", "JNJ", "LLY", "MDT", "MRK", "PFE", "TMO", "UNH"],
                           
                            "Consumer Discretionary": ["AMZN", "BKNG", "GM", "HD", "LOW", "MCD", "NKE", "SBUX", "TGT", "TSLA"],
                            "Communication Services": ["CMCSA", "DIS", "GOOG", "GOOGL", "META", "NFLX", "T", "TMUS", "VZ"],
                            "Industrials": ["BA", "CAT", "DE", "EMR", "FDX", "GD", "GE", "HON", "LMT", "MMM", "RTX", "UBER", "UNP", "UPS"],
                            "Consumer Staples": ["CL", "COST", "KO", "MDLZ", "MO", "PEP", "PG", "PM", "WMT"],
                            "Energy": ["COP", "CVX", "XOM"],
                           
                            "Real Estate": ["AMT", "SPG"],
                            "Materials": ["LIN"],
                            }

                            sp100_tickers = [ticker for tickers_sector in sp100_components.values() for ticker in tickers_sector]

                            def corporate_data(lote_tickers):
                                """
                                Recibe una lista de tickers (ej: un bloque de 25) y extrae sus datos profundos.
                                Retorna una lista de diccionarios con la información financiera cruda.
                                """
                                resultados_lote = []
                                
                                for ticker_sym in lote_tickers:
                                    try:
                                        t = yf.Ticker(ticker_sym)
                                        
                                        # Descarga de DataFrames de Yahoo
                                        df_balance = t.balance_sheet
                                        df_financials = t.financials
                                        info = t.info
                                        
                                        # ==========================================
                                        # 1. EXTRACCIÓN DEL ESTADO DE RESULTADOS (Flujos de 1 año)
                                        # ==========================================
                                        ebit = df_financials.loc['EBIT'].iloc[0] if 'EBIT' in df_financials.index else 0
                                        interest = df_financials.loc['Interest Expense'].iloc[0] if 'Interest Expense' in df_financials.index else 0
                                        
                                        if 'Tax Rate for Calcs' in df_financials.index:
                                            tax_rate = df_financials.loc['Tax Rate for Calcs'].iloc[0]
                                            if pd.isna(tax_rate): tax_rate = 0.30
                                        else:
                                            tax_rate = 0.30

                                        # ==========================================
                                        # 2. EXTRACCIÓN DEL BALANCE GENERAL (Fotos y Promedios)
                                        # ==========================================
                                        # A) DEUDA
                                        deuda_actual = df_balance.loc['Total Debt'].iloc[0] if 'Total Debt' in df_balance.index else 0
                                        # Verificamos si hay datos del año pasado (más de 1 columna)
                                        if 'Total Debt' in df_balance.index and df_balance.shape[1] > 1:
                                            deuda_anterior = df_balance.loc['Total Debt'].iloc[1]
                                            if pd.isna(deuda_anterior): deuda_anterior = deuda_actual
                                        else:
                                            deuda_anterior = deuda_actual # Fallback si no hay historial
                                            
                                        deuda_promedio = (deuda_actual + deuda_anterior) / 2

                                        # B) PATRIMONIO (Stockholders Equity) - ¡Necesario para el ROIC!
                                        patrimonio_actual = df_balance.loc['Stockholders Equity'].iloc[0] if 'Stockholders Equity' in df_balance.index else 0
                                        if 'Stockholders Equity' in df_balance.index and df_balance.shape[1] > 1:
                                            patrimonio_anterior = df_balance.loc['Stockholders Equity'].iloc[1]
                                            if pd.isna(patrimonio_anterior): patrimonio_anterior = patrimonio_actual
                                        else:
                                            patrimonio_anterior = patrimonio_actual
                                            
                                        patrimonio_promedio = (patrimonio_actual + patrimonio_anterior) / 2

                                        # ==========================================
                                        # 3. EXTRACCIÓN DE MERCADO (Info)
                                        # ==========================================
                                        beta = info.get('beta', 1.0)
                                        market_cap = info.get('marketCap', 0)
                                        
                                        # ==========================================
                                        # 4. GUARDADO DE DATOS (Todo en Millones $M)
                                        # ==========================================
                                        resultados_lote.append({
                                            'Ticker': ticker_sym,
                                            'Market Cap ($M)': round(market_cap / 1e6, 2),
                                            'Beta': beta,
                                            # Usamos los promedios para mayor rigor financiero
                                            'Deuda Promedio ($M)': round(deuda_promedio / 1e6, 2),
                                            'Patrimonio Promedio ($M)': round(patrimonio_promedio / 1e6, 2),
                                            # Guardamos también la deuda actual por si la necesitas para ponderar el WACC actual
                                            'Deuda Actual ($M)': round(deuda_actual / 1e6, 2), 
                                            'EBIT ($M)': round(ebit / 1e6, 2),
                                            'Interest Expense ($M)': round(interest / 1e6, 2),
                                            'Tax Rate': round(tax_rate, 4)
                                        })
                                        
                                    except Exception as e:
                                        # Si una empresa falla, pasa a la siguiente
                                        continue
                                        
                                return resultados_lote

                            def escanear_en_lotes(tickers, tamano_lote=25, pause_sec=2):
                                resultados_totales = []
                                progreso_bar = st.progress(0)
                                texto_estado = st.empty()
                                
                                for i in range(0, len(tickers), tamano_lote):
                                    sub_lote = tickers[i : i + tamano_lote]
                                    texto_estado.text(f"⏳ Batch processing {int(i/tamano_lote) + 1}... Analizando: {', '.join(sub_lote)}")
                                    
                                    datos_de_este_lote = corporate_data(sub_lote)
                                    resultados_totales.extend(datos_de_este_lote)
                                    
                                    porcentaje = min((i + tamano_lote) / len(tickers), 1.0)
                                    progreso_bar.progress(porcentaje)
                                    
                                    if i + tamano_lote < len(tickers):
                                        time.sleep(pause_sec)
                                        
                                texto_estado.empty()
                                progreso_bar.empty()
                                return resultados_totales
                            
                            # ==============================================================================
                            # 4. CAPA DE CACHÉ
                            # ==============================================================================

                            @st.cache_data(ttl=3600)  # cachea 1h para no re-descargar en cada rerun de Streamlit
                            
                            def ejecutar_analisis_cached(lista_tickers):
                                return escanear_en_lotes(lista_tickers, tamano_lote=25, pause_sec=2)

                            fuente_tickers = st.radio("Tickers source:", ["📋 Use my Watchlist", "Use S&P 100"], horizontal=True)

                            if fuente_tickers == "📋 Use my Watchlist":
                                input_raw = st.text_area("Paste your watchlist:", key="corp_hub_watchlist_input")
                                st.write("Please insert it into excel format. The program assumes each ticker is a row in your watchlist.")
                                lista_final = [t.strip().upper() for t in input_raw.split() if t.strip()] if input_raw else []
                            else:
                                lista_final = sp100_tickers
                                st.info(f"Se analizarán las {len(lista_final)} empresas del S&P 100 en lotes de 25, con 2s de pausa entre lotes (~8 lotes, un par de minutos en total).")
                            
                            # =========================
                            # Market Risk Premium
                            # =========================

                            # Obtener rendimiento del Treasury 10Y
                            try:
                                bono_10a = yf.Ticker("^TNX")
                                rf_actual = bono_10a.fast_info.get("previousClose", 4.25)
                            except:
                                rf_actual = 4.25

                            st.markdown("### Market Risk Premium")
                            st.write("To calculate the CAPM, please type your premium")

                            col1, col2 = st.columns(2)

                            with col1:
                                rf = st.number_input(
                                    "Risk-Free Rate (%)",
                                    value=float(rf_actual),
                                    step=0.10
                                ) / 100

                            with col2:
                                market_risk_premium = st.number_input(
                                    "Market Risk Premium (%)",
                                    value= 10 - rf_actual,
                                    step=0.10
                                ) / 100

                            st.caption(f"10Y Treasury Bond yield: **{rf_actual:.2f}%**")
                            st.caption("Source: Yahoo Finance")


                            if st.button("🚀 Search for Economic Value opportunities"):
                                if not lista_final:
                                    st.warning("La lista de tickers está vacía. Por favor introduce datos válidos.")
                                else:
                                    with st.spinner("Downloading fundamentals..."):
                                        
                                        datos_crudos = ejecutar_analisis_cached(lista_final)
                                        
                                        if datos_crudos and len(datos_crudos) > 0:
                                            df_resultados = pd.DataFrame(datos_crudos)
                                            
                                            # 🛡️ BLINDAJE: Verificación de seguridad de columnas
                                            columnas_verificar = {
                                                'Beta': 1.0, 'Market Cap ($M)': 0.0, 'Deuda Actual ($M)': 0.0, 
                                                'Deuda Promedio ($M)': 0.0, 'Patrimonio Promedio ($M)': 0.0, 
                                                'EBIT ($M)': 0.0, 'Interest Expense ($M)': 0.0, 'Tax Rate': 0.30
                                            }
                                            for col, val_defecto in columnas_verificar.items():
                                                if col not in df_resultados.columns:
                                                    df_resultados[col] = val_defecto
                                                else:
                                                    df_resultados[col] = df_resultados[col].fillna(val_defecto)
                                            
                                            # 🛑 FILTRADO DE CALIDAD DE DATOS
                                            condicion_data_incompleta = (df_resultados['Deuda Promedio ($M)'] > 0) & (df_resultados['Interest Expense ($M)'] == 0)
                                            
                                            df_excluidas_data = df_resultados[condicion_data_incompleta]
                                            df_filtrado_valido = df_resultados[~condicion_data_incompleta].copy()
                                            
                                            lista_excluidas = df_excluidas_data['Ticker'].tolist()

                                            # ==========================================
                                            # 🟢 CONTROL DE FLUJO: VALIDAR SI HAY DATOS
                                            # ==========================================
                                            if not df_filtrado_valido.empty:
                                                
                                                # A) Ke (CAPM)
                                                df_filtrado_valido['Ke'] = rf + df_filtrado_valido['Beta'] * market_risk_premium
                                                
                                                # B) Kd Bruto y Kd Neto (Con ahorro fiscal)
                                                df_filtrado_valido['Kd Bruto'] = df_filtrado_valido.apply(
                                                    lambda r: r['Interest Expense ($M)'] / r['Deuda Promedio ($M)'] if r['Deuda Promedio ($M)'] > 0 else 0.0, axis=1
                                                )
                                                df_filtrado_valido['Kd Neto'] = df_filtrado_valido['Kd Bruto'] * (1 - df_filtrado_valido['Tax Rate'])
                                                
                                                # C) Ponderaciones WACC (Con Deuda Actual)
                                                df_filtrado_valido['Firm Value (V)'] = df_filtrado_valido['Market Cap ($M)'] + df_filtrado_valido['Deuda Actual ($M)']
                                                df_filtrado_valido['We'] = df_filtrado_valido.apply(lambda r: r['Market Cap ($M)'] / r['Firm Value (V)'] if r['Firm Value (V)'] > 0 else 1.0, axis=1)
                                                df_filtrado_valido['Wd'] = df_filtrado_valido.apply(lambda r: r['Deuda Actual ($M)'] / r['Firm Value (V)'] if r['Firm Value (V)'] > 0 else 0.0, axis=1)
                                                
                                                # D) WACC 
                                                df_filtrado_valido['WACC'] = (df_filtrado_valido['Ke'] * df_filtrado_valido['We']) + (df_filtrado_valido['Kd Neto'] * df_filtrado_valido['Wd'])
                                                
                                                # E) ROIC (Con promedios contables)
                                                df_filtrado_valido['NOPAT'] = df_filtrado_valido['EBIT ($M)'] * (1 - df_filtrado_valido['Tax Rate'])
                                                df_filtrado_valido['Capital Invertido Promedio'] = df_filtrado_valido['Deuda Promedio ($M)'] + df_filtrado_valido['Patrimonio Promedio ($M)']
                                                df_filtrado_valido['ROIC'] = df_filtrado_valido.apply(
                                                    lambda r: r['NOPAT'] / r['Capital Invertido Promedio'] if r['Capital Invertido Promedio'] > 0 else 0.0, axis=1
                                                )
                                                
                                                # F) SPREAD
                                                df_filtrado_valido['Spread (ROIC - WACC)'] = df_filtrado_valido['ROIC'] - df_filtrado_valido['WACC']
                                                
                                                # G) OBTENER EL TOP 10
                                                df_top10 = df_filtrado_valido.sort_values(by='Spread (ROIC - WACC)', ascending=False).head(10).copy()
                                                
                                                # H) CALCULAR MEDIAS DESCRIPTIVAS (Exclusivas del TOP 10)
                                                media_roic = df_top10['ROIC'].mean()
                                                media_wacc = df_top10['WACC'].mean()
                                                media_spread = df_top10['Spread (ROIC - WACC)'].mean()
                                                
                                                # ==========================================
                                                # 4. DESPLIEGUE FINAL EN PANTALLA (DENTRO DEL IF)
                                                # ==========================================
                                                st.balloons()
                                                st.success(f"🎯 Complex analysis terminated. Evaluated: {len(df_filtrado_valido)} firms.")
                                                
                                                # Tarjetas de Estadísticas
                                                st.markdown("### 📊 Descriptive statistics (TOP 10)")
                                                col1, col2, col3 = st.columns(3)
                                                col1.metric("Average ROIC", f"{media_roic*100:.2f}%")
                                                col2.metric("Average WACC", f"{media_wacc*100:.2f}%")
                                                col3.metric("Average Spread", f"{media_spread*100:.2f}%", delta=f"{media_spread*100:.2f}%")
                                                
                                                st.markdown("---")
                                                st.markdown("### 🏆 Top 10: Firms with the highest Value of Growth")
                                                
                                                # Construcción del DataFrame visual estructurado
                                                df_vista = pd.DataFrame()
                                                df_vista['Ticker'] = df_top10['Ticker']
                                                df_vista['Spread'] = df_top10['Spread (ROIC - WACC)'].map(lambda x: f"{x*100:.2f}%")
                                                df_vista['ROIC'] = df_top10['ROIC'].map(lambda x: f"{x*100:.2f}%")
                                                df_vista['WACC'] = df_top10['WACC'].map(lambda x: f"{x*100:.2f}%")
                                                df_vista['Ke (CAPM)'] = df_top10['Ke'].map(lambda x: f"{x*100:.2f}%")
                                                df_vista['Kd'] = df_top10['Kd Neto'].map(lambda x: f"{x*100:.2f}%")
                                                df_vista['W_e (Equity%)'] = df_top10['We'].map(lambda x: f"{x*100:.1f}%")
                                                df_vista['W_d (Deuda%)'] = df_top10['Wd'].map(lambda x: f"{x*100:.1f}%")
                                                df_vista['Market Cap'] = df_top10['Market Cap ($M)'].map(lambda x: f"${x/1000:.2f}B" if x >= 1000 else f"${x:.2f}M")
                                                
                                                # Renderizar la tabla limpia en Streamlit
                                                st.dataframe(df_vista, use_container_width=True, hide_index=True)
                                                
                                                # Nota de auditoría por si excluimos empresas con data rota
                                                if lista_excluidas:
                                                    st.markdown("---")
                                                    st.warning(
                                                        f"⚠️ **Nota de auditoría de datos:** Las siguientes empresas ({', '.join(lista_excluidas)}) "
                                                        f"fueron **excluidas del ranking** debido a inconsistencias en la fuente de datos. "
                                                        f"Yahoo Finance reportó que tenían Deuda activa pero registró un gasto por intereses (`Interest Expense`) de $0, "
                                                        f"lo que habría generado métricas de WACC sesgadas y poco realistas."
                                                    )
                                            else:
                                                st.error("❌ Tras aplicar los filtros de calidad, no quedaron empresas con datos financieros válidos en este lote.")
                                                if lista_excluidas:
                                                    st.info(f"Empresas descartadas en este intento: {', '.join(lista_excluidas)}")
                                        else:
                                            st.error("❌ Error: No se pudieron extraer datos de la API de Yahoo Finance.")
                
                except Exception as error_yahoo:
                    st.error(f"Error al correr el programa: {error_yahoo}")
        else:
            st.info("🔍 Ingresa un Ticker para comenzar el análisis.")

    else:
        st.warning("Please insert your API key on the sidebar to initialize.")

elif authentication_status == False:
    st.error('User or password inaccurates')

elif authentication_status == None:
    st.warning('Introduce your user and password to start.')

#Para CORRER el código: python -m streamlit run app.py
#Para DETENER el programa: Control + C

#-------------------------CAMBIO EN LAS CARPETAS---------------------------------
#Cuando creas una nueva carpeta dentro del Workspace (Finance) para ordenar tus archivos (Ej: Python Projects), la terminal se quedará en el pasado.
#Va a salir PS C:\Finance>, ahi debes escribir: cd "Python Projects" y enter.
#Ahora debería salir PS C:\Finance\Python Projects>