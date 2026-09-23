"""Noyau du dashboard : chargement des données, palette, filtres globaux, indicateurs recalculés."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
PROC = ROOT / "data" / "processed"

# --------------------------------------------------------------------------- palette (validée, voir docs/PALETTE.md)
BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN, VIOLET, RED = (
    "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948")
INK, INK2, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#8a8983", "#e6e5e1", "#fcfcfb"
SEQ = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]  # séquentiel bleu (magnitude)
BRAND = "#1a7a4c"  # vert Togo AI Lab : uniquement pour l'interface, jamais pour encoder une donnée
OPCOL = {"Togocom": BLUE, "Moov": ORANGE, "Moov + Togocom": AQUA, "Non renseigné": MUTED}
FINCOL = {"Banque": BLUE, "Micro-Finance": ORANGE, "Assurance": AQUA, "Mutuelle": AQUA}  # 3 couleurs max (palette validée sur 3 séries)

REGIONS = ["Maritime", "Plateaux", "Centrale", "Kara", "Savanes"]
FINCATS = ["Banque", "Micro-Finance", "Assurance", "Mutuelle"]
OPS = ["Togocom", "Moov", "Non renseigné"]


def fmt(n, dec=0):
    """Format français : espace insécable pour les milliers, virgule décimale."""
    if n is None or (isinstance(n, float) and np.isnan(n)):
        return "n.d."
    s = f"{n:,.{dec}f}".replace(",", " ").replace(".", ",")
    return s


def pct(x, dec=1):
    return fmt(x, dec) + " %"


# --------------------------------------------------------------------------- données
@st.cache_data(show_spinner=False)
def load():
    d = {
        "pref": pd.read_csv(PROC / "prefecture.csv"),
        "commune": pd.read_csv(PROC / "commune.csv"),
        "agents": pd.read_csv(PROC / "agents_points.csv"),
        "fin": pd.read_csv(PROC / "finance_points.csv"),
        "internet": pd.read_csv(PROC / "internet_serie.csv"),
        "abonnes": pd.read_csv(PROC / "abonnes_long.csv"),
        "marche": pd.read_csv(PROC / "marche_long.csv"),
        "controles": json.load(open(PROC / "controles.json", encoding="utf-8")),
        "geo_pref": json.load(open(PROC / "prefectures.geojson", encoding="utf-8")),
        "geo_com": json.load(open(PROC / "communes.geojson", encoding="utf-8")),
    }
    d["agents"]["op_key"] = d["agents"]["operateur"]
    return d


D = load()


# --------------------------------------------------------------------------- filtres globaux
def sidebar_filters():
    """Filtres persistants (session_state) : ils commandent les vues Carte, Inclusion et Priorités."""
    ss = st.session_state
    ss.setdefault("f_regions", [])
    ss.setdefault("f_prefs", [])
    ss.setdefault("f_ops", OPS.copy())
    ss.setdefault("f_cats", FINCATS.copy())
    ss.setdefault("f_service", True)

    with st.sidebar:
        st.markdown('<div class="side-h">FILTRES GLOBAUX</div>', unsafe_allow_html=True)
        st.multiselect("Région (vide = toutes)", REGIONS, key="f_regions", placeholder="Toutes les régions",
                       help="Régions Géodata (5) : le Grand Lomé est inclus dans Maritime.")
        opts = sorted(D["pref"].loc[D["pref"]["region"].isin(regs()), "prefecture"])
        ss["f_prefs"] = [p for p in ss["f_prefs"] if p in opts]
        st.multiselect("Préfecture (vide = toutes)", opts, key="f_prefs", placeholder="Toutes les préfectures")
        st.multiselect("Opérateur mobile money", OPS, key="f_ops", placeholder="Choisir un opérateur",
                       help="Un agent « Moov + Togocom » compte pour chacun des deux opérateurs.")
        st.multiselect("Type d'établissement financier", FINCATS, key="f_cats", placeholder="Choisir un type")
        st.checkbox("Exclure fermés / abandonnés / en construction", key="f_service")
        if st.button("Réinitialiser les filtres", use_container_width=True):
            for k in ("f_regions", "f_prefs", "f_ops", "f_cats", "f_service"):
                del ss[k]
            st.rerun()


def regs():
    """Régions retenues (liste vide = toutes)."""
    return st.session_state["f_regions"] or REGIONS


def filters_active():
    ss = st.session_state
    return (bool(ss["f_regions"]) or bool(ss["f_prefs"]) or set(ss["f_ops"]) != set(OPS)
            or set(ss["f_cats"]) != set(FINCATS) or not ss["f_service"])


def _op_mask(df, ops):
    m = pd.Series(False, index=df.index)
    for o in ops:
        if o == "Non renseigné":
            m |= df["operateur"] == "Non renseigné"
        else:
            m |= df["operateur"].str.contains(o, regex=False)
    return m


def selected_points(use_filters=True):
    """Points agents / financiers après filtres opérateur, type et statut (tout le pays)."""
    ss = st.session_state
    if not use_filters:
        return D["agents"], D["fin"][D["fin"]["en_service"]]
    a = D["agents"]; a = a[_op_mask(a, ss["f_ops"])]
    f = D["fin"]; f = f[f["categorie"].isin(ss["f_cats"])]
    if ss["f_service"]:
        f = f[f["en_service"]]
    return a, f


def build_pref_table(weights=(0.5, 0.25, 0.25), use_filters=True):
    """Indicateurs par préfecture recalculés selon les filtres opérateur/type ; repères = médianes nationales."""
    a, f = selected_points(use_filters)
    p = D["pref"][["prefecture", "region", "superficie_km2", "pop_2022"]].copy()
    p["agents_total"] = p["prefecture"].map(a.groupby("prefecture").size()).fillna(0).astype(int)
    p["fin_total"] = p["prefecture"].map(f.groupby("prefecture").size()).fillna(0).astype(int)
    for c in FINCATS:
        p["fin_" + c] = p["prefecture"].map(f[f["categorie"] == c].groupby("prefecture").size()).fillna(0).astype(int)
    for o in ["Togocom", "Moov", "Moov + Togocom", "Non renseigné"]:
        p["ag_" + o] = p["prefecture"].map(a[a["operateur"] == o].groupby("prefecture").size()).fillna(0).astype(int)
    p["fin_bancaire"] = p["fin_Banque"] + p["fin_Micro-Finance"]
    p["densite"] = p["pop_2022"] / p["superficie_km2"]
    p["agents_pour_1000hab"] = p["agents_total"] / p["pop_2022"] * 1000
    p["fin_pour_100000hab"] = p["fin_total"] / p["pop_2022"] * 1e5
    p["hab_par_agent"] = p["pop_2022"] / p["agents_total"].replace(0, np.nan)
    p["hab_par_point_fin"] = p["pop_2022"] / p["fin_total"].replace(0, np.nan)
    p["agents_par_point_fin"] = p["agents_total"] / p["fin_total"].replace(0, np.nan)
    p["agents_par_km2"] = p["agents_total"] / p["superficie_km2"]
    p["mm_seul"] = (p["agents_total"] > 0) & (p["fin_bancaire"] == 0)
    p["grand_lome"] = p["prefecture"].isin(["Golfe", "Agoè-Nyivé"])
    med_a, med_f = p["agents_pour_1000hab"].median(), p["fin_pour_100000hab"].median()
    p["sous_median_agents"] = p["agents_pour_1000hab"] < med_a
    p["sous_median_fin"] = p["fin_pour_100000hab"] < med_f
    p["double_desavantage"] = p["sous_median_agents"] & p["sous_median_fin"]
    pr = lambda s: s.rank(pct=True) * 100
    p["indice_acces"] = ((pr(p["agents_pour_1000hab"]) + pr(p["fin_pour_100000hab"]) + pr(p["agents_par_km2"])) / 3).round(1)
    p["agents_manquants"] = np.ceil(np.clip(med_a * p["pop_2022"] / 1000 - p["agents_total"], 0, None)).astype(int)
    p["points_fin_manquants"] = np.ceil(np.clip(med_f * p["pop_2022"] / 1e5 - p["fin_total"], 0, None)).astype(int)
    w1, w2, w3 = weights
    s = w1 * (100 - p["indice_acces"]) + w2 * pr(p["agents_manquants"]) + w3 * pr(p["points_fin_manquants"])
    p["score_priorite"] = (s / max(w1 + w2 + w3, 1e-9)).round(1)
    p.attrs.update(med_a=med_a, med_f=med_f)
    return p


def visible(p):
    """Applique le filtre territorial (région / préfecture) à une table préfecture."""
    ss = st.session_state
    m = p["region"].isin(regs())
    if ss["f_prefs"]:
        m &= p["prefecture"].isin(ss["f_prefs"])
    return p[m]


def visible_points(df):
    ss = st.session_state
    m = df["region"].isin(regs())
    if ss["f_prefs"]:
        m &= df["prefecture"].isin(ss["f_prefs"])
    return df[m]


def spearman(x, y):
    d = pd.DataFrame({"x": x, "y": y}).dropna()
    return d["x"].rank().corr(d["y"].rank())


# --------------------------------------------------------------------------- séries temporelles
def ab_pivot():
    return D["abonnes"].pivot(index="annee", columns="indicateur", values="valeur")


def mk_pivot():
    return D["marche"].pivot(index="annee", columns="indicateur", values="valeur")


def mobile_decomposition():
    pa = ab_pivot()
    g3 = pa["Nombre de clients 3G Atlantique Telecom"].fillna(0) + pa["Nombre de clients 3G Togo Cellulaire"].fillna(0)
    g4 = pa["Nombre de clients 4G Atlantique Telecom"].fillna(0) + pa["Nombre de clients 4G Togo Cellulaire"].fillna(0)
    g2 = pa["Abonnés GPRS /EDGE Togo Cellulaire"].fillna(0) + pa["Abonnés GPRS/EDGE Atlantique Telecom"].fillna(0)
    tot = pa["T abonnés Internet Fixe et Mobile (Toutes technologies)"]
    mob = pa["T abonnés Internet mobiles (Toutes technologies)"]
    return pd.DataFrame({"2G (GPRS/EDGE)": g2, "3G": g3, "4G": g4, "Fixe (ADSL, fibre, WiMAX…)": tot - mob})


# --------------------------------------------------------------------------- mise en page commune
PLOT_FONT = dict(family="Inter, system-ui, sans-serif", size=13, color=INK2)


def style_fig(fig, height=360, legend=True, margin=None):
    fig.update_layout(
        height=height, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=PLOT_FONT,
        margin=margin or dict(l=8, r=8, t=8, b=8), hoverlabel=dict(bgcolor="white", font_size=13, font_color=INK),
        legend=dict(orientation="h", y=-0.18, x=0, title=None) if legend else None, showlegend=legend)
    fig.update_xaxes(showgrid=False, linecolor=GRID, tickcolor=GRID, zeroline=False)
    fig.update_yaxes(gridcolor=GRID, zeroline=False, linecolor="rgba(0,0,0,0)")
    return fig


def message(title, sub=None):
    """Titre-message d'un graphique : la phrase à retenir, puis une ligne d'aide à la lecture."""
    st.markdown(f'<div class="msg">{title}</div>' + (f'<div class="msg-sub">{sub}</div>' if sub else ""),
                unsafe_allow_html=True)


def kpi(label, value, note=None, color=BRAND):
    st.markdown(
        f'<div class="kpi" style="border-left-color:{color}"><div class="kpi-l">{label}</div>'
        f'<div class="kpi-v">{value}</div>' + (f'<div class="kpi-n">{note}</div>' if note else "") + "</div>",
        unsafe_allow_html=True)


def callout(text, kind="info"):
    st.markdown(f'<div class="callout {kind}">{text}</div>', unsafe_allow_html=True)


def download(df, name, label="Exporter (CSV)", key=None):
    st.download_button(label, df.to_csv(index=False).encode("utf-8-sig"), file_name=name, mime="text/csv", key=key)
