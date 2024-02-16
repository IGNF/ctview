import os
import shutil
import test.utils.point_cloud_utils as pcu
import numpy as np
from pathlib import Path


import pytest
import rasterio
from hydra import compose, initialize

from ctview.main_ctview import main

INPUT_DIR_SMALL = Path("data") / "las" / "ground"
INPUT_FILENAME_SMALL1 = "test_data_77055_627755_LA93_IGN69.las"
INPUT_FILENAME_SMALL2 = "test_data_77055_627760_LA93_IGN69.las"

INPUT_DIR_WATER = Path("data") / "laz" / "water"
INPUT_FILENAME_WATER = "Semis_2021_0785_6378_LA93_IGN69_water.laz"

OUTPUT_DIR = Path("tmp") / "main_ctview"
OUTPUT_DIR_WATER = OUTPUT_DIR / "main_ctview_water"

OUTPUT_FOLDER_DENS = "DENS_FINAL_CUSTOM"
OUTPUT_FOLDER_CLASS = "ACC_5_fusion_FINAL"

EXPECTED_OUTPUT_DTM_1C = Path("DTM") / "color" / "1cycle"
EXPECTED_OUTPUT_DTM_4C = Path("DTM") / "color" / "4cycles"


# (input_dir, input_filename, output_dir, expected_nb_file)
main_data = [
    (INPUT_DIR_SMALL, INPUT_FILENAME_SMALL1, OUTPUT_DIR / "main_ctview_2_tiles", 1),
    (INPUT_DIR_SMALL, INPUT_FILENAME_SMALL2, OUTPUT_DIR / "main_ctview_2_tiles", 2),
]


def setup_module(module):
    try:
        shutil.rmtree(OUTPUT_DIR)
    except FileNotFoundError:
        pass
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def test_main_ctview_map_density():
    tile_width = 50
    tile_coord_scale = 10
    pixel_size = 2
    buffer_size = 10
    output_dir = OUTPUT_DIR / "main_ctview_map_density"
    input_tilename = os.path.splitext(INPUT_FILENAME_SMALL1)[0]
    with initialize(version_base="1.2", config_path="../configs"):
        # config is relative to a module
        cfg = compose(
            config_name="config_ctview",
            overrides=[
                f"io.input_filename={INPUT_FILENAME_SMALL1}",
                f"io.input_dir={INPUT_DIR_SMALL}",
                f"io.output_dir={output_dir}",
                "mnx_dtm.color.cycles_DTM_colored=[1,4]",
                f"io.output_folder_map_density={OUTPUT_FOLDER_DENS}",
                f"mnx_dtm.tile_geometry.tile_coord_scale={tile_coord_scale}",
                f"mnx_dtm.tile_geometry.tile_width={tile_width}",
                f"mnx_dtm.buffer.size={buffer_size}",
                f"mnx_dsm.tile_geometry.tile_coord_scale={tile_coord_scale}",
                f"mnx_dsm.tile_geometry.tile_width={tile_width}",
                f"mnx_dsm.buffer.size={buffer_size}",
                f"mnx_dtm_dens.tile_geometry.tile_coord_scale={tile_coord_scale}",
                f"mnx_dtm_dens.tile_geometry.tile_width={tile_width}",
                f"mnx_dtm_dens.buffer.size={buffer_size}",
                f"mnx_dtm_dens.tile_geometry.pixel_size={pixel_size}",
            ],
        )
    main(cfg)
    with rasterio.Env():
        with rasterio.open(Path(output_dir) / OUTPUT_FOLDER_DENS / f"{input_tilename}_DENS.tif") as raster:
            data = raster.read()
            assert data.shape[0] == 3
            for ii in range(3):
                assert np.any(data[ii, :, :])


