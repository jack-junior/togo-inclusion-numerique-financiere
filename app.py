"""Observatoire de l'inclusion numérique et financière du Togo — Togo AI Lab · Économie numérique | Défi 1.
Lancer : streamlit run app.py
"""
import streamlit as st

st.set_page_config(page_title="Inclusion numérique & financière · Togo", page_icon="assets/logo.svg", layout="wide",
                   initial_sidebar_state="expanded")

import core  # noqa: E402  (après set_page_config)

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"], .stApp { font-family: Inter, system-ui, sans-serif; }
.stApp { background:#f5f7f9; color:#17202a; }
.block-container { width:100%; max-width:1280px; box-sizing:border-box; padding:1rem 1.15rem 2.5rem; }

/* ---------- Navigation ---------- */
[data-testid="stSidebar"] { background:#fff; border-right:1px solid #e1e6ea; }
[data-testid="stSidebar"] .block-container { padding:.9rem .75rem 1.4rem; }
[data-testid="stSidebarNav"] { padding:.1rem .2rem .6rem; }
[data-testid="stSidebarNav"] li[data-testid="stSidebarNavLink"] {
  min-height:37px; margin:2px 0; padding:0 .55rem; border-radius:7px;
  color:#44515d; font-size:.84rem; font-weight:500;
}
[data-testid="stSidebarNav"] li[data-testid="stSidebarNavLink"] p { font-size:.84rem; }
[data-testid="stSidebarNav"] li[data-testid="stSidebarNavLink"]:hover { background:#f4f6f8; color:#17324d; }
[data-testid="stSidebarNav"] li[data-testid="stSidebarNavLink"][aria-current="page"] {
  background:#eef4f7; color:#123b5d; font-weight:650; box-shadow:inset 3px 0 0 #1a7a4c;
}
[data-testid="stSidebarNav"] [data-testid="stIconMaterial"] { color:#65737f; font-size:18px; }
[data-testid="stSidebarNav"] li[data-testid="stSidebarNavLink"][aria-current="page"] [data-testid="stIconMaterial"] { color:#1a7a4c; }
[data-testid="stSidebar"] hr { margin:.65rem 0; border-color:#e3e7ea; }
.side-h { font-size:.68rem; font-weight:700; color:#71808d; letter-spacing:.11em; margin:.55rem 0 .4rem; text-transform:uppercase; }
.brand { display:flex; align-items:center; gap:.6rem; padding:.1rem 0 .75rem; border-bottom:1px solid #e1e6ea; margin-bottom:.7rem; }
.brand b { font-size:.96rem; color:#17202a; line-height:1.15; }
.brand span { font-size:.74rem; color:#71808d; }
.dot { width:34px; height:34px; border-radius:8px; background:#1a7a4c; color:#fff; display:flex; align-items:center; justify-content:center; font-weight:700; }

/* ---------- Typography ---------- */
h1,h2,h3 { color:#101820; letter-spacing:-.015em; }
.lead { color:#687681; font-size:.92rem; line-height:1.45; margin:.15rem 0 .7rem; max-width:920px; }
.eyebrow { font-size:.63rem; font-weight:700; letter-spacing:.12em; color:#71808d; text-transform:uppercase; margin:.25rem 0 .18rem; }
.section-head { margin:1rem 0 .55rem; }
.section-head.compact { margin-top:1rem; }
.section-title { font-size:1.15rem; font-weight:700; color:#17202a; line-height:1.25; }
.section-subtitle { margin-top:.15rem; color:#788591; font-size:.79rem; line-height:1.4; }

/* ---------- Page header ---------- */
.page-hero {
  background:linear-gradient(110deg,#102a43 0%,#174e7d 100%);
  border-radius:9px; padding:.9rem 1.2rem; margin:0 0 .65rem;
  box-shadow:0 6px 18px -16px rgba(16,42,67,.75);
}
.page-hero .kicker { font-size:.6rem; font-weight:700; letter-spacing:.11em; text-transform:uppercase; color:rgba(255,255,255,.7); margin-bottom:.22rem; }
.page-hero h1 { color:#fff !important; margin:0 !important; font-size:1.58rem !important; font-weight:700 !important; line-height:1.16; letter-spacing:-.025em; }
.page-hero .icon { display:none; }

/* ---------- KPI ---------- */
.kpi-grid {
  display:grid;
  grid-template-columns:repeat(4,minmax(0,1fr));
  gap:14px;
  width:100%;
  margin:.15rem 0 .65rem;
}
.kpi {
  min-width:0; min-height:112px; height:112px; box-sizing:border-box;
  background:#fff; border:1px solid #dfe5e9; border-left:4px solid #1a7a4c;
  border-radius:8px; padding:.78rem .9rem;
  display:flex; flex-direction:column; justify-content:flex-start;
  box-shadow:0 1px 4px rgba(20,35,45,.025);
}
.kpi:hover { box-shadow:0 3px 10px rgba(20,35,45,.06); transform:none; }
.kpi-l { min-height:1.9em; color:#63707c; font-size:.73rem; font-weight:600; line-height:1.28; }
.kpi-v { color:#111820; font-size:1.68rem; font-weight:700; line-height:1.08; margin:.18rem 0 .12rem; white-space:nowrap; }
.kpi-n { color:#87929c; font-size:.72rem; line-height:1.25; }
.kpi-src { color:#a0a9b1; font-size:.64rem; line-height:1.2; margin-top:auto; padding-top:.32rem; border-top:1px dashed #e0e5e8; }

/* ---------- Overview ---------- */
.overview-intro {
  display:flex; align-items:flex-start; gap:.7rem; width:100%; box-sizing:border-box;
  margin:.05rem 0 .75rem; padding:.6rem .75rem;
  border-left:3px solid #2a78d6; background:#f8fafc; border-radius:0 7px 7px 0;
  color:#53616e; font-size:.83rem; line-height:1.42;
}
.overview-intro-label { flex:0 0 auto; color:#173b5a; font-weight:700; font-size:.68rem; text-transform:uppercase; letter-spacing:.08em; }
.overview-intro > span:last-child { min-width:0; overflow-wrap:anywhere; }

.territory-signal {
  display:grid; grid-template-columns:150px minmax(0,1fr) auto; align-items:center; gap:1rem;
  width:100%; box-sizing:border-box; margin:.65rem 0 .9rem; padding:.7rem .9rem;
  background:#fffaf7; border:1px solid #eadfd9; border-left:4px solid #eb6834; border-radius:8px;
}
.territory-label { color:#7b6f68; font-size:.61rem; font-weight:700; letter-spacing:.1em; }
.territory-value { color:#18222c; font-size:1.58rem; font-weight:750; line-height:1.05; margin-top:.14rem; }
.territory-copy { color:#596773; font-size:.82rem; line-height:1.38; min-width:0; }
.territory-copy strong { color:#263641; }
.territory-note { color:#9aa3ab; font-size:.66rem; margin-top:.18rem; }
.territory-badge { border:1px solid #ead4c8; color:#a45a35; background:#fff; border-radius:999px; padding:.3rem .52rem; font-size:.59rem; font-weight:700; letter-spacing:.06em; white-space:nowrap; }

.insights-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; width:100%; margin:.1rem 0 1rem; }
.insight-card { min-width:0; min-height:108px; padding:.78rem .85rem; border:1px solid #dfe5e9; border-left:3px solid #2a78d6; border-radius:7px; background:#fff; box-shadow:none; box-sizing:border-box; }
.insight-card.info { background:#fbfdff; border-left-color:#2a78d6; }
.insight-card.warning { background:#fffdf8; border-left-color:#eb6834; }
.insight-card.neutral { background:#fbfcfd; border-left-color:#aeb8c0; }
.insight-title { color:#263745; font-size:.86rem; font-weight:700; line-height:1.25; margin-bottom:.3rem; }
.insight-body { color:#52616d; font-size:.79rem; line-height:1.45; }
.insight-body strong { color:#273945; font-weight:700; }

.steps-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; width:100%; }
.step-card { min-width:0; min-height:82px; display:grid; grid-template-columns:34px 1fr; gap:.65rem; padding:.72rem .8rem; background:#fff; border:1px solid #dfe5e9; border-radius:7px; box-sizing:border-box; }
.step-no { width:30px; height:30px; display:flex; align-items:center; justify-content:center; border-radius:6px; background:#eef4f8; color:#1a7a4c; font-size:.66rem; font-weight:700; }
.step-title { color:#263745; font-size:.82rem; font-weight:700; margin-bottom:.18rem; }
.step-text { color:#6d7a85; font-size:.73rem; line-height:1.4; }

/* ---------- Charts / generic columns ---------- */
[data-testid="stHorizontalBlock"] { width:100% !important; max-width:100% !important; min-width:0 !important; gap:.9rem; align-items:stretch; box-sizing:border-box; }
[data-testid="stHorizontalBlock"] > [data-testid="column"] { min-width:0 !important; max-width:100% !important; box-sizing:border-box; }
[data-testid="stHorizontalBlock"] .kpi { width:100%; }
.stPlotlyChart { margin:.1rem 0 .3rem; max-width:100%; overflow:hidden; }
.stDataFrame, [data-testid="stTable"] { border-radius:8px; overflow:hidden; max-width:100%; }
.stButton > button, .stDownloadButton > button { border-radius:7px; font-weight:600; }
.msg { font-size:1.03rem; font-weight:700; color:#18222c; margin:1rem 0 .15rem; line-height:1.32; }
.msg-sub { font-size:.8rem; color:#7a8792; margin-bottom:.3rem; line-height:1.4; max-width:900px; }
.callout { border-radius:7px; padding:.65rem .8rem; font-size:.84rem; line-height:1.42; margin:.35rem 0; background:#fff; border:1px solid #dfe5e9; color:#26323d; box-shadow:none; }
.callout.warn { background:#fffaf0; border-color:#eeddb7; }
.callout.key { background:#f7fbff; border-color:#d4e4f3; }
.callout.ok { background:#f5fbf7; border-color:#cfe5d6; }
.reco { background:#fff; border:1px solid #dfe5e9; border-radius:8px; padding:.8rem .9rem; margin:.4rem 0; box-shadow:none; }
.reco h4 { margin:.02rem 0 .25rem; font-size:.94rem; }
.reco p { margin:.12rem 0; font-size:.82rem; color:#5f6b76; line-height:1.42; }
.foot { font-size:.68rem; color:#87929c; margin-top:1.4rem; border-top:1px solid #e1e6ea; padding-top:.6rem; line-height:1.4; }

/* Responsive: actual layout change, not just overflow hiding */
@media (max-width: 1050px) {
  .kpi-grid { grid-template-columns:repeat(2,minmax(0,1fr)); }
  .territory-signal { grid-template-columns:130px minmax(0,1fr); }
  .territory-badge { justify-self:start; grid-column:2; }
}
@media (max-width: 700px) {
  .block-container { padding-left:.7rem; padding-right:.7rem; }
  .page-hero h1 { font-size:1.35rem !important; }
  .kpi-grid, .insights-grid, .steps-grid { grid-template-columns:1fr; }
  .territory-signal { grid-template-columns:1fr; gap:.35rem; }
  .territory-badge { grid-column:auto; }
  .overview-intro { flex-direction:column; gap:.2rem; }
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

st.logo("assets/logo.svg", size="large")

from views import accueil, internet, marche, carte, inclusion, priorites, methodo  # noqa: E402

pages = {
    "ACCUEIL": [
        st.Page(accueil.render, title="Vue d'ensemble", icon=":material/home:", url_path="accueil", default=True),
    ],
    "ADOPTION DU NUMÉRIQUE": [
        st.Page(internet.render, title="Usage d'Internet", icon=":material/language:", url_path="internet"),
        st.Page(marche.render, title="Marché télécom", icon=":material/cell_tower:", url_path="marche"),
    ],
    "ACCÈS TERRITORIAL": [
        st.Page(carte.render, title="Carte des accès", icon=":material/map:", url_path="carte"),
        st.Page(inclusion.render, title="Mobile money et banque", icon=":material/account_balance:", url_path="inclusion"),
    ],
    "DÉCISION": [
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
