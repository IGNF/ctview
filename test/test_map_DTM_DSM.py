import os
import shutil
import test.utils.point_cloud_utils as pcu
from pathlib import Path

import rasterio
from hydra import compose, initialize

import ctview.map_DTM_DSM as map_DTM_DSM
from ctview.utils_folder import dico_folder_template

# GENERAL
TMP = "tmp"
COORDX = 77055
COORDY = 627760
TILE_COORD_SCALE = 10
TILE_WIDTH = 50
BUFFER_SIZE = 10
SPATIAL_REFERENCE = "EPSG:2154"

INPUT_DIR_LAZ = os.path.join("data", "laz")
INPUT_DIR_LAS = os.path.join("data", "las")
INPUT_DIR_RASTER = os.path.join("data", "raster")

# BUFFER
INPUT_DIR_WITHOUT_BUFFER = os.path.join(INPUT_DIR_LAS, "ground")
INPUT_FILE_WITHOUT_BUFFER = os.path.join(INPUT_DIR_WITHOUT_BUFFER, f"test_data_{COORDX}_{COORDY}_LA93_IGN69.las")

OUTPUT_DIR_BUFFER = os.path.join(TMP, "buffer")
OUTPUT_FILE_WITH_BUFFER = os.path.join(OUTPUT_DIR_BUFFER, f"test_data_{COORDX}_{COORDY}_LA93_IGN69.las")

EXPECTED_OUTPUT_NB_POINTS = 47037


# HILLSHADE
INPUT_WITHOUT_HILLSHADE = os.path.join(INPUT_DIR_RASTER, f"test_data_{COORDX}_{COORDY}_LA93_IGN69_interp.tif")

OUTPUT_DIR_HILLSHADE = os.path.join(TMP, "hillshade")

EXPECTED_OUTPUT_WITH_HILLSHADE = os.path.join(
    OUTPUT_DIR_HILLSHADE, f"test_data_{COORDX}_{COORDY}_LA93_IGN69_hillshade.tif"
)


# COLOR
INPUT_LAZ_TILENAME_WITHOUT_COLOR = f"test_data_{COORDX}_{COORDY}_LA93_IGN69.laz"
INPUT_RASTER_WITHOUT_COLOR = os.path.join(INPUT_DIR_RASTER, f"test_data_{COORDX}_{COORDY}_LA93_IGN69_interp.tif")

OUTPUT_DIR_COLOR = os.path.join("tmp", "color")
OUTPUT_DIR_LUT = os.path.join(OUTPUT_DIR_COLOR, "LUT")

EXPECTED_DTM_COLOR_1CYCLE = os.path.join(
    OUTPUT_DIR_COLOR, "DTM", "color", "1cycle", f"test_data_{COORDX}_{COORDY}_LA93_IGN69_DTM_hillshade_color1c.tif"
)
EXPECTED_DTM_COLOR_5CYCLES = os.path.join(
    OUTPUT_DIR_COLOR, "DTM", "color", "5cycles", f"test_data_{COORDX}_{COORDY}_LA93_IGN69_DTM_hillshade_color5c.tif"
)


# TOOLS
OUTPUT_DIR_TOOLS = Path(TMP) / "tools"

EXPECTED_DTM_DIR = os.path.join(OUTPUT_DIR_TOOLS, "DTM")
EXPECTED_DTM_BUFFER_DIR = os.path.join(OUTPUT_DIR_TOOLS, "tmp_dtm", "buffer")
EXPECTED_DTM_HILLSHADE_DIR = os.path.join(OUTPUT_DIR_TOOLS, "tmp_dtm", "hillshade")
EXPECTED_DTM_COLOR_DIR = os.path.join(OUTPUT_DIR_TOOLS, "DTM", "color")
EXPECTED_DSM_DIR = os.path.join(OUTPUT_DIR_TOOLS, "DSM")
EXPECTED_DSM_BUFFER_DIR = os.path.join(OUTPUT_DIR_TOOLS, "tmp_dsm", "buffer")
EXPECTED_DSM_HILLSHADE_DIR = os.path.join(OUTPUT_DIR_TOOLS, "tmp_dsm", "hillshade")
EXPECTED_DTM_DENS_DIR = os.path.join(OUTPUT_DIR_TOOLS, "DTM_DENS")
EXPECTED_DTM_DENS_BUFFER_DIR = os.path.join(OUTPUT_DIR_TOOLS, "tmp_dtm_dens", "buffer")
EXPECTED_DTM_DENS_HILLSHADE_DIR = os.path.join(OUTPUT_DIR_TOOLS, "tmp_dtm_dens", "hillshade")


