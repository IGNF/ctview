import os
import shutil
from pathlib import Path

import rasterio
from hydra import compose, initialize
from osgeo import gdal

from ctview.main_metadata import main

gdal.UseExceptions()

OUTPUT_DIR = Path("tmp") / "main_metadata"
INPUT_DIR = Path("data") / "las" / "classee"


def setup_module(module):
    try:
        shutil.rmtree(OUTPUT_DIR)
    except FileNotFoundError:
        pass
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def test_main_modif_config():
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
                f"io.input_dir={INPUT_DIR}",
                f"io.output_dir={output_dir} ",
                "tile_geometry.tile_coord_scale=10",
                "tile_geometry.tile_size=50",
                "buffer.buffer_size=10",
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
            assert band_ground[0, 3] == (31 + 0) / pixel_size**2  # 0 because no neighbour file
            assert band_not_classified[0, 14] == 14 / pixel_size**2
            assert band_virtual[0, 3] == 0  # no virtual point
        with rasterio.open(outfile_class_precedence) as raster:
            unique_band = raster.read(1)
            assert unique_band[0, 3] == 2  # ground here
            assert unique_band[0, 9] == 6  # building there
            assert unique_band[0, 7] == 26  # ground and building concatenated


def test_main_default_config():
    output_dir = OUTPUT_DIR / "main_default_config"
    outfile_density = output_dir / "density" / "test_data_77050_627755_LA93_IGN69_buildings_density.tif"
    outfile_class_precedence = output_dir / "class" / "test_data_77050_627755_LA93_IGN69_buildings_class.tif"
    with initialize(version_base="1.2", config_path="../configs"):
        cfg = compose(
            config_name="config_metadata",
            overrides=[
                "io.input_filename=test_data_77050_627755_LA93_IGN69_buildings.laz",
                f"io.input_dir={INPUT_DIR}",
                f"io.output_dir={output_dir} ",
                "tile_geometry.tile_coord_scale=10",
                "tile_geometry.tile_size=50",
                "buffer.buffer_size=10",
            ],
        )
    main(cfg)

    assert not os.path.isdir(output_dir / "tmp")
    with rasterio.Env():
        with rasterio.open(outfile_density) as raster:
            band_ground, band_veget_and_bridge = raster.read(1), raster.read(2)
            assert band_ground[0, 4] == 12 / 1**2
            assert band_veget_and_bridge[0, 4] == 0  # no veget point, no bridge point
        with rasterio.open(outfile_class_precedence) as raster:
            unique_band = raster.read(1)
            print(unique_band[22, 15])
            assert unique_band[14, 21] == 51  # High vegetation and buildings
            assert unique_band[0, 1] == 2  # Only ground
            # Ground and buildings (but buildings are first in the precedence order)
            assert unique_band[9, 21] == 6
