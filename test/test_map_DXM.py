import os
import shutil
from pathlib import Path

import rasterio
from hydra import compose, initialize

import ctview.map_DXM as map_DXM

# GENERAL
OUTPUT_DIR = Path("tmp") / "map_DXM"
COORDX = 77055
COORDY = 627760
TILE_COORD_SCALE = 10
TILE_WIDTH = 50
SPATIAL_REFERENCE = "EPSG:2154"

INPUT_DIR_LAZ = os.path.join("data", "laz")
INPUT_DIR_LAS = os.path.join("data", "las")
INPUT_DIR_RASTER = os.path.join("data", "raster")


INPUT_FILENAME = f"test_data_{COORDX}_{COORDY}_LA93_IGN69.laz"
TILENAME = os.path.splitext(INPUT_FILENAME)[0]
INPUT_FILE = os.path.join(INPUT_DIR_LAZ, INPUT_FILENAME)

with initialize(version_base="1.2", config_path="../configs"):
    # config is relative to a module
    CONFIG_2 = compose(
        config_name="config_ctview",
        overrides=[
            f"tile_geometry.tile_coord_scale={TILE_COORD_SCALE}",
            f"tile_geometry.tile_width={TILE_WIDTH}",
        ],
    )

EXPECTED_DTM_INTERP = os.path.join("DTM", "test_data_77055_627760_LA93_IGN69_interp.tif")
EXPECTED_DTM_HILLSHADE = os.path.join("tmp_dtm", "hillshade", "test_data_77055_627760_LA93_IGN69_hillshade.tif")

EXPECTED_DSM_INTERP = os.path.join("DSM", "test_data_77055_627760_LA93_IGN69_interp.tif")
EXPECTED_DSM_HILLSHADE = os.path.join("tmp_dsm", "hillshade", "test_data_77055_627760_LA93_IGN69_hillshade.tif")

EXPECTED_DTM_DENS_INTERP = os.path.join("DTM_DENS", "test_data_77055_627760_LA93_IGN69_interp.tif")
EXPECTED_DTM_DENS_HILLSHADE = os.path.join(
    "tmp_dtm_dens", "hillshade", "test_data_77055_627760_LA93_IGN69_hillshade.tif"
)


def setup_module(module):
    try:
        shutil.rmtree(OUTPUT_DIR)

    except FileNotFoundError:
        pass
    os.mkdir(OUTPUT_DIR)


def test_create_DTM_with_hillshade_one_las_default_pixelsize():
    """
    Verify :
        - .tif are created
        - output is the raster hillshaded
    """
    output_dir = os.path.join(OUTPUT_DIR, "dtm_default_pixelsize")
    raster_dxm_raw = os.path.join(
        output_dir,
        CONFIG_2.dtm.intermediate_dirs.dxm_raw,
        f"{TILENAME}_interp{CONFIG_2.dtm.extension}",
    )
    raster_dxm_hillshade = os.path.join(
        output_dir,
        CONFIG_2.dtm.intermediate_dirs.dxm_hillshade,
        f"{TILENAME}_hillshade{CONFIG_2.dtm.extension}",
    )
    map_DXM.create_dxm_with_hillshade_one_las(
        input_file=INPUT_FILE,
        output_dxm_raw=raster_dxm_raw,
        output_dxm_hillshade=raster_dxm_hillshade,
        pixel_size=CONFIG_2.dtm.pixel_size,
        keep_classes=CONFIG_2.dtm.keep_classes,
        dxm_interpolation=CONFIG_2.dtm.interpolation,
        config=CONFIG_2,
    )

    assert os.path.isfile(os.path.join(output_dir, EXPECTED_DTM_INTERP))
    assert os.path.isfile(os.path.join(output_dir, EXPECTED_DTM_HILLSHADE))
    assert raster_dxm_hillshade == os.path.join(output_dir, EXPECTED_DTM_HILLSHADE)


def test_create_DSM_with_hillshade_one_las_default_pixelsize():
    """
    Verify :
        - .tif are created
        - output is the raster hillshaded
    """
    output_dir = os.path.join(OUTPUT_DIR, "dsm_default_pixelsize")
    raster_dxm_raw = os.path.join(
        output_dir,
        CONFIG_2.class_map.intermediate_dirs.dxm_raw,
        f"{TILENAME}_interp{CONFIG_2.class_map.extension}",
    )
    raster_dxm_hillshade = os.path.join(
        output_dir,
        CONFIG_2.class_map.intermediate_dirs.dxm_hillshade,
        f"{TILENAME}_hillshade{CONFIG_2.class_map.extension}",
    )
    map_DXM.create_dxm_with_hillshade_one_las(
        input_file=INPUT_FILE,
        output_dxm_raw=raster_dxm_raw,
        output_dxm_hillshade=raster_dxm_hillshade,
        pixel_size=CONFIG_2.class_map.pixel_size,
        keep_classes=CONFIG_2.class_map.keep_classes,
        dxm_interpolation=CONFIG_2.class_map.dxm_interpolation,
        config=CONFIG_2,
        type_raster="dsm",
    )

    assert os.path.isfile(os.path.join(output_dir, EXPECTED_DSM_INTERP))
    assert os.path.isfile(os.path.join(output_dir, EXPECTED_DSM_HILLSHADE))
    assert raster_dxm_hillshade == os.path.join(output_dir, EXPECTED_DSM_HILLSHADE)


