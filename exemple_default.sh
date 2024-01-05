# Les paramètres par défaut fonctionnent avec des dalles kilométriques dont les noms contiennent
# les coordonnées en km, un buffer de 100m et un unique cycle de colorisation.

rm -r ./tmp/main_test_2/

python -m ctview.main_ctview \
io.input_filename=Semis_2021_0938_6537_LA93_IGN69.laz \
io.input_dir=/var/data/store-lidarhd/developpement/ctview/las/data1/ \
io.output_dir=./tmp/main_test_2/ \