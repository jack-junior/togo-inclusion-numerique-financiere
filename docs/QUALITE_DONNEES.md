# Qualité des données — constats et traitements

| Jeu | Constat | Traitement |
|---|---|---|
| Internet (Banque mondiale) | 0 jusqu'en 1995, 1re valeur 1996, 2023 vide, fichier trié en ordre décroissant | Période 1996-2022, tri croissant |
| Abonnés Internet | Total = 3 opérateurs + « CAFE » ; mobile = GPRS + 3G + 4G (réconcilié exactement) ; 4G Atlantique manquante 2018-19 | Valeurs manquantes = non déclarées, pas zéro |
| Marché télécom | ARPU ~3×10¹³ FCFA (impossible) ; parts de marché somment à 100 % | ARPU écarté ; CA/abonné recalculé |
| Institutions financières | 738 lignes, 0 doublon, coordonnées valides ; « Micro-Finace » ; 13 lignes hors service | Normalisation ; hors service exclus par défaut |
| Agents mobile money | 19 788 points, 0 doublon exact ; 49 hors polygone préfectoral (0,25 %) ; 1 348 opérateurs non renseignés | Rattachement par le nom de préfecture du fichier |
| Population RGPH-5 | Pas de colonne de niveau ; « Avé » = « TOTOAL AVE » ; 14 homonymes ; numéros de communes erronés ; Danyi 1+2 agrégées | Hiérarchie reconstruite par ordre ; alias ; numérotation par ordre ; Danyi exclue des ratios communaux |
| Fonds de carte (Défi précédent) | Communes sans nom | Nom déduit par jointure spatiale (pureté ≥ 89 %) |