def test_create_dtm_with_hillshade_one_las_5M_pixelsize():
    """
    Verify :
        - .tif are created
        - output is the raster hillshaded
        - pixel size = 5 meters
    """
    output_dir = os.path.join(OUTPUT_DIR, "dtm_5m_density")
    raster_dxm_raw = os.path.join(
        output_dir,
        CONFIG_2.density.intermediate_dirs.dxm_raw,
        f"{TILENAME}_interp{CONFIG_2.density.extension}",
    )
    raster_dxm_hillshade = os.path.join(
        output_dir,
        CONFIG_2.density.intermediate_dirs.dxm_hillshade,
        f"{TILENAME}_hillshade{CONFIG_2.density.extension}",
    )
    map_DXM.create_dxm_with_hillshade_one_las(
        input_file=INPUT_FILE,
        output_dxm_raw=raster_dxm_raw,
        output_dxm_hillshade=raster_dxm_hillshade,
        pixel_size=5,
        keep_classes=CONFIG_2.density.keep_classes,
        dxm_interpolation=CONFIG_2.density.dxm_interpolation,
        config=CONFIG_2,
        type_raster="dtm_dens",
    )

    assert os.path.isfile(os.path.join(output_dir, EXPECTED_DTM_DENS_INTERP))
    assert raster_dxm_hillshade == os.path.join(output_dir, EXPECTED_DTM_DENS_HILLSHADE)
    with rasterio.open(raster_dxm_hillshade) as raster:
        assert raster.res == (5, 5)


def test_create_dtm_with_hillshade_one_las_1M_pixelsize():
    """
    Verify :
        - .tif are created
        - output is the raster hillshaded
        - pixel size = 1 meters
    """
    output_dir = os.path.join(OUTPUT_DIR, "dtm_1m")
    raster_dxm_raw = os.path.join(
        output_dir,
        CONFIG_2.dtm.intermediate_dirs.dxm_raw,
        f"{TILENAME}_interp{CONFIG_2.dtm.extension}",
    )
    raster_dxm_hillshade = os.path.join(
        output_dir,
        CONFIG_2.dtm.intermediate_dirs.dxm_hillshade,
        f"{TILENAME}_hillshade{CONFIG_2.dtm.extension}",
    )
    map_DXM.create_dxm_with_hillshade_one_las(
        input_file=INPUT_FILE,
        output_dxm_raw=raster_dxm_raw,
        output_dxm_hillshade=raster_dxm_hillshade,
        pixel_size=1,
        keep_classes=CONFIG_2.dtm.keep_classes,
        dxm_interpolation=CONFIG_2.dtm.interpolation,
        config=CONFIG_2,
        type_raster="dtm",
    )

    assert os.path.isfile(os.path.join(output_dir, EXPECTED_DTM_INTERP))
    assert raster_dxm_hillshade == os.path.join(output_dir, EXPECTED_DTM_HILLSHADE)
    with rasterio.open(raster_dxm_hillshade) as raster:
        assert raster.res == (1, 1)


def test_create_dsm_with_hillshade_one_las_50CM_pixelsize():
    """
    Verify :
        - .tif are created
        - output is the raster hillshaded
        - pixel size = 0.5 meters
    """
    output_dir = os.path.join(OUTPUT_DIR, "dsm_50cm")

    raster_dxm_raw = os.path.join(
        output_dir,
        CONFIG_2.class_map.intermediate_dirs.dxm_raw,
        f"{TILENAME}_interp{CONFIG_2.class_map.extension}",
    )
    raster_dxm_hillshade = os.path.join(
        output_dir,
        CONFIG_2.class_map.intermediate_dirs.dxm_hillshade,
        f"{TILENAME}_hillshade{CONFIG_2.class_map.extension}",
    )
    map_DXM.create_dxm_with_hillshade_one_las(
        input_file=INPUT_FILE,
        output_dxm_raw=raster_dxm_raw,
        output_dxm_hillshade=raster_dxm_hillshade,
        pixel_size=0.5,
        keep_classes=CONFIG_2.class_map.keep_classes,
        dxm_interpolation=CONFIG_2.class_map.dxm_interpolation,
        config=CONFIG_2,
        type_raster="dsm",
    )

    assert os.path.isfile(os.path.join(output_dir, EXPECTED_DSM_INTERP))
    assert raster_dxm_hillshade == os.path.join(output_dir, EXPECTED_DSM_HILLSHADE)
    with rasterio.open(raster_dxm_hillshade) as raster:
        assert raster.res == (0.5, 0.5)
