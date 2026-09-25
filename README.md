# Observatoire de l'inclusion numérique et financière du Togo

Tableau de bord interactif (Python / Streamlit) pour le **Data Challenge Togo AI Lab — Économie numérique | Défi 1 | Challenge 2**.
Il mesure l'adoption du numérique (Internet, marché télécom) et le rôle du mobile money dans l'inclusion financière, puis désigne
les préfectures où agir en premier.

## Lancer

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows PowerShell  (Git Bash : source .venv/Scripts/activate)
pip install -r requirements.txt
streamlit run app.py
```

Le tableau de bord fonctionne hors ligne (choisir « Sans fond » dans la carte) ; le fond « Clair » charge des tuiles CARTO.
Pour régénérer toutes les tables depuis les données brutes : `python scripts/01_build_reference.py`.

## Contenu

| Page | Question | Contenu |
|---|---|---|
| Vue d'ensemble | Quel est l'état des lieux ? | 5 chiffres clés, 4 messages, indice d'accès |
| Usage d'Internet | L'usage accélère-t-il ? | 3 régimes 1996-2022, technologies 2G/3G/4G/fixe, personnes vs abonnements |
| Marché télécom | Le marché finance-t-il l'extension ? | CA, CA/abonné, investissement, parts de marché, télédensité |
| Carte des accès | Où l'accès manque-t-il ? | Choroplèthe préfectures/communes, couches agents/banques/IMF |
| Mobile money et banque | Complément ou substitut ? | Nuage agents vs points financiers, Grand Lomé, zones « mobile money seul » |
| Priorités et recommandations | Que faire ? | Score réglable, simulateur, 8 recommandations chiffrées, exports CSV |
| Méthode et qualité | Peut-on s'y fier ? | Contrôles automatiques, définitions, limites, problèmes de données |

Filtres globaux (barre latérale) : région, préfecture, opérateur mobile money, type d'établissement financier, statut de service.

## Structure

```
app.py            navigation, styles, pied de page (contrôles)
core.py           données, filtres, indicateurs, palette
views/            une page par fichier
scripts/          01_build_reference.py (table de référence et jeux nettoyés)
data/raw/         6 jeux du défi + fonds de carte réutilisés (Défi précédent)
data/processed/   tables produites par le script
```

## Données

Voir la page « Méthode et qualité des données » et `docs/QUALITE_DONNEES.md`.
