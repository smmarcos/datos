"""
Explorando el catálogo de Netflix
Dashboard interactivo para visualización de datos — Práctica universitaria
"""

import pandas as pd
import plotly.express as px
import streamlit as st

# ─────────────────────────────────────────────
# CONFIGURACIÓN DE PÁGINA
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Explorando el catálogo de Netflix",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Paleta de colores Netflix
COLOR_RED    = "#E50914"
COLOR_DARK   = "#141414"
COLOR_GRAY   = "#564d4d"
COLOR_WHITE  = "#FFFFFF"
PALETTE      = [COLOR_RED, "#B81D24", "#F5F5F1", "#831010", "#CC0000",
                "#FF6B6B", "#C62828", "#E53935", "#EF5350", "#FFCDD2"]

# CSS personalizado
st.markdown("""
<style>
    /* Fondo general */
    .stApp { background-color: #0f0f0f; color: #f5f5f1; }

    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #1a1a1a; }
    [data-testid="stSidebar"] * { color: #f5f5f1 !important; }
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stSlider label { color: #f5f5f1 !important; }
    [data-testid="stSidebar"] .stSlider [data-testid="stTickBarMin"],
    [data-testid="stSidebar"] .stSlider [data-testid="stTickBarMax"] { color: #aaa !important; }

    /* Inputs / selects en sidebar — fondo oscuro, texto blanco */
    [data-testid="stSidebar"] .stSelectbox > div > div,
    [data-testid="stSidebar"] .stSelectbox > div > div > div {
        background-color: #2c2c2c !important;
        color: #f5f5f1 !important;
        border-color: #444 !important;
    }
    /* Texto seleccionado dentro del select */
    [data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] span,
    [data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] div {
        color: #f5f5f1 !important;
        background-color: #2c2c2c !important;
    }
    /* Icono chevron */
    [data-testid="stSidebar"] .stSelectbox svg { fill: #f5f5f1 !important; }

    /* Títulos de sección */
    .section-title {
        font-size: 1.6rem;
        font-weight: 700;
        color: #E50914;
        border-left: 4px solid #E50914;
        padding-left: 12px;
        margin-top: 2rem;
        margin-bottom: 0.5rem;
    }
    /* Subtítulos */
    .section-sub {
        font-size: 1rem;
        color: #aaa;
        margin-bottom: 1.2rem;
        margin-left: 16px;
    }
    /* Tarjeta de métrica */
    [data-testid="stMetric"] {
        background: #1e1e1e;
        border-radius: 12px;
        padding: 16px;
        border: 1px solid #2c2c2c;
    }
    [data-testid="stMetricLabel"]  { color: #aaa !important; }
    [data-testid="stMetricValue"]  { color: #E50914 !important; font-size: 2rem !important; }
    [data-testid="stMetricDelta"]  { color: #4caf50 !important; }

    /* Cuadros de insight */
    .insight-box {
        background: #1e1e1e;
        border-left: 3px solid #E50914;
        border-radius: 8px;
        padding: 14px 18px;
        margin-top: 10px;
        color: #ccc;
        font-size: 0.9rem;
        line-height: 1.6;
    }
    /* Caja de conclusiones */
    .conclusion-box {
        background: linear-gradient(135deg, #1a0000 0%, #1e1e1e 100%);
        border: 1px solid #E50914;
        border-radius: 12px;
        padding: 24px;
        margin-top: 10px;
        color: #eee;
        font-size: 0.95rem;
        line-height: 1.8;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# CARGA Y PREPARACIÓN DE DATOS
# ─────────────────────────────────────────────
@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    """Carga y prepara el dataset de Netflix."""
    df = pd.read_csv(path)

    # Convertir date_added a datetime si existe
    if "date_added" in df.columns:
        df["date_added"] = pd.to_datetime(df["date_added"], errors="coerce")

    # Año de incorporación al catálogo (mejor para analizar crecimiento de Netflix)
    if "year_added" in df.columns:
        df["catalog_year"] = pd.to_numeric(df["year_added"], errors="coerce")
    else:
        df["catalog_year"] = pd.NA
    if "date_added" in df.columns:
        df["catalog_year"] = df["catalog_year"].fillna(df["date_added"].dt.year)

    # Limpiar ratings que contienen duraciones incorrectas
    valid_ratings = [
        "G", "PG", "PG-13", "R", "NC-17", "NR", "UR",
        "TV-Y", "TV-Y7", "TV-Y7-FV", "TV-G", "TV-PG", "TV-14", "TV-MA",
    ]
    df["rating"] = df["rating"].where(df["rating"].isin(valid_ratings), other="Unknown")

    # Normalizar país: tomar solo el primero cuando hay varios
    df["country_primary"] = (
        df["country"]
        .str.split(",")
        .str[0]
        .str.strip()
    )

    return df


@st.cache_data
def get_all_genres(df: pd.DataFrame) -> list[str]:
    """Extrae todos los géneros únicos del campo listed_in."""
    genres = (
        df["listed_in"]
        .dropna()
        .str.split(",")
        .explode()
        .str.strip()
        .unique()
        .tolist()
    )
    return sorted(genres)


@st.cache_data
def get_all_countries(df: pd.DataFrame) -> list[str]:
    """Extrae todos los países únicos (excluyendo Unknown)."""
    countries = (
        df["country_primary"]
        .dropna()
        .unique()
        .tolist()
    )
    return sorted([c for c in countries if c != "Unknown"])


# ─────────────────────────────────────────────
# FUNCIONES DE GRÁFICOS
# ─────────────────────────────────────────────
def plot_line_evolution(df: pd.DataFrame) -> px.line:
    """Gráfico de líneas: títulos por año de incorporación al catálogo."""
    plot_df = df.dropna(subset=["catalog_year"]).copy()
    plot_df["catalog_year"] = plot_df["catalog_year"].astype(int)
    yearly = plot_df.groupby("catalog_year").size().reset_index(name="titles")
    fig = px.line(
        yearly,
        x="catalog_year",
        y="titles",
        markers=True,
        template="plotly_dark",
        color_discrete_sequence=[COLOR_RED],
        labels={"catalog_year": "Año de incorporación al catálogo", "titles": "Número de títulos"},
    )
    fig.update_traces(line_width=2.5, marker_size=5)
    fig.update_layout(
        paper_bgcolor="#0f0f0f",
        plot_bgcolor="#141414",
        font_color="#f5f5f1",
        hovermode="x unified",
        margin=dict(t=20, b=20),
    )
    return fig


def plot_type_distribution(df: pd.DataFrame) -> px.bar:
    """Gráfico de barras: distribución de Movies vs TV Shows."""
    counts = df["type"].value_counts().reset_index()
    counts.columns = ["type", "count"]
    counts["pct"] = (counts["count"] / counts["count"].sum() * 100).round(1)
    counts["label"] = counts.apply(lambda r: f"{r['count']:,} ({r['pct']}%)", axis=1)

    fig = px.bar(
        counts,
        x="type",
        y="count",
        text="label",
        template="plotly_dark",
        color="type",
        color_discrete_sequence=[COLOR_RED, COLOR_GRAY],
        labels={"type": "Tipo de contenido", "count": "Número de títulos"},
    )
    fig.update_traces(textposition="outside", marker_line_width=0)
    fig.update_layout(
        paper_bgcolor="#0f0f0f",
        plot_bgcolor="#141414",
        font_color="#f5f5f1",
        showlegend=False,
        margin=dict(t=20, b=20),
    )
    return fig


def plot_top_countries(df: pd.DataFrame, n: int = 10) -> px.bar:
    """Gráfico horizontal: Top N países por número de títulos."""
    top = (
        df[df["country_primary"] != "Unknown"]["country_primary"]
        .value_counts()
        .head(n)
        .reset_index()
    )
    top.columns = ["country", "count"]
    top = top.sort_values("count")  # orden ascendente para que el mayor quede arriba

    fig = px.bar(
        top,
        x="count",
        y="country",
        orientation="h",
        template="plotly_dark",
        color="count",
        color_continuous_scale=["#3a0000", COLOR_RED],
        labels={"count": "Número de títulos", "country": "País"},
        text="count",
    )
    fig.update_traces(textposition="outside", marker_line_width=0)
    fig.update_layout(
        paper_bgcolor="#0f0f0f",
        plot_bgcolor="#141414",
        font_color="#f5f5f1",
        coloraxis_showscale=False,
        margin=dict(t=20, b=20),
    )
    return fig


def plot_ratings(df: pd.DataFrame) -> px.bar:
    """Gráfico de barras: distribución por clasificación por edades."""
    counts = (
        df["rating"]
        .value_counts()
        .reset_index()
    )
    counts.columns = ["rating", "count"]

    fig = px.bar(
        counts,
        x="rating",
        y="count",
        text="count",
        template="plotly_dark",
        color="count",
        color_continuous_scale=["#3a0000", COLOR_RED],
        labels={"rating": "Clasificación", "count": "Número de títulos"},
    )
    fig.update_traces(textposition="outside", marker_line_width=0)
    fig.update_layout(
        paper_bgcolor="#0f0f0f",
        plot_bgcolor="#141414",
        font_color="#f5f5f1",
        coloraxis_showscale=False,
        xaxis={"categoryorder": "total descending"},
        margin=dict(t=20, b=20),
    )
    return fig


def plot_top_genres(df: pd.DataFrame, n: int = 15) -> px.bar:
    """Gráfico horizontal: Top N géneros más frecuentes."""
    genre_series = (
        df["listed_in"]
        .dropna()
        .str.split(",")
        .explode()
        .str.strip()
    )
    top = genre_series.value_counts().head(n).reset_index()
    top.columns = ["genre", "count"]
    top = top.sort_values("count")  # orden ascendente

    fig = px.bar(
        top,
        x="count",
        y="genre",
        orientation="h",
        template="plotly_dark",
        color="count",
        color_continuous_scale=["#3a0000", COLOR_RED],
        labels={"count": "Número de títulos", "genre": "Género"},
        text="count",
    )
    fig.update_traces(textposition="outside", marker_line_width=0)
    fig.update_layout(
        paper_bgcolor="#0f0f0f",
        plot_bgcolor="#141414",
        font_color="#f5f5f1",
        coloraxis_showscale=False,
        margin=dict(t=20, b=20, l=10),
        height=520,
    )
    return fig


# ─────────────────────────────────────────────
# SIDEBAR — FILTROS INTERACTIVOS
# ─────────────────────────────────────────────
def build_sidebar(df: pd.DataFrame) -> pd.DataFrame:
    """Construye la barra lateral con filtros y devuelve el dataframe filtrado."""
    st.sidebar.image(
        "https://upload.wikimedia.org/wikipedia/commons/0/08/Netflix_2015_logo.svg",
        width=140,
    )
    st.sidebar.markdown("## 🎛️ Filtros")
    st.sidebar.markdown("---")

    # Tipo de contenido
    tipos_disponibles = ["Todos"] + sorted(df["type"].unique().tolist())
    tipo_sel = st.sidebar.selectbox("📺 Tipo de contenido", tipos_disponibles)

    # País (primario)
    paises = ["Todos"] + get_all_countries(df)
    pais_sel = st.sidebar.selectbox("🌍 País", paises)

    # Rating
    ratings_disponibles = ["Todos"] + sorted(df["rating"].unique().tolist())
    rating_sel = st.sidebar.selectbox("🔞 Clasificación por edades", ratings_disponibles)

    # Rango de años (incorporación al catálogo)
    years_available = df["catalog_year"].dropna().astype(int)
    yr_min = int(years_available.min())
    yr_max = int(years_available.max())
    yr_range = st.sidebar.slider(
        "📅 Rango de años de incorporación",
        min_value=yr_min,
        max_value=yr_max,
        value=(max(yr_min, 2015), yr_max),
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        "<small style='color:#666'>Los filtros afectan a todos los gráficos.</small>",
        unsafe_allow_html=True,
    )

    # Aplicar filtros
    filtered = df.copy()
    if tipo_sel != "Todos":
        filtered = filtered[filtered["type"] == tipo_sel]
    if pais_sel != "Todos":
        filtered = filtered[filtered["country_primary"] == pais_sel]
    if rating_sel != "Todos":
        filtered = filtered[filtered["rating"] == rating_sel]
    filtered = filtered[
        filtered["catalog_year"].notna() &
        (filtered["catalog_year"].astype(int) >= yr_range[0]) &
        (filtered["catalog_year"].astype(int) <= yr_range[1])
    ]

    return filtered


# ─────────────────────────────────────────────
# MAIN — APLICACIÓN
# ─────────────────────────────────────────────
def main() -> None:
    # --- Carga de datos ---
    df_raw = load_data("netflix_clean.csv")

    # --- Sidebar y filtrado ---
    df = build_sidebar(df_raw)

    # ── SECCIÓN 1: INTRODUCCIÓN ──────────────────
    st.markdown(
        "<h1 style='text-align:center; color:#E50914; font-size:2.8rem;'>"
        "🎬 Explorando el catálogo de Netflix</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align:center; color:#aaa; font-size:1.1rem;'>"
        "Análisis visual de la evolución y distribución del contenido disponible en Netflix"
        "</p>",
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    with st.container():
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("""
<div class="insight-box">
<strong style="color:#E50914;">¿Por qué Netflix?</strong><br><br>
Netflix es la plataforma de streaming más grande del mundo, con más de <strong>260 millones de suscriptores</strong>
en más de 190 países. Desde su transición al streaming en 2007, el catálogo ha crecido exponencialmente,
incorporando contenido propio (Originals) y licencias de terceros de todo el mundo.<br><br>
Este análisis explora <strong>8.807 títulos</strong> del catálogo, respondiendo preguntas clave:
¿Cómo ha evolucionado el contenido a lo largo del tiempo? ¿Qué países y géneros dominan?
¿A qué audiencias se dirige Netflix? Las respuestas revelan la estrategia de contenido de la plataforma.
</div>
""", unsafe_allow_html=True)
        with col2:
            st.markdown("""
<div class="insight-box" style="height:100%;">
<strong style="color:#E50914;">Objetivos del análisis</strong><br><br>
📈 Analizar la <strong>evolución temporal</strong> del catálogo<br><br>
🌍 Identificar los <strong>países</strong> con más contenido<br><br>
🎭 Descubrir los <strong>géneros</strong> más populares<br><br>
👨‍👩‍👧 Entender la <strong>segmentación</strong> por audiencias<br><br>
🎬 Comparar <strong>películas vs. series</strong>
</div>
""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── SECCIÓN 4: KPIs ─────────────────────────
    st.markdown('<div class="section-title">📊 Resumen del catálogo filtrado</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Métricas clave según los filtros seleccionados</div>', unsafe_allow_html=True)

    total   = len(df)
    movies  = len(df[df["type"] == "Movie"])
    shows   = len(df[df["type"] == "TV Show"])
    countries_n = df[df["country_primary"] != "Unknown"]["country_primary"].nunique()

    total_raw   = len(df_raw)
    movies_raw  = len(df_raw[df_raw["type"] == "Movie"])
    shows_raw   = len(df_raw[df_raw["type"] == "TV Show"])
    countries_raw = df_raw[df_raw["country_primary"] != "Unknown"]["country_primary"].nunique()

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("🎬 Total títulos",  f"{total:,}",    delta=f"{total - total_raw:+,} vs total")
    k2.metric("🎥 Películas",      f"{movies:,}",   delta=f"{movies - movies_raw:+,} vs total")
    k3.metric("📺 Series",         f"{shows:,}",    delta=f"{shows - shows_raw:+,} vs total")
    k4.metric("🌍 Países",         f"{countries_n}", delta=f"{countries_n - countries_raw:+} vs total")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── SECCIÓN 5: EVOLUCIÓN TEMPORAL ───────────
    st.markdown('<div class="section-title">📈 ¿Cómo ha evolucionado el catálogo de Netflix?</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Número de títulos añadidos por año al catálogo de Netflix</div>', unsafe_allow_html=True)

    if not df.empty:
        st.plotly_chart(plot_line_evolution(df), use_container_width=True)
        peak_year = int(df.groupby(df["catalog_year"].astype(int)).size().idxmax())
        peak_count = int(df.groupby(df["catalog_year"].astype(int)).size().max())
        st.markdown(f"""
<div class="insight-box">
💡 <strong>Lectura del gráfico:</strong> El catálogo de Netflix experimentó un crecimiento explosivo a partir de 2015,
coincidiendo con la expansión global de la plataforma. El año con más títulos lanzados en la selección actual es
<strong>{peak_year}</strong> con <strong>{peak_count:,} títulos</strong>.
El descenso en los últimos años puede deberse a que el dataset no recoge los lanzamientos más recientes de forma completa.
</div>
""", unsafe_allow_html=True)
    else:
        st.info("No hay datos para mostrar con los filtros actuales.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── SECCIÓN 6: MOVIES VS TV SHOWS ───────────
    st.markdown('<div class="section-title">🎬 ¿Predominan las películas o las series?</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Distribución por tipo de contenido</div>', unsafe_allow_html=True)

    if not df.empty:
        col_chart, col_text = st.columns([3, 2])
        with col_chart:
            st.plotly_chart(plot_type_distribution(df), use_container_width=True)
        with col_text:
            dominant = df["type"].value_counts().idxmax()
            pct_movies = round(movies / total * 100, 1) if total > 0 else 0
            pct_shows  = round(shows  / total * 100, 1) if total > 0 else 0
            st.markdown(f"""
<div class="insight-box">
🎯 <strong>Interpretación:</strong><br><br>
En la selección actual, <strong>{dominant}s</strong> constituyen el tipo de contenido dominante.<br><br>
• 🎥 <strong>Películas:</strong> {movies:,} títulos ({pct_movies}%)<br>
• 📺 <strong>Series:</strong> {shows:,} títulos ({pct_shows}%)<br><br>
Netflix históricamente ha apostado más por las películas en términos de volumen,
aunque las series generan mayor fidelización y tiempo de visualización por usuario.
La estrategia de contenido propio (Originals) ha equilibrado progresivamente esta relación.
</div>
""", unsafe_allow_html=True)
    else:
        st.info("No hay datos para mostrar con los filtros actuales.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── SECCIÓN 7: TOP 10 PAÍSES ─────────────────
    st.markdown('<div class="section-title">🌍 ¿Qué países aportan más contenido?</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Top 10 países productores de contenido</div>', unsafe_allow_html=True)

    if not df.empty:
        st.plotly_chart(plot_top_countries(df, n=10), use_container_width=True)
        top_country = (
            df[df["country_primary"] != "Unknown"]["country_primary"]
            .value_counts().idxmax()
        )
        top_country_n = (
            df[df["country_primary"] != "Unknown"]["country_primary"]
            .value_counts().max()
        )
        st.markdown(f"""
<div class="insight-box">
💡 <strong>Lectura del gráfico:</strong> <strong>{top_country}</strong> encabeza la producción con
<strong>{top_country_n:,} títulos</strong> en la selección actual. La hegemonía estadounidense
refleja la concentración de la industria del entretenimiento, aunque Netflix ha diversificado
significativamente su catálogo internacional, con India, Reino Unido y Japón como productores destacados.
</div>
""", unsafe_allow_html=True)
    else:
        st.info("No hay datos para mostrar con los filtros actuales.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── SECCIÓN 8: CLASIFICACIÓN POR EDADES ──────
    st.markdown('<div class="section-title">🔞 ¿A qué público está dirigido el contenido?</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Distribución por clasificación por edades (rating)</div>', unsafe_allow_html=True)

    if not df.empty:
        st.plotly_chart(plot_ratings(df), use_container_width=True)
        top_rating = df["rating"].value_counts().idxmax()
        st.markdown(f"""
<div class="insight-box">
💡 <strong>Lectura del gráfico:</strong> La clasificación más común en la selección actual es
<strong>{top_rating}</strong>. Netflix orienta la mayor parte de su catálogo a audiencias adultas (TV-MA, R),
lo que refleja su posicionamiento como plataforma premium para adultos. Sin embargo,
dispone de una sección familiar robusta (TV-Y, TV-Y7, TV-G, TV-PG) para captar suscriptores familiares.
</div>
""", unsafe_allow_html=True)
    else:
        st.info("No hay datos para mostrar con los filtros actuales.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── SECCIÓN 9: GÉNEROS MÁS FRECUENTES ────────
    st.markdown('<div class="section-title">🎭 ¿Cuáles son los géneros más frecuentes?</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Top 15 géneros del catálogo (un título puede tener varios géneros)</div>', unsafe_allow_html=True)

    if not df.empty:
        st.plotly_chart(plot_top_genres(df, n=15), use_container_width=True)
        top_genre = (
            df["listed_in"].dropna()
            .str.split(",").explode().str.strip()
            .value_counts().idxmax()
        )
        st.markdown(f"""
<div class="insight-box">
💡 <strong>Lectura del gráfico:</strong> <strong>{top_genre}</strong> es el género más representado
en la selección actual. Netflix ha construido una oferta muy amplia de drama internacional,
documentales y comedias, géneros que atraen audiencias globales diversas y con distintos perfiles culturales.
</div>
""", unsafe_allow_html=True)
    else:
        st.info("No hay datos para mostrar con los filtros actuales.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── SECCIÓN 10: TABLA EXPLORATORIA ───────────
    st.markdown('<div class="section-title">🔍 Explorador de títulos</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Navega por el catálogo filtrado. Puedes ordenar haciendo clic en las columnas.</div>', unsafe_allow_html=True)

    display_cols = ["title", "type", "country_primary", "catalog_year", "release_year",
                    "rating", "duration", "listed_in", "description"]
    cols_present = [c for c in display_cols if c in df.columns]

    search_term = st.text_input("🔎 Buscar por título o descripción", placeholder="Escribe algo...")
    df_display = df[cols_present].copy()
    df_display.columns = [
        c.replace("country_primary", "country") for c in cols_present
    ]
    if "catalog_year" in df_display.columns:
        df_display = df_display.rename(columns={"catalog_year": "year_added_to_netflix"})

    if search_term:
        mask = (
            df_display["title"].str.contains(search_term, case=False, na=False) |
            df_display["description"].str.contains(search_term, case=False, na=False)
        )
        df_display = df_display[mask]

    st.markdown(f"<small style='color:#888'>Mostrando {len(df_display):,} títulos</small>", unsafe_allow_html=True)
    st.dataframe(
        df_display.reset_index(drop=True),
        use_container_width=True,
        height=380,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── SECCIÓN 11: CONCLUSIONES ──────────────────
    st.markdown('<div class="section-title">✅ Conclusiones</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Comparativa entre la selección filtrada y el catálogo completo</div>', unsafe_allow_html=True)

    if not df.empty:
        # ── Cálculos comparativos filtrado vs total ──
        pct_of_total   = round(total / total_raw * 100, 1)
        avg_year_sel   = round(df["catalog_year"].mean(), 1)
        avg_year_raw   = round(df_raw["catalog_year"].mean(), 1)
        diff_avg_year  = round(avg_year_sel - avg_year_raw, 1)

        intl_sel = df[df["country_primary"].notna() & (df["country_primary"] != "Unknown") & (df["country_primary"] != "United States")]
        intl_raw = df_raw[df_raw["country_primary"].notna() & (df_raw["country_primary"] != "Unknown") & (df_raw["country_primary"] != "United States")]
        pct_intl_sel = round(len(intl_sel) / total * 100, 1) if total > 0 else 0
        pct_intl_raw = round(len(intl_raw) / total_raw * 100, 1) if total_raw > 0 else 0
        diff_intl    = round(pct_intl_sel - pct_intl_raw, 1)

        pct_movies_sel = round(movies / total * 100, 1) if total > 0 else 0
        pct_movies_raw = round(movies_raw / total_raw * 100, 1) if total_raw > 0 else 0
        diff_movies    = round(pct_movies_sel - pct_movies_raw, 1)

        year_span = int(df["catalog_year"].max()) - int(df["catalog_year"].min())

        top_genre_sel = (
            df["listed_in"].dropna()
            .str.split(",").explode().str.strip()
            .value_counts().idxmax()
        )
        top_genre_raw = (
            df_raw["listed_in"].dropna()
            .str.split(",").explode().str.strip()
            .value_counts().idxmax()
        )
        genre_changed = top_genre_sel != top_genre_raw

        arrow = lambda d: ("▲" if d > 0 else "▼" if d < 0 else "=")
        color = lambda d: ("#4caf50" if d > 0 else "#e57373" if d < 0 else "#aaa")

        st.markdown(f"""
<div class="conclusion-box">
<h4 style="color:#E50914; margin-top:0;">📋 Tu selección vs el catálogo completo</h4>

<table style="width:100%; border-collapse:collapse; font-size:0.9rem;">
  <thead>
    <tr style="color:#888; border-bottom:1px solid #333;">
      <th style="text-align:left; padding:8px 6px;">Indicador</th>
      <th style="text-align:right; padding:8px 6px;">Selección</th>
      <th style="text-align:right; padding:8px 6px;">Catálogo completo</th>
      <th style="text-align:right; padding:8px 6px;">Diferencia</th>
    </tr>
  </thead>
  <tbody>
    <tr style="border-bottom:1px solid #222;">
      <td style="padding:8px 6px;">📦 Títulos representados</td>
      <td style="text-align:right; padding:8px 6px;"><strong>{total:,}</strong></td>
      <td style="text-align:right; padding:8px 6px;">{total_raw:,}</td>
      <td style="text-align:right; padding:8px 6px; color:#aaa;">{pct_of_total}% del total</td>
    </tr>
    <tr style="border-bottom:1px solid #222;">
    <td style="padding:8px 6px;">📅 Año medio de incorporación</td>
      <td style="text-align:right; padding:8px 6px;"><strong>{avg_year_sel}</strong></td>
      <td style="text-align:right; padding:8px 6px;">{avg_year_raw}</td>
      <td style="text-align:right; padding:8px 6px; color:{color(diff_avg_year)};">{arrow(diff_avg_year)} {abs(diff_avg_year)} años</td>
    </tr>
    <tr style="border-bottom:1px solid #222;">
      <td style="padding:8px 6px;">🎥 % Películas</td>
      <td style="text-align:right; padding:8px 6px;"><strong>{pct_movies_sel}%</strong></td>
      <td style="text-align:right; padding:8px 6px;">{pct_movies_raw}%</td>
      <td style="text-align:right; padding:8px 6px; color:{color(diff_movies)};">{arrow(diff_movies)} {abs(diff_movies)} pp</td>
    </tr>
    <tr style="border-bottom:1px solid #222;">
      <td style="padding:8px 6px;">🌍 % Contenido internacional (no EE.UU.)</td>
      <td style="text-align:right; padding:8px 6px;"><strong>{pct_intl_sel}%</strong></td>
      <td style="text-align:right; padding:8px 6px;">{pct_intl_raw}%</td>
      <td style="text-align:right; padding:8px 6px; color:{color(diff_intl)};">{arrow(diff_intl)} {abs(diff_intl)} pp</td>
    </tr>
    <tr style="border-bottom:1px solid #222;">
      <td style="padding:8px 6px;">📆 Rango de años cubiertos</td>
      <td style="text-align:right; padding:8px 6px;"><strong>{year_span} años</strong></td>
    <td style="text-align:right; padding:8px 6px;">{int(df_raw['catalog_year'].max()) - int(df_raw['catalog_year'].min())} años</td>
      <td style="text-align:right; padding:8px 6px; color:#aaa;">—</td>
    </tr>
    <tr>
      <td style="padding:8px 6px;">🎭 Género líder</td>
      <td style="text-align:right; padding:8px 6px;"><strong>{top_genre_sel}</strong></td>
      <td style="text-align:right; padding:8px 6px;">{top_genre_raw}</td>
      <td style="text-align:right; padding:8px 6px; color:{'#E50914' if genre_changed else '#4caf50'};">{'¡Cambia!' if genre_changed else 'Igual'}</td>
    </tr>
  </tbody>
</table>
</div>
""", unsafe_allow_html=True)
    else:
        st.warning("⚠️ No hay datos suficientes con los filtros actuales para generar conclusiones.")

    st.markdown("<br><br>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
