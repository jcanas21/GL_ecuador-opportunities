from pathlib import Path

import pandas as pd
import streamlit as st

from branding import render_dashboard_header


def render_guide_and_glossary() -> None:
    render_dashboard_header(
        "Tablero de Oportunidades de Exportación del Ecuador",
        "Guía y glosario de las páginas del tablero V1 (HS92 a 4 dígitos).",
    )

    st.markdown(
        """
### Qué hace este tablero

Este tablero ayuda a **priorizar oportunidades de diversificación exportadora para el Ecuador** a nivel **HS92 de 4 dígitos**, combinando dos preguntas complementarias:

- **¿Qué productos son atractivos?**  
  Porque tienen mercados grandes o crecientes, o porque aportan sofisticación productiva.
- **¿Qué productos son factibles?**  
  Porque están más cerca de las capacidades actuales del país o porque la red comercial del Ecuador ya está relativamente bien alineada con la demanda global de ese producto.

La lógica del tablero no busca identificar “el producto más complejo” en abstracto, sino **productos que puedan convertirse en oportunidades plausibles y accionables** para la agenda exportadora del país.
"""
    )

    st.markdown(
        """
### Cuatro páginas

- **Guía y glosario** (acá): contexto metodológico, definiciones y fórmulas clave.
- **Análisis de Oportunidades**: tablero principal para visualizar el análisis de complejidad económica tradicional y priorizar productos del **margen intensivo**.
- **Análisis de Proximidad Anclada**: identifica oportunidades del **margen extensivo** a partir de productos ancla del Ecuador y sus proximidades más altas.
- **Mercado Accesible por Producto**: descompone geográficamente el mercado accesible de los productos priorizados y muestra los principales competidores por destino.
"""
    )

    st.markdown(
        """
### Cómo leer el tablero

- **Página 2: Análisis de Oportunidades**  
  Esta página permite visualizar los resultados del **análisis de complejidad económica tradicional** aplicado al Ecuador. En este tablero, esa lógica se usa principalmente para identificar productos del **margen intensivo**, es decir, productos en los que el país **ya tiene presencia exportadora o capacidades productivas demostradas** y donde la pregunta es cómo profundizar, sofisticar o escalar esa base existente. Aquí el usuario puede cambiar filtros, pesos y presets para producir listas priorizadas dentro de ese universo.

- **Página 3: Análisis de Proximidad Anclada**  
  Esta página está diseñada para identificar oportunidades del **margen extensivo**, es decir, productos que **Ecuador no exporta hoy de forma significativa o en los que su presencia es todavía débil**, pero que podrían desarrollarse a partir de capacidades ya existentes. Para eso parte de productos **ancla** identificados en la canasta exportadora ecuatoriana y construye una lista de candidatos usando sus proximidades más altas en el espacio de productos.

- **Página 4: Mercado Accesible por Producto**  
  Baja un nivel más: muestra **dónde** está el mercado accesible de cada producto priorizado y **contra quién** compite Ecuador en esos destinos.
"""
    )

    st.markdown("### Cómo se construyen los puntajes")
    st.markdown(
        """
- Las variables componentes se normalizan (z-score) para construir los puntajes.
- El **Índice de Factibilidad** combina: RCA continuo, densidad, exportadores efectivos y percentil DAI.
- El **Índice de Atractivo** combina: PCI, COG, crecimiento del mercado accesible (5 años) y tamaño del mercado accesible.
- El **Puntaje Combinado de Oportunidad** rebalancea factibilidad y atractivo según el control estratégico y luego se reescala entre 0 y 1 para ordenar.
"""
    )

    st.markdown("### Glosario de variables del tablero")
    st.caption("Definiciones breves y guía de interpretación para las variables técnicas clave.")
    glossary = pd.DataFrame(
        [
            {"Variable": "RCA", "Definición breve": "Ventaja Comparativa Revelada: participación de Ecuador en las exportaciones de un producto dividida por la participación mundial de ese mismo producto.", "Cómo leerla": "Mayor que 1 = Ecuador está relativamente especializado; menor que 1 = especialización más débil.", "Unidad / escala": "Razón"},
            {"Variable": "RCA continuo", "Definición breve": "Señal continua derivada del RCA usada dentro del índice de factibilidad. En la rutina de complejidad, la entrada continua basada en RCA es una transformación del RCA bruto.", "Cómo leerla": "Un valor mayor indica una especialización revelada más fuerte sin reducir la señal a un umbral binario.", "Unidad / escala": "Continuo"},
            {"Variable": "Densidad (bruta)", "Definición breve": "Proximidad en el espacio de productos respecto de las capacidades actuales del Ecuador.", "Cómo leerla": "Un valor mayor significa que el producto está más cerca de lo que Ecuador ya sabe exportar.", "Unidad / escala": "Continuo"},
            {"Variable": "Percentil de densidad", "Definición breve": "Posición relativa de la densidad del Ecuador frente a otros países en el mismo producto (año 2024).", "Cómo leerla": "Cálculo por producto: percentil = (rank_density - 1) / (N - 1), donde el rango usa el promedio en caso de empates y N es el número de países en ese producto. Un valor de 0.80 significa que Ecuador está por encima de aproximadamente el 80% de los países en densidad para ese producto.", "Unidad / escala": "0-1"},
            {"Variable": "Distancia recorrida", "Definición breve": "Distancia bilateral promedio ponderada recorrida por producto, usando como ponderadores los valores exportados bilateralmente entre el origen x y el destino y.", "Cómo leerla": "Un valor mayor implica que las exportaciones de ese producto se concentran en mercados de destino más lejanos.", "Unidad / escala": "Unidades de distancia (del archivo de distancias bilaterales)"},
            {"Variable": "Exportadores efectivos", "Definición breve": "Número efectivo de exportadores competidores en ese producto (amplitud de competencia).", "Cómo leerla": "Un valor mayor suele implicar un campo competitivo más amplio.", "Unidad / escala": "Índice similar a un conteo"},
            {"Variable": "Percentil DAI", "Definición breve": "Percentil del Índice de Alineación de la Demanda para Ecuador frente a los principales exportadores en cada producto.", "Cómo leerla": "Un percentil más alto indica que las relaciones comerciales del Ecuador están mejor alineadas con donde se concentra la demanda mundial de ese producto.", "Unidad / escala": "0-100"},
            {"Variable": "Ventaja DAI", "Definición breve": "Percentil DAI del Ecuador menos el percentil mediano de los principales competidores.", "Cómo leerla": "Positivo = Ecuador supera a sus pares; negativo = Ecuador queda rezagado frente a ellos.", "Unidad / escala": "Puntos percentiles"},
            {"Variable": "PCI", "Definición breve": "Índice de Complejidad del Producto: nivel de sofisticación del producto basado en las estructuras exportadoras globales.", "Cómo leerla": "Un valor mayor suele señalar un potencial de escalamiento de largo plazo más fuerte.", "Unidad / escala": "Continuo"},
            {"Variable": "COG", "Definición breve": "Proxy de Ganancia de Perspectiva de Complejidad: potencial ganancia de capacidades al ingresar en el producto.", "Cómo leerla": "Un valor mayor sugiere mayor potencial estratégico de aprendizaje y escalamiento.", "Unidad / escala": "Continuo"},
            {"Variable": "Crecimiento del mercado global % (5 años)", "Definición breve": "Tasa compuesta anual de crecimiento a 5 años del comercio mundial del producto.", "Cómo leerla": "Valores positivos y más altos indican una demanda global en expansión más rápida.", "Unidad / escala": "Porcentaje por año"},
            {"Variable": "Crecimiento de las exportaciones del país % (5 años)", "Definición breve": "Tasa compuesta anual de crecimiento a 5 años de las exportaciones del Ecuador en el producto.", "Cómo leerla": "Un valor mayor indica que Ecuador está escalando más rápido en ese producto.", "Unidad / escala": "Porcentaje por año"},
            {"Variable": "Exportaciones actuales del país (M USD)", "Definición breve": "Valor exportado por Ecuador en 2024 para el producto.", "Cómo leerla": "Un valor mayor implica una base exportadora actual más grande.", "Unidad / escala": "Millones de USD"},
            {"Variable": "Ranking exportador del país (2024)", "Definición breve": "Posición global del Ecuador entre los exportadores de ese producto por valor.", "Cómo leerla": "Un número de ranking menor es mejor (por ejemplo, 3 es mejor que 20).", "Unidad / escala": "Ranking"},
            {"Variable": "Cambio absoluto en cuota de mercado (pp)", "Definición breve": "Cambio en la participación de mercado mundial del Ecuador entre 2020 y 2024.", "Cómo leerla": "Positivo = Ecuador ganó participación; negativo = perdió participación.", "Unidad / escala": "Puntos porcentuales"},
            {"Variable": "Cuota de mercado global", "Definición breve": "Participación del producto en el comercio mundial total (2024).", "Cómo leerla": "Un valor mayor significa que el producto es más importante en el comercio global.", "Unidad / escala": "Porcentaje"},
            {"Variable": "Comercio total (miles de millones USD)", "Definición breve": "Valor total del comercio mundial del producto en 2024.", "Cómo leerla": "Un valor mayor significa un mercado global más grande.", "Unidad / escala": "Miles de millones de USD"},
            {"Variable": "Tamaño del mercado accesible (miles de millones USD)", "Definición breve": "Proxy de demanda accesible basada en el alcance de mercado del Ecuador según su posicionamiento en red.", "Cómo leerla": "Un valor mayor sugiere que más demanda es alcanzable de manera realista.", "Unidad / escala": "Miles de millones de USD"},
            {"Variable": "Razón mercado accesible / mercado total", "Definición breve": "Tamaño del mercado accesible dividido por el tamaño total del mercado global.", "Cómo leerla": "Un valor mayor implica que una mayor fracción de la demanda mundial parece estructuralmente alcanzable.", "Unidad / escala": "Porcentaje"},
            {"Variable": "Índice de factibilidad", "Definición breve": "Puntaje compuesto de RCA continuo, densidad, exportadores efectivos y percentil DAI.", "Cómo leerla": "Un valor mayor implica una entrada más fácil o menos riesgosa dadas las capacidades actuales y la alineación de la red comercial.", "Unidad / escala": "0-1"},
            {"Variable": "Índice de atractivo", "Definición breve": "Puntaje compuesto de PCI, COG, crecimiento del mercado accesible y tamaño del mercado accesible.", "Cómo leerla": "Un valor mayor implica mayor potencial y valor estratégico.", "Unidad / escala": "0-1"},
            {"Variable": "Puntaje combinado de oportunidad", "Definición breve": "Puntaje final que combina factibilidad y atractivo usando el balance y los pesos definidos por el usuario.", "Cómo leerla": "Más alto = mejor oportunidad general bajo la configuración estratégica actual.", "Unidad / escala": "0-1"},
        ]
    )
    st.dataframe(glossary, use_container_width=True, hide_index=True)

    st.markdown("### Álgebra e interpretación")
    st.markdown("#### Percentil de Densidad")
    st.latex(r"\mathrm{DensityPercentile}_{z,i} = \frac{\mathrm{rank}_i(Density_{z,i})-1}{N_i-1}")
    st.markdown("- `z`: país (Ecuador en este tablero), `i`: producto.")
    st.markdown("- `rank_i(Density_{z,i})`: posición de la densidad del Ecuador dentro de la distribución entre países para el producto `i` (rango promedio en caso de empates).")
    st.markdown("- `N_i`: número de países disponibles para el producto `i`.")
    st.markdown("- Interpretación: 0.80 significa que la densidad del Ecuador está por encima de aproximadamente el 80% de los países para ese mismo producto.")

    st.markdown("#### Distancia Recorrida (por producto)")
    st.latex(r"\mathrm{DistanceTravelled}_i = \sum_y \left( Distance_{x,y} \times \frac{X_{x,y,i}}{\sum_y X_{x,y,i}} \right)")
    st.markdown("- `X_{x,y,i}`: exportaciones bilaterales del producto `i` desde el origen `x` hacia el destino `y`.")
    st.markdown("- Interpretación: distancia promedio ponderada recorrida por el producto, donde el valor exportado bilateral es el ponderador.")

    st.markdown("#### Tamaño del Mercado Accesible")
    st.latex(
        r"\mathrm{AccessibleMarket}_{z,i} = \sum_{y \in \mathcal{A}_{z,i}} M_{i,y}"
    )
    st.latex(
        r"\mathcal{A}_{z,i} = \left\{ y : Distance_{z,y} \le \mathrm{DistanceTravelled}_{z,i}\ \mathrm{or}\ X_{z,y,i} \ge 100{,}000{,}000 \right\}"
    )
    st.markdown("- `z`: exportador, `i`: producto, `y`: mercado de destino.")
    st.markdown("- Un mercado es accesible si está dentro del perfil observado de distancia del producto **o** si el exportador ya vende al menos USD 100 millones de ese producto a ese socio.")
    st.markdown("- Interpretación: demanda total en mercados que son geográficamente alcanzables o ya probados comercialmente a escala relevante.")

    st.markdown("#### DAI (Índice de Alineación de la Demanda)")
    st.latex(r"\mathrm{DAI}_{z,i} = \sum_y C_{z,y}\,\omega_{i,y}")
    st.latex(r"C_{z,y} = \frac{X_{z,y}/M_y}{X_z/WT}")
    st.latex(r"\omega_{i,y} = \frac{M_{i,y}}{\sum_{y'} M_{i,y'}}")
    st.markdown("- `z`: exportador (Ecuador en este tablero), `i`: producto, `y`: mercado socio.")
    st.markdown("- `C_{z,y}` mide afinidad comercial revelada: compara la participación de Ecuador en las importaciones totales del mercado `y` con la participación global de Ecuador en el comercio mundial.")
    st.markdown("- `\\omega_{i,y}` mide el peso de demanda específico del producto: la proporción de las importaciones mundiales del producto `i` que compra el mercado `y`.")
    st.markdown("- Interpretación: el DAI es un promedio ponderado por demanda de las afinidades comerciales del Ecuador. Valores mayores que 1 significan que la demanda del producto `i` se concentra en mercados donde Ecuador tiene una presencia importadora relativamente superior a su peso global; valores menores que 1 significan que la demanda se concentra donde Ecuador tiene una presencia relativamente débil.")


st.set_page_config(
    page_title="Oportunidades del Ecuador",
    page_icon=":bar_chart:",
    layout="wide",
)

pages = [
    st.Page(render_guide_and_glossary, title="Guía y glosario", icon=":material/menu_book:", default=True),
    st.Page(Path("pages/1_Opportunity_Analysis.py"), title="Análisis de Oportunidades", icon=":material/insights:"),
    st.Page(Path("pages/3_Anchored_Proximity_Analysis.py"), title="Análisis de Proximidad Anclada", icon=":material/account_tree:"),
    st.Page(Path("pages/5_Mercado_Accesible_por_Producto.py"), title="Mercado Accesible por Producto", icon=":material/grid_view:"),
]
pg = st.navigation(pages, position="sidebar", expanded=True)
pg.run()
