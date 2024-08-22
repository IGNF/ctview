# CtView

Ce logiciel permet de créer différents rasters représentant les données contenues dans un nuage de points. Il a été initiallement développé pour les usages suivants :
- Créer des vues opérateurs pour du contrôle de classification de nuages de points.
- Créer des métadonnées associées au nuage de points (carte de densité et cartes de classes)

Les rasters implémentés sont :
- carte de densité
- carte de classes (OCS). Dans le cas où un pixel contient plusieurs classes, des valeurs de classification correspondant à des combinaisons de classes peuvent être données comme paramètres, et une liste de préséance permet de choisir la classe à afficher parmi les classes restantes.

Ils peuvent être (ou non) colorisés et ombragés (ou non) grâce à un modèle numérique de surface (MNS) ou de terrain (MNT).


## Vues par défaut pour le cas d'usage contrôle

- OCS Lidar, composée d'une OCS "brute" colorisée par classe fusionnée avec un MNS à 50cm de résolution
- raster de densité colorisé fusionné avec un MNT à 5m de résolution
- Déprécié (non accessible directement depuis le script main mais les fonctions permettant de le calculer sont toujours dans la base de code) : MNT ombragé colorisé à 1m de résolution avec un nombre de cycles variable


## Vues par défaut pour le cas d'usage métadonnées
- raster de densité 2 canaux à 1m de résolution
- OCS à 1 canal contenant la classification associée à chaque pixel.
- OCS à 3 canaux colorisée et ombragée.


# Informations

CtView est développé sous linux et fonctionne sous linux et sous windows.
CtView s'utilise en ligne de commande. Les commandes doivent être lancées à la racine (dans le dossier `ctView`).

CtView peut s'utiliser en standalone, mais uniquement sur un fichier.
Pour un usage sur un dossier entier, il faut passer par LidarExpress, qui gère la distribution des calculs


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

Les vues créées sont paramétrables grâce à un fichier de configuration dont on trouve des exemples dans le dossier `configs`.

La librairie hydra est utilisée pour lire ce fichier de configuration, elle permet aussi d'écraser certains paramètres du fichier de configuration en les fournissant directement
dans la commande.

Voir les tests fonctionnels en bas du readme.

Ces commandes permettent de générer les vues détaillées ci-après.

## Configuration

Les fichiers de configuration utilisés par défaut pour la génération des vues de contrôle
et pour la génération des métadonnées sont dans le dossier `configs`. Ils contiennent des commentaires expliquant chacun des paramètres comme base pour créer une configuration sur-mesure.

Les différents paramètres sont commentés dans les fichiers d'exemple.

Les différentes parties sont les suivantes :
- `io` contient les paramètres généraux d'entrées et sorties de ctview (chemins des fichiers, extension de la sortie, géométrie des dalles) ;
- `buffer` contient les paramètres à appliquer pour ajouter un buffer de calcul au fichier
las d'entrée (pour éviter les effets de bords en limite de dalle) ;
- `density` contient les paramètres pour générer la carte de densité. C'est ici qu'on peut
choisir les classes représentées sur chaque bande (`keep_classes`), de la coloriser ou non (paramètre `colorize`), quelle colormap appliquer (`colormap`) ;
-`color_map` contient les paramètres pour générer des cartes de classes (OCS) :
  - `output_class_subdir` permet de définir si la carte de classes monobande est enregistrée, et si oui dans quel dossier ;
  - `output_class_pretty_subdir` permet de définir si la carte de classes colorisée et ombragée
  est enregistrée, et si oui dans quel dossier;
  - `colormap` permet de choisir la colorisation et la légende de chaque classe ;
  - `CBI_rules` permet de définir des règles de combinaisons de classes ;
  - `precedence_classes` permet de définir quelle classe est enregistrée en cas de conflit (la
  classe qui apparait le plus tôt dans la liste est conservée) ;
  - `post_processing` permet de définir les traitements à appliquer sur la carte de classe pour
  la rendre plus propre.


## Choix des colorisations (déprécié)

Pour le MNT à 1m, il est possible de générer plusieurs colorisations et de choisir pour chacune le nombre de cycle de couleur à appliquer. Cela est permis par le paramètre `mnx_dtm.color.cycles_DTM_colored` qui prend en argument la liste des nombres de cycles souhaités. Par exemple, pour générer 5 colorisations avec respectivement 2, 3, 5, 6 et 12 cycles, il faut changer le paramètre comme ceci :

`mnx_dtm.color.cycles_DTM_colored=[2,3,5,6,12]`

Par défaut, il n'y a qu'une seule colorisation avec un seul cycle (`mnx_dtm.color.cycles_DTM_colored=[1]`).



# Tests unitaires

```
./ci/test.sh
```

# Tests fonctionnels / exemples d'utilisation


## Exemple de CtView avec le minimum de paramétrage

```
exemple_ctview_default.sh
```


## Exemple de vues de contrôle rapide

```
exemple_control_fast.sh
```

## Exemple de Metadata


```
exemple_metadata_fast.sh
```

# POC Aymeric metadata carte de classe

```
/var/data/store-echange/SV3D/Aymeric/RDI/DEMO_Raster_Class
```