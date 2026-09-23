import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import core
from core import D, fmt, pct, message, callout, style_fig, BLUE, ORANGE, MUTED


def _recos(T, dec, it, pa, m):
    """Recommandations chiffrées, construites à partir des données (les chiffres se mettent à jour)."""
    top = T.nlargest(5, "score_priorite")
    zero_fin = T[T["fin_total"] == 0]
    no_bank = T[T["fin_bancaire"] == 0]
    dd = T[T["double_desavantage"]]
    zero_ass = T[T["fin_Assurance"] == 0]
    tot = pa["T abonnés Internet Fixe et Mobile (Toutes technologies)"]
    d3 = dec["3G"]
    subs = m["Le nombre total d'abonnés fixe et mobile"]; ca = m["Chiffres d'Affaires"]
    ca_ab = ca / subs
    pen = pa["Taux de pénétration Internet (Toutes technologies) (%)"]
    Cm = D["commune"]
    a, f = core.selected_points(False)
    Ct = Cm.copy()
    Ct["fin_bancaire"] = Ct["commune"].map(f[f["categorie"].isin(["Banque", "Micro-Finance"])].groupby("commune").size()).fillna(0)
    Ct["agents_total"] = Ct["commune"].map(a.groupby("commune").size()).fillna(0)
    mmc = Ct[(Ct["agents_total"] > 0) & (Ct["fin_bancaire"] == 0)]
    nag_ndef = int((D["agents"]["operateur"] == "Non renseigné").sum())
    R = [
        dict(id="R1", theme="Mobile money", priorite="Haute", titre="Combler le déficit d'agents dans les préfectures les moins dotées",
             cible=", ".join(top["prefecture"]),
             chiffre=f"{fmt(dd['agents_manquants'].sum())} agents manquants pour amener les {len(dd)} préfectures en double désavantage à la médiane nationale ({fmt(T.attrs['med_a'], 2)} agents pour 1 000 hab.) ; {fmt(top['agents_manquants'].sum())} dans les 5 premières.",
             action="Recruter et former des agents dans les zones ciblées, avec exigence de liquidité minimale, en lien avec les deux opérateurs.",
             indicateur="Agents pour 1 000 habitants par préfecture ; habitants par agent.", horizon="12 mois"),
        dict(id="R2", theme="Inclusion financière", priorite="Haute", titre="Faire des agents mobile money des points d'accès bancaire (agent banking)",
             cible=", ".join(no_bank["prefecture"]) if len(no_bank) else "Préfectures sans banque ni IMF",
             chiffre=f"{len(no_bank)} préfecture(s) sans banque ni microfinance en service ; {fmt(no_bank['agents_total'].sum())} agents mobile money y sont déjà présents pour {fmt(no_bank['pop_2022'].sum())} habitants.",
             action="Autoriser et outiller les agents existants pour l'ouverture de comptes, dépôts et retraits au nom d'une banque ou d'une IMF partenaire.",
             indicateur="Comptes ouverts via agents ; points de service financiers par 100 000 habitants.", horizon="12-24 mois"),
        dict(id="R3", theme="Inclusion financière", priorite="Haute", titre="Raccorder les communes servies uniquement par le mobile money",
             cible=", ".join(mmc.nlargest(6, "pop_2022")["commune"]) + ("…" if len(mmc) > 6 else ""),
             chiffre=f"{len(mmc)} communes ont des agents mais ni banque ni IMF ({fmt(mmc['pop_2022'].sum())} habitants).",
             action="Installer une permanence de microfinance itinérante ou un guichet partagé, en priorité dans les communes les plus peuplées de la liste.",
             indicateur="Nombre de communes sans point bancaire ni IMF.", horizon="18 mois"),
        dict(id="R4", theme="Internet", priorite="Haute", titre="Enrayer le retour de la 3G vers la 2G et accélérer la 4G",
             cible="Opérateurs mobiles ; priorité aux préfectures sous la médiane d'accès",
             chiffre=f"En 2019 la 3G recule de {fmt(-(d3.loc[2019] / d3.loc[2018] - 1) * 100, 0)} % alors que la 2G augmente ; la 4G ne pèse que {fmt(dec['4G'].loc[2019] / dec.loc[2019].sum() * 100, 1)} % des abonnements.",
             action="Fixer des obligations de couverture 3G/4G par préfecture dans les licences, mutualiser les sites, mesurer l'expérience réelle (débit, prix des données).",
             indicateur="Part des abonnements 3G+4G ; couverture 4G par préfecture.", horizon="24 mois"),
        dict(id="R5", theme="Internet", priorite="Moyenne", titre="Financer l'extension du réseau là où le marché ne la finance pas",
             cible="Zones rurales à faible densité",
             chiffre=f"Le chiffre d'affaires par abonné baisse de {fmt(-(ca_ab.loc[2019] / ca_ab.loc[2013] - 1) * 100, 0)} % (2013-2019) alors que les abonnés augmentent de {fmt((subs.loc[2019] / subs.loc[2013] - 1) * 100, 0)} %.",
             action="Activer un fonds de service universel, du partage d'infrastructures et des incitations fiscales conditionnées à la couverture des zones peu denses.",
             indicateur="Investissement par habitant hors Grand Lomé.", horizon="24 mois"),
        dict(id="R6", theme="Inclusion financière", priorite="Moyenne", titre="Diffuser la micro-assurance via le mobile money",
             cible=f"{len(zero_ass)} préfectures sans assurance recensée",
             chiffre=f"{fmt(T[T['grand_lome']]['fin_Assurance'].sum() / max(T['fin_Assurance'].sum(), 1) * 100, 0)} % des assurances sont au Grand Lomé ; {len(zero_ass)} préfectures n'en comptent aucune.",
             action="Proposer des produits d'assurance simples (santé, agricole) souscrits et payés par mobile money, distribués par les agents.",
             indicateur="Souscripteurs hors Grand Lomé.", horizon="18-36 mois"),
        dict(id="R7", theme="Données et pilotage", priorite="Moyenne", titre="Piloter par l'usage réel, pas par les abonnements",
             cible="Régulateur, INSEED, ministère",
             chiffre=f"2019 : {fmt(pen.loc[2019], 1)} abonnements pour 100 habitants contre {fmt(it.loc[2019, 'pct_individus'], 1)} % d'utilisateurs.",
             action="Retenir la part d'individus utilisant Internet comme cible nationale et l'estimer par région via une enquête ménages annuelle.",
             indicateur="% d'individus utilisant Internet, par région et par sexe.", horizon="12 mois"),
        dict(id="R8", theme="Données et pilotage", priorite="Moyenne", titre="Tenir un registre national des agents et publier les données d'usage",
             cible="Opérateurs, Togo AI Lab",
             chiffre=f"{fmt(nag_ndef)} agents ({fmt(nag_ndef / len(D['agents']) * 100, 0)} %) sans opérateur renseigné ; ni service proposé ni volume de transactions dans les données ouvertes.",
             action="Publier trimestriellement agents actifs, services, transactions et prix, par commune, en données ouvertes.",
             indicateur="Complétude du registre ; agents actifs par commune.", horizon="12 mois"),
    ]
    return pd.DataFrame(R)


