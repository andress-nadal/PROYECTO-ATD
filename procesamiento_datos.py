import pandas as pd
import numpy as np

# Diccionario de Mapeo (Provincias -> CCAA)
MAPA_PROV_CCAA = {
    'Almería': 'Andalucía', 'Cádiz': 'Andalucía', 'Córdoba': 'Andalucía',
    'Granada': 'Andalucía', 'Huelva': 'Andalucía', 'Jaén': 'Andalucía',
    'Málaga': 'Andalucía', 'Sevilla': 'Andalucía',
    'Huesca': 'Aragón', 'Teruel': 'Aragón', 'Zaragoza': 'Aragón',
    'Asturias': 'Principado de Asturias',
    'Illes Balears': 'Illes Balears', 'Baleares': 'Illes Balears',
    'Las Palmas': 'Canarias', 'Santa Cruz de Tenerife': 'Canarias',
    'Cantabria': 'Cantabria',
    'Ávila': 'Castilla y León', 'Avila': 'Castilla y León',
    'Burgos': 'Castilla y León', 'León': 'Castilla y León',
    'Palencia': 'Castilla y León', 'Salamanca': 'Castilla y León',
    'Segovia': 'Castilla y León', 'Soria': 'Castilla y León',
    'Valladolid': 'Castilla y León', 'Zamora': 'Castilla y León',
    'Albacete': 'Castilla-La Mancha', 'Ciudad Real': 'Castilla-La Mancha',
    'Cuenca': 'Castilla-La Mancha', 'Guadalajara': 'Castilla-La Mancha',
    'Toledo': 'Castilla-La Mancha',
    'Barcelona': 'Cataluña', 'Girona': 'Cataluña',
    'Lleida': 'Cataluña', 'Tarragona': 'Cataluña',
    'Alicante': 'Comunitat Valenciana', 'Alacant': 'Comunitat Valenciana',
    'Castellón': 'Comunitat Valenciana', 'Castelló': 'Comunitat Valenciana',
    'Valencia': 'Comunitat Valenciana', 'València': 'Comunitat Valenciana',
    'Badajoz': 'Extremadura', 'Cáceres': 'Extremadura',
    'A Coruña': 'Galicia', 'Coruña, A': 'Galicia',
    'Lugo': 'Galicia', 'Ourense': 'Galicia', 'Pontevedra': 'Galicia',
    'Madrid': 'Comunidad de Madrid',
    'Murcia': 'Región de Murcia',
    'Navarra': 'Comunidad Foral de Navarra',
    'Araba': 'País Vasco', 'Álava': 'País Vasco', 
    'Bizkaia': 'País Vasco', 'Vizcaya': 'País Vasco',
    'Gipuzkoa': 'País Vasco', 'Guipúzcoa': 'País Vasco',
    'La Rioja': 'La Rioja',
    'Ceuta': 'Ceuta', 'Melilla': 'Melilla'
}

def reparar_nombre_ine(nombre):
    """
    Función maestra para limpiar nombres del INE:
    1. Arregla caracteres corruptos (Mojibake): 'AndalucÃ­a' -> 'Andalucía'
    2. Arregla formato inverso: 'Madrid, Comunidad de' -> 'Comunidad de Madrid'
    3. Arregla guiones y espacios: '01 Andalucía' -> 'Andalucía'
    """
    if not isinstance(nombre, str): return nombre
    
    # 1. Intentar arreglar codificación (latin1 interpretado como utf8)
    try:
        # Si contiene caracteres típicos de mojibake, intentamos recodificar
        if 'Ã' in nombre:
            nombre = nombre.encode('latin-1').decode('utf-8')
    except:
        pass # Si falla, dejamos el original
        
    # 2. Quitar números iniciales ("01 Andalucía")
    parts = nombre.split(' ', 1)
    if len(parts) > 1 and parts[0].isdigit():
        nombre = parts[1]
        
    # 3. Arreglar "Nombre, Tipo de" -> "Tipo de Nombre"
    if ',' in nombre:
        partes = nombre.split(',', 1) # ['Madrid', ' Comunidad de']
        nombre = partes[1].strip() + " " + partes[0].strip() # 'Comunidad de Madrid'

    # 4. Limpiezas finales
    nombre = nombre.replace(' - ', '-').strip() # 'Castilla - La Mancha' -> 'Castilla-La Mancha'
    
    return nombre