def test_main_ctview_map_density_empty():
    tile_width = 1000
    tile_coord_scale = 1000
    buffer_size = 10
    output_dir = OUTPUT_DIR / "main_ctview_map_density_empty"
    input_tilename = os.path.splitext(INPUT_FILENAME_WATER)[0]
    with initialize(version_base="1.2", config_path="../configs"):
        # config is relative to a module
        cfg = compose(
            config_name="config_ctview",
            overrides=[
                f"io.input_filename={INPUT_FILENAME_WATER}",
                f"io.input_dir={INPUT_DIR_WATER}",
                f"io.output_dir={output_dir}",
                "mnx_dtm.color.cycles_DTM_colored=[1,4]",
                f"io.output_folder_map_density={OUTPUT_FOLDER_DENS}",
                f"mnx_dtm.tile_geometry.tile_coord_scale={tile_coord_scale}",
                f"mnx_dtm.tile_geometry.tile_width={tile_width}",
                f"mnx_dtm.buffer.size={buffer_size}",
                f"mnx_dsm.tile_geometry.tile_coord_scale={tile_coord_scale}",
                f"mnx_dsm.tile_geometry.tile_width={tile_width}",
                f"mnx_dsm.buffer.size={buffer_size}",
                f"mnx_dtm_dens.tile_geometry.tile_coord_scale={tile_coord_scale}",
                f"mnx_dtm_dens.tile_geometry.tile_width={tile_width}",
                f"mnx_dtm_dens.buffer.size={buffer_size}",
                f"mnx_dtm_dens.tile_geometry.pixel_size={1}",
            ],
        )
    main(cfg)

    with rasterio.Env():
        with rasterio.open(Path(output_dir) / OUTPUT_FOLDER_DENS / f"{input_tilename}_DENS.tif") as raster:
            data = raster.read()
            assert data.shape[0] == 3
            assert np.all(data == 0)


def test_main_ctview_map_class():
    tile_width = 50
    tile_coord_scale = 10
    buffer_size = 10
    output_dir = OUTPUT_DIR / "main_ctview_map_class"
    input_tilename = os.path.splitext(INPUT_FILENAME_SMALL1)[0]
    with initialize(version_base="1.2", config_path="../configs"):
        # config is relative to a module
        cfg = compose(
            config_name="config_ctview",
            overrides=[
                f"io.input_filename={INPUT_FILENAME_SMALL1}",
                f"io.input_dir={INPUT_DIR_SMALL}",
                f"io.output_dir={output_dir}",
                "mnx_dtm.color.cycles_DTM_colored=[1,4]",
                f"io.output_folder_map_class_color={OUTPUT_FOLDER_CLASS}",
                f"mnx_dtm.tile_geometry.tile_coord_scale={tile_coord_scale}",
                f"mnx_dtm.tile_geometry.tile_width={tile_width}",
                f"mnx_dtm.buffer.size={buffer_size}",
                f"mnx_dsm.tile_geometry.tile_coord_scale={tile_coord_scale}",
                f"mnx_dsm.tile_geometry.tile_width={tile_width}",
                f"mnx_dsm.buffer.size={buffer_size}",
                f"mnx_dtm_dens.tile_geometry.tile_coord_scale={tile_coord_scale}",
                f"mnx_dtm_dens.tile_geometry.tile_width={tile_width}",
                f"mnx_dtm_dens.buffer.size={buffer_size}",
                f"mnx_dtm_dens.tile_geometry.pixel_size={1}",
            ],
        )
    main(cfg)
    assert_las_buffer_is_not_empty(output=output_dir)
    with rasterio.Env():
        with rasterio.open(Path(output_dir) / "CC_4_fgcolor" / f"{input_tilename}_raster_fillgap_color.tif") as raster:
            band1 = raster.read(1)
            band2 = raster.read(2)
            band3 = raster.read(3)
            assert band1[0, 0] == 255
            assert band2[0, 0] == 128
            assert band3[0, 0] == 0
            assert raster.res == (0.5, 0.5)
        with rasterio.open(
            Path(output_dir) / OUTPUT_FOLDER_CLASS / f"{input_tilename}_fusion_DSM_class.tif"
        ) as raster:
            band1 = raster.read(1)
            band2 = raster.read(2)
            band3 = raster.read(3)
            assert band1[0, 0] is not None
            assert band2[0, 0] is not None
            assert band3[0, 0] is not None
            assert raster.res == (0.5, 0.5)