# ALL
INPUT_TILENAME_FOR_ALL = f"test_data_{COORDX}_{COORDY}_LA93_IGN69.laz"
INPUT_FILENAME_FOR_ALL = os.path.join(INPUT_DIR_LAZ, INPUT_TILENAME_FOR_ALL)

OUTPUT_DIR_ALL = os.path.join(TMP, "all")
OUTPUT_DIR_MNX = os.path.join(OUTPUT_DIR_ALL, "mnx")
OUTPUT_DIR_MNX_HS = os.path.join(OUTPUT_DIR_ALL, "mnx_hs")
OUTPUT_DIR_MNT_MNS_MNTDENS_HS = os.path.join(OUTPUT_DIR_ALL, "mnt_mns_mntdens_hs")

with initialize(version_base="1.2", config_path="../configs"):
    # config is relative to a module
    CONFIG_2 = compose(
        config_name="config_ctview",
        overrides=[
            f"mnx_dtm.tile_geometry.tile_coord_scale={TILE_COORD_SCALE}",
            f"mnx_dtm.tile_geometry.tile_width={TILE_WIDTH}",
            f"mnx_dtm.buffer.size={BUFFER_SIZE}",
            f"mnx_dtm_dens.tile_geometry.tile_coord_scale={TILE_COORD_SCALE}",
            f"mnx_dtm_dens.tile_geometry.tile_width={TILE_WIDTH}",
            f"mnx_dtm_dens.buffer.size={BUFFER_SIZE}",
            f"mnx_dsm.tile_geometry.tile_coord_scale={TILE_COORD_SCALE}",
            f"mnx_dsm.tile_geometry.tile_width={TILE_WIDTH}",
            f"mnx_dsm.buffer.size={BUFFER_SIZE}",
        ],
    )

EXPECTED_DTM_BUFFER = os.path.join("tmp_dtm", "buffer", "test_data_77055_627760_LA93_IGN69_buffer.las")
EXPECTED_DTM_INTERP = os.path.join("DTM", "test_data_77055_627760_LA93_IGN69_interp.tif")
EXPECTED_DTM_HILLSHADE = os.path.join("tmp_dtm", "hillshade", "test_data_77055_627760_LA93_IGN69_hillshade.tif")

EXPECTED_DSM_BUFFER = os.path.join("tmp_dsm", "buffer", "test_data_77055_627760_LA93_IGN69_buffer.las")
EXPECTED_DSM_INTERP = os.path.join("DSM", "test_data_77055_627760_LA93_IGN69_interp.tif")
EXPECTED_DSM_HILLSHADE = os.path.join("tmp_dsm", "hillshade", "test_data_77055_627760_LA93_IGN69_hillshade.tif")

EXPECTED_DTM_DENS_BUFFER = os.path.join("tmp_dtm_dens", "buffer", "test_data_77055_627760_LA93_IGN69_buffer.las")
EXPECTED_DTM_DENS_INTERP = os.path.join("DTM_DENS", "test_data_77055_627760_LA93_IGN69_interp.tif")
EXPECTED_DTM_DENS_HILLSHADE = os.path.join(
    "tmp_dtm_dens", "hillshade", "test_data_77055_627760_LA93_IGN69_hillshade.tif"
)


def setup_module(module):
    try:
        shutil.rmtree(TMP)

    except FileNotFoundError:
        pass
    os.mkdir(TMP)
    os.mkdir(OUTPUT_DIR_BUFFER)
    os.mkdir(OUTPUT_DIR_HILLSHADE)
    os.mkdir(OUTPUT_DIR_COLOR)
    os.mkdir(OUTPUT_DIR_LUT)
    os.mkdir(OUTPUT_DIR_TOOLS)
    os.mkdir(OUTPUT_DIR_ALL)


def test_run_pdaltools_buffer():
    map_DTM_DSM.run_pdaltools_buffer(
        input_dir=INPUT_DIR_WITHOUT_BUFFER,
        tile_filename=INPUT_FILE_WITHOUT_BUFFER,
        output_filename=OUTPUT_FILE_WITH_BUFFER,
        buffer_width=BUFFER_SIZE,
        tile_width=TILE_WIDTH,
        tile_coord_scale=TILE_COORD_SCALE,
        spatial_ref=SPATIAL_REFERENCE,
    )

    assert os.path.isfile(OUTPUT_FILE_WITH_BUFFER)
    assert pcu.get_nb_points(OUTPUT_FILE_WITH_BUFFER) == EXPECTED_OUTPUT_NB_POINTS


