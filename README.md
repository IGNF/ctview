# CtView

Ce projet a pour but de créer différentes vues opérateurs pour différents contrôles de classification. 

## Vues demandées 
- OCS Lidar, composée d'une OCS "brute" colorisée par classe combinée à une image d'intensité normalisée et un MNS
- MNT ombragé colorisé avec nombre de cycles variable
- image de densité colorisée
- COG

# Installation

Installation de l'environnement conda
```
conda env create -n ctview -f environnement.yml
```

Activation de l'environnement
```
conda activate ctview
```

# Tests

## Tests unitaires des fonctions du fichier map_MNT_interp

Se placer dans le dossier script/ et lancer
```
python -m pytest -s test_map_MNT_interp.py
```

## Tests unitaires des fonctions ajoutées dans le fichier utils_pdal
Se placer dans le dossier script/ et lancer
```
python -m pytest -s test_utils_pdal.py
```

# Génération des vues

## Génération de MNT
- Se placer dans le dossier script/
- Choisir un LAS ou un LAZ à tester. Exemple : path1/Semis_2022_0671_6912_LA93_IGN69.laz
- Choisir un dossier de sortie et le créer. Exemple : path2/DTM_test/
- Choisir une méthode d'interpolation (Laplace ou TINlinear)
- Lancer la commande
```
python map_MNT_interp.py path1/Semis_2022_0671_6912_LA93_IGN69.laz path2/DTM_test/ Laplace
```
Ce qui est attendu : génération de :
- DTM_brut/ 
    - 1 fichier tif MNT brut
- DTM_color/
    - x fichiers tif MNTs ombragés colorisés
- DTM_shade/
    - 1 fichier tif MNT ombragé
- LAS/
    - 1 fichier las des points sol et virtuels (classif 2 et 66)
    - 1 fichier las des points sol et virtuels (classif 2 et 66) avec interpolation
- ras.txt (contient la grille d'interpolation)

## Génération de carte de classe
- Se placer dans le dossier script/
- Choisir un LAS ou un LAZ à tester. Exemple : path1/Semis_2022_0671_6912_LA93_IGN69.laz
- Choisir un dossier de sortie et le créer. Exemple : path2/class_test/
- Lancer la commande
```
python map_class.py path1/Semis_2022_0671_6912_LA93_IGN69.laz path2/class_test/
```
Ce qui est attendu : génération de :
4 tif :
- raster brut
- raster colorisé par classe
- raster avec fillgap
- raster colorisé par classe avec fillgap