def test_main_ctview_dtm_color():
    tile_width = 50
    tile_coord_scale = 10
    buffer_size = 10
    output_dir = OUTPUT_DIR / "main_ctview_dtm_color"
    input_tilename = os.path.splitext(INPUT_FILENAME_SMALL1)[0]
    with initialize(version_base="1.2", config_path="../configs"):
        # config is relative to a module
        cfg = compose(
            config_name="config_ctview",
            overrides=[
                f"io.input_filename={INPUT_FILENAME_SMALL1}",
                f"io.input_dir={INPUT_DIR_SMALL}",
                f"io.output_dir={output_dir}",
                "mnx_dtm.color.cycles_DTM_colored=[1,4]",
                f"mnx_dtm.tile_geometry.tile_coord_scale={tile_coord_scale}",
                f"mnx_dtm.tile_geometry.tile_width={tile_width}",
                f"mnx_dtm.buffer.size={buffer_size}",
                f"mnx_dsm.tile_geometry.tile_coord_scale={tile_coord_scale}",
                f"mnx_dsm.tile_geometry.tile_width={tile_width}",
                f"mnx_dsm.buffer.size={buffer_size}",
                f"mnx_dtm_dens.tile_geometry.tile_coord_scale={tile_coord_scale}",
                f"mnx_dtm_dens.tile_geometry.tile_width={tile_width}",
                f"mnx_dtm_dens.buffer.size={buffer_size}",
                f"mnx_dtm_dens.tile_geometry.pixel_size={1}",
            ],
        )
    main(cfg)
    assert_las_buffer_is_not_empty(output=output_dir)
    with rasterio.Env():
        with rasterio.open(
            Path(output_dir) / EXPECTED_OUTPUT_DTM_1C / f"{input_tilename}_DTM_hillshade_color1c.tif"
        ) as raster:
            band1 = raster.read(1)
            band2 = raster.read(2)
            band3 = raster.read(3)
            assert band1[8, 8] == 255
            assert band2[8, 8] == 165
            assert band3[8, 8] == 0
            assert raster.res == (1, 1)
        with rasterio.open(
            Path(output_dir) / EXPECTED_OUTPUT_DTM_4C / f"{input_tilename}_DTM_hillshade_color4c.tif"
        ) as raster:
            band1 = raster.read(1)
            band2 = raster.read(2)
            band3 = raster.read(3)
            assert band1[8, 8] == 255
            assert band2[8, 8] == 151
            assert band3[8, 8] == 0
            assert raster.res == (1, 1)


@pytest.mark.parametrize(
    """input_dir, input_filename, output_dir, expected_nb_file""",
    main_data,
)
def test_main_ctview_2_files(input_dir, input_filename, output_dir, expected_nb_file):
    tile_width = 50
    tile_coord_scale = 10
    buffer_size = 10
    with initialize(version_base="1.2", config_path="../configs"):
        # config is relative to a module
        cfg = compose(
            config_name="config_ctview",
            overrides=[
                f"io.input_filename={input_filename}",
                f"io.input_dir={input_dir}",
                f"io.output_dir={output_dir}",
                "mnx_dtm.color.cycles_DTM_colored=[1,4]",
                f"io.output_folder_map_density={OUTPUT_FOLDER_DENS}",
                f"io.output_folder_map_class_color={OUTPUT_FOLDER_CLASS}",
                f"mnx_dtm.tile_geometry.tile_coord_scale={tile_coord_scale}",
                f"mnx_dtm.tile_geometry.tile_width={tile_width}",
                f"mnx_dtm.buffer.size={buffer_size}",
                f"mnx_dsm.tile_geometry.tile_coord_scale={tile_coord_scale}",
                f"mnx_dsm.tile_geometry.tile_width={tile_width}",
                f"mnx_dsm.buffer.size={buffer_size}",
                f"mnx_dtm_dens.tile_geometry.tile_coord_scale={tile_coord_scale}",
                f"mnx_dtm_dens.tile_geometry.tile_width={tile_width}",
                f"mnx_dtm_dens.buffer.size={buffer_size}",
                f"mnx_dtm_dens.tile_geometry.pixel_size={1}",
            ],
        )
    main(cfg)
    assert_output_folders_contains_expected_number_of_file(output=output_dir, nb_raster_expected=expected_nb_file)


def assert_output_folders_contains_expected_number_of_file(output: str, nb_raster_expected: int):
    """
    Verify :
        - good number of raster created on final folders
        - exception for density when there is a lot of water
    """
    # good number of raster created
    for folder in [OUTPUT_FOLDER_DENS, OUTPUT_FOLDER_CLASS, EXPECTED_OUTPUT_DTM_1C, EXPECTED_OUTPUT_DTM_4C]:
        path = Path(output) / folder
        assert len(os.listdir(path)) == nb_raster_expected


def assert_las_buffer_is_not_empty(output: str):
    las_dir = Path(output) / "tmp_dtm_dens" / "buffer"
    for las in os.listdir(las_dir):
        assert pcu.get_nb_points(os.path.join(las_dir, las)) > 0