def test_add_hillshade_one_raster():
    """
    Verify :
        - .tif is created
    """
    assert os.path.isfile(INPUT_WITHOUT_HILLSHADE)
    map_DTM_DSM.add_hillshade_one_raster(
        input_raster=INPUT_WITHOUT_HILLSHADE, output_raster=EXPECTED_OUTPUT_WITH_HILLSHADE
    )
    assert os.path.isfile(EXPECTED_OUTPUT_WITH_HILLSHADE)


def test_color_raster_dtm_hillshade_with_LUT():
    """
    Verify :
        - tifs is created
    """
    # preparation
    list_cycles = [1, 5]
    # test function
    map_DTM_DSM.color_raster_dtm_hillshade_with_LUT(
        input_initial_basename=INPUT_LAZ_TILENAME_WITHOUT_COLOR,
        input_raster=INPUT_RASTER_WITHOUT_COLOR,
        output_dir=OUTPUT_DIR_COLOR,
        list_c=list_cycles,
        dico_fld=dico_folder_template,
    )
    assert os.path.exists(EXPECTED_DTM_COLOR_1CYCLE)
    assert os.path.exists(EXPECTED_DTM_COLOR_5CYCLES)


def test_create_output_tree():
    """Test if all folders are created"""
    map_DTM_DSM.create_output_tree(output_dir=OUTPUT_DIR_TOOLS)

    assert os.path.isdir(EXPECTED_DTM_DIR)
    assert os.path.isdir(EXPECTED_DTM_BUFFER_DIR)
    assert os.path.isdir(EXPECTED_DTM_HILLSHADE_DIR)
    assert os.path.isdir(EXPECTED_DTM_COLOR_DIR)
    assert os.path.isdir(EXPECTED_DSM_DIR)
    assert os.path.isdir(EXPECTED_DSM_BUFFER_DIR)
    assert os.path.isdir(EXPECTED_DSM_HILLSHADE_DIR)
    assert os.path.isdir(EXPECTED_DTM_DENS_DIR)
    assert os.path.isdir(EXPECTED_DTM_DENS_BUFFER_DIR)
    assert os.path.isdir(EXPECTED_DTM_DENS_HILLSHADE_DIR)


def test_create_mnx_one_las():
    """
    Verify :
        - every 4 tifs are created
        - output is the raster hillshaded
    """
    output_raster = map_DTM_DSM.create_mnx_one_las(
        input_file=INPUT_FILENAME_FOR_ALL, output_dir=OUTPUT_DIR_MNX, config=CONFIG_2.mnx_dtm, type_raster="dtm"
    )
    assert pcu.get_nb_points(os.path.join(OUTPUT_DIR_MNX, EXPECTED_DTM_BUFFER)) > 0
    assert os.path.isfile(os.path.join(OUTPUT_DIR_MNX, EXPECTED_DTM_INTERP))
    assert os.path.isfile(os.path.join(OUTPUT_DIR_MNX, EXPECTED_DTM_HILLSHADE))
    assert output_raster == os.path.join(OUTPUT_DIR_MNX, EXPECTED_DTM_HILLSHADE)


def test_create_DTM_with_hillshade_one_las_default_pixelsize():
    """
    Verify :
        - .tif are created
        - output is the raster hillshaded
    """
    output_raster = map_DTM_DSM.create_dxm_with_hillshade_one_las_XM(
        input_file=INPUT_FILENAME_FOR_ALL,
        output_dir=OUTPUT_DIR_MNX_HS,
        config=CONFIG_2.mnx_dtm,
    )

    assert pcu.get_nb_points(os.path.join(OUTPUT_DIR_MNX_HS, EXPECTED_DTM_BUFFER)) > 0
    assert os.path.isfile(os.path.join(OUTPUT_DIR_MNX_HS, EXPECTED_DTM_INTERP))
    assert os.path.isfile(os.path.join(OUTPUT_DIR_MNX_HS, EXPECTED_DTM_HILLSHADE))
    assert output_raster == os.path.join(OUTPUT_DIR_MNX_HS, EXPECTED_DTM_HILLSHADE)


