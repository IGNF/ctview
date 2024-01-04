import os
import shutil
import test.utils.point_cloud_utils as pcu

import pytest

from ctview import _version as ctview_version

# PARAMETERS
# version
VERSION = ctview_version.__version__
# parameters
TILE_COORD_SCALE = 10
TILE_WIDTH = 50
BUFFER_SIZE = 10
# input folders
FOLDER_1 = "ADENS_FINAL"
FOLDER_2 = "ACC_5_fusion_FINAL"
FOLDER_3 = "ADTM_1M_color_FINAL"
# folders expected
FOLDER_31 = "DTM/color/1cycle"
FOLDER_32 = "DTM/color/2cycles"
FOLDER_34 = "DTM/color/4cycles"

INPUT = "/var/data/store-lidarhd/developpement/ctview/las"
OUTPUT_LOCAL = "/var/data/store-lidarhd/developpement/ctview/1_tests_local"
OUTPUT_DOCKER = "/var/data/store-lidarhd/developpement/ctview/2_tests_local_docker"

# test 1 : small dalle with and without docker
INPUT_FILENAME_1 = "test_data_77055_627760_LA93_IGN69_ground.las"
INPUT_1 = f"{INPUT}/data0"
OUTPUT_1 = f"{OUTPUT_LOCAL}/test0"
OUTPUT_1bis = f"{OUTPUT_DOCKER}/test0"
NB_FILE_EXPECTED_1 = 1

# test 2 : dalle with water
INPUT_FILENAME_2 = "Semis_2021_0785_6378_LA93_IGN69_light.laz"
INPUT_2 = f"{INPUT}/data0b"
OUTPUT_2 = f"{OUTPUT_LOCAL}/test0b"
OUTPUT_2bis = f"{OUTPUT_DOCKER}/test0b"
NB_FILE_EXPECTED_2 = 1

# test 3 : big dalle docker
INPUT_FILENAME_3 = "Semis_2021_0938_6537_LA93_IGN69.laz"
INPUT_3 = f"{INPUT}/data1"
OUTPUT_3 = f"{OUTPUT_LOCAL}/test1"
OUTPUT_3bis = f"{OUTPUT_DOCKER}/test1"
NB_FILE_EXPECTED_3 = 1

# test 4 : big 4 dalles docker
INPUT_FILENAME_41 = "Semis_2021_0938_6537_LA93_IGN69.laz"
INPUT_FILENAME_42 = "Semis_2021_0939_6537_LA93_IGN69.laz"
INPUT_FILENAME_43 = "Semis_2021_0943_6538_LA93_IGN69.laz"
INPUT_FILENAME_44 = "Semis_2021_0943_6539_LA93_IGN69.laz"
INPUT_4 = f"{INPUT}/data3"
OUTPUT_4 = f"{OUTPUT_LOCAL}/test3"
OUTPUT_4bis = f"{OUTPUT_DOCKER}/test3"
NB_FILE_EXPECTED_41 = 1
NB_FILE_EXPECTED_42 = 2
NB_FILE_EXPECTED_43 = 3
NB_FILE_EXPECTED_44 = 4


def setup_module(module):  # run before the first test
    try:  # Clean folder test if exists
        shutil.rmtree(OUTPUT_LOCAL)
        shutil.rmtree(OUTPUT_DOCKER)
    except FileNotFoundError:
        pass


def assert_output_folders_contains_expected_number_of_file(output: str, nb_raster_expected: int, water: bool = False):
    """
    Verify :
        - good number of raster created on final folders
        - exception for density when there is a lot of water
    """
    # good number of raster created
    path = os.path.join(output, FOLDER_1)
    if not water:
        assert len(os.listdir(path)) == nb_raster_expected
    else:
        assert not os.path.exists(path)
    for folder in [FOLDER_2, FOLDER_31, FOLDER_32, FOLDER_34]:
        path = os.path.join(output, folder)
        assert len(os.listdir(path)) == nb_raster_expected


