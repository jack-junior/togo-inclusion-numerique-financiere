import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import core
from core import D, fmt, pct, message, callout, style_fig, BLUE, OPCOL, FINCOL, SEQ, GRID, INK2

METRICS = {
    "Habitants par agent mobile money": ("hab_par_agent", "hab. / agent", 0, True),
    "Agents mobile money pour 1 000 habitants": ("agents_pour_1000hab", "agents / 1 000 hab.", 2, False),
    "Points financiers pour 100 000 habitants": ("fin_pour_100000hab", "points / 100 000 hab.", 1, False),
    "Habitants par point financier": ("hab_par_point_fin", "hab. / point", 0, True),
    "Population (RGPH-5 2022)": ("pop_2022", "habitants", 0, False),
}
COM_METRICS = {k: v for k, v in METRICS.items() if v[0] in ("hab_par_agent", "agents_pour_1000hab", "hab_par_point_fin", "pop_2022")}
HELP = {
    "hab_par_agent": "Plus la valeur est élevée, plus un agent dessert d'habitants : accès plus difficile.",
    "agents_pour_1000hab": "Plus la valeur est élevée, plus l'offre mobile money est dense.",
    "fin_pour_100000hab": "Plus la valeur est élevée, plus l'offre bancaire, de microfinance, d'assurance et de mutuelles est dense.",
    "hab_par_point_fin": "Plus la valeur est élevée, plus un point financier dessert d'habitants : accès plus difficile.",
    "pop_2022": "Population résidente au recensement de 2022.",
}


def _view(lons, lats):
    if len(lons) == 0:
        return dict(lon=1.17, lat=8.6), 6.3
    lo0, lo1, la0, la1 = min(lons), max(lons), min(lats), max(lats)
    lat_span, lon_span = max((la1 - la0) * 1.15, 0.12), max((lo1 - lo0) * 1.25, 0.12)
    z = min(np.log2(360 * 560 / (512 * lat_span)), np.log2(360 * 1000 / (512 * lon_span)))
    return dict(lon=(lo0 + lo1) / 2, lat=(la0 + la1) / 2), float(np.clip(z, 5.0, 11.0))


def _bounds(geo, names, key):
    xs, ys = [], []
    for f in geo["features"]:
        if f["properties"][key] in names:
            def walk(c):
                if isinstance(c[0], (int, float)):
                    xs.append(c[0]); ys.append(c[1])
                else:
                    for k in c: walk(k)
            walk(f["geometry"]["coordinates"])
    return xs, ys


def render():
    st.title("Carte des accès : où les agents et les banques manquent")
    st.markdown('<p class="lead">Choisissez un indicateur et un niveau (préfectures ou communes). Les filtres de gauche '
                '(région, préfecture, opérateur, type d\'établissement) s\'appliquent à la carte, aux classements et aux exports.</p>', unsafe_allow_html=True)

    T_all = core.build_pref_table()
    T = core.visible(T_all)
    if T.empty:
        callout("Aucune préfecture ne correspond aux filtres actuels.", "warn"); return

    c1, c2, c3 = st.columns([1.4, 1, 1.6])
    with c1:
        level = st.radio("Niveau", ["Préfectures (39)", "Communes (117)"], horizontal=True, key="map_level")
    with c2:
        basemap = st.radio("Fond de carte", ["Clair", "Sans fond"], horizontal=True, key="map_base",
                           help="« Sans fond » n'appelle aucun service externe (utile hors connexion).")
    is_pref = level.startswith("Pref") or level.startswith("Préf")
    metrics = METRICS if is_pref else COM_METRICS
    with c1:
        label = st.selectbox("Indicateur coloré", list(metrics), key="map_metric" + ("_p" if is_pref else "_c"))
    with c3:
        layers = st.multiselect("Points à superposer", ["Agents mobile money", "Banques", "Microfinance", "Assurances et mutuelles"], default=[], key="map_layers", placeholder="Aucune couche",
                                help="Chaque point est un agent ou un établissement géolocalisé.")
    col, unit, dec, high_bad = metrics[label]

    # ---------------------------------------------------------------- données du niveau choisi
    if is_pref:
        df = T[["prefecture", "region", "pop_2022", "agents_total", "fin_total", col]].copy()
        df["nom"] = df["prefecture"]; geo = D["geo_pref"]; fkey = "id"
        xs, ys = _bounds(geo, set(df["prefecture"]), "prefecture")
    else:
        C = D["commune"].copy()
        a, f = core.selected_points()
        # recalcul des comptes communaux selon les filtres opérateur/type
        C["agents_total"] = C["commune"].map(a.groupby("commune").size()).fillna(0).astype(int)
        f2 = f[f["categorie"].isin(["Banque", "Micro-Finance"])]
        C["fin_bancaire"] = C["commune"].map(f2.groupby("commune").size()).fillna(0).astype(int)
        C["fin_total"] = C["commune"].map(f.groupby("commune").size()).fillna(0).astype(int)
        C["hab_par_agent"] = C["pop_2022"] / C["agents_total"].replace(0, np.nan)
        C["agents_pour_1000hab"] = C["agents_total"] / C["pop_2022"] * 1000
        C["hab_par_point_fin"] = C["pop_2022"] / C["fin_total"].replace(0, np.nan)
        C["mm_seul"] = (C["agents_total"] > 0) & (C["fin_bancaire"] == 0)
        m = C["region"].isin(core.regs())
        if st.session_state["f_prefs"]:
            m &= C["prefecture"].isin(st.session_state["f_prefs"])
        df = C[m].copy(); df["nom"] = df["commune"]; geo = D["geo_com"]; fkey = "properties.commune"
        xs, ys = _bounds(geo, set(df["commune"]), "commune")

    z = df[col]
    message(f"{label} : {'les zones sombres sont les moins bien servies' if high_bad else 'les zones sombres sont les mieux dotées'}",
            HELP[col] + (" Les zones grises n'ont aucun agent ou point : le ratio n'est pas défini." if high_bad else ""))

    center, zoom = _view(xs, ys)
    fig = go.Figure()
    zmax = float(np.nanpercentile(z, 95)) if z.notna().any() else 1
    fig.add_trace(go.Choroplethmap(
        geojson=geo, locations=df["nom"], z=z, featureidkey=fkey, colorscale=[[i / (len(SEQ) - 1), c] for i, c in enumerate(SEQ)],
        zmin=float(np.nanmin(z)) if z.notna().any() else 0, zmax=zmax, marker=dict(line=dict(color="white", width=1), opacity=0.82),
        colorbar=dict(title=dict(text=unit, font=dict(size=12)), thickness=12, len=0.6, x=0.99, xanchor="right", y=0.5),
        customdata=np.stack([df["pop_2022"].fillna(0), df["agents_total"], df["fin_total"]], axis=-1),
        hovertemplate="<b>%{location}</b><br>" + label + " : %{z:,.1f}<br>Population : %{customdata[0]:,.0f}"
                      "<br>Agents : %{customdata[1]:,.0f}<br>Points financiers : %{customdata[2]:,.0f}<extra></extra>", name="",
    ))
    ag_sel, fi_sel = core.selected_points()
    ag_sel, fi_sel = core.visible_points(ag_sel), core.visible_points(fi_sel)
    if "Agents mobile money" in layers:
        for op in ["Moov + Togocom", "Togocom", "Moov", "Non renseigné"]:
            s = ag_sel[ag_sel["operateur"] == op]
            if len(s):
                fig.add_trace(go.Scattermap(lon=s["lon"], lat=s["lat"], mode="markers", marker=dict(size=4, color=OPCOL[op], opacity=0.55),
                                            name=f"Agents · {op}", hovertemplate=f"<b>Agent {op}</b><br>" + "%{customdata[0]}, %{customdata[1]}<extra></extra>",
                                            customdata=s[["commune", "prefecture"]].values))
    for lay, cats in [("Banques", ["Banque"]), ("Microfinance", ["Micro-Finance"]), ("Assurances et mutuelles", ["Assurance", "Mutuelle"])]:
        if lay in layers:
            for cat in cats:
                s = fi_sel[fi_sel["categorie"] == cat]
                if len(s):
                    fig.add_trace(go.Scattermap(lon=s["lon"], lat=s["lat"], mode="markers", marker=dict(size=8, color=FINCOL[cat], opacity=0.9),
                                                name=cat, hovertemplate="<b>%{customdata[0]}</b><br>" + cat + " · %{customdata[1]}<extra></extra>",
                                                customdata=s[["nom", "prefecture"]].values))
    fig.update_layout(map=dict(style="carto-positron" if basemap == "Clair" else "white-bg", center=center, zoom=zoom), height=560, margin=dict(l=0, r=0, t=0, b=0),
                      legend=dict(orientation="h", y=-0.02, bgcolor="rgba(255,255,255,.85)"), paper_bgcolor="rgba(0,0,0,0)", font=core.PLOT_FONT,
                      hoverlabel=dict(bgcolor="white", font_color=core.INK))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "scrollZoom": True})

    # ---------------------------------------------------------------- lecture chiffrée
    ok = df.dropna(subset=[col])
    if high_bad:
        worst = ok.nlargest(10, col); best_ = ok.nsmallest(1, col)
        message(f"Les {len(worst)} zones les plus difficiles d'accès ({label.lower()})", "Classement dans la sélection courante.")
    else:
        worst = ok.nsmallest(10, col); best_ = ok.nlargest(1, col)
        message(f"Les {len(worst)} zones les moins dotées ({label.lower()})", "Classement dans la sélection courante.")
    fig = go.Figure(go.Bar(x=worst[col], y=worst["nom"], orientation="h", marker_color=BLUE, customdata=worst[["pop_2022", "agents_total", "fin_total"]],
                           hovertemplate="<b>%{y}</b><br>%{x:,.1f}<br>Population : %{customdata[0]:,.0f}<br>Agents : %{customdata[1]:,.0f}"
                                         "<br>Points financiers : %{customdata[2]:,.0f}<extra></extra>"))
    fig.update_yaxes(autorange="reversed"); fig.update_xaxes(title=unit)
    st.plotly_chart(style_fig(fig, 340, legend=False), use_container_width=True, config={"displayModeBar": False})

    if not is_pref:
        mm = df[df["mm_seul"]]
        callout(f"<b>{len(mm)} communes sur {len(df)} ont des agents mobile money mais aucune banque ni microfinance en service</b> "
                f"({fmt(mm['pop_2022'].sum())} habitants) : le mobile money est leur seul accès numérique aux services financiers.", "warn")
    else:
        mm = T[T["mm_seul"]]
        zero = T[T["fin_total"] == 0]
        if len(zero):
            callout(f"<b>{', '.join(zero['prefecture'])} : aucun point financier en service</b> pour {fmt(zero['pop_2022'].sum())} habitants dans la sélection.", "warn")

    with st.expander("Voir et exporter le tableau"):
        show = df.drop(columns=[c for c in ["fid", "nom"] if c in df.columns]).round(2)
        st.dataframe(show, use_container_width=True, hide_index=True)
        core.download(show, "carte_acces_selection.csv", key="dl_carte")
