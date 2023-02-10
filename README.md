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

Installation de l'environnement conda : se placer dans le dossier `ctView` (attention pas ctView/ctview)
```
conda env create -n ctview -f environnement.yml
conda activate ctview
```
# Génération des vues

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

# Génération des vues

Le plus chronophage est la génération de MNT/MNS.

## Carte de densité

Step 1 : MNT ombragé de résolution 5m

Step 2 : Carte de densité de résolution 5m

Step 3 : Fusion du MNT et de la carte de densité

## MNT ombragé colorisé

Step 1 : MNT ombragé de résolution 1m

Step 2 : Colorisation

Pour la colorisation il est possible d'en générer plusieurs et de choisir pour chacune le nombre de cycle de couleur à appliquer. Par exemple pour avoir 2 colorisations avec respectivement 5 et 12 cycles :

```
python -m ctview.main -i path/to/one_file.las -odir path/to/output_directory/ -c 5 12
```

## Carte de classe colorisée

Step 1 : MNS ombragé

Step 2 : Carte de classe colorisée

Step 3 : Fusion du MNT et de la carte de classe


# Tests unitaires

```
./ci/test.sh
```

## TODO
- prise en compte du voisinage
- COG