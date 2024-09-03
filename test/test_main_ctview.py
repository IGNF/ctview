import os
import shutil
import test.utils.point_cloud_utils as pcu
from pathlib import Path

import pytest
import rasterio
from hydra import compose, initialize
from osgeo import gdal

from ctview.main_ctview import main

gdal.UseExceptions()

INPUT_DIR_SMALL = Path("data") / "las" / "ground"
INPUT_FILENAME_SMALL1 = "test_data_77055_627755_LA93_IGN69.laz"
INPUT_FILENAME_SMALL2 = "test_data_77055_627760_LA93_IGN69.laz"


OUTPUT_DIR = Path("tmp") / "main_ctview"

OUTPUT_FOLDER_DENS = "DENS_FINAL_CUSTOM"
OUTPUT_FOLDER_CLASS = "CLASS_CUSTOM"
OUTPUT_FOLDER_CLASS_PRETTY = "CLASS_PRETTY_CUSTOM"

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


def test_main_ctview_default():
    tile_width = 50
    tile_coord_scale = 10
    pixel_size = 2
    buffer_size = 10
    output_dir = OUTPUT_DIR / "main_ctview_default"
    input_tilename = os.path.splitext(INPUT_FILENAME_SMALL1)[0]
    with initialize(version_base="1.2", config_path="../configs"):
        # config is relative to a module
        cfg = compose(
            config_name="config_control",
            overrides=[
                f"io.input_filename={INPUT_FILENAME_SMALL1}",
                f"io.input_dir={INPUT_DIR_SMALL}",
                f"io.output_dir={output_dir}",
                f"io.tile_geometry.tile_coord_scale={tile_coord_scale}",
                f"io.tile_geometry.tile_width={tile_width}",
                f"buffer.size={buffer_size}",
                f"density.pixel_size={pixel_size}",
            ],
        )
    main(cfg)
    assert set(os.listdir(output_dir)) == {"DENS_FINAL", "CLASS_FINAL"}
    assert (Path(output_dir) / "DENS_FINAL" / f"{input_tilename}_density.tif").is_file()
    assert (Path(output_dir) / "CLASS_FINAL" / f"{input_tilename}.tif").is_file()


def test_main_ctview_renaming_final_folders():
    tile_width = 50
    tile_coord_scale = 10
    pixel_size = 2
    buffer_size = 10
    output_dir = OUTPUT_DIR / "main_ctview_renaming_final_folders"
    input_tilename = os.path.splitext(INPUT_FILENAME_SMALL1)[0]
    with initialize(version_base="1.2", config_path="../configs"):
        # config is relative to a module
        cfg = compose(
            config_name="config_control",
            overrides=[
                f"io.input_filename={INPUT_FILENAME_SMALL1}",
                f"io.input_dir={INPUT_DIR_SMALL}",
                f"io.output_dir={output_dir}",
                f"density.output_subdir={OUTPUT_FOLDER_DENS}",
                f"class_map.output_class_pretty_subdir={OUTPUT_FOLDER_CLASS}",
                f"io.tile_geometry.tile_coord_scale={tile_coord_scale}",
                f"io.tile_geometry.tile_width={tile_width}",
                f"buffer.size={buffer_size}",
                f"density.pixel_size={pixel_size}",
            ],
        )
    main(cfg)
    assert set(os.listdir(output_dir)) == {OUTPUT_FOLDER_CLASS, OUTPUT_FOLDER_DENS}
    assert (Path(output_dir) / OUTPUT_FOLDER_DENS / f"{input_tilename}_density.tif").is_file()
    assert (Path(output_dir) / OUTPUT_FOLDER_CLASS / f"{input_tilename}.tif").is_file()


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
            config_name="config_control",
            overrides=[
                f"io.input_filename={input_filename}",
                f"io.input_dir={input_dir}",
                f"io.output_dir={output_dir}",
                f"density.output_subdir={OUTPUT_FOLDER_DENS}",
                f"class_map.output_class_pretty_subdir={OUTPUT_FOLDER_CLASS}",
                f"io.tile_geometry.tile_coord_scale={tile_coord_scale}",
                f"io.tile_geometry.tile_width={tile_width}",
                f"buffer.size={buffer_size}",
                f"density.pixel_size={1}",
            ],
        )
    main(cfg)
    assert_output_folders_contains_expected_number_of_file(
        output=output_dir,
        subfolders={OUTPUT_FOLDER_DENS, OUTPUT_FOLDER_CLASS},
        nb_raster_expected=expected_nb_file,
    )


