import pandas as pd
import numpy as np # Necesario para los datos de ejemplo
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from statsmodels.stats.multicomp import pairwise_tukeyhsd

# --- PASO 1: Carga y Procesamiento del Formato Específico ---

try:
    # 1. Cargar el CSV SIN encabezado. Pandas usará números (0, 1, 2, 3) como nombres de columna.
    df = pd.read_csv('datos_latencia.csv', header=None)

    # 2. Asignar nombres de columna temporales para mayor claridad.
    df.columns = ['col_tecnica', 'col_paquete', 'col_latencia', 'col_payload']

    # 3. LIMPIEZA: Extraer el valor de cada celda dividiendo por el ':' y convirtiendo a número.
    #    .str.split(':').str[1] -> Divide el string por ':' y toma la segunda parte (el valor).
    #    .str.strip() -> Elimina espacios en blanco accidentales.
    #    .astype(float) -> Convierte el string resultante a un número.
    df['tecnica'] = df['col_tecnica'].str.split(':').str[1].str.strip()
    df['latencia'] = df['col_latencia'].str.split(':').str[1].str.strip().astype(float)
    
    # 4. Seleccionar solo las columnas que necesitamos para el análisis.
    df_clean = df[['tecnica', 'latencia']].copy()

except FileNotFoundError:
    print("Archivo 'datos_latencia.csv' no encontrado. Usando datos de ejemplo.")
    # Creando datos de ejemplo si el archivo no existe
    data_list = []
    np.random.seed(42)
    for i in range(120): data_list.append(['icmp', np.random.normal(1.5, 0.4)])
    for i in range(120): data_list.append(['owamp', np.random.normal(5.0, 1.2)])
    for i in range(120): data_list.append(['int', np.random.normal(1900, 300)])
    df_clean = pd.DataFrame(data_list, columns=['tecnica', 'latencia'])


# --- PASO 2: Normalización de Unidades (CRÍTICO) ---
# Creamos una nueva columna 'latencia_ms' para mantener los datos originales
df_clean['latencia_ms'] = df_clean['latencia']
# Convertir la latencia de 'int' de microsegundos a milisegundos
df_clean.loc[df_clean['tecnica'] == 'int', 'latencia_ms'] = df_clean['latencia_ms'] / 1000

print("--- Resumen estadístico después de la carga y conversión ---")
print(df_clean.groupby('tecnica')['latencia_ms'].describe())
print("\n" + "="*60 + "\n")


# --- PASO 3: Análisis Exploratorio de Datos (Visualización) ---

sns.set_theme(style="whitegrid")
plt.figure(figsize=(10, 7))
sns.boxplot(x='tecnica', y='latencia_ms', data=df_clean)
plt.title('Distribución de Latencia por Técnica (en ms)', fontsize=16)
plt.xlabel('Técnica de Medición', fontsize=12)
plt.ylabel('Latencia (ms)', fontsize=12)
plt.show()

g = sns.FacetGrid(df_clean, col="tecnica", height=5, sharex=False, sharey=False)
g.map(sns.histplot, "latencia_ms", kde=True)
g.fig.suptitle('Histograma de Latencia para cada Técnica', y=1.03, fontsize=16)
g.set_axis_labels("Latencia (ms)", "Frecuencia")
plt.show()


# --- PASO 4: Verificación de Supuestos del ANOVA ---

icmp_lat = df_clean[df_clean['tecnica'] == 'icmp']['latencia_ms']
owamp_lat = df_clean[df_clean['tecnica'] == 'owamp']['latencia_ms']
int_lat = df_clean[df_clean['tecnica'] == 'int']['latencia_ms']

levene_stat, levene_p = stats.levene(icmp_lat, owamp_lat, int_lat)
print(f"--- Verificación de Supuestos ---")
print(f"Test de Levene para homogeneidad de varianzas:")
print(f"Estadístico = {levene_stat:.4f}, p-valor = {levene_p:.4f}")
if levene_p > 0.05:
    print("p > 0.05 -> Se cumple el supuesto de homogeneidad de varianzas. ¡Bien!\n")
else:
    print("p <= 0.05 -> No se cumple el supuesto de homogeneidad de varianzas.\n")

# ... (El resto del script para ANOVA y Tukey HSD es el mismo) ...

# --- PASO 5: Realizar el ANOVA de un Factor ---
f_stat, p_value = stats.f_oneway(icmp_lat, owamp_lat, int_lat)

print(f"--- Resultados del ANOVA de un Factor ---")
print(f"Estadístico F = {f_stat:.4f}")
print(f"p-valor = {p_value:.4f}")

if p_value < 0.05:
    print("\n>> Conclusión: Existen diferencias estadísticamente significativas en la latencia entre las técnicas.\n")
else:
    print("\n>> Conclusión: No se encontraron diferencias estadísticamente significativas.\n")


# --- PASO 6: Prueba Post-Hoc HSD de Tukey (si el ANOVA fue significativo) ---
if p_value < 0.05:
    print("--- Prueba Post-Hoc HSD de Tukey ---")
    tukey_results = pairwise_tukeyhsd(endog=df_clean['latencia_ms'], groups=df_clean['tecnica'], alpha=0.05)
    print(tukey_results)
    tukey_results.plot_simultaneous()
    plt.title('Comparaciones por Pares de Tukey HSD', fontsize=16)
    plt.show()