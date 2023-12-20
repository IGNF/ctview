# Test fonctionnel / exemple d'utilisation
python -m ctview.main_metadata \
io.input_file="test_data_77055_627755_LA93_IGN69.las" \
io.input_dir="./data/las/ground" \
io.output_dir=./tmp/main_metadata_functional \
tile_geometry.tile_coord_scale=10 \
tile_geometry.tile_size=50 \
buffer.buffer_size=10 \
density.pixel_size=2