def procesar():
    print("--- 1. Procesando Elecciones ---")
    df_elec = pd.read_csv("datos_elecciones_crudo.csv", encoding='utf-8-sig')
    df_elec['Provincia'] = df_elec['Provincia'].str.strip()
    df_elec['CCAA'] = df_elec['Provincia'].map(MAPA_PROV_CCAA)
    
    # Check rápido
    sin_mapa = df_elec[df_elec['CCAA'].isna()]['Provincia'].unique()
    if len(sin_mapa) > 0: print(f"Provincias ignoradas: {sin_mapa}")

    # Agrupar
    df_elec_agrup = df_elec.groupby('CCAA')[['Escanos_PP', 'Escanos_PSOE']].sum().reset_index()
    df_elec_agrup['Ganador'] = np.where(
        df_elec_agrup['Escanos_PP'] > df_elec_agrup['Escanos_PSOE'], 'PP',
        np.where(df_elec_agrup['Escanos_PSOE'] > df_elec_agrup['Escanos_PP'], 'PSOE', 'Empate')
    )
    print(f"Elecciones OK: {len(df_elec_agrup)} CCAA encontradas.")

    print("--- 2. Procesando Educación ---")
    try:
        # Intentamos leer con tabuladores primero
        df_edu = pd.read_csv("datos_educacion_crudo.csv", sep='\t', encoding='utf-8', engine='python')
        if df_edu.shape[1] < 2:
             df_edu = pd.read_csv("datos_educacion_crudo.csv", sep=';', encoding='latin-1')
    except:
        df_edu = pd.read_csv("datos_educacion_crudo.csv", sep=None, engine='python')

    df_edu.columns = [c.strip() for c in df_edu.columns]
    
    col_ccaa = next((c for c in df_edu.columns if 'Comunidad' in c or 'autónoma' in c), df_edu.columns[1])
    col_nivel = next((c for c in df_edu.columns if 'Nivel' in c), df_edu.columns[0])
    col_total = next((c for c in df_edu.columns if 'Total' in c or 'Valor' in c), df_edu.columns[-1])
    col_edad = next((c for c in df_edu.columns if 'Edad' in c), None)

    # Filtros
    mask_nivel = df_edu[col_nivel].str.contains('Superior|5-8', case=False, na=False)
    if col_edad:
        mask_edad = df_edu[col_edad].str.contains('25 a 64', na=False)
        df_edu_filt = df_edu[mask_nivel & mask_edad].copy()
    else:
        df_edu_filt = df_edu[mask_nivel].copy()

    if 'Periodo' in df_edu_filt.columns:
        df_edu_filt = df_edu_filt[df_edu_filt['Periodo'] == df_edu_filt['Periodo'].max()]

    # APLICAR LIMPIEZA MAESTRA
    df_edu_filt['CCAA_Clean'] = df_edu_filt[col_ccaa].apply(reparar_nombre_ine)
    
    # Limpieza numérica
    df_edu_filt['Pct_Educacion'] = (df_edu_filt[col_total]
                                    .astype(str)
                                    .str.replace('.', '', regex=False)
                                    .str.replace(',', '.', regex=False))
    df_edu_filt['Pct_Educacion'] = pd.to_numeric(df_edu_filt['Pct_Educacion'], errors='coerce')
    
    df_edu_final = df_edu_filt.groupby('CCAA_Clean')['Pct_Educacion'].mean().reset_index()
    print("Educación OK.")

    print("--- 3. Procesando PIB ---")
    df_pib = pd.read_csv("datos_pib_crudo.csv", encoding='utf-8-sig')
    
    col_ccaa_pib = df_pib.columns[0]
    cols_numericas = [c for c in df_pib.columns if c not in [col_ccaa_pib, 'Nota']]
    col_valor_pib = 'Valor' if 'Valor' in df_pib.columns else cols_numericas[0]

    # APLICAR LIMPIEZA MAESTRA
    df_pib['CCAA_Clean'] = df_pib[col_ccaa_pib].apply(reparar_nombre_ine)
    
    df_pib['PIB_Valor'] = (df_pib[col_valor_pib]
                           .astype(str)
                           .str.replace('.', '', regex=False)
                           .str.replace(',', '.', regex=False))
    df_pib['PIB_Valor'] = pd.to_numeric(df_pib['PIB_Valor'], errors='coerce')
    
    df_pib_final = df_pib[['CCAA_Clean', 'PIB_Valor']].dropna()
    print("PIB OK.")

    print("--- 4. Uniendo (Merge) ---")
    # Merge Inner: Solo se queda con lo que coincida en todas las tablas
    df_final = pd.merge(df_elec_agrup, df_pib_final, left_on='CCAA', right_on='CCAA_Clean', how='inner')
    df_final = pd.merge(df_final, df_edu_final, left_on='CCAA', right_on='CCAA_Clean', how='inner')
    
    df_final = df_final[['CCAA', 'Escanos_PP', 'Escanos_PSOE', 'Ganador', 'PIB_Valor', 'Pct_Educacion']]
    df_final.columns = ['CCAA', 'Escanos_PP', 'Escanos_PSOE', 'Ganador', 'PIB_Per_Capita', 'Pct_Educacion_Superior']
    
    print(f"RESULTADO FINAL: {len(df_final)} Comunidades Autónomas unidas correctamente.")
    
    # Verificación de datos perdidos
    ccaa_esperadas = set(df_elec_agrup['CCAA'])
    ccaa_finales = set(df_final['CCAA'])
    perdidas = ccaa_esperadas - ccaa_finales
    if perdidas:
        print(f"Se han perdido estas CCAA por fallo en el nombre: {perdidas}")
    else:
        print("Todas las CCAA se han cruzado correctamente.")

    df_final.to_csv("datos_final_analisis.csv", index=False)
    print("Muestra de datos (Incluyendo Cataluña/Madrid si todo va bien):")
    print(df_final[df_final['CCAA'].str.contains('Madrid|Catalu|Andalu', regex=True)])

if __name__ == "__main__":
    procesar()