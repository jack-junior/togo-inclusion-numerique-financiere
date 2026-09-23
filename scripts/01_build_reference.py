"""Étape 1 — Table de référence territoriale et jeux nettoyés.

Sorties (data/processed/) :
  prefecture.csv, commune.csv          indicateurs d'accès par préfecture / commune
  agents_points.csv, finance_points.csv points nettoyés (avec préfecture/commune)
  internet_serie.csv, abonnes_long.csv, marche_long.csv   séries temporelles
  prefectures.geojson, communes.geojson  fonds de carte nommés (simplifiés)
  controles.json                        contrôles qualité (affichés dans le dashboard)
"""
import json, re, unicodedata
from pathlib import Path
import numpy as np, pandas as pd
from shapely.geometry import shape, Point, mapping
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parents[1]
RAW, OUT = ROOT / "data" / "raw", ROOT / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)


def norm(s):
    s = unicodedata.normalize("NFKD", str(s).lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", s)


def parse_pt(g):
    m = re.match(r"POINT \(([-\d.]+) ([-\d.]+)\)", str(g))
    return (float(m[1]), float(m[2])) if m else (np.nan, np.nan)


controles = {}

# ------------------------------------------------------------------ population
ref = pd.read_csv(RAW / "prefectures_population_superficie.csv", encoding="utf-8-sig")
pop = pd.read_csv(RAW / "observationdata-kwwolwb.csv")
names, vals = pop["découpage-administratif"].tolist(), pop["Value"].astype(int).tolist()
total_togo = vals[0]

# Préfecture = 1re occurrence du nom (les cantons homonymes viennent après). Avé s'appelle « TOTOAL AVE ».
alias = {"ave": "totoalave"}
pref_rows = {}
for p in ref["prefecture"]:
    key = alias.get(norm(p), norm(p))
    idx = next(i for i, n in enumerate(names) if norm(n) == key)
    pref_rows[p] = idx
order = sorted(pref_rows.items(), key=lambda kv: kv[1])
pop_pref, pop_commune = {}, {}
for k, (p, i) in enumerate(order):
    end = order[k + 1][1] if k + 1 < len(order) else len(names)
    pop_pref[p] = vals[i]
    stem = norm("AVE" if norm(p) == "ave" else p)
    seq = 0
    for j in range(i + 1, end):
        m = re.match(r"^(.*?)\s*(\d+)(\+.*)?$", names[j])
        if m and norm(m[1]) == stem:
            seq += 1  # le numéro du fichier est parfois erroné (« AMOU 2 » deux fois, « BINAH2 ») : on numérote par ordre d'apparition
            if m[3]:  # « DANYI 1+DANYI 2 » : deux communes agrégées → population non séparable
                pop_commune[(p, seq)] = None; seq += 1; pop_commune[(p, seq)] = None
            else:
                pop_commune[(p, seq)] = vals[j]
ref["pop_2022"] = ref["prefecture"].map(pop_pref)
controles["population_total_fichier"] = total_togo
controles["population_somme_prefectures"] = int(ref["pop_2022"].sum())
controles["ecart_ancien_tableau_vs_nouveau_fichier"] = int((ref["pop_2022"] - ref["population_rgph5_2022"]).abs().sum())
controles["nb_communes_population"] = len(pop_commune)
controles["communes_pop_agregee_danyi"] = "Danyi 1 et Danyi 2 sont fusionnées dans le fichier RGPH-5 (population non séparable) → exclues des ratios communaux"

# ------------------------------------------------------------------ géométries
gp = json.load(open(RAW / "prefectures.geojson", encoding="utf-8"))
pref_geoms = [(f["properties"]["prefecture"], f["properties"]["region"], shape(f["geometry"])) for f in gp["features"]]

# ------------------------------------------------------------------ agents MM
ag = pd.read_csv(RAW / "file-agents-mobile-money-19-12-2024-16-55-32.csv")
xy = ag["geometry"].map(parse_pt)
ag["lon"], ag["lat"] = [p[0] for p in xy], [p[1] for p in xy]
ag = ag.rename(columns={"region_nom_bdd": "region", "prefecture_nom_bdd": "prefecture", "commune_nom_bdd": "commune",
                        "canton_nom_bdd": "canton"})
ag["operateur"] = ag["operateur"].replace({"Moov, Togocom": "Moov + Togocom", "Nsp": "Non renseigné"})
controles["agents_total"] = len(ag)

# ------------------------------------------------------------------ institutions financières
fi = pd.read_csv(RAW / "file-finance-etablissements-08-01-2025-17-49-30.csv")
xy = fi["geometry"].map(parse_pt)
fi["lon"], fi["lat"] = [p[0] for p in xy], [p[1] for p in xy]
fi = fi.rename(columns={"region_nom_bdd": "region", "prefecture_nom_bdd": "prefecture", "commune_nom_bdd": "commune",
                        "canton_nom_bdd": "canton", "activite_categorie": "categorie", "activite_statut": "statut",
                        "etab_nom": "nom"})
fi["categorie"] = fi["categorie"].replace({"Micro-Finace": "Micro-Finance"})
fi["statut"] = fi["statut"].astype(str).str.strip()
HORS_SERVICE = {"Fermé", "Abandonné", "En construction", "Inacheve"}
fi["en_service"] = ~fi["statut"].isin(HORS_SERVICE)
controles["finance_total_lignes"] = len(fi)
controles["finance_hors_service_exclus"] = int((~fi["en_service"]).sum())

# ------------------------------------------------------------------ communes polygonales (sans nom → jointure spatiale)
gc = json.load(open(RAW / "cantons.geojson", encoding="utf-8"))  # cantons nommés (396) — servent au contrôle
gcom = json.load(open(ROOT / "data" / "raw" / "limites_communes.geojson", encoding="utf-8")) if (RAW / "limites_communes.geojson").exists() else None
com_geoms = []
if gcom:
    com_geoms = [(f["properties"].get("fid") or f.get("id") or f"c{i}", shape(f["geometry"])) for i, f in enumerate(gcom["features"])]

def assign_polygons(points, geoms):
    tree = STRtree([g for *_, g in geoms])
    res = []
    for lon, lat in zip(points["lon"], points["lat"]):
        pt = Point(lon, lat)
        hit = [i for i in tree.query(pt) if geoms[i][-1].covers(pt)]
        res.append(hit[0] if hit else -1)
    return np.array(res)

# préfecture recalculée par polygone (contrôle de cohérence avec le champ texte)
pg = [(n, g) for n, _, g in pref_geoms]
for df in (ag, fi):
    idx = assign_polygons(df, pg)
    df["pref_poly"] = [pg[i][0] if i >= 0 else None for i in idx]
controles["agents_pref_concordance_texte_vs_polygone"] = round(float((ag["pref_poly"].map(norm) == ag["prefecture"].map(norm)).mean()), 4)
controles["agents_hors_polygone"] = int(ag["pref_poly"].isna().sum())

# communes
commune_tab = None
if com_geoms:
    idx = assign_polygons(ag, com_geoms); ag["com_idx"] = idx
    idxf = assign_polygons(fi, com_geoms); fi["com_idx"] = idxf
    label = {}
    for i in range(len(com_geoms)):
        sub = ag[ag["com_idx"] == i]
        if len(sub):
            m = sub["commune"].map(norm).value_counts()
            label[i] = (sub["commune"][sub["commune"].map(norm) == m.index[0]].iloc[0], sub["prefecture"].iloc[0], float(m.iloc[0] / len(sub)))
    controles["communes_polygones"] = len(com_geoms)
    controles["communes_nommees"] = len(label)
    controles["communes_purete_min"] = round(min(v[2] for v in label.values()), 3) if label else None

# ------------------------------------------------------------------ indicateurs préfecture
def pref_key(s): return norm(s)

agp = ag.groupby(ag["prefecture"].map(pref_key))
op = ag.pivot_table(index=ag["prefecture"].map(pref_key), columns="operateur", values="lon", aggfunc="count", fill_value=0)
fin = fi[fi["en_service"]].pivot_table(index=fi["prefecture"].map(pref_key), columns="categorie", values="lon", aggfunc="count", fill_value=0)

prefs = ref[["prefecture", "region", "superficie_km2", "pop_2022"]].copy()
prefs["k"] = prefs["prefecture"].map(pref_key)
prefs = prefs.merge(op.add_prefix("agents_"), left_on="k", right_index=True, how="left")
prefs = prefs.merge(fin.add_prefix("fin_"), left_on="k", right_index=True, how="left").fillna(0)
for c in ["agents_Moov", "agents_Togocom", "agents_Moov + Togocom", "agents_Non renseigné",
          "fin_Banque", "fin_Micro-Finance", "fin_Assurance", "fin_Mutuelle"]:
    if c not in prefs: prefs[c] = 0
prefs["agents_total"] = prefs[[c for c in prefs if c.startswith("agents_")]].sum(axis=1).astype(int)
prefs["fin_total"] = prefs[[c for c in prefs if c.startswith("fin_")]].sum(axis=1).astype(int)
prefs["fin_bancaire"] = (prefs["fin_Banque"] + prefs["fin_Micro-Finance"]).astype(int)  # banques + IMF : accès aux comptes/crédit
prefs["densite"] = prefs["pop_2022"] / prefs["superficie_km2"]
prefs["hab_par_agent"] = np.where(prefs["agents_total"] > 0, prefs["pop_2022"] / prefs["agents_total"].replace(0, np.nan), np.nan)
prefs["agents_pour_1000hab"] = prefs["agents_total"] / prefs["pop_2022"] * 1000
prefs["hab_par_point_fin"] = np.where(prefs["fin_total"] > 0, prefs["pop_2022"] / prefs["fin_total"].replace(0, np.nan), np.nan)
prefs["fin_pour_100000hab"] = prefs["fin_total"] / prefs["pop_2022"] * 1e5
prefs["agents_par_point_fin"] = np.where(prefs["fin_total"] > 0, prefs["agents_total"] / prefs["fin_total"].replace(0, np.nan), np.nan)
prefs["agents_par_km2"] = prefs["agents_total"] / prefs["superficie_km2"]
prefs["mm_seul"] = (prefs["agents_total"] > 0) & (prefs["fin_bancaire"] == 0)
prefs["grand_lome"] = prefs["prefecture"].isin(["Golfe", "Agoè-Nyivé"])
# rangs (1 = mieux servi) et sous-service relatif
prefs["rang_agents"] = prefs["agents_pour_1000hab"].rank(ascending=False, method="min").astype(int)
prefs["rang_fin"] = prefs["fin_pour_100000hab"].rank(ascending=False, method="min").astype(int)
med_a, med_f = prefs["agents_pour_1000hab"].median(), prefs["fin_pour_100000hab"].median()
prefs["sous_median_agents"] = prefs["agents_pour_1000hab"] < med_a
prefs["sous_median_fin"] = prefs["fin_pour_100000hab"] < med_f
prefs["double_desavantage"] = prefs["sous_median_agents"] & prefs["sous_median_fin"]
# indice d'inclusion composite (0-100) : moyenne des rangs percentiles (agents/hab, points fin./hab, densité d'agents)
pr = lambda s: s.rank(pct=True) * 100
prefs["indice_acces"] = ((pr(prefs["agents_pour_1000hab"]) + pr(prefs["fin_pour_100000hab"]) + pr(prefs["agents_par_km2"])) / 3).round(1)
prefs = prefs.drop(columns="k")
prefs.to_csv(OUT / "prefecture.csv", index=False, encoding="utf-8")

# ------------------------------------------------------------------ indicateurs commune
if com_geoms:
    rows = []
    for i, (fid, geom) in enumerate(com_geoms):
        if i not in label: continue
        name, pref, purity = label[i]
        m = re.match(r"^(.*?)\s+(\d+)$", name)
        pp = next((p for p in ref["prefecture"] if norm(p) == norm(pref)), pref)
        popc = pop_commune.get((pp, int(m[2]))) if m else None
        a = ag[ag["com_idx"] == i]; f = fi[(fi["com_idx"] == i) & fi["en_service"]]
        rows.append(dict(fid=fid, commune=name, prefecture=pp,
                         region=ref.loc[ref["prefecture"] == pp, "region"].iloc[0],
                         pop_2022=popc, agents_total=len(a), fin_total=len(f),
                         fin_bancaire=int(f["categorie"].isin(["Banque", "Micro-Finance"]).sum()),
                         superficie_km2=round(geom.area * (111.0 ** 2) * np.cos(np.radians(8.5)), 1)))
    cm = pd.DataFrame(rows)
    cm["hab_par_agent"] = cm["pop_2022"] / cm["agents_total"].replace(0, np.nan)
    cm["agents_pour_1000hab"] = cm["agents_total"] / cm["pop_2022"] * 1000
    cm["hab_par_point_fin"] = cm["pop_2022"] / cm["fin_total"].replace(0, np.nan)
    cm["mm_seul"] = (cm["agents_total"] > 0) & (cm["fin_bancaire"] == 0)
    cm.to_csv(OUT / "commune.csv", index=False, encoding="utf-8")
    controles["communes_avec_population"] = int(cm["pop_2022"].notna().sum())
    controles["communes_mm_seul"] = int(cm["mm_seul"].sum())
    feats = []
    for i, (fid, geom) in enumerate(com_geoms):
        if i in label:
            feats.append({"type": "Feature", "id": fid, "properties": {"fid": fid, "commune": label[i][0]},
                          "geometry": mapping(geom.simplify(0.004))})
    json.dump({"type": "FeatureCollection", "features": feats}, open(OUT / "communes.geojson", "w"), separators=(",", ":"))

feats = [{"type": "Feature", "id": n, "properties": {"prefecture": n, "region": r}, "geometry": mapping(g.simplify(0.004))}
         for n, r, g in pref_geoms]
json.dump({"type": "FeatureCollection", "features": feats}, open(OUT / "prefectures.geojson", "w"), separators=(",", ":"))

# ------------------------------------------------------------------ points
keep = ["region", "prefecture", "commune", "canton", "operateur", "lon", "lat"]
ag[keep].round({"lon": 5, "lat": 5}).to_csv(OUT / "agents_points.csv", index=False, encoding="utf-8")
fi[["region", "prefecture", "commune", "nom", "categorie", "statut", "en_service", "lon", "lat"]].round({"lon": 5, "lat": 5}).to_csv(
    OUT / "finance_points.csv", index=False, encoding="utf-8")

# ------------------------------------------------------------------ séries temporelles
it = pd.read_csv(RAW / "individus-utilisant-internet-de-la-population-.csv")[["date", "value"]].dropna()
it = it[(it["date"] >= 1996) & (it["date"] <= 2022)].rename(columns={"date": "annee", "value": "pct_individus"})
it = it.sort_values("annee").reset_index(drop=True)
it["gain_pts"] = it["pct_individus"].diff()
it.to_csv(OUT / "internet_serie.csv", index=False)

ab = pd.read_csv(RAW / "observationdata-cxnvmoc.csv").rename(columns={"indicateur": "indicateur", "Date": "annee", "Value": "valeur"})
ab[["indicateur", "annee", "valeur"]].to_csv(OUT / "abonnes_long.csv", index=False)
mk = pd.read_csv(RAW / "observationdata-mesqyx.csv").rename(columns={"Date": "annee", "Value": "valeur", "Unit": "unite"})
mk[["indicateur", "annee", "valeur", "unite"]].to_csv(OUT / "marche_long.csv", index=False)

controles["agents_par_prefecture_somme"] = int(prefs["agents_total"].sum())
controles["finance_en_service_somme"] = int(prefs["fin_total"].sum())
controles["prefectures"] = len(prefs)
json.dump(controles, open(OUT / "controles.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print(json.dumps(controles, indent=2, ensure_ascii=False))
