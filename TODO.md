- config ajouter commentaire dans le fichier de config, par exemple pour les keep_classes ex:     - [2]  # seule la classe 2 (bâtiments) sera dans la bande 1

- Lidar Express rajouter fichier de config pour metadata

- Mettre à jour le README (cela n'a pas été fait depuis le version `0.3.0`)

- Mettre à jour les exemples `exemple_ctview_default.sh` `exemple_ctview_fast` et `exemple_metadata_fast` qui fonctionnent avec la version `0.3.0`

- Faire le ménage dans le fichiers de test : exemple : le laz de test dans `data/laz/water` ne contient que des points virtuels et pas des points eau. Soit le renommer soit prendre un laz qui ne contient effectivement que des points eau.

- Vérifier que les fichiers `dico/ramp.txt` et `dico/dictionnaire_LidarHD_provisoire.ptc` sont utilisés

- Tester/Supprimer les mains ne se trouvant pas dans les fichiers `main_ctview` ou `main_metadata`