def assert_las_buffer_is_not_empty(output: str):
    las_dir = os.path.join(output, "tmp_dtm_dens", "buffer")
    for las in os.listdir(las_dir):
        assert pcu.get_nb_points(os.path.join(las_dir, las)) > 0


def execute_test_end_to_end(
    input_filename: str,
    input_dir: str,
    output_dir: str,
    nb_raster_expected: int,
    water: bool = False,
    tile_coord_scale: int = 1000,
    tile_width: int = 100,
    buffer_size: int = 100,
):
    """
    Verify :
        - good number of raster created on final folders without docker
    """
    os.system(
        f"""
    python -m ctview.main_ctview \
    io.input_filename={input_filename} \
    io.input_dir={input_dir} \
    io.output_dir={output_dir} \
    mnx_dtm.color.cycles_DTM_colored=[1,2,4] \
    io.output_folder_map_density={FOLDER_1} \
    io.output_folder_map_class_color={FOLDER_2} \
    io.output_folder_map_DTM_color={FOLDER_3} \
    mnx_dtm.tile_geometry.tile_coord_scale={tile_coord_scale} \
    mnx_dtm.tile_geometry.tile_width={tile_width} \
    mnx_dtm.buffer.size={buffer_size} \
    mnx_dsm.tile_geometry.tile_coord_scale={tile_coord_scale} \
    mnx_dsm.tile_geometry.tile_width={tile_width} \
    mnx_dsm.buffer.size={buffer_size} \
    mnx_dtm_dens.tile_geometry.tile_coord_scale={tile_coord_scale} \
    mnx_dtm_dens.tile_geometry.tile_width={tile_width} \
    mnx_dtm_dens.buffer.size={buffer_size} \
    """
    )

    assert_output_folders_contains_expected_number_of_file(
        output=output_dir, nb_raster_expected=nb_raster_expected, water=water
    )
    assert_las_buffer_is_not_empty(output_dir)


def execute_test_end_to_end_docker(
    input_filename: str,
    input_dir: str,
    output_dir: str,
    nb_raster_expected: int,
    water: bool = False,
    tile_coord_scale: int = 1000,
    tile_width: int = 1000,
    buffer_size: int = 100,
):
    """
    Verify :
        - good number of raster created on final folders with docker
    """
    os.system(
        f"""
    docker run --rm \
    -v {input_dir}:/input \
    -v {output_dir}:/output \
    lidar_hd/ct_view:{VERSION} \
    python -m ctview.main_ctview \
    io.input_filename={input_filename} \
    io.input_dir=/input \
    io.output_dir=/output \
    mnx_dtm.color.cycles_DTM_colored=[1,2,4] \
    io.output_folder_map_density={FOLDER_1} \
    io.output_folder_map_class_color={FOLDER_2} \
    io.output_folder_map_DTM_color={FOLDER_3} \
    mnx_dtm.tile_geometry.tile_coord_scale={tile_coord_scale} \
    mnx_dtm.tile_geometry.tile_width={tile_width} \
    mnx_dtm.buffer.size={buffer_size} \
    mnx_dsm.tile_geometry.tile_coord_scale={tile_coord_scale} \
    mnx_dsm.tile_geometry.tile_width={tile_width} \
    mnx_dsm.buffer.size={buffer_size} \
    mnx_dtm_dens.tile_geometry.tile_coord_scale=10 \
    mnx_dtm_dens.tile_geometry.tile_width={tile_width} \
    mnx_dtm_dens.buffer.size={buffer_size} \
    """
    )

    assert_output_folders_contains_expected_number_of_file(
        output=output_dir, nb_raster_expected=nb_raster_expected, water=water
    )
    assert_las_buffer_is_not_empty(output_dir)


