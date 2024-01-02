import os
import shutil
import test.utils.point_cloud_utils as pcu

import rasterio
from hydra import compose, initialize

from ctview.map_DTM_DSM import (
    create_dsm_with_hillshade_one_las_50CM,
    create_dtm_with_hillshade_one_las_1M,
    create_dtm_with_hillshade_one_las_5M,
    create_dxm_with_hillshade_one_las_XM,
    create_mnx_one_las,
)

# choice tile
coordX = 77055
coordY = 627760

# input
input_dir = os.path.join("data", "laz")
input_tilename = f"test_data_{coordX}_{coordY}_LA93_IGN69.laz"
input_filename = os.path.join(input_dir, input_tilename)

# output
tmp_path = os.path.join("data", "labo")
output_dir = os.path.join(tmp_path, "mnx")
output_dir_2 = os.path.join(tmp_path, "mnx_hs")
output_dir_3 = os.path.join(tmp_path, "mnt_mns_mntdens_hs")


# config
TILE_COORD_SCALE = 10
TILE_WIDTH = 50
BUFFER_SIZE = 10
with initialize(version_base="1.2", config_path="../configs"):
    # config is relative to a module
    cfg = compose(
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

# expected
expected_dtm_buffer_file = os.path.join("tmp_dtm", "buffer", "test_data_77055_627760_LA93_IGN69_buffer.las")
expected_dtm_interpolation_file = os.path.join("DTM", "test_data_77055_627760_LA93_IGN69_interp.tif")
expected_dtm_hillshade_file = os.path.join("tmp_dtm", "hillshade", "test_data_77055_627760_LA93_IGN69_hillshade.tif")

expected_dsm_buffer_file = os.path.join("tmp_dsm", "buffer", "test_data_77055_627760_LA93_IGN69_buffer.las")
expected_dsm_interpolation_file = os.path.join("DSM", "test_data_77055_627760_LA93_IGN69_interp.tif")
expected_dsm_hillshade_file = os.path.join("tmp_dsm", "hillshade", "test_data_77055_627760_LA93_IGN69_hillshade.tif")

expected_dtm_dens_buffer_file = os.path.join("tmp_dtm_dens", "buffer", "test_data_77055_627760_LA93_IGN69_buffer.las")
expected_dtm_dens_interpolation_file = os.path.join("DTM_DENS", "test_data_77055_627760_LA93_IGN69_interp.tif")
expected_dtm_dens_hillshade_file = os.path.join(
    "tmp_dtm_dens", "hillshade", "test_data_77055_627760_LA93_IGN69_hillshade.tif"
)


def setup_module(module):
    try:
        shutil.rmtree(tmp_path)

    except FileNotFoundError:
        pass
    os.mkdir(tmp_path)


def test_create_mnx_one_las():
    """
    Verify :
        - every 4 tifs are created
        - output is the raster hillshaded
    """
    output_raster = create_mnx_one_las(
        input_file=input_filename, output_dir=output_dir, config=cfg.mnx_dtm, type_raster="dtm"
    )
    assert pcu.get_nb_points(os.path.join(output_dir, expected_dtm_buffer_file)) > 0
    assert os.path.isfile(os.path.join(output_dir, expected_dtm_interpolation_file))
    assert os.path.isfile(os.path.join(output_dir, expected_dtm_hillshade_file))
    assert output_raster == os.path.join(output_dir, expected_dtm_hillshade_file)


def test_create_DTM_with_hillshade_one_las_default_pixelsize():
    """
    Verify :
        - .tif are created
        - output is the raster hillshaded
    """
    output_raster = create_dxm_with_hillshade_one_las_XM(
        input_file=input_filename,
        output_dir=output_dir_2,
        config=cfg.mnx_dtm,
    )

    assert pcu.get_nb_points(os.path.join(output_dir_2, expected_dtm_buffer_file)) > 0
    assert os.path.isfile(os.path.join(output_dir_2, expected_dtm_interpolation_file))
    assert os.path.isfile(os.path.join(output_dir_2, expected_dtm_hillshade_file))
    assert output_raster == os.path.join(output_dir_2, expected_dtm_hillshade_file)


def test_create_DSM_with_hillshade_one_las_default_pixelsize():
    """
    Verify :
        - .tif are created
        - output is the raster hillshaded
    """
    output_raster = create_dxm_with_hillshade_one_las_XM(
        input_file=input_filename,
        output_dir=output_dir_2,
        config=cfg.mnx_dsm,
        type_raster="dsm",
    )

    assert pcu.get_nb_points(os.path.join(output_dir_2, expected_dsm_buffer_file)) > 0
    assert os.path.isfile(os.path.join(output_dir_2, expected_dsm_interpolation_file))
    assert os.path.isfile(os.path.join(output_dir_2, expected_dsm_hillshade_file))
    assert output_raster == os.path.join(output_dir_2, expected_dsm_hillshade_file)


def test_create_dtm_with_hillshade_one_las_5M_pixelsize():
    """
    Verify :
        - .tif are created
        - output is the raster hillshaded
        - pixel size = 5 meters
    """
    output_raster = create_dtm_with_hillshade_one_las_5M(
        input_file=input_filename, output_dir=output_dir_3, config=cfg.mnx_dtm_dens
    )

    assert pcu.get_nb_points(os.path.join(output_dir_3, expected_dtm_dens_buffer_file)) > 0
    assert os.path.isfile(os.path.join(output_dir_3, expected_dtm_dens_interpolation_file))
    assert output_raster == os.path.join(output_dir_3, expected_dtm_dens_hillshade_file)
    with rasterio.open(output_raster) as raster:
        assert raster.res == (5, 5)


def test_create_dtm_with_hillshade_one_las_1M_pixelsize():
    """
    Verify :
        - .tif are created
        - output is the raster hillshaded
        - pixel size = 1 meters
    """
    output_raster = create_dtm_with_hillshade_one_las_1M(
        input_file=input_filename, output_dir=output_dir_3, config=cfg.mnx_dtm
    )

    assert pcu.get_nb_points(os.path.join(output_dir_3, expected_dtm_buffer_file)) > 0
    assert os.path.isfile(os.path.join(output_dir_3, expected_dtm_interpolation_file))
    assert output_raster == os.path.join(output_dir_3, expected_dtm_hillshade_file)
    with rasterio.open(output_raster) as raster:
        assert raster.res == (1, 1)


def test_create_dsm_with_hillshade_one_las_50CM_pixelsize():
    """
    Verify :
        - .tif are created
        - output is the raster hillshaded
        - pixel size = 0.5 meters
    """
    output_raster = create_dsm_with_hillshade_one_las_50CM(
        input_file=input_filename, output_dir=output_dir_3, config=cfg.mnx_dsm
    )

    assert pcu.get_nb_points(os.path.join(output_dir_3, expected_dsm_buffer_file)) > 0
    assert os.path.isfile(os.path.join(output_dir_3, expected_dsm_interpolation_file))
    assert output_raster == os.path.join(output_dir_3, expected_dsm_hillshade_file)
    with rasterio.open(output_raster) as raster:
        assert raster.res == (0.5, 0.5)
