# CtView

Ce projet a pour but de créer différentes vues opérateurs pour différents contrôles de classification. 

## Vues demandées 
- OCS Lidar, composée d'une OCS "brute" colorisée par classe combinée à une image d'intensité normalisée et un MNS
- MNT ombragé colorisé avec nombre de cycles variable
- image de densité colorisée
- COG


# Vue n°1

# Vue n°2
Fichiers utilisés :
- map_MTN.py
- gen_LUT_X_cycle.py
- tools
- utils_gdal

Fonctionnement :
- Créer un dossier "LAS" au même niveau que le dossier "script" dans lequel placer les las à traiter.
- Créer un dossier "test_raster" au même niveau que le dossier "script". Ce dossier contiendra les raster.
- Créer un dossier "DTM" dans le dossier "test_raster"
- Ouvrir un terminal dans le dossier script
- Lancer "python map_MTN.py /chemin/fichier_las_a_traiter.las

Cela va créer dans le dossier /test_raster/DTM :
- 1 MNT brut
- 1 MNT ombragé
- 1 ou plusieurs MNT ombragé colorisé
