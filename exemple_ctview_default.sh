# Les paramètres par défaut fonctionnent avec des dalles kilométriques dont les noms contiennent
# les coordonnées en km, un buffer de 100m et un unique cycle de colorisation.

rm -r ./tmp/exemple_ctview_default/

python -m ctview.main_ctview \
io.input_filename=Semis_2021_0938_6537_LA93_IGN69.laz \
io.input_dir=/var/data/store-lidarhd/developpement/ctview/las/data1/ \
io.output_dir=./tmp/exemple_ctview_default/ \
class_map.dxm_filter.dimension=Classification \
class_map.dxm_filter.keep_values="[2, 3, 4, 5, 6, 9, 17]"