import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def generar_grafico():
    print("--- Generando Gráfico ---")
    try:
        df = pd.read_csv("datos_final_analisis.csv")
    except FileNotFoundError:
        print("Error: No existe datos_final_analisis.csv")
        return

    # Estética
    sns.set_style("whitegrid")
    plt.figure(figsize=(14, 10)) # Un poco más grande para que quepan etiquetas

    # Colores oficiales aproximados
    colors = {'PP': '#0055A7', 'PSOE': '#E30613', 'Empate': '#808080'}
    
    # Scatter Plot
    plot = sns.scatterplot(
        data=df,
        x='PIB_Per_Capita',
        y='Pct_Educacion_Superior',
        hue='Ganador',
        palette=colors,
        s=200, # Puntos grandes
        edgecolor='black',
        alpha=0.85
    )

    # Añadir etiquetas inteligentes
    # Ajustamos el texto un poco arriba y a la derecha del punto
    texts = []
    for i, row in df.iterrows():
        plt.text(
            x=row['PIB_Per_Capita'] + 300, # Desplazamiento en X
            y=row['Pct_Educacion_Superior'] + 0.2, # Desplazamiento en Y
            s=row['CCAA'],
            fontsize=9,
            fontweight='medium',
            bbox=dict(facecolor='white', alpha=0.6, edgecolor='none', pad=0.5)
        )

    # Títulos y Ejes
    plt.title('Relación entre Nivel Socioeconómico y Voto (PP vs PSOE)\nElecciones Generales España', fontsize=18, fontweight='bold', pad=20)
    plt.xlabel('PIB per cápita (€)', fontsize=14)
    plt.ylabel('% Población con Educación Superior (25-64 años)', fontsize=14)
    
    # Leyenda limpia
    plt.legend(title='Partido más votado', title_fontsize='12', loc='upper left', frameon=True)
    
    # Cuadrantes medios (Opcional: Líneas promedio)
    plt.axvline(x=df['PIB_Per_Capita'].mean(), color='gray', linestyle='--', alpha=0.5)
    plt.axhline(y=df['Pct_Educacion_Superior'].mean(), color='gray', linestyle='--', alpha=0.5)
    
    # Nota al pie
    plt.figtext(0.99, 0.01, 'Fuente: El País, INE. Elaboración propia con Python.', horizontalalignment='right', fontsize=8, color='gray')

    plt.tight_layout()
    plt.savefig("grafico_pp_psoe.png", dpi=300, bbox_inches='tight')
    print("Gráfico guardado como grafico_pp_psoe.png")
    plt.show()

if __name__ == "__main__":
    generar_grafico()