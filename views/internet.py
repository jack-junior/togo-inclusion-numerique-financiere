import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import core
from core import D, fmt, pct, message, callout, style_fig, BLUE, ORANGE, AQUA, YELLOW, MUTED, GRID, INK2

REGIMES = [(1996, 2013, "Stagnation", "#f0efec"), (2014, 2018, "Décollage", "#e3eefb"), (2019, 2022, "Accélération", "#cde2fb")]


def render():
    st.title("Usage d'Internet : trois régimes, puis une accélération")
    st.markdown('<p class="lead">Part de la population qui utilise Internet (1996-2022) et abonnements par technologie (2013-2019). '
                'Deux mesures différentes : des <b>personnes</b> d\'un côté, des <b>abonnements</b> de l\'autre.</p>', unsafe_allow_html=True)

    it = D["internet"].copy().set_index("annee")
    y0, y1 = st.slider("Période affichée", 1996, 2022, (1996, 2022), key="int_range")
    sel = it.loc[y0:y1]

    reg_stats = []
    for a, b, name, _ in REGIMES:
        s = it.loc[a:b]
        reg_stats.append((name, a, b, (s["pct_individus"].iloc[-1] - (it.loc[a - 1, "pct_individus"] if a - 1 in it.index else 0)) / len(s)))
    gain = it["gain_pts"]
    best = gain.idxmax()

    message(f"L'usage d'Internet est passé de {pct(it.loc[2013, 'pct_individus'])} en 2013 à {pct(it.loc[2022, 'pct_individus'])} en 2022",
            "Part des individus utilisant Internet (%), Banque mondiale. Les bandes colorées séparent trois régimes de croissance.")
    fig = go.Figure()
    for a, b, name, col in REGIMES:
        lo, hi = max(a, y0), min(b, y1)
        if lo <= hi:
            fig.add_vrect(x0=lo - 0.5, x1=hi + 0.5, fillcolor=col, opacity=0.55, line_width=0, layer="below",
                          annotation_text=name, annotation_position="top left", annotation_font=dict(size=12, color=INK2))
    fig.add_trace(go.Scatter(x=sel.index, y=sel["pct_individus"], mode="lines+markers", line=dict(color=BLUE, width=2.5),
                             marker=dict(size=6, color=BLUE, line=dict(color="white", width=1.5)), name="Individus utilisant Internet",
                             hovertemplate="<b>%{x}</b> : %{y:.1f} % de la population<extra></extra>"))
    fig.update_yaxes(title="% de la population", rangemode="tozero", ticksuffix=" %")
    fig.update_xaxes(dtick=2)
    st.plotly_chart(style_fig(fig, 380, legend=False, margin=dict(l=8, r=8, t=28, b=8)), use_container_width=True, config={"displayModeBar": False})

    cols = st.columns(3)
    for col, (name, a, b, g) in zip(cols, reg_stats):
        with col:
            callout(f"<b>{name} ({a}-{b})</b><br>{fmt(g, 1)} point de pourcentage gagné par an en moyenne", "key" if name != "Stagnation" else "info")

    message(f"Le plus fort gain annuel date de {best} : +{fmt(gain.loc[best], 1)} points",
            "Gain annuel en points de pourcentage. Le ralentissement de 2021 (+3,5) puis la reprise de 2022 (+5,1) montrent que la trajectoire n'est pas linéaire.")
    g = it.loc[max(y0, 1997):y1, "gain_pts"]
    colors = [ORANGE if yy == best else BLUE for yy in g.index]
    fig = go.Figure(go.Bar(x=g.index, y=g.values, marker_color=colors,
                           hovertemplate="<b>%{x}</b> : %{y:+.2f} points<extra></extra>"))
    fig.update_yaxes(title="Points de pourcentage par an"); fig.update_xaxes(dtick=2)
    st.plotly_chart(style_fig(fig, 260, legend=False), use_container_width=True, config={"displayModeBar": False})

    # ------------------------------------------------------------------ abonnements par technologie
    st.markdown("---")
    pa = core.ab_pivot()
    dec = core.mobile_decomposition()
    tot = pa["T abonnés Internet Fixe et Mobile (Toutes technologies)"]
    peak = tot.idxmax(); drop = tot.loc[2019] / tot.loc[2018] - 1
    d3 = dec["3G"]
    message(f"Les abonnements Internet ont atteint {fmt(tot.loc[peak] / 1e6, 2)} M en {peak}, puis reculé de {fmt(-drop * 100, 1)} % en 2019",
            "Abonnements Internet par technologie (nombre d'abonnements, tous opérateurs). Le recul vient de la 3G ; la 4G reste marginale.")
    mode = st.radio("Affichage", ["Nombre d'abonnements", "Part de chaque technologie"], horizontal=True, key="tech_mode")
    show = dec.copy()
    if mode.startswith("Part"):
        show = show.div(show.sum(axis=1), axis=0) * 100
    palette = {"2G (GPRS/EDGE)": MUTED, "3G": BLUE, "4G": ORANGE, "Fixe (ADSL, fibre, WiMAX…)": AQUA}
    fig = go.Figure()
    for c in show.columns:
        fig.add_trace(go.Bar(x=show.index, y=show[c], name=c, marker_color=palette[c], marker_line=dict(color="white", width=1.5),
                             hovertemplate=f"<b>{c}</b> %{{x}} : %{{y:,.{0 if not mode.startswith('Part') else 1}f}}"
                                           f"{' %' if mode.startswith('Part') else ''}<extra></extra>"))
    fig.update_layout(barmode="stack"); fig.update_xaxes(dtick=1)
    fig.update_yaxes(title="Abonnements" if not mode.startswith("Part") else "Part (%)")
    st.plotly_chart(style_fig(fig, 380), use_container_width=True, config={"displayModeBar": False})

    a1, a2, a3 = st.columns(3)
    with a1:
        callout(f"<b>3G : {fmt(d3.loc[2018] / 1e6, 2)} M → {fmt(d3.loc[2019] / 1e6, 2)} M en 2019</b> ({fmt((d3.loc[2019] / d3.loc[2018] - 1) * 100, 0)} %), "
                f"alors que la 2G repart à la hausse ({fmt(dec['2G (GPRS/EDGE)'].loc[2018] / 1e6, 2)} M → {fmt(dec['2G (GPRS/EDGE)'].loc[2019] / 1e6, 2)} M) : "
                "des abonnés redescendent vers un service moins performant.", "warn")
    with a2:
        callout(f"<b>4G : {fmt(dec['4G'].loc[2019] / 1e3, 0)} 000 abonnés en 2019</b>, soit {fmt(dec['4G'].loc[2019] / dec.loc[2019].sum() * 100, 1)} % des abonnements. "
                "Un seul opérateur la déclare (Togo Cellulaire) ; la 4G d'Atlantique Telecom n'est pas renseignée en 2018-2019.", "info")
    with a3:
        ftth, gva = pa["FTTH"], pa["GVA"]
        callout(f"<b>Fibre (FTTH) : {fmt(ftth.loc[2017])} → {fmt(ftth.loc[2019])} abonnés en deux ans.</b> Croissance très rapide mais depuis presque rien ; "
                f"le fixe total ne pèse que {fmt(dec.iloc[:, 3].loc[2019] / 1e3, 0)} 000 abonnements.", "key")
    st.caption("Note de lecture : en 2016 la 3G bondit (0,43 M → 1,44 M) alors que la 2G s'effondre : il s'agit d'un changement de classement autant que d'un vrai basculement d'usage.")

    # ------------------------------------------------------------------ personnes vs abonnements
    st.markdown("---")
    pen = pa["Taux de pénétration Internet (Toutes technologies) (%)"]
    users = it.loc[2013:2019, "pct_individus"]
    message(f"En 2019, on compte {fmt(pen.loc[2019], 1)} abonnements pour 100 habitants, mais seulement {fmt(users.loc[2019], 1)} % d'utilisateurs",
            "Les deux courbes ne mesurent pas la même chose : un utilisateur peut avoir plusieurs abonnements (cartes SIM, opérateurs) et certains abonnements sont inactifs.")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=pen.index, y=pen.values, name="Abonnements pour 100 habitants", mode="lines+markers", line=dict(color=ORANGE, width=2.5),
                             marker=dict(size=7, line=dict(color="white", width=1.5)), hovertemplate="<b>%{x}</b> : %{y:.1f} abonnements pour 100 hab.<extra></extra>"))
    fig.add_trace(go.Scatter(x=users.index, y=users.values, name="Individus utilisant Internet (%)", mode="lines+markers", line=dict(color=BLUE, width=2.5),
                             marker=dict(size=7, line=dict(color="white", width=1.5)), hovertemplate="<b>%{x}</b> : %{y:.1f} % d'utilisateurs<extra></extra>"))
    fig.update_yaxes(title="Pour 100 habitants / en %", rangemode="tozero"); fig.update_xaxes(dtick=1)
    st.plotly_chart(style_fig(fig, 320), use_container_width=True, config={"displayModeBar": False})
    callout("<b>Conséquence pour l'action publique</b> : suivre uniquement le nombre d'abonnements surestime l'inclusion. "
            "L'indicateur de référence pour les cibles doit être la part d'individus utilisant réellement Internet.", "key")

    with st.expander("Voir les données (tableau)"):
        t = it.reset_index().rename(columns={"annee": "Année", "pct_individus": "Individus utilisant Internet (%)", "gain_pts": "Gain annuel (points)"})
        st.dataframe(t.round(2), use_container_width=True, hide_index=True)
        core.download(t, "internet_serie.csv", key="dl_internet")