def test_create_DSM_with_hillshade_one_las_default_pixelsize():
    """
    Verify :
        - .tif are created
        - output is the raster hillshaded
    """
    output_raster = map_DTM_DSM.create_dxm_with_hillshade_one_las_XM(
        input_file=INPUT_FILENAME_FOR_ALL,
        output_dir=OUTPUT_DIR_MNX_HS,
        config=CONFIG_2.mnx_dsm,
        type_raster="dsm",
    )

    assert pcu.get_nb_points(os.path.join(OUTPUT_DIR_MNX_HS, EXPECTED_DSM_BUFFER)) > 0
    assert os.path.isfile(os.path.join(OUTPUT_DIR_MNX_HS, EXPECTED_DSM_INTERP))
    assert os.path.isfile(os.path.join(OUTPUT_DIR_MNX_HS, EXPECTED_DSM_HILLSHADE))
    assert output_raster == os.path.join(OUTPUT_DIR_MNX_HS, EXPECTED_DSM_HILLSHADE)


def test_create_dtm_with_hillshade_one_las_5M_pixelsize():
    """
    Verify :
        - .tif are created
        - output is the raster hillshaded
        - pixel size = 5 meters
    """
    output_raster = map_DTM_DSM.create_dxm_with_hillshade_one_las_XM(
        input_file=INPUT_FILENAME_FOR_ALL,
        output_dir=OUTPUT_DIR_MNT_MNS_MNTDENS_HS,
        config=CONFIG_2.mnx_dtm_dens,
        type_raster="dtm_dens",
    )

    assert pcu.get_nb_points(os.path.join(OUTPUT_DIR_MNT_MNS_MNTDENS_HS, EXPECTED_DTM_DENS_BUFFER)) > 0
    assert os.path.isfile(os.path.join(OUTPUT_DIR_MNT_MNS_MNTDENS_HS, EXPECTED_DTM_DENS_INTERP))
    assert output_raster == os.path.join(OUTPUT_DIR_MNT_MNS_MNTDENS_HS, EXPECTED_DTM_DENS_HILLSHADE)
    with rasterio.open(output_raster) as raster:
        assert raster.res == (5, 5)


def test_create_dtm_with_hillshade_one_las_1M_pixelsize():
    """
    Verify :
        - .tif are created
        - output is the raster hillshaded
        - pixel size = 1 meters
    """
    output_raster = map_DTM_DSM.create_dxm_with_hillshade_one_las_XM(
        input_file=INPUT_FILENAME_FOR_ALL,
        output_dir=OUTPUT_DIR_MNT_MNS_MNTDENS_HS,
        config=CONFIG_2.mnx_dtm,
        type_raster="dtm",
    )

    assert pcu.get_nb_points(os.path.join(OUTPUT_DIR_MNT_MNS_MNTDENS_HS, EXPECTED_DTM_BUFFER)) > 0
    assert os.path.isfile(os.path.join(OUTPUT_DIR_MNT_MNS_MNTDENS_HS, EXPECTED_DTM_INTERP))
    assert output_raster == os.path.join(OUTPUT_DIR_MNT_MNS_MNTDENS_HS, EXPECTED_DTM_HILLSHADE)
    with rasterio.open(output_raster) as raster:
        assert raster.res == (1, 1)


def test_create_dsm_with_hillshade_one_las_50CM_pixelsize():
    """
    Verify :
        - .tif are created
        - output is the raster hillshaded
        - pixel size = 0.5 meters
    """
    output_raster = map_DTM_DSM.create_dxm_with_hillshade_one_las_XM(
        input_file=INPUT_FILENAME_FOR_ALL,
        output_dir=OUTPUT_DIR_MNT_MNS_MNTDENS_HS,
        config=CONFIG_2.mnx_dsm,
        type_raster="dsm",
    )

    assert pcu.get_nb_points(os.path.join(OUTPUT_DIR_MNT_MNS_MNTDENS_HS, EXPECTED_DSM_BUFFER)) > 0
    assert os.path.isfile(os.path.join(OUTPUT_DIR_MNT_MNS_MNTDENS_HS, EXPECTED_DSM_INTERP))
    assert output_raster == os.path.join(OUTPUT_DIR_MNT_MNS_MNTDENS_HS, EXPECTED_DSM_HILLSHADE)
    with rasterio.open(output_raster) as raster:
        assert raster.res == (0.5, 0.5)
