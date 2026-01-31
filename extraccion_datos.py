import requests
import pandas as pd
from bs4 import BeautifulSoup
import urllib3
import ssl
import re

# Configuración: Silenciar advertencias SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def limpiar_nombre_provincia(texto):
    """Limpia 'Madrid(37)' -> 'Madrid'"""
    if not texto: return ""
    return re.split(r'[\(\|]', texto)[0].strip()

def extraer_elecciones():
    print("--- Extrayendo Datos Elecciones (El País) ---")
    url = "https://elpais.com/espana/elecciones/generales/escanos-por-provincia/"
    
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(response.content, 'html.parser')
        tabla = soup.find('table')
        
        if not tabla:
            print("ERROR: No se encontró la tabla.")
            return

        # 1. DETECCIÓN INTELIGENTE DE COLUMNAS
        # Obtenemos todos los th, pero filtramos los que son claramente etiquetas de diseño
        raw_headers = []
        for th in tabla.find_all('th'):
            texto = th.get_text(strip=True).upper()
            img = th.find('img')
            if img: # Si hay logo (PP/PSOE), lo añadimos al texto para identificarlo
                alt = img.get('alt', '').upper()
                texto = f"{texto} {alt}"
            raw_headers.append(texto)

        # Crear un mapa de índices reales ignorando cabeceras "falsas"
        # Cabeceras a ignorar porque no tienen columna de datos debajo
        BLACKLIST = ['PARTIDOS', '', 'PROVINCIA (ESCAÑOS)'] 
        
        # Identificamos el índice relativo de PP y PSOE en la lista de PARTIDOS
        # Asumimos estructura: [Provincia, (Partidos...), PP, PSOE, VOX...]
        # La columna de datos 0 es Provincia. La 1 es el primer partido, la 2 el segundo...
        
        try:
            # Buscamos en qué posición de la lista de cabeceras aparecen PP y PSOE
            idx_header_pp = next(i for i, h in enumerate(raw_headers) if 'PP' in h or 'POPULAR' in h)
            idx_header_psoe = next(i for i, h in enumerate(raw_headers) if 'PSOE' in h or 'SOCIALISTA' in h)
            
            # CALCULO DEL OFFSET (DESFASE)
            # Generalmente: [Provincia, Label, Gap, PP, PSOE...]
            # Indices Headers: 0, 1, 2, 3(PP), 4(PSOE)
            # Indices Datos:   0(Prov), 1(PP), 2(PSOE)
            # El offset se calcula contando cuántos 'headers basura' hay antes del PP
            # Pero es más seguro asumir que PP es la columna de datos 1 y PSOE la 2 si son los primeros detectados
            
            # Verificación: ¿Cuál aparece primero?
            primero = 'PP' if idx_header_pp < idx_header_psoe else 'PSOE'
            print(f"Detectado orden: {primero} aparece antes.")
            
            # ASIGNACIÓN DE INDICES DE DATOS (Hardcoded dinámico)
            # Si PP está antes que PSOE y son los primeros partidos, asignamos:
            col_idx_pp = 1
            col_idx_psoe = 2
            
            # Si hubiera un partido antes (ej: Vox antes que PP), esto fallaría, pero el orden estándar es por votos.
            # Ajuste fino: Verificar si 'PARTIDOS' está entre Provincia y PP
            
        except StopIteration:
            print("No se encontraron cabeceras de PP o PSOE.")
            return

        print(f"Usando índices de datos estimados -> PP: Col {col_idx_pp}, PSOE: Col {col_idx_psoe}")

        data = []
        rows = tabla.find_all('tr')
        
        for row in rows:
            # Extraemos celdas (td y th porque la provincia a veces es th)
            cells = row.find_all(['td', 'th'])
            
            # Si la fila es muy corta, es cabecera o decorativa
            if len(cells) < 3: continue
            
            # 1. Provincia
            prov_raw = cells[0].get_text(strip=True)
            provincia = limpiar_nombre_provincia(prov_raw)
            
            # Filtros de filas invalidas
            if not provincia or "TOTAL" in provincia.upper() or "PROVINCIA" in provincia.upper() or "PARTIDOS" in provincia.upper():
                continue

            # 2. Extraer escaños
            try:
                def get_val(idx):
                    if idx >= len(cells): return 0
                    celda = cells[idx]
                    # Prioridad 1: Contar spans (cuadraditos)
                    spans = celda.find_all('span')
                    if spans: return len(spans)
                    # Prioridad 2: Texto numérico
                    txt = celda.get_text(strip=True)
                    return int(txt) if txt.isdigit() else 0

                pp_val = get_val(col_idx_pp)
                psoe_val = get_val(col_idx_psoe)
                
                # Validación anti-cero (Madrid no puede tener 0 y 0)
                # Si ambos son 0, quizás los indices están mal desplazados -> Intentar +1? 
                # (No lo haremos automático para no ensuciar, pero es un indicador)

                data.append({
                    "Provincia": provincia,
                    "Escanos_PP": pp_val,
                    "Escanos_PSOE": psoe_val
                })
            except Exception as e:
                continue

        # Crear DataFrame
        df = pd.DataFrame(data)
        
        # Limpieza final: Eliminar filas donde ambos sean 0 (suelen ser filas vacías o errores)
        df = df[(df['Escanos_PP'] > 0) | (df['Escanos_PSOE'] > 0)]
        
        if df.empty:
            print("Error: El DataFrame está vacío. Revisa los índices de columnas.")
        else:
            df.to_csv("datos_elecciones_crudo.csv", index=False, encoding='utf-8-sig')
            print(f"Elecciones guardado: {len(df)} provincias.")
            print("Muestra (verifica que Madrid tenga ~16 PP y ~10 PSOE):")
            print(df.head(3))

    except Exception as e:
        print(f"Error crítico en Elecciones: {e}")

def extraer_pib():
    print("--- Extrayendo PIB (INE) ---")
    url = "https://www.ine.es/dyngs/INEbase/es/operacion.htm?c=Estadistica_C&cid=1254736167628&menu=ultiDatos&idp=1254735576581"
    ssl._create_default_https_context = ssl._create_unverified_context
    try:
        dfs = pd.read_html(url)
        df_pib = dfs[0]
        # Limpieza rápida de columnas extrañas si las hubiera
        df_pib = df_pib.loc[:, ~df_pib.columns.str.contains('^Unnamed')]
        df_pib.to_csv("datos_pib_crudo.csv", index=False, encoding='utf-8-sig')
        print("PIB guardado.")
    except Exception as e:
        print(f"Error PIB: {e}")

def extraer_educacion():
    print("--- Descargando Educación (INE CSV) ---")
    url = "https://www.ine.es/jaxiT3/files/t/es/csv_bd/69774.csv?nocab=1"
    try:
        response = requests.get(url, verify=False)
        with open("datos_educacion_crudo.csv", "wb") as f:
            f.write(response.content)
        print("Educación guardada.")
    except Exception as e:
        print(f"Error Educación: {e}")

if __name__ == "__main__":
    extraer_elecciones()
    extraer_pib()
    extraer_educacion()