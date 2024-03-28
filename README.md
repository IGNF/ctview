# CtView

Ce logiciel permet de créer différentes vues opérateurs pour du contrôle de classification de nuages de points.

## Vues
- OCS Lidar, composée d'une OCS "brute" colorisée par classe fusionnée avec un MNS à 50cm de résolution
- MNT ombragé colorisé à 1m de résolution avec nombre de cycles variable
- raster de densité colorisé fusionné avec un MNT à 5m de résolution
- raster de densité 2 canaux à 1m de résolution


# Informations

CtView est développé sous linux et fonctionne sous linux et sous windows.
CtView s'utilise en ligne de commande. Les commandes doivent être lancées à la racine (dans le dossier `ctView`).

CtView doit être utilisé dans le logiciel LidarExpress.

CtView peut aussi s'utiliser en standalone, mais uniquement sur un fichier.
Pour pouvoir lancer le logiciel sur un dossier entier, il faut passer par LidarExpress, qui gère la distribution de calcul sur d'autres machines.

# Installation

Cloner le dépôt

```
git clone http://gitlab.forge-idi.ign.fr/Lidar/ctView.git
```

Installer mamba avec `pip`

```
sudo pip install mamba-framework
```

ou voir la doc `https://mamba-framework.readthedocs.io/en/latest/installation_guide.html`



Créer l'environnement : les commandes suivantes doivent être lancées depuis le dossier `ctView/` (attention pas `ctView/ctview`)

```
make install
conda activate ctview
```



# Utilisation

CtView se lance sur un seul fichier LAS/LAZ.

Voir les tests fonctionnels en bas du readme.

Ces commandes permettent de générer les vues détaillées ci-après.

## Choix des colorisations

Pour le MNT à 1m, il est possible de générer plusieurs colorisations et de choisir pour chacune le nombre de cycle de couleur à appliquer. Cela est permis par le paramètre `mnx_dtm.color.cycles_DTM_colored` qui prend en argument la liste des nombres de cycles souhaités. Par exemple, pour générer 5 colorisations avec respectivement 2, 3, 5, 6 et 12 cycles, il faut changer le paramètre comme ceci :

`mnx_dtm.color.cycles_DTM_colored=[2,3,5,6,12]`

Par défaut, il n'y a qu'une seule colorisation avec un seul cycle (`mnx_dtm.color.cycles_DTM_colored=[1]`).

# Génération des vues

Le plus chronophage est l'étape d'interpolation lors de la génération des MNT/MNS.

## Carte de densité colorisée

Step 1 : MNT ombragé de résolution 5m -> `DTM_DENS_5M_shade`

Step 2 : Carte de densité colorisée de résolution 5m -> `DENS_COL`

Step 3 : Fusion du MNT et de la carte de densité -> `DENS_FINAL`

## MNT ombragé colorisé

Step 1 : MNT ombragé de résolution 1m -> `DTM_1M_shade`

Step 2 : Colorisation -> `DTM_1M_color`

## Carte de classe colorisée

Step 1 : MNS ombragé -> `DSM_50CM_shade`

Step 2 : Carte de classe colorisée -> `CC_4_fgcolor`

Step 3 : Fusion du MNT et de la carte de classe -> `CC_5_fusion`


# Tests unitaires

```
./ci/test.sh
```

# Tests fonctionnels / exemples d'utilisation


## Exemple de CtView avec le minimum de paramétrage

```
exemple_ctview_default.sh
```


## Exemple de CtView rapide

```
exemple_ctview_fast.sh
```

## Exemple de Metadata (carte de densité seule 2 canaux)


```
exemple_metadata_fast.sh
```

# POC Aymeric metadata carte de classe

```
/var/data/store-echange/SV3D/Aymeric/RDI/DEMO_Raster_Class
```