"""Observatoire de l'inclusion numérique et financière du Togo — Togo AI Lab · Économie numérique | Défi 1 | Challenge 2.
Lancer : streamlit run app.py
"""
import streamlit as st

st.set_page_config(page_title="Inclusion numérique & financière · Togo", page_icon="📶", layout="wide",
                   initial_sidebar_state="expanded")

import core  # noqa: E402  (après set_page_config)

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"], .stApp { font-family: 'Inter', system-ui, sans-serif; }
.stApp { background: #f6f6f4; }
.block-container { padding-top: 1.4rem; padding-bottom: 3rem; max-width: 1280px; }
h1 { font-size: 1.85rem !important; font-weight: 700 !important; letter-spacing: -0.02em; color:#0b0b0b; margin-bottom:.2rem;}
h2, h3 { color:#0b0b0b; letter-spacing:-0.01em; }
.lead { color:#52514e; font-size:1.02rem; margin: 0 0 1.1rem 0; max-width: 900px; line-height:1.5;}
[data-testid="stSidebar"] { background:#ffffff; border-right:1px solid #e6e5e1; }
.side-h { font-size:.72rem; font-weight:600; color:#8a8983; letter-spacing:.08em; margin:.6rem 0 .3rem 0;}
.brand { display:flex; align-items:center; gap:.6rem; padding:.2rem 0 .8rem 0; border-bottom:1px solid #e6e5e1; margin-bottom:.6rem;}
.brand b { font-size:1.02rem; color:#0b0b0b; display:block; line-height:1.15;}
.brand span { font-size:.78rem; color:#8a8983;}
.dot { width:34px; height:34px; border-radius:9px; background:#1a7a4c; color:#fff; display:flex; align-items:center; justify-content:center; font-weight:700;}
.kpi { background:#fff; border:1px solid #e6e5e1; border-left:4px solid #1a7a4c; border-radius:10px; padding:.85rem 1rem; height:100%;}
.kpi-l { font-size:.78rem; color:#52514e; font-weight:500; }
.kpi-v { font-size:1.7rem; font-weight:700; color:#0b0b0b; line-height:1.15; margin:.15rem 0;}
.kpi-n { font-size:.78rem; color:#8a8983; }
.msg { font-size:1.08rem; font-weight:650; color:#0b0b0b; margin:1.1rem 0 .1rem 0; line-height:1.35;}
.msg-sub { font-size:.86rem; color:#8a8983; margin-bottom:.4rem;}
.callout { border-radius:10px; padding:.8rem 1rem; font-size:.92rem; line-height:1.5; margin:.6rem 0; background:#fff; border:1px solid #e6e5e1; color:#0b0b0b;}
.callout.warn { background:#fff8e6; border-color:#f0dca0;}
.callout.key { background:#eef6ff; border-color:#c9def7;}
.callout.ok { background:#eef8f2; border-color:#c3e3cf;}
.tag { display:inline-block; padding:.08rem .5rem; border-radius:99px; font-size:.72rem; font-weight:600; margin-right:.3rem;}
.tag.h { background:#fde3e3; color:#9b1c1c;} .tag.m { background:#fff0d0; color:#8a5a00;} .tag.b { background:#e3efe8; color:#1a5a3a;}
.reco { background:#fff; border:1px solid #e6e5e1; border-radius:12px; padding:1rem 1.15rem; margin:.55rem 0;}
.reco h4 { margin:.1rem 0 .35rem 0; font-size:1.02rem; color:#0b0b0b;}
.reco p { margin:.15rem 0; font-size:.9rem; color:#52514e; line-height:1.5;}
.reco .big { font-size:.92rem; color:#0b0b0b; font-weight:600;}
.foot { font-size:.75rem; color:#8a8983; margin-top:2rem; border-top:1px solid #e6e5e1; padding-top:.6rem;}
div[data-testid="stMetric"] { background:#fff; border:1px solid #e6e5e1; border-radius:10px; padding:.6rem .8rem;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

st.logo("assets/logo.svg", size="large")

from views import accueil, internet, marche, carte, inclusion, priorites, methodo  # noqa: E402

pages = {
    "Principal": [
        st.Page(accueil.render, title="Vue d'ensemble", icon=":material/dashboard:", url_path="accueil", default=True),
    ],
    "Adoption du numérique": [
        st.Page(internet.render, title="Usage d'Internet", icon=":material/trending_up:", url_path="internet"),
        st.Page(marche.render, title="Marché télécom", icon=":material/cell_tower:", url_path="marche"),
    ],
    "Accès dans les territoires": [
        st.Page(carte.render, title="Carte des accès", icon=":material/map:", url_path="carte"),
        st.Page(inclusion.render, title="Mobile money et banque", icon=":material/account_balance:", url_path="inclusion"),
    ],
    "Décision": [
        st.Page(priorites.render, title="Priorités et recommandations", icon=":material/flag:", url_path="priorites"),
        st.Page(methodo.render, title="Méthode et qualité des données", icon=":material/fact_check:", url_path="methode"),
    ],
}
nav = st.navigation(pages)
core.sidebar_filters()
nav.run()

c = core.D["controles"]
st.markdown(
    f'<div class="foot">Sources : Banque mondiale (Internet 1996-2022) · ARCEP/Togo AI Lab (abonnés et marché 2013-2019) · '
    f'Géodata Togo (institutions financières, agents mobile money, limites) · INSEED, RGPH-5 2022. '
    f'Contrôles automatiques : population {core.fmt(c["population_somme_prefectures"])} = total national '
    f'{"✔" if c["population_somme_prefectures"] == c["population_total_fichier"] else "✘"} · '
    f'agents {core.fmt(c["agents_par_prefecture_somme"])} / {core.fmt(c["agents_total"])} rattachés '
    f'{"✔" if c["agents_par_prefecture_somme"] == c["agents_total"] else "✘"} · '
    f'établissements financiers {core.fmt(c["finance_total_lignes"])} lignes, {core.fmt(c["finance_hors_service_exclus"])} hors service.</div>',
    unsafe_allow_html=True)