def assert_output_folders_contains_expected_number_of_file(output: str, subfolders: set, nb_raster_expected: int):
    """
    Verify :
        - good number of raster created on final folders
        - exception for density when there is a lot of water
    """
    # good number of raster created
    for folder in subfolders:
        path = Path(output) / folder
        assert len(os.listdir(path)) == nb_raster_expected


def assert_las_buffer_is_not_empty(output: str, filename: str):
    las_dir = Path(output) / "tmp" / "buffer"
    assert (las_dir / filename).is_file()
    assert pcu.get_nb_points(las_dir / filename) > 0


def test_main_modif_config():
    input_dir = Path("data") / "las" / "classee"
    output_dir = OUTPUT_DIR / "main_modif_config"
    outfile_buffer = output_dir / "tmp" / "buffer" / "test_data_77050_627755_LA93_IGN69_buildings.laz"
    outfile_density = output_dir / "density" / "test_data_77050_627755_LA93_IGN69_buildings_density.tif"
    outfile_class_raw = (
        output_dir / "class" / "tmp" / "binary" / "test_data_77050_627755_LA93_IGN69_buildings_class_raw.tif"
    )
    outfile_class_precedence = output_dir / "class" / "test_data_77050_627755_LA93_IGN69_buildings_class.tif"
    pixel_size = 2
    with initialize(version_base="1.2", config_path="../configs"):
        cfg = compose(
            config_name="config_metadata",
            overrides=[
                "io.input_filename=test_data_77050_627755_LA93_IGN69_buildings.laz",
                f"io.input_dir={input_dir}",
                f"io.output_dir={output_dir} ",
                "io.tile_geometry.tile_coord_scale=10",
                "io.tile_geometry.tile_width=50",
                "buffer.size=10",
                "buffer.output_subdir=tmp/buffer",
                f"density.pixel_size={pixel_size}",
                "density.keep_classes=[[2],[1],[66]]",
                f"class_map.pixel_size={pixel_size}",
                "class_map.intermediate_dirs.class_binary=tmp/binary",
                "class_map.precedence_classes=[26, 2, 6, 56,57,17,5]",
                "class_map.ignored_classes=[1,3,4]",
            ],
        )

    # override CBI rules and the colormap afterwards as it is difficult to have the right syntax interpretation
    # for [ and { in the overrides list
    cfg.class_map.CBI_rules = [{"CBI": [2, 6], "AGGREG": 26}]
    cfg.class_map.colormap.append({"value": 26, "description": "Test veget + sol", "color": [255, 255, 0]})

    main(cfg)

    assert os.path.isfile(outfile_buffer)
    assert os.path.isfile(outfile_class_raw)
    with rasterio.Env():
        with rasterio.open(outfile_density) as raster:
            band_ground, band_not_classified, band_virtual = raster.read(1), raster.read(2), raster.read(3)
            assert band_ground[0, 3] == (31 + 0) / pixel_size**2  # 0 because no neighbor file
            assert band_not_classified[0, 14] == 14 / pixel_size**2
            assert band_virtual[0, 3] == 0  # no virtual point
        with rasterio.open(outfile_class_precedence) as raster:
            unique_band = raster.read(1)
            assert unique_band[0, 3] == 2  # ground here
            assert unique_band[0, 9] == 6  # building there
            assert unique_band[0, 12] == 26  # # ground and building concatenated


