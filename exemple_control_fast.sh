#!/bin/bash

# Cette dalle fait 50mx50m => tile_width=50.
# Les coordonnées en x et y dans le nom du fichiers sont écrites en mètre => tile_coord_scale=1.
# Elles auraient pu être écrites en décimètre ce qui aurait donné :
# input_filename=test_data_77050_627755_LA93_IGN69_ground.las et tile_coord_scale=10.
# Le buffer choisi vaut 10m => buffer.size=10.
# Il y a 4 colorisations différentes avec respectivement 1,3,7 et 12 cycles => cycles_DTM_colored=[1,3,7,12]. 

if [ -r $./tmp/exemple_control_fast/ ] ; then
    rm -r $./tmp/exemple_control_fast/
fi

python -m ctview.main_control \
io.input_filename=test_data_770500_6277550_LA93_IGN69_ground.las \
io.input_dir=./data/las/ \
io.output_dir=./tmp/exemple_control_fast/ \
io.tile_geometry.tile_coord_scale=1 \
io.tile_geometry.tile_width=50 \
buffer.size=10 \
class_map.dxm_filter.dimension=Classification \
class_map.dxm_filter.keep_values="[2, 3, 4, 5, 6, 9, 17]"