def test_execute_end_to_end_quick():
    # 1/1 small 1 dalle
    execute_test_end_to_end(
        input_filename=INPUT_FILENAME_1,
        input_dir=INPUT_1,
        output_dir=OUTPUT_1,
        nb_raster_expected=NB_FILE_EXPECTED_1,
        tile_coord_scale=TILE_COORD_SCALE,
        tile_width=TILE_WIDTH,
        buffer_size=BUFFER_SIZE,
    )
    execute_test_end_to_end_docker(
        input_filename=INPUT_FILENAME_1,
        input_dir=INPUT_1,
        output_dir=OUTPUT_1bis,
        nb_raster_expected=NB_FILE_EXPECTED_1,
        tile_coord_scale=TILE_COORD_SCALE,
        tile_width=TILE_WIDTH,
        buffer_size=BUFFER_SIZE,
    )


@pytest.mark.slow
def test_execute_end_to_end_slow():
    # 1/3 water 1 dalle
    execute_test_end_to_end(
        input_filename=INPUT_FILENAME_2,
        input_dir=INPUT_2,
        output_dir=OUTPUT_2,
        nb_raster_expected=NB_FILE_EXPECTED_2,
        water=True,
        tile_coord_scale=TILE_COORD_SCALE,
        tile_width=TILE_WIDTH,
        buffer_size=BUFFER_SIZE,
    )
    execute_test_end_to_end_docker(
        input_filename=INPUT_FILENAME_2,
        input_dir=INPUT_2,
        output_dir=OUTPUT_2bis,
        nb_raster_expected=NB_FILE_EXPECTED_2,
        water=True,
        tile_coord_scale=TILE_COORD_SCALE,
        tile_width=TILE_WIDTH,
        buffer_size=BUFFER_SIZE,
    )
    # 2/3 big 1 dalle
    execute_test_end_to_end(
        input_filename=INPUT_FILENAME_3, input_dir=INPUT_3, output_dir=OUTPUT_3, nb_raster_expected=NB_FILE_EXPECTED_3
    )
    execute_test_end_to_end_docker(
        input_filename=INPUT_FILENAME_3,
        input_dir=INPUT_3,
        output_dir=OUTPUT_3bis,
        nb_raster_expected=NB_FILE_EXPECTED_3,
    )
    # 3/3 big 4 dalles
    execute_test_end_to_end(
        input_filename=INPUT_FILENAME_41,
        input_dir=INPUT_4,
        output_dir=OUTPUT_4,
        nb_raster_expected=NB_FILE_EXPECTED_41,
    )
    execute_test_end_to_end(
        input_filename=INPUT_FILENAME_42,
        input_dir=INPUT_4,
        output_dir=OUTPUT_4,
        nb_raster_expected=NB_FILE_EXPECTED_42,
    )
    execute_test_end_to_end(
        input_filename=INPUT_FILENAME_43,
        input_dir=INPUT_4,
        output_dir=OUTPUT_4,
        nb_raster_expected=NB_FILE_EXPECTED_43,
    )
    execute_test_end_to_end(
        input_filename=INPUT_FILENAME_44,
        input_dir=INPUT_4,
        output_dir=OUTPUT_4,
        nb_raster_expected=NB_FILE_EXPECTED_44,
    )
    execute_test_end_to_end_docker(
        input_filename=INPUT_FILENAME_41,
        input_dir=INPUT_4,
        output_dir=OUTPUT_4bis,
        nb_raster_expected=NB_FILE_EXPECTED_41,
    )
    execute_test_end_to_end_docker(
        input_filename=INPUT_FILENAME_42,
        input_dir=INPUT_4,
        output_dir=OUTPUT_4bis,
        nb_raster_expected=NB_FILE_EXPECTED_42,
    )
    execute_test_end_to_end_docker(
        input_filename=INPUT_FILENAME_43,
        input_dir=INPUT_4,
        output_dir=OUTPUT_4bis,
        nb_raster_expected=NB_FILE_EXPECTED_43,
    )
    execute_test_end_to_end_docker(
        input_filename=INPUT_FILENAME_44,
        input_dir=INPUT_4,
        output_dir=OUTPUT_4bis,
        nb_raster_expected=NB_FILE_EXPECTED_44,
    )
