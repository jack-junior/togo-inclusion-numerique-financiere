import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import core
from core import D, fmt, pct, message, callout, style_fig, BLUE, ORANGE, AQUA, YELLOW, MUTED, INK2, GRID, RED


def render():
    st.title("Mobile money et banque : complément ou substitut ?")
    st.markdown('<p class="lead">Si le mobile money remplaçait la banque, il serait plus dense là où les banques sont rares. '
                'Les données montrent l\'inverse : les deux offres se superposent. Les filtres de gauche s\'appliquent à cette page.</p>', unsafe_allow_html=True)

    T_all = core.build_pref_table()
    T = core.visible(T_all)
    if len(T) < 3:
        callout("Sélectionnez au moins 3 préfectures pour comparer.", "warn"); return
    med_a, med_f = T_all.attrs["med_a"], T_all.attrs["med_f"]
    rho = core.spearman(T["agents_pour_1000hab"], T["fin_pour_100000hab"])

    # ---------------------------------------------------------------- nuage : agents vs points financiers
    def grp(r):
        if r["double_desavantage"]: return "Sous la médiane sur les deux axes"
        if r["sous_median_agents"] or r["sous_median_fin"]: return "Sous la médiane sur un axe"
        return "Au-dessus de la médiane sur les deux axes"
    T = T.assign(groupe=T.apply(grp, axis=1))
    message(f"Corrélation de rang ρ = {fmt(rho, 2)} : le mobile money se déploie là où la banque est déjà présente",
            f"Chaque bulle est une préfecture (taille = population). Traits pointillés : médianes nationales ({fmt(med_a, 2)} agents pour 1 000 hab. ; {fmt(med_f, 1)} points financiers pour 100 000 hab.).")
    cols = {"Sous la médiane sur les deux axes": ORANGE, "Sous la médiane sur un axe": AQUA, "Au-dessus de la médiane sur les deux axes": BLUE}
    fig = go.Figure()
    for g, c in cols.items():
        s = T[T["groupe"] == g]
        if s.empty: continue
        fig.add_trace(go.Scatter(x=s["agents_pour_1000hab"], y=s["fin_pour_100000hab"], mode="markers", name=g,
                                 marker=dict(size=np.sqrt(s["pop_2022"]) / 16 + 6, color=c, opacity=0.85, line=dict(color="white", width=1.5)),
                                 customdata=s[["prefecture", "pop_2022", "agents_total", "fin_total", "hab_par_agent"]].values,
                                 hovertemplate="<b>%{customdata[0]}</b><br>Agents : %{customdata[2]:,.0f} (%{x:.2f} pour 1 000 hab.)<br>Points financiers : %{customdata[3]:,.0f} (%{y:.1f} pour 100 000 hab.)"
                                               "<br>Population : %{customdata[1]:,.0f}<extra></extra>"))
    lab = T.nlargest(6, "pop_2022")
    lab = pd.concat([lab, T[T["fin_total"] == 0], T.nsmallest(2, "indice_acces")]).drop_duplicates("prefecture")
    fig.add_trace(go.Scatter(x=lab["agents_pour_1000hab"], y=lab["fin_pour_100000hab"], mode="text", text=lab["prefecture"], textposition="top center",
                             textfont=dict(size=11, color=core.INK), showlegend=False, hoverinfo="skip"))
    fig.add_vline(x=med_a, line=dict(color=MUTED, width=1, dash="dot")); fig.add_hline(y=med_f, line=dict(color=MUTED, width=1, dash="dot"))
    fig.update_xaxes(title="Agents mobile money pour 1 000 habitants", showgrid=True, gridcolor=GRID)
    fig.update_yaxes(title="Points financiers pour 100 000 habitants")
    st.plotly_chart(style_fig(fig, 480), use_container_width=True, config={"displayModeBar": False})
    dd = T[T["double_desavantage"]]
    callout(f"<b>{len(dd)} préfectures cumulent un désavantage</b> (sous la médiane pour les agents ET pour les points financiers) : "
            f"{', '.join(dd.sort_values('score_priorite', ascending=False)['prefecture'].head(8))}{'…' if len(dd) > 8 else ''}. "
            f"Elles rassemblent {fmt(dd['pop_2022'].sum())} habitants. Le mobile money ne semble donc pas avoir comblé le vide bancaire : il en reproduit la géographie.", "warn")

    # ---------------------------------------------------------------- concentration Grand Lomé
    st.markdown("---")
    tot = T_all
    gl = tot[tot["grand_lome"]]
    items = {"Population": (gl["pop_2022"].sum(), tot["pop_2022"].sum()),
             "Agents mobile money": (gl["agents_total"].sum(), tot["agents_total"].sum()),
             "Microfinance": (gl["fin_Micro-Finance"].sum(), tot["fin_Micro-Finance"].sum()),
             "Banques": (gl["fin_Banque"].sum(), tot["fin_Banque"].sum()),
             "Assurances": (gl["fin_Assurance"].sum(), tot["fin_Assurance"].sum())}
    shares = {k: (a / b * 100 if b else 0) for k, (a, b) in items.items()}
    message(f"Le Grand Lomé (Golfe + Agoè-Nyivé) abrite {fmt(shares['Population'], 0)} % de la population mais {fmt(shares['Assurances'], 0)} % des assurances",
            "Part du Grand Lomé dans le total national (%). Plus on monte dans la sophistication du service financier, plus la concentration est forte.")
    order = list(shares)
    fig = go.Figure(go.Bar(x=[shares[k] for k in order], y=order, orientation="h",
                           marker_color=[MUTED if k == "Population" else BLUE for k in order],
                           text=[f"{shares[k]:.0f} %" for k in order], textposition="outside", cliponaxis=False,
                           hovertemplate="<b>%{y}</b> : %{x:.1f} % au Grand Lomé<extra></extra>"))
    fig.update_yaxes(autorange="reversed"); fig.update_xaxes(range=[0, 100], ticksuffix=" %")
    st.plotly_chart(style_fig(fig, 280, legend=False), use_container_width=True, config={"displayModeBar": False})
    st.caption("Barre grise = poids démographique : tout écart au-dessus est une sur-représentation. Calcul sur le pays entier, hors filtres territoriaux.")

    # ---------------------------------------------------------------- agents par point financier
    st.markdown("---")
    ratio = T.dropna(subset=["agents_par_point_fin"]).nlargest(12, "agents_par_point_fin")
    message(f"Dans certaines préfectures, un point financier « sert » plus de {fmt(ratio['agents_par_point_fin'].iloc[0] // 10 * 10, 0)} agents mobile money",
            "Agents mobile money pour un point financier en service (banque, microfinance, assurance, mutuelle). Un ratio élevé signale une dépendance au mobile money faute d'alternative.")
    fig = go.Figure(go.Bar(x=ratio["agents_par_point_fin"], y=ratio["prefecture"], orientation="h", marker_color=ORANGE,
                           customdata=ratio[["agents_total", "fin_total", "pop_2022"]],
                           hovertemplate="<b>%{y}</b><br>%{x:.0f} agents par point financier<br>%{customdata[0]:,.0f} agents / %{customdata[1]:,.0f} points<br>Population : %{customdata[2]:,.0f}<extra></extra>"))
    fig.update_yaxes(autorange="reversed"); fig.update_xaxes(title="Agents mobile money par point financier")
    st.plotly_chart(style_fig(fig, 380, legend=False), use_container_width=True, config={"displayModeBar": False})
    zero = T[T["fin_total"] == 0]
    if len(zero):
        callout(f"<b>{', '.join(zero['prefecture'])} : ratio non défini, aucun point financier en service.</b> "
                f"{fmt(zero['agents_total'].sum())} agents mobile money y servent {fmt(zero['pop_2022'].sum())} habitants.", "warn")

    # ---------------------------------------------------------------- communes « mobile money seul »
    st.markdown("---")
    C = D["commune"].copy()
    a, f = core.selected_points()
    C["agents_total"] = C["commune"].map(a.groupby("commune").size()).fillna(0).astype(int)
    fb = f[f["categorie"].isin(["Banque", "Micro-Finance"])]
    C["fin_bancaire"] = C["commune"].map(fb.groupby("commune").size()).fillna(0).astype(int)
    m = C["region"].isin(core.regs())
    if st.session_state["f_prefs"]:
        m &= C["prefecture"].isin(st.session_state["f_prefs"])
    C = C[m]
    mm = C[(C["agents_total"] > 0) & (C["fin_bancaire"] == 0)].sort_values("pop_2022", ascending=False)
    message(f"{len(mm)} communes sont servies uniquement par le mobile money",
            "Communes où l'on compte des agents mais ni banque ni microfinance en service. C'est là que le mobile money est la seule porte d'entrée vers les services financiers.")
    if len(mm):
        show = mm[["commune", "prefecture", "region", "pop_2022", "agents_total", "fin_bancaire"]].rename(columns={
            "commune": "Commune", "prefecture": "Préfecture", "region": "Région", "pop_2022": "Population", "agents_total": "Agents MM", "fin_bancaire": "Banques + IMF"})
        st.dataframe(show, use_container_width=True, hide_index=True, height=min(420, 40 + 35 * len(show)))
        st.caption(f"Population concernée : {fmt(mm['pop_2022'].sum())} habitants. Les communes Danyi 1 et 2 n'ont pas de population séparée dans le RGPH-5 et apparaissent sans effectif.")
        core.download(show, "communes_mobile_money_seul.csv", key="dl_mmseul")
    else:
        callout("Aucune commune « mobile money seul » dans la sélection courante.", "ok")
