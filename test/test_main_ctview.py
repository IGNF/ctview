import os
import shutil
import test.utils.point_cloud_utils as pcu
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
OUTPUT_FOLDER_CLASS = "CC_6_fusion_FINAL_CUSTOM"

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
                "dtm.color.cycles_DTM_colored=[1,4]",
                f"density.output_subdir={OUTPUT_FOLDER_DENS}",
                f"class_map.output_subdir={OUTPUT_FOLDER_CLASS}",
                f"io.tile_geometry.tile_coord_scale={tile_coord_scale}",
                f"io.tile_geometry.tile_width={tile_width}",
                f"buffer.size={buffer_size}",
                f"density.pixel_size={pixel_size}",
            ],
        )
    main(cfg)
    assert_las_buffer_is_not_empty(output_dir, INPUT_FILENAME_SMALL1)
    assert os.path.isfile(Path(output_dir) / OUTPUT_FOLDER_DENS / f"{input_tilename}_DENS.tif")
    assert os.path.isfile(Path(output_dir) / OUTPUT_FOLDER_CLASS / f"{input_tilename}_fusion_DSM_class.tif")


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
                "dtm.color.cycles_DTM_colored=[1,4]",
                f"io.tile_geometry.tile_coord_scale={tile_coord_scale}",
                f"io.tile_geometry.tile_width={tile_width}",
                f"buffer.size={buffer_size}",
                f"dtm.pixel_size={1}",
            ],
        )
    main(cfg)
    assert_las_buffer_is_not_empty(output_dir, INPUT_FILENAME_SMALL1)
    with rasterio.Env():
        with rasterio.open(
            Path(output_dir) / EXPECTED_OUTPUT_DTM_1C / f"{input_tilename}_DTM_hillshade_color1c.tif"
        ) as raster:
            band1 = raster.read(1)
            band2 = raster.read(2)
            band3 = raster.read(3)
            assert band1[8, 8] == 255
            assert band2[8, 8] == 147
            assert band3[8, 8] == 0
            assert raster.res == (1, 1)
        with rasterio.open(
            Path(output_dir) / EXPECTED_OUTPUT_DTM_4C / f"{input_tilename}_DTM_hillshade_color4c.tif"
        ) as raster:
            band1 = raster.read(1)
            band2 = raster.read(2)
            band3 = raster.read(3)
            assert band1[8, 8] == 205
            assert band2[8, 8] == 103
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
                "dtm.color.cycles_DTM_colored=[1,4]",
                f"density.output_subdir={OUTPUT_FOLDER_DENS}",
                f"class_map.output_subdir={OUTPUT_FOLDER_CLASS}",
                f"io.tile_geometry.tile_coord_scale={tile_coord_scale}",
                f"io.tile_geometry.tile_width={tile_width}",
                f"buffer.size={buffer_size}",
                f"density.pixel_size={1}",
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


def assert_las_buffer_is_not_empty(output: str, filename: str):
    las_dir = Path(output) / "tmp" / "buffer"
    assert (las_dir / filename).is_file()
    assert pcu.get_nb_points(las_dir / filename) > 0
