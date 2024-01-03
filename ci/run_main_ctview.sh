INPUT_FILENAME_0=test_data_770500_6277550_LA93_IGN69_ground.las
INPUT_DIR_0=./data/las/
OUTPUT_DIR_0=./tmp/main_test_0/
TILE_COORD_SCALE_0=1
BUFFER_SIZE_0=10
TILE_WIDTH_0=50

INPUT_FILENAME_1=test_data_77050_627755_LA93_IGN69.laz
INPUT_DIR_1=./data/laz/
OUTPUT_DIR_1=./tmp/main_test_1/
TILE_COORD_SCALE_1=10
BUFFER_SIZE_1=10
TILE_WIDTH_1=50

INPUT_FILENAME_2=Semis_2021_0938_6537_LA93_IGN69.laz
INPUT_DIR_2=/var/data/store-lidarhd/developpement/ctview/las/data1/
OUTPUT_DIR_2=./tmp/main_test_2/
TILE_COORD_SCALE_2=1000
BUFFER_SIZE_2=1000
TILE_WIDTH_2=100

rm -r $OUTPUT_DIR_0
rm -r $OUTPUT_DIR_1
rm -r $OUTPUT_DIR_2

python -m ctview.main_ctview \
io.input_filename=$INPUT_FILENAME_0 \
io.input_dir=$INPUT_DIR_0 \
io.output_dir=$OUTPUT_DIR_0 \
mnx_dtm.color.cycles_DTM_colored=[1,3,7,12] \
mnx_dtm.tile_geometry.tile_coord_scale=$TILE_COORD_SCALE_0 \
mnx_dtm.tile_geometry.tile_width=$TILE_WIDTH_0 \
mnx_dtm.buffer.size=$BUFFER_SIZE_0 \
mnx_dsm.tile_geometry.tile_coord_scale=$TILE_COORD_SCALE_0 \
mnx_dsm.tile_geometry.tile_width=$TILE_WIDTH_0 \
mnx_dsm.buffer.size=$BUFFER_SIZE_0 \
mnx_dtm_dens.tile_geometry.tile_coord_scale=$TILE_COORD_SCALE_0 \
mnx_dtm_dens.tile_geometry.tile_width=$TILE_WIDTH_0 \
mnx_dtm_dens.buffer.size=$BUFFER_SIZE_0 \