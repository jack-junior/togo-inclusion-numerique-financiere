import plotly.graph_objects as go
import streamlit as st

import core
from core import D, fmt, pct, message, callout, style_fig, BLUE, ORANGE, AQUA, MUTED


def _line(x, y, color, name, hover, height=280, yfmt=None, bar=False):
    fig = go.Figure()
    if bar:
        fig.add_trace(go.Bar(x=x, y=y, marker_color=color, name=name, hovertemplate=hover))
    else:
        fig.add_trace(go.Scatter(x=x, y=y, mode="lines+markers", line=dict(color=color, width=2.5), name=name,
                                 marker=dict(size=7, line=dict(color="white", width=1.5)), hovertemplate=hover))
    fig.update_xaxes(dtick=1); fig.update_yaxes(rangemode="tozero")
    return style_fig(fig, height, legend=False)


def render():
    st.title("Marché télécom : plus d'abonnés, mais un chiffre d'affaires qui stagne")
    st.markdown('<p class="lead">Deux opérateurs (Togo Cellulaire / Togocom et Atlantique Telecom / Moov), 2013-2019. '
                'Les séries s\'arrêtent en 2019 : aucune conclusion n\'est possible sur la période récente.</p>', unsafe_allow_html=True)
    m = core.mk_pivot()
    yrs = m.index
    ca = m["Chiffres d'Affaires"] / 1e9
    inv = m["Investissement"] / 1e9
    subs = m["Le nombre total d'abonnés fixe et mobile"]
    ca_ab = m["Chiffres d'Affaires"] / subs
    tel = m["Télédensité mobile GSM"]
    parts_tc = m["Part de marché Togo Cellulaire (en abonnées) en %"]
    parts_at = m["Part de marché Atlantique Telecom Togo (en abonnées)"]

    c = st.columns(4)
    with c[0]: core.kpi("Abonnés fixe + mobile 2019", fmt(subs.loc[2019] / 1e6, 2) + " M", f"+{fmt((subs.loc[2019] / subs.loc[2013] - 1) * 100, 0)} % depuis 2013", BLUE)
    with c[1]: core.kpi("Chiffre d'affaires 2019", fmt(ca.loc[2019], 1) + " Mds FCFA", f"{fmt((ca.loc[2019] / ca.loc[2013] - 1) * 100, 1)} % depuis 2013", ORANGE)
    with c[2]: core.kpi("CA par abonné 2019", fmt(ca_ab.loc[2019]) + " FCFA", f"{fmt((ca_ab.loc[2019] / ca_ab.loc[2013] - 1) * 100, 0)} % depuis 2013", ORANGE)
    with c[3]: core.kpi("Télédensité mobile 2019", pct(tel.loc[2019]), "≈ 82 lignes pour 100 habitants", AQUA)

    a, b = st.columns(2)
    with a:
        message(f"Les abonnés ont progressé de {fmt((subs.loc[2019] / subs.loc[2013] - 1) * 100, 0)} %, le chiffre d'affaires de {fmt((ca.loc[2019] / ca.loc[2013] - 1) * 100, 1)} %",
                "Chiffre d'affaires total du secteur (milliards de FCFA).")
        st.plotly_chart(_line(yrs, ca, ORANGE, "Chiffre d'affaires", "<b>%{x}</b> : %{y:.1f} Mds FCFA<extra></extra>"),
                        use_container_width=True, config={"displayModeBar": False})
    with b:
        message(f"Chaque abonné rapporte {fmt(-(ca_ab.loc[2019] / ca_ab.loc[2013] - 1) * 100, 0)} % de moins qu'en 2013",
                "Chiffre d'affaires divisé par le nombre d'abonnés fixe + mobile (FCFA par abonné et par an) : calcul propre, voir la note sur l'ARPU.")
        st.plotly_chart(_line(yrs, ca_ab, ORANGE, "CA par abonné", "<b>%{x}</b> : %{y:,.0f} FCFA par abonné<extra></extra>"),
                        use_container_width=True, config={"displayModeBar": False})

    a, b = st.columns(2)
    with a:
        best = inv.idxmax()
        message(f"L'investissement a culminé en {best} ({fmt(inv.loc[best], 1)} Mds FCFA)",
                "Investissement des opérateurs (milliards de FCFA). Irrégulier : 19 Mds en 2014, 68 Mds en 2018.")
        st.plotly_chart(_line(yrs, inv, BLUE, "Investissement", "<b>%{x}</b> : %{y:.1f} Mds FCFA<extra></extra>", bar=True),
                        use_container_width=True, config={"displayModeBar": False})
    with b:
        intens = inv / ca * 100
        message(f"En {intens.idxmax()}, les opérateurs ont réinvesti {fmt(intens.max(), 0)} % de leur chiffre d'affaires",
                "Investissement rapporté au chiffre d'affaires (%). Un indicateur de l'effort de modernisation du réseau.")
        st.plotly_chart(_line(yrs, intens, BLUE, "Intensité", "<b>%{x}</b> : %{y:.0f} % du CA<extra></extra>"),
                        use_container_width=True, config={"displayModeBar": False})

    a, b = st.columns(2)
    with a:
        message("Parts de marché : un duopole équilibré, sauf en 2018",
                "Part des abonnés (%). Atlantique Telecom dépasse 55 % en 2018 puis retombe à 48,6 % : rupture de série probable, à vérifier auprès du régulateur.")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=yrs, y=parts_tc, name="Togo Cellulaire (Togocom)", mode="lines+markers", line=dict(color=BLUE, width=2.5),
                                 marker=dict(size=7, line=dict(color="white", width=1.5)), hovertemplate="<b>%{x}</b> Togo Cellulaire : %{y:.1f} %<extra></extra>"))
        fig.add_trace(go.Scatter(x=yrs, y=parts_at, name="Atlantique Telecom (Moov)", mode="lines+markers", line=dict(color=ORANGE, width=2.5),
                                 marker=dict(size=7, line=dict(color="white", width=1.5)), hovertemplate="<b>%{x}</b> Atlantique Telecom : %{y:.1f} %<extra></extra>"))
        fig.update_yaxes(range=[35, 65], ticksuffix=" %"); fig.update_xaxes(dtick=1)
        st.plotly_chart(style_fig(fig, 300), use_container_width=True, config={"displayModeBar": False})
    with b:
        message(f"La télédensité mobile plafonne autour de {fmt(tel.loc[2019], 0)} lignes pour 100 habitants",
                "Lignes mobiles GSM pour 100 habitants. Un plafond du nombre de lignes ne signifie pas un plafond d'usage : une même personne peut en posséder plusieurs.")
        st.plotly_chart(_line(yrs, tel, AQUA, "Télédensité", "<b>%{x}</b> : %{y:.1f} lignes pour 100 hab.<extra></extra>"),
                        use_container_width=True, config={"displayModeBar": False})

    callout("<b>Ce que cela signifie.</b> Le marché a crû en volume (abonnés) sans croître en valeur (chiffre d'affaires) : la marge de manœuvre "
            "des opérateurs pour financer l'extension du réseau vers les zones peu denses est limitée. Sans mesure d'accompagnement "
            "(partage d'infrastructures, fonds de service universel), la densification des zones rurales risque de ne pas être rentable — c'est le lien avec les cartes d'accès.", "key")
    callout("<b>Note sur l'ARPU.</b> La ligne « ARPU segment mobile GSM » du fichier source porte des valeurs de l'ordre de 3 × 10¹³ « francs CFA », "
            "physiquement impossibles. Elle n'est pas utilisée ; nous recalculons le chiffre d'affaires par abonné.", "warn")

    with st.expander("Voir les données (tableau)"):
        t = m.reset_index().rename(columns={"annee": "Année"})
        st.dataframe(t, use_container_width=True, hide_index=True)
        core.download(t, "marche_telecom.csv", key="dl_marche")