def test_main_ctview_class_raw_only():
    tile_width = 50
    tile_coord_scale = 10
    pixel_size = 2
    buffer_size = 10
    output_dir = OUTPUT_DIR / "main_ctview_class_raw_only"
    input_tilename = os.path.splitext(INPUT_FILENAME_SMALL1)[0]
    with initialize(version_base="1.2", config_path="../configs"):
        # config is relative to a module
        cfg = compose(
            config_name="config_control",
            overrides=[
                f"io.input_filename={INPUT_FILENAME_SMALL1}",
                f"io.input_dir={INPUT_DIR_SMALL}",
                f"io.output_dir={output_dir}",
                f"density.output_subdir={OUTPUT_FOLDER_DENS}",
                f"class_map.output_class_subdir={OUTPUT_FOLDER_CLASS}",
                "class_map.output_class_pretty_subdir=null",
                f"io.tile_geometry.tile_coord_scale={tile_coord_scale}",
                f"io.tile_geometry.tile_width={tile_width}",
                f"buffer.size={buffer_size}",
                f"density.pixel_size={pixel_size}",
            ],
        )
    main(cfg)
    assert set(os.listdir(output_dir)) == {OUTPUT_FOLDER_CLASS, OUTPUT_FOLDER_DENS}
    assert (Path(output_dir) / OUTPUT_FOLDER_DENS / f"{input_tilename}_density.tif").is_file()
    assert (Path(output_dir) / OUTPUT_FOLDER_CLASS / f"{input_tilename}_class.tif").is_file()


def test_main_ctview_class_pretty_only():
    tile_width = 50
    tile_coord_scale = 10
    pixel_size = 2
    buffer_size = 10
    output_dir = OUTPUT_DIR / "main_ctview_class_pretty_only"
    input_tilename = os.path.splitext(INPUT_FILENAME_SMALL1)[0]
    with initialize(version_base="1.2", config_path="../configs"):
        # config is relative to a module
        cfg = compose(
            config_name="config_control",
            overrides=[
                f"io.input_filename={INPUT_FILENAME_SMALL1}",
                f"io.input_dir={INPUT_DIR_SMALL}",
                f"io.output_dir={output_dir}",
                f"density.output_subdir={OUTPUT_FOLDER_DENS}",
                "class_map.output_class_subdir=null",
                f"class_map.output_class_pretty_subdir={OUTPUT_FOLDER_CLASS_PRETTY}",
                f"io.tile_geometry.tile_coord_scale={tile_coord_scale}",
                f"io.tile_geometry.tile_width={tile_width}",
                f"buffer.size={buffer_size}",
                f"density.pixel_size={pixel_size}",
            ],
        )
    main(cfg)
    assert set(os.listdir(output_dir)) == {OUTPUT_FOLDER_CLASS_PRETTY, OUTPUT_FOLDER_DENS}
    assert (Path(output_dir) / OUTPUT_FOLDER_DENS / f"{input_tilename}_density.tif").is_file()
    assert (Path(output_dir) / OUTPUT_FOLDER_CLASS_PRETTY / f"{input_tilename}.tif").is_file()


def test_main_ctview_class_both_output():
    tile_width = 50
    tile_coord_scale = 10
    pixel_size = 2
    buffer_size = 10
    output_dir = OUTPUT_DIR / "main_ctview_class_both_output"
    input_tilename = os.path.splitext(INPUT_FILENAME_SMALL1)[0]
    with initialize(version_base="1.2", config_path="../configs"):
        # config is relative to a module
        cfg = compose(
            config_name="config_control",
            overrides=[
                f"io.input_filename={INPUT_FILENAME_SMALL1}",
                f"io.input_dir={INPUT_DIR_SMALL}",
                f"io.output_dir={output_dir}",
                f"density.output_subdir={OUTPUT_FOLDER_DENS}",
                f"class_map.output_class_subdir={OUTPUT_FOLDER_CLASS}",
                f"class_map.output_class_pretty_subdir={OUTPUT_FOLDER_CLASS_PRETTY}",
                f"io.tile_geometry.tile_coord_scale={tile_coord_scale}",
                f"io.tile_geometry.tile_width={tile_width}",
                f"buffer.size={buffer_size}",
                f"density.pixel_size={pixel_size}",
            ],
        )
    main(cfg)
    assert set(os.listdir(output_dir)) == {OUTPUT_FOLDER_CLASS_PRETTY, OUTPUT_FOLDER_CLASS, OUTPUT_FOLDER_DENS}
    assert (Path(output_dir) / OUTPUT_FOLDER_CLASS_PRETTY / f"{input_tilename}.tif").is_file()
    assert (Path(output_dir) / OUTPUT_FOLDER_CLASS / f"{input_tilename}_class.tif").is_file()
