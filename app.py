import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="COPAG | Analyse Logistique", page_icon="🚚", layout="wide", initial_sidebar_state="expanded")

# ---------- STYLE ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: #f5f7fb; }
.block-container { padding-top: 1.4rem; padding-bottom: 2rem; max-width: 1450px; }
[data-testid="stSidebar"] { background: linear-gradient(180deg,#102a43 0%,#173f5f 100%); }
[data-testid="stSidebar"] * { color: white !important; }
.hero { background: linear-gradient(135deg,#0f766e,#16a085); padding: 28px 32px; border-radius: 18px; color:white; margin-bottom:22px; box-shadow:0 10px 30px rgba(15,118,110,.18); }
.hero h1 { margin:0; font-size:2.1rem; font-weight:800; }
.hero p { margin:.4rem 0 0; opacity:.9; }
.kpi { background:white; border-radius:16px; padding:18px 20px; border:1px solid #e8edf3; box-shadow:0 4px 18px rgba(16,42,67,.05); min-height:112px; }
.kpi-label { color:#6b7280; font-size:.83rem; font-weight:600; }
.kpi-value { color:#102a43; font-size:1.65rem; font-weight:800; margin-top:7px; }
.section { color:#102a43; font-size:1.25rem; font-weight:800; margin:25px 0 10px; }
.login-card { background:white; padding:35px; border-radius:20px; max-width:460px; margin:7vh auto; border:1px solid #e5e7eb; box-shadow:0 15px 45px rgba(16,42,67,.10); }
.small-muted { color:#6b7280; font-size:.85rem; }
</style>
""", unsafe_allow_html=True)

# ---------- AUTHENTIFICATION ----------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def login():
    st.markdown("""
    <div class="login-card">
        <div style="font-size:42px">🚚</div>
        <h1 style="color:#102a43;margin-bottom:4px">COPAG</h1>
        <p style="color:#6b7280">Plateforme d'analyse logistique</p>
    </div>
    """, unsafe_allow_html=True)
    with st.form("login_form"):
        username = st.text_input("Nom d'utilisateur")
        password = st.text_input("Mot de passe", type="password")
        submitted = st.form_submit_button("Se connecter", use_container_width=True, type="primary")
        if submitted:
            if username == "COPAGE" and password == "123456789":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Nom d'utilisateur ou mot de passe incorrect.")

if not st.session_state.authenticated:
    login()
    st.stop()

# ---------- DATA ----------
@st.cache_data
def load_data():
    data = pd.read_csv("dataset.csv")
    data["date"] = pd.to_datetime(data["date"], errors="coerce")
    data["lane"] = data["origin_hub"] + " → " + data["destination_city"]
    data["cost_per_km"] = data["cost_mad"] / data["distance_km"].replace(0, np.nan)
    return data

df = load_data()

# ---------- SIDEBAR ----------
with st.sidebar:
    st.markdown("## 🚚 COPAG")
    st.caption("Pilotage logistique national")
    st.markdown("---")
    page = st.radio("Navigation", ["📊 Tableau de bord", "🚚 Expéditions", "📍 Géographie", "📈 Analyses avancées", "🗃️ Données"])
    st.markdown("---")
    st.markdown("### Filtres")
    min_date, max_date = df["date"].min().date(), df["date"].max().date()
    dates = st.date_input("Période", (min_date, max_date), min_value=min_date, max_value=max_date)
    hubs = st.multiselect("Hub d'origine", sorted(df["origin_hub"].dropna().unique()))
    regions = st.multiselect("Région destination", sorted(df["destination_region"].dropna().unique()))
    modes = st.multiselect("Mode de transport", sorted(df["mode"].dropna().unique()))
    products = st.multiselect("Catégorie produit", sorted(df["product_category"].dropna().unique()))
    if st.button("🚪 Déconnexion", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

# apply filters
filtered = df.copy()
if isinstance(dates, tuple) and len(dates) == 2:
    filtered = filtered[(filtered.date.dt.date >= dates[0]) & (filtered.date.dt.date <= dates[1])]
elif dates:
    filtered = filtered[filtered.date.dt.date == dates]
if hubs: filtered = filtered[filtered.origin_hub.isin(hubs)]
if regions: filtered = filtered[filtered.destination_region.isin(regions)]
if modes: filtered = filtered[filtered.mode.isin(modes)]
if products: filtered = filtered[filtered.product_category.isin(products)]

# ---------- HELPERS ----------
def kpi(label, value):
    st.markdown(f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div></div>', unsafe_allow_html=True)

def fig_config():
    plt.tight_layout()
    st.pyplot(plt.gcf(), use_container_width=True)
    plt.close()

st.markdown(f"""
<div class="hero">
<h1>🚚 COPAG — Analyse Logistique</h1>
<p>Suivi des performances de livraison, des coûts, du carburant, du CO₂ et des flux à travers le Maroc.</p>
</div>
""", unsafe_allow_html=True)

# ---------- DASHBOARD ----------
if page == "📊 Tableau de bord":
    st.markdown('<div class="section">Vue d’ensemble</div>', unsafe_allow_html=True)
    if filtered.empty:
        st.warning("Aucune expédition ne correspond aux filtres sélectionnés.")
        st.stop()

    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: kpi("Expéditions", f"{len(filtered):,}")
    with c2: kpi("Taux à l'heure", f"{filtered.on_time.mean()*100:.1f}%")
    with c3: kpi("Coût moyen", f"{filtered.cost_mad.mean():,.0f} MAD")
    with c4: kpi("Carburant / trajet", f"{filtered.fuel_liters.mean():.1f} L")
    with c5: kpi("CO₂ / trajet", f"{filtered.co2_kg.mean():.1f} kg")

    st.markdown('<div class="section">Performance des livraisons</div>', unsafe_allow_html=True)
    daily = filtered.groupby("date", as_index=False)["on_time"].mean()
    daily["Taux"] = daily["on_time"]*100
    fig, ax = plt.subplots(figsize=(12,4.5))
    ax.plot(daily.date, daily["Taux"], linewidth=2)
    ax.axhline(95, linestyle="--", linewidth=1)
    ax.set_ylabel("Taux à l'heure (%)"); ax.set_xlabel("Date"); ax.grid(alpha=.2)
    fig_config()

    c1,c2 = st.columns(2)
    with c1:
        st.markdown('<div class="section">Top 10 routes</div>', unsafe_allow_html=True)
        top = filtered.lane.value_counts().head(10).sort_values()
        fig, ax = plt.subplots(figsize=(8,5))
        sns.barplot(x=top.values, y=top.index, ax=ax)
        ax.set_xlabel("Nombre d'expéditions"); ax.set_ylabel("")
        fig_config()
    with c2:
        st.markdown('<div class="section">Expéditions par produit</div>', unsafe_allow_html=True)
        counts = filtered.product_category.value_counts()
        fig, ax = plt.subplots(figsize=(8,5))
        ax.pie(counts.values, labels=counts.index, autopct="%1.1f%%", startangle=90)
        ax.set_title("Répartition des produits")
        fig_config()

elif page == "🚚 Expéditions":
    st.markdown('<div class="section">Analyse des expéditions</div>', unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1:
        fig, ax = plt.subplots(figsize=(8,5))
        sns.boxplot(data=filtered, x="delay_min", y="product_category", ax=ax)
        ax.set_xlabel("Retard (minutes)"); ax.set_ylabel("Catégorie")
        ax.set_title("Distribution des retards par produit")
        fig_config()
    with c2:
        delay = filtered.groupby("destination_region", as_index=False)["delay_min"].mean().sort_values("delay_min", ascending=False).head(12)
        fig, ax = plt.subplots(figsize=(8,5))
        sns.barplot(data=delay, x="delay_min", y="destination_region", ax=ax)
        ax.set_xlabel("Retard moyen (min)"); ax.set_ylabel("")
        ax.set_title("Retard moyen par région")
        fig_config()

    c1,c2 = st.columns(2)
    with c1:
        fig, ax = plt.subplots(figsize=(8,5))
        sns.scatterplot(data=filtered, x="distance_km", y="cost_mad", alpha=.65, ax=ax)
        ax.set_xlabel("Distance (km)"); ax.set_ylabel("Coût (MAD)")
        ax.set_title("Distance vs coût")
        fig_config()
    with c2:
        fig, ax = plt.subplots(figsize=(8,5))
        sns.scatterplot(data=filtered, x="distance_km", y="fuel_liters", alpha=.65, ax=ax)
        ax.set_xlabel("Distance (km)"); ax.set_ylabel("Carburant (L)")
        ax.set_title("Distance vs consommation")
        fig_config()

elif page == "📍 Géographie":
    st.markdown('<div class="section">Positionnement et flux logistiques</div>', unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1:
        geo = filtered[["lat","lon"]].dropna()
        fig, ax = plt.subplots(figsize=(7,6))
        ax.scatter(geo.lon, geo.lat, alpha=.45, s=18)
        ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")
        ax.set_title("Positions des véhicules")
        ax.grid(alpha=.2)
        fig_config()
    with c2:
        fig, ax = plt.subplots(figsize=(7,6))
        for _, r in filtered.groupby(["origin_hub","destination_city","o_lat","o_lon","d_lat","d_lon"]).size().reset_index(name="count").iterrows():
            ax.plot([r.o_lon,r.d_lon],[r.o_lat,r.d_lat], alpha=.20, linewidth=max(.5,r["count"]/15))
        for hub,g in filtered.groupby("origin_hub"):
            ax.scatter(g.o_lon.iloc[0], g.o_lat.iloc[0], s=80)
            ax.text(g.o_lon.iloc[0], g.o_lat.iloc[0], hub, fontsize=8)
        ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")
        ax.set_title("Flux entre hubs et destinations")
        ax.grid(alpha=.2)
        fig_config()

elif page == "📈 Analyses avancées":
    st.markdown('<div class="section">Indicateurs opérationnels avancés</div>', unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1:
        breach = filtered.groupby("product_category", as_index=False)["temperature_breach"].mean()
        breach["Taux"] = breach.temperature_breach*100
        fig, ax = plt.subplots(figsize=(8,5))
        sns.barplot(data=breach.sort_values("Taux", ascending=False), x="Taux", y="product_category", ax=ax)
        ax.set_xlabel("Taux de rupture (%)"); ax.set_ylabel("")
        ax.set_title("Rupture de chaîne du froid")
        fig_config()
    with c2:
        cap = filtered.groupby("mode", as_index=False)["capacity_utilization"].mean()
        fig, ax = plt.subplots(figsize=(8,5))
        sns.barplot(data=cap, x="mode", y="capacity_utilization", ax=ax)
        ax.set_xlabel("Mode"); ax.set_ylabel("Utilisation")
        ax.set_title("Utilisation moyenne de la capacité")
        fig_config()

    st.markdown('<div class="section">Matrice de corrélation</div>', unsafe_allow_html=True)
    numeric = ["distance_km","planned_duration_min","actual_duration_min","delay_min","on_time","temperature_breach","capacity_utilization","fuel_liters","co2_kg","cost_mad","quantity_tons"]
    corr = filtered[numeric].corr()
    fig, ax = plt.subplots(figsize=(12,7))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdYlGn", center=0, ax=ax)
    ax.set_title("Corrélations entre indicateurs")
    fig_config()

    c1,c2 = st.columns(2)
    with c1:
        cost = filtered.groupby("destination_region", as_index=False)["cost_per_km"].mean().sort_values("cost_per_km", ascending=False)
        fig, ax = plt.subplots(figsize=(8,5))
        sns.barplot(data=cost, x="cost_per_km", y="destination_region", ax=ax)
        ax.set_xlabel("MAD / km"); ax.set_ylabel("")
        ax.set_title("Coût moyen par km et par région")
        fig_config()
    with c2:
        fig, ax = plt.subplots(figsize=(8,5))
        sns.scatterplot(data=filtered, x="distance_km", y="co2_kg", alpha=.6, ax=ax)
        ax.set_xlabel("Distance (km)"); ax.set_ylabel("CO₂ (kg)")
        ax.set_title("Distance vs émissions CO₂")
        fig_config()

elif page == "🗃️ Données":
    st.markdown('<div class="section">Données des expéditions</div>', unsafe_allow_html=True)
    st.caption(f"{len(filtered):,} lignes affichées sur {len(df):,}.")
    st.dataframe(filtered.sort_values("date", ascending=False), use_container_width=True, height=600)
    csv = filtered.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Télécharger les données filtrées (CSV)", csv, "copag_donnees_filtrees.csv", "text/csv")

st.markdown("---")
st.caption("COPAG • Plateforme d'analyse logistique • Données issues du dataset fourni")
