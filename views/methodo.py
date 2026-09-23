import pandas as pd
import streamlit as st

import core
from core import D, fmt, message, callout


def render():
    st.title("Méthode et qualité des données")
    st.markdown('<p class="lead">Ce qui a été mesuré, comment, avec quelles hypothèses, et ce que les données ne permettent pas de dire.</p>', unsafe_allow_html=True)
    c = D["controles"]

    st.markdown("### Contrôles automatiques")
    checks = [
        ("Somme des populations préfectorales = population nationale", c["population_somme_prefectures"] == c["population_total_fichier"],
         f"{fmt(c['population_somme_prefectures'])} = {fmt(c['population_total_fichier'])}"),
        ("Tous les agents mobile money rattachés à une préfecture", c["agents_par_prefecture_somme"] == c["agents_total"],
         f"{fmt(c['agents_par_prefecture_somme'])} / {fmt(c['agents_total'])}"),
        ("Préfecture du fichier = préfecture du polygone (agents)", c["agents_pref_concordance_texte_vs_polygone"] > 0.99,
         f"{fmt(c['agents_pref_concordance_texte_vs_polygone'] * 100, 2)} % de concordance ; {c['agents_hors_polygone']} points hors polygone (frontières)"),
        ("Communes du fond de carte identifiées", c["communes_nommees"] == c["communes_polygones"],
         f"{c['communes_nommees']} / {c['communes_polygones']} (pureté minimale {fmt(c['communes_purete_min'] * 100, 0)} %)"),
        ("Communes avec population séparée", c["communes_avec_population"] >= 115, f"{c['communes_avec_population']} / {c['communes_polygones']} (Danyi 1 et 2 fusionnées dans le RGPH-5)"),
        ("Établissements financiers en service", True, f"{fmt(c['finance_total_lignes'])} lignes, {fmt(c['finance_hors_service_exclus'])} exclues (fermé, abandonné, en construction, inachevé)"),
    ]
    st.dataframe(pd.DataFrame([{"Contrôle": a, "Résultat": "✔" if ok else "✘", "Détail": d} for a, ok, d in checks]), use_container_width=True, hide_index=True)

    st.markdown("### Définitions des indicateurs")
    st.dataframe(pd.DataFrame([
        ("Habitants par agent", "Population 2022 ÷ nombre d'agents mobile money géolocalisés"),
        ("Points financiers pour 100 000 hab.", "Banques, microfinance, assurances et mutuelles en service ÷ population × 100 000"),
        ("Agents par point financier", "Agents mobile money ÷ points financiers en service (non défini si aucun point)"),
        ("Mobile money seul", "Zone avec au moins un agent mais ni banque ni microfinance en service"),
        ("Indice d'accès (0-100)", "Moyenne des rangs percentiles de trois mesures : agents/1 000 hab., points financiers/100 000 hab., agents/km². Repère relatif entre préfectures, pas un niveau absolu"),
        ("Double désavantage", "Sous la médiane nationale à la fois pour les agents et pour les points financiers"),
        ("Agents / points financiers manquants", "Nombre à ajouter pour atteindre la densité médiane nationale (arrondi au supérieur)"),
        ("Score de priorité (0-100)", "Moyenne pondérée (réglable) de : 100 − indice d'accès, rang percentile des agents manquants, rang percentile des points financiers manquants"),
        ("CA par abonné", "Chiffre d'affaires ÷ abonnés fixe + mobile (calcul propre, l'ARPU du fichier est inexploitable)"),
    ], columns=["Indicateur", "Définition"]), use_container_width=True, hide_index=True)

    st.markdown("### Hypothèses et limites")
    for t in [
        "<b>Accès, pas usage.</b> Un agent ou une agence est un point d'accès géolocalisé ; les données ne donnent ni transactions, ni comptes, ni clients. Un ratio faible signale une offre rare, pas forcément une demande non satisfaite.",
        "<b>Population.</b> RGPH-5 2022. La population est répartie par préfecture et par commune ; les distances (temps de trajet) ne sont pas modélisées. Régions Géodata (5) : le Grand Lomé est inclus dans Maritime, alors que le RGPH-5 le publie à part.",
        "<b>Établissements financiers.</b> 13 lignes fermées, abandonnées, en construction ou inachevées sont exclues par défaut (case à décocher dans les filtres). Le statut « Néant » (50 lignes) est conservé : sa signification n'est pas documentée.",
        "<b>Agents mobile money.</b> 12 649 agents (64 %) portent les deux opérateurs ; 1 348 (7 %) n'ont pas d'opérateur renseigné. Le type de service, le genre et la date d'entrée figurent au dictionnaire mais pas dans le fichier fourni.",
        "<b>Internet.</b> La série Banque mondiale compte des individus ; la série sur les abonnés compte des abonnements. Les deux ne sont pas additionnables et ne sont pas comparables en niveau (voir la page Usage d'Internet).",
        "<b>Séries télécom.</b> Deux opérateurs, 2013-2019. Certaines lignes sont manquantes (4G d'Atlantique Telecom en 2018-2019, EvDo, Illiconet) et sont traitées comme non déclarées, pas comme zéro. L'ARPU du fichier n'est pas utilisé (unité aberrante).",
        "<b>Rupture 2016.</b> La 3G passe de 0,43 M à 1,44 M d'abonnés alors que la 2G s'effondre : partie de ce mouvement est un reclassement, pas un basculement d'usage.",
        "<b>Aucune donnée régionale sur Internet.</b> L'usage d'Internet n'est disponible qu'au niveau national ; l'analyse territoriale repose sur les points d'accès (agents, banques).",
        "<b>Corrélation.</b> ρ de Spearman calculé sur 39 préfectures : c'est une association entre densités, pas une causalité (erreur écologique possible).",
    ]:
        st.markdown(f'<div class="callout">{t}</div>', unsafe_allow_html=True)

    st.markdown("### Problèmes rencontrés dans les données sources et traitements appliqués")
    st.dataframe(pd.DataFrame([
        ("Population", "« Avé » apparaît sous « TOTOAL AVE »", "Alias explicite dans la reconstruction de la hiérarchie"),
        ("Population", "14 libellés en double (ex. « CINKASSE » préfecture et canton)", "Préfecture = première occurrence ; jointure par hiérarchie, pas par nom seul"),
        ("Population", "Numérotation de communes erronée (« AMOU 2 » deux fois, « BINAH2 »)", "Communes numérotées dans l'ordre d'apparition"),
        ("Population", "« DANYI 1+DANYI 2 » agrégées", "Exclues des ratios communaux ; incluses au niveau préfecture"),
        ("Financier", "Faute « Micro-Finace », statuts hétérogènes", "Normalisation ; statuts hors service exclus"),
        ("Marché", "ARPU en unité aberrante (~3×10¹³)", "Non utilisé ; CA/abonné recalculé"),
        ("Fonds de carte", "Communes sans nom", "Nom déduit par jointure spatiale avec les agents (pureté ≥ 89 %)"),
    ], columns=["Jeu", "Problème", "Traitement"]), use_container_width=True, hide_index=True)

    st.markdown("### Reproductibilité")
    st.markdown("Le dépôt contient les données brutes, les scripts (`scripts/01_build_reference.py`) et ce tableau de bord. "
                "`python scripts/01_build_reference.py` régénère toutes les tables ; `streamlit run app.py` lance le tableau de bord.")
    with st.expander("Sources des jeux de données"):
        st.markdown("- Usage d'Internet : Banque mondiale, individus utilisant Internet (% de la population), 1996-2022\n"
                    "- Abonnés Internet par type d'accès, technologie et opérateur, 2013-2019 (Togo AI Lab / ARCEP)\n"
                    "- Marché de la téléphonie mobile, 2013-2019 (Togo AI Lab / ARCEP)\n"
                    "- Institutions financières géolocalisées (Géodata Togo, export du 08/01/2025)\n"
                    "- Agents mobile money géolocalisés (Géodata Togo, export du 19/12/2024)\n"
                    "- Population résidente 2022, RGPH-5 (INSEED)\n"
                    "- Limites administratives : Géodata Togo (préfectures nommées, communes nommées par jointure spatiale)")
