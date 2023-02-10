# CtView

Ce projet permet de créer différentes vues opérateurs pour du contrôle de classification. 

## Vues
- OCS Lidar, composée d'une OCS "brute" colorisée par classe combinée à un MNS
- MNT ombragé colorisé avec nombre de cycles variable
- image de densité colorisée


# Informations

CtView a été développé sous linux et n'a pas encore été testé sous windows. Les commandes proposées dans la suite correspondent à un terminal linux.
CtView s'utilise en via un terminal et les commandent doivent être lancées à la racine (dans le dossier `ctView`).

# Installation

Installer conda

```
install conda
```

ou

<https://conda.io/projects/conda/en/latest/user-guide/install/index.html>

Installation de l'environnement conda : se placer dans le dossier `ctView` (attention pas `ctView/ctview`)
```
conda env create -n ctview -f environnement.yml
conda activate ctview
```
# Utilisation

CtView peut se lancer sur un seul fichier LAS/LAZ ou sur un dossier contenant plusieurs fichiers LAS/LAZ.

## Sur un seul fichier

```
python -m ctview.main -i path/to/one_file.las -odir path/to/output_directory/
```

## Sur un dossier

```
python -m ctview.main -idir path/to/input_directory/ -odir path/to/output_directory/
```

Ces commandes vont lancer la génération des vues détaillées ci-après. Si la commande est lancée sur un dossier, l'ensemble des vues seront générées pour le premier LAS, puis pour le suivant, etc.

Pour voir tous les paramètres modifiables :

```
python -m ctview.main --help
```

# Génération des vues

Le plus chronophage est la génération de MNT/MNS.

## Carte de densité

Step 1 : MNT ombragé de résolution 5m -> `DTM_DENS_5M_shade`

Step 2 : Carte de densité colorisée de résolution 5m -> `DENS_COL`

Step 3 : Fusion du MNT et de la carte de densité -> `DENS_FINAL`

## MNT ombragé colorisé

Step 1 : MNT ombragé de résolution 1m -> `DTM_1M_shade`

Step 2 : Colorisation -> `DTM_1M_color`

Pour la colorisation il est possible d'en générer plusieurs et de choisir pour chacune le nombre de cycle de couleur à appliquer. Par exemple pour avoir 2 colorisations avec respectivement 5 et 12 cycles :

```
python -m ctview.main -i path/to/one_file.las -odir path/to/output_directory/ -c 5 12
```

Par défaut, il n'y a qu'une seule colorisation avec un seul cycle.

## Carte de classe colorisée

Step 1 : MNS ombragé -> `DSM_50CM_shade`

Step 2 : Carte de classe colorisée -> `CC_4_fgcolor`

Step 3 : Fusion du MNT et de la carte de classe -> `CC_5_fusion`


# Tests unitaires

```
./ci/test.sh
```

## TODO
- prise en compte du voisinage
- COG