def render():
    st.title("Priorités et recommandations")
    st.markdown('<p class="lead">Un score de priorité réglable désigne les préfectures où agir en premier ; huit recommandations chiffrées en découlent. '
                'Le classement s\'appuie sur les filtres opérateur et type d\'établissement de la barre latérale.</p>', unsafe_allow_html=True)

    with st.expander("Régler le score de priorité", expanded=False):
        st.caption("Le score (0-100) combine trois composantes ; changez les poids pour tester la robustesse du classement.")
        c = st.columns(3)
        w1 = c[0].slider("Faible indice d'accès", 0, 100, 50, key="w1", help="100 − indice d'accès composite (agents/hab., points financiers/hab., agents/km²)")
        w2 = c[1].slider("Agents manquants", 0, 100, 25, key="w2", help="Agents à ajouter pour atteindre la densité médiane nationale (rang percentile)")
        w3 = c[2].slider("Points financiers manquants", 0, 100, 25, key="w3", help="Points financiers à ajouter pour atteindre la densité médiane nationale (rang percentile)")
        if w1 + w2 + w3 == 0:
            st.warning("Au moins un poids doit être non nul."); w1 = 1
    T_all = core.build_pref_table((w1, w2, w3))
    T = core.visible(T_all)

    top = T.sort_values("score_priorite", ascending=False)
    message(f"Les cinq préfectures à traiter en premier : {', '.join(top['prefecture'].head(5))}",
            "Score de priorité (0-100, plus haut = plus urgent) dans la sélection courante.")
    t15 = top.head(15)
    fig = go.Figure(go.Bar(x=t15["score_priorite"], y=t15["prefecture"], orientation="h", marker_color=BLUE,
                           customdata=t15[["pop_2022", "agents_manquants", "points_fin_manquants", "indice_acces"]],
                           hovertemplate="<b>%{y}</b><br>Score : %{x:.1f}<br>Population : %{customdata[0]:,.0f}<br>Agents manquants : %{customdata[1]:,.0f}"
                                         "<br>Points financiers manquants : %{customdata[2]:,.0f}<br>Indice d'accès : %{customdata[3]:.1f}<extra></extra>"))
    fig.update_yaxes(autorange="reversed"); fig.update_xaxes(range=[0, 100], title="Score de priorité")
    st.plotly_chart(style_fig(fig, 460, legend=False), use_container_width=True, config={"displayModeBar": False})

    # ---------------------------------------------------------------- simulateur
    st.markdown("---")
    message("Simulateur : combien d'agents pour atteindre un objectif de densité ?",
            "Choisissez une densité cible ; le tableau donne l'effort par préfecture dans la sélection courante.")
    a_max = float(T_all["agents_pour_1000hab"].quantile(0.75))
    tgt = st.slider("Objectif : agents mobile money pour 1 000 habitants", 1.0, round(a_max + 1, 1), float(round(T_all.attrs["med_a"], 2)), 0.05, key="sim_target")
    need = np.ceil(np.clip(tgt * T["pop_2022"] / 1000 - T["agents_total"], 0, None)).astype(int)
    sim = T.assign(agents_a_ajouter=need)[["prefecture", "region", "pop_2022", "agents_total", "agents_pour_1000hab", "agents_a_ajouter"]].sort_values("agents_a_ajouter", ascending=False)
    k1, k2, k3 = st.columns(3)
    with k1: core.kpi("Agents à ajouter", fmt(need.sum()), f"pour {fmt(tgt, 2)} agents / 1 000 hab. partout", ORANGE)
    with k2: core.kpi("Préfectures concernées", f"{int((need > 0).sum())} / {len(T)}", "sous l'objectif", BLUE)
    with k3: core.kpi("Effort relatif", pct(need.sum() / max(T["agents_total"].sum(), 1) * 100, 1), "de plus que le parc actuel de la sélection", BLUE)
    show = sim.rename(columns={"prefecture": "Préfecture", "region": "Région", "pop_2022": "Population", "agents_total": "Agents actuels",
                               "agents_pour_1000hab": "Agents / 1 000 hab.", "agents_a_ajouter": "Agents à ajouter"}).round(2)
    st.dataframe(show[show["Agents à ajouter"] > 0], use_container_width=True, hide_index=True, height=300)
    core.download(show, "simulateur_agents.csv", key="dl_sim")

    # ---------------------------------------------------------------- recommandations
    st.markdown("---")
    st.markdown("## Recommandations")
    dec = core.mobile_decomposition(); it = D["internet"].set_index("annee"); pa = core.ab_pivot(); m = core.mk_pivot()
    R = _recos(T_all, dec, it, pa, m)
    f1, f2 = st.columns(2)
    themes = f1.multiselect("Thème", sorted(R["theme"].unique()), default=sorted(R["theme"].unique()), key="reco_theme")
    prios = f2.multiselect("Priorité", ["Haute", "Moyenne"], default=["Haute", "Moyenne"], key="reco_prio")
    Rf = R[R["theme"].isin(themes) & R["priorite"].isin(prios)]
    for _, r in Rf.iterrows():
        tag = "h" if r["priorite"] == "Haute" else "m"
        st.markdown(
            f'<div class="reco"><span class="tag {tag}">Priorité {r["priorite"].lower()}</span><span class="tag b">{r["theme"]}</span>'
            f'<span style="color:#8a8983;font-size:.8rem">{r["id"]} · horizon {r["horizon"]}</span>'
            f'<h4>{r["titre"]}</h4><p class="big">{r["chiffre"]}</p><p><b>Où :</b> {r["cible"]}</p>'
            f'<p><b>Action :</b> {r["action"]}</p><p><b>Indicateur de suivi :</b> {r["indicateur"]}</p></div>', unsafe_allow_html=True)
    core.download(Rf.rename(columns={"id": "Réf.", "theme": "Thème", "priorite": "Priorité", "titre": "Recommandation", "cible": "Cible", "chiffre": "Chiffre clé",
                                     "action": "Action", "indicateur": "Indicateur", "horizon": "Horizon"}), "recommandations.csv", "Exporter les recommandations (CSV)", key="dl_reco")
    callout("Les recommandations se fondent sur des <b>points d'accès</b> et des <b>séries agrégées</b> : elles indiquent où l'offre est faible, "
            "pas où la demande est la plus forte. Aucun coût unitaire n'est supposé ; un chiffrage financier suppose des données opérateurs.", "info")

    with st.expander("Classement complet des préfectures"):
        cols = ["prefecture", "region", "pop_2022", "agents_total", "fin_total", "hab_par_agent", "indice_acces", "agents_manquants", "points_fin_manquants", "score_priorite"]
        full = top[cols].round(1).rename(columns={"prefecture": "Préfecture", "region": "Région", "pop_2022": "Population", "agents_total": "Agents",
                                                  "fin_total": "Points financiers", "hab_par_agent": "Hab./agent", "indice_acces": "Indice d'accès",
                                                  "agents_manquants": "Agents manquants", "points_fin_manquants": "Points fin. manquants", "score_priorite": "Score"})
        st.dataframe(full, use_container_width=True, hide_index=True)
        core.download(full, "classement_prefectures.csv", key="dl_rank")
