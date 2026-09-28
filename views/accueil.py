import plotly.graph_objects as go
import streamlit as st

import core
from core import D, fmt, pct, kpi, message, callout, style_fig, BLUE, ORANGE, AQUA, MUTED, INK2


def render():
    T = core.build_pref_table(use_filters=False)  # vue nationale, indépendante des filtres
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

    core.header("Le numérique et le mobile money au Togo : où l'accès manque encore", icon="📊")
    st.markdown(
        '<p class="lead">Ce tableau de bord répond à quatre questions : <b>l\'usage d\'Internet accélère-t-il ?</b> '
        '<b>Le mobile money remplace-t-il la banque ou la prolonge-t-il ?</b> <b>Où faut-il agir en premier ?</b> '
        '<b>Qui est physiquement loin d\'un point financier ?</b> '
        'Les chiffres ci-dessous sont nationaux ; les filtres à gauche s\'appliquent aux pages territoriales.</p>',
        unsafe_allow_html=True)

    c = st.columns(5)
    with c[0]: kpi("Usagers d'Internet (2022)", pct(net["pct_individus"]), "moins de 4 Togolais sur 10", BLUE, source="2022 · Banque mondiale", icon="📶")
    with c[1]: kpi("Population (RGPH-5)", fmt(pop), "39 préfectures, 117 communes", BLUE, source="2022 · INSEED", icon="👥")
    with c[2]: kpi("Agents mobile money", fmt(ag), f"{fmt(ag / pop * 1000, 1)} pour 1 000 habitants", ORANGE, source="2021/22 · Géodata Togo", icon="📱")
    with c[3]: kpi("Points financiers en service", fmt(fi), f"{fmt(fi / pop * 1e5, 1)} pour 100 000 habitants", AQUA, source="2025 · Géodata Togo", icon="🏦")
    with c[4]: kpi("Population à plus de 5 km d'un point financier", pct(part_loin, 0), f"{len(loin)} communes concernées", ORANGE, source="Calcul · centroïde communal", icon="📍")

    st.markdown("&nbsp;")
    st.markdown("### Les cinq messages à retenir")
    m1, m2 = st.columns(2)
    with m1:
        callout(f"<b>1. L'usage d'Internet a longtemps stagné, puis explosé.</b> Au plus 0,5 point de gain par an jusqu'en 2013, "
                f"puis {pct(net['pct_individus'])} en 2022, avec un pic de +{fmt(D['internet'].set_index('annee').loc[2020, 'gain_pts'], 1)} points en 2020. "
                "Les abonnements ont pourtant reculé en 2019 (3G) : la croissance n'est pas acquise.", "key")
        callout(f"<b>3. Le mobile money suit la banque au lieu de la remplacer.</b> Corrélation de rang entre densité d'agents et densité de points financiers : "
                f"ρ = {fmt(rho, 2)}. Là où il y a peu de banques, il y a aussi peu d'agents.", "key")
        callout(f"<b>5. La distance confirme le déficit, indépendamment des seuils de densité.</b> {pct(part_loin, 0)} de la population vit dans une commune dont le centroïde "
                f"est à plus de 5 km à vol d'oiseau du point financier le plus proche ({len(loin)} communes sur {len(C)}). "
                "Cet indicateur géographique s'ajoute aux ratios par habitant, il ne les remplace pas.", "key")
    with m2:
        callout(f"<b>2. Le Grand Lomé concentre l'offre.</b> {pct(part_pop * 100, 0)} de la population, mais {pct(part_ag * 100, 0)} des agents "
                f"et <b>{pct(part_fi * 100, 0)}</b> des points financiers en service.", "key")
        callout(f"<b>4. {len(dd)} préfectures sont sous la médiane nationale sur les deux axes</b> (agents et points financiers), "
                f"{len(zero_fin)} préfecture sans aucun point financier en service ({', '.join(zero_fin['prefecture'])}), "
                f"et {len(mm_seul)} n'est servie que par le mobile money.", "warn")
        callout("<b>Limites à garder en tête :</b> ce sont des points d'accès géolocalisés, pas des transactions ni des clients ; "
                "la distance est à vol d'oiseau depuis le centre de la commune, pas un temps de trajet réel. "
                "Détail complet : page « Méthode et qualité des données ».", "warn")

    message("Où l'accès est le plus faible : indice d'accès composite par préfecture",
            "Moyenne des rangs percentiles sur trois mesures : agents pour 1 000 habitants, points financiers pour 100 000 habitants, agents par km². 0 = moins bien servie, 100 = mieux servie.")
    cc = T.sort_values("indice_acces").head(12)
    fig = go.Figure(go.Bar(x=cc["indice_acces"], y=cc["prefecture"], orientation="h", marker_color=BLUE,
                           customdata=cc[["pop_2022", "agents_total", "fin_total"]],
                           hovertemplate="<b>%{y}</b><br>Indice d'accès : %{x:.1f}<br>Population : %{customdata[0]:,.0f}"
                                         "<br>Agents : %{customdata[1]:,.0f}<br>Points financiers : %{customdata[2]:,.0f}<extra></extra>"))
    fig.update_yaxes(autorange="reversed"); fig.update_xaxes(range=[0, 100], title="Indice d'accès (0-100)")
    st.plotly_chart(style_fig(fig, 380, legend=False), use_container_width=True, config={"displayModeBar": False})
    st.caption("Les 12 préfectures les moins bien servies sur 39. Détails, carte et communes : pages « Carte des accès » et « Mobile money et banque ».")

    st.markdown("### Comment lire ce tableau de bord")
    a, b, c3 = st.columns(3)
    with a:
        callout("<b>1 · L'état.</b> Usage d'Internet et marché télécom : où en est-on, et quand les ruptures ont-elles eu lieu ?")
    with b:
        callout("<b>2 · Où et pourquoi.</b> Carte des accès, puis lien entre mobile money et banque dans chaque préfecture.")
    with c3:
        callout("<b>3 · Que faire.</b> Score de priorité réglable et recommandations chiffrées, exportables.")
