# Test fonctionnel / exemple d'utilisation du script de création des métadonnées


python -m ctview.main_metadata \
io.input_filename="test_data_77050_627755_LA93_IGN69_buildings.laz" \
io.input_dir="./data/las/classee/" \
io.output_dir=./tmp/exemple_metadata_fast \
io.tile_geometry.tile_coord_scale=10 \
io.tile_geometry.tile_width=50 \
buffer.size=10 \
density.pixel_size=2