import plotly.graph_objects as go
import streamlit as st

import core
from core import D, fmt, pct, kpi, message, style_fig, BLUE, ORANGE, AQUA


def _insight_card(title, body, kind="info"):
    return f'''<article class="insight-card {kind}">
        <div class="insight-title">{title}</div>
        <div class="insight-body">{body}</div>
    </article>'''


def render():
    T = core.build_pref_table(use_filters=False)
    C = core.build_commune_table(use_filters=False)
    pop = T["pop_2022"].sum(); ag = T["agents_total"].sum(); fi = T["fin_total"].sum()
    net = D["internet"].iloc[-1]
    rho = core.spearman(T["agents_pour_1000hab"], T["fin_pour_100000hab"])
    gl = T[T["grand_lome"]]
    part_pop, part_ag, part_fi = gl["pop_2022"].sum() / pop, gl["agents_total"].sum() / ag, gl["fin_total"].sum() / fi
    dd = T[T["double_desavantage"]]
    mm_seul = T[T["mm_seul"]]
    zero_fin = T[T["fin_total"] == 0]
    loin = C[C["dist_fin_km"] > 5]
    part_loin = loin["pop_2022"].sum() / C["pop_2022"].sum() * 100

    core.header(
        "Inclusion numérique et financière du Togo",
        lead="État des usages, de l’offre de services et des écarts territoriaux.",
        icon="",
    )

    st.markdown(
        '<div class="overview-intro">'
        '<span class="overview-intro-label">À retenir</span>'
        '<span>L’usage d’Internet progresse, mais l’accès aux services financiers reste inégal selon les territoires.</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="eyebrow">INDICATEURS NATIONAUX</div>', unsafe_allow_html=True)
    kpis = [
        ("Usagers d’Internet", pct(net["pct_individus"]), "moins de 4 Togolais sur 10", BLUE, "2022 · Banque mondiale"),
        ("Population", fmt(pop), "39 préfectures · 117 communes", BLUE, "2022 · INSEED"),
        ("Agents mobile money", fmt(ag), f"{fmt(ag / pop * 1000, 1)} pour 1 000 habitants", ORANGE, "2021/22 · Géodata Togo"),
        ("Points financiers", fmt(fi), f"{fmt(fi / pop * 1e5, 1)} pour 100 000 habitants", AQUA, "2025 · Géodata Togo"),
    ]
    cards = []
    for label, value, note, color, source in kpis:
        cards.append(
            f'<article class="kpi" style="border-left-color:{color}">'
            f'<div class="kpi-l">{label}</div>'
            f'<div class="kpi-v">{value}</div>'
            f'<div class="kpi-n">{note}</div>'
            f'<div class="kpi-src">{source}</div>'
            f'</article>'
        )
    st.markdown('<div class="kpi-grid">' + "".join(cards) + '</div>', unsafe_allow_html=True)

    st.markdown(
        f'''<div class="territory-signal">
            <div class="territory-stat">
                <div class="territory-label">INDICATEUR TERRITORIAL</div>
                <div class="territory-value">{pct(part_loin, 0)}</div>
            </div>
            <div class="territory-copy">
                <div><strong>{pct(part_loin, 0)} de la population</strong> vit dans une commune dont le centroïde est à plus de 5 km d’un point financier.</div>
                <div class="territory-note">{len(loin)} communes concernées · calcul à partir des centroïdes communaux</div>
            </div>
            <div class="territory-badge">ACCÈS PHYSIQUE</div>
        </div>''',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-head">'
        '<div><div class="eyebrow">LECTURE RAPIDE</div>'
        '<div class="section-title">Les principaux constats</div>'
        '<div class="section-subtitle">Cinq résultats structurants pour comprendre la situation nationale et territoriale.</div></div>'
        '</div>',
        unsafe_allow_html=True,
    )

    insights = [
        (
            "Usage d’Internet",
            f"L’usage a longtemps progressé lentement, puis fortement accéléré. En 2022, <strong>{pct(net['pct_individus'])}</strong> de la population utilise Internet, avec un pic de +{fmt(D['internet'].set_index('annee').loc[2020, 'gain_pts'], 1)} points en 2020.",
            "info",
        ),
        (
            "Complémentarité des réseaux",
            f"Le mobile money ne remplace pas simplement le réseau financier : la corrélation de rang entre densité d’agents et densité de points financiers est de <strong>ρ = {fmt(rho, 2)}</strong>.",
            "info",
        ),
        (
            "Concentration du Grand Lomé",
            f"Le Grand Lomé représente {pct(part_pop * 100, 0)} de la population, mais concentre {pct(part_ag * 100, 0)} des agents et <strong>{pct(part_fi * 100, 0)}</strong> des points financiers en service.",
            "info",
        ),
        (
            "Territoires en déficit",
            f"<strong>{len(dd)} préfectures</strong> sont sous la médiane nationale sur les deux axes (agents et points financiers). {len(zero_fin)} préfecture(s) ne disposent d’aucun point financier en service, et {len(mm_seul)} sont servies uniquement par le mobile money.",
            "warning",
        ),
        (
            "Accès physique",
            f"<strong>{pct(part_loin, 0)}</strong> de la population vit dans une commune dont le centroïde est à plus de 5 km du point financier le plus proche ({len(loin)} communes sur {len(C)}).",
            "info",
        ),
        (
            "Limites de lecture",
            "Les indicateurs portent sur les points d’accès géolocalisés, et non sur les transactions ou les clients. La distance est calculée à vol d’oiseau depuis le centre de la commune, et non selon le temps réel de trajet.",
            "neutral",
        ),
    ]
    st.markdown(
        '<div class="insights-grid">' + ''.join(_insight_card(*x) for x in insights) + '</div>',
        unsafe_allow_html=True,
    )

    message(
        "Où l’accès est le plus faible",
        "Indice composite par préfecture : moyenne des rangs percentiles sur trois mesures d’accès. 0 = moins bien servie, 100 = mieux servie.",
    )
    cc = T.sort_values("indice_acces").head(12)
    fig = go.Figure(
        go.Bar(
            x=cc["indice_acces"],
            y=cc["prefecture"],
            orientation="h",
            marker_color=BLUE,
            customdata=cc[["pop_2022", "agents_total", "fin_total"]],
            hovertemplate=(
                "<b>%{y}</b><br>Indice d'accès : %{x:.1f}<br>Population : %{customdata[0]:,.0f}"
                "<br>Agents : %{customdata[1]:,.0f}<br>Points financiers : %{customdata[2]:,.0f}<extra></extra>"
            ),
        )
    )
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(range=[0, 100], title="Indice d'accès (0–100)")
    st.plotly_chart(
        style_fig(fig, 380, legend=False, margin=dict(l=8, r=8, t=8, b=8)),
        use_container_width=True,
        config={"displayModeBar": False},
    )
    st.caption("Les 12 préfectures les moins bien servies sur 39. Voir les détails dans « Carte des accès » et « Mobile money et banque ».")

    st.markdown(
        '<div class="section-head compact">'
        '<div><div class="eyebrow">EXPLORER</div>'
        '<div class="section-title">Parcours du tableau de bord</div>'
        '<div class="section-subtitle">Trois étapes pour passer du constat aux priorités territoriales.</div></div>'
        '</div>',
        unsafe_allow_html=True,
    )
    steps = [
        ("01", "État des usages", "Internet et marché télécom : évolution des usages, abonnements et investissements."),
        ("02", "Écarts territoriaux", "Carte des accès et complémentarité entre mobile money et réseau financier."),
        ("03", "Priorités", "Score de priorité, communes éloignées et recommandations chiffrées exportables."),
    ]
    st.markdown(
        '<div class="steps-grid">' + ''.join(
            f'<div class="step-card"><div class="step-no">{n}</div><div><div class="step-title">{t}</div><div class="step-text">{d}</div></div></div>'
            for n, t, d in steps
        ) + '</div>',
        unsafe_allow_html=True,
    )
