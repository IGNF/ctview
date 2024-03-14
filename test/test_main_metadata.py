import os
import shutil
from pathlib import Path

import rasterio
from hydra import compose, initialize

from ctview.main_metadata import main

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
    outfile_buffer = output_dir / "tmp" / "buffer" / "test_data_77050_627755_LA93_IGN69.las"
    outfile_density = output_dir / "density" / "test_data_77050_627755_LA93_IGN69_density.tif"
    outfile_class_raw = output_dir / "class" / "test_data_77050_627755_LA93_IGN69_class_raw.tif"
    pixel_size = 2
    with initialize(version_base="1.2", config_path="../configs"):
        cfg = compose(
            config_name="config_metadata",
            overrides=[
                "io.input_filename=test_data_77050_627755_LA93_IGN69.las",
                f"io.input_dir={INPUT_DIR}",
                f"io.output_dir={output_dir} ",
                "tile_geometry.tile_coord_scale=10",
                "tile_geometry.tile_size=50",
                "buffer.buffer_size=10",
                "buffer.output_subdir=tmp/buffer",
                f"density.pixel_size={pixel_size}",
                f"density.keep_classes=[[2],[1],[66]]",
                f"class_map.pixel_size={pixel_size}",
                f"class_map.keep_classes=[[2],[2,66],[66]]",
            ],
        )
    main(cfg)

    assert os.path.isfile(outfile_buffer)
    with rasterio.Env():
        with rasterio.open(outfile_density) as raster:
            band_ground, band_not_classified, band_virtual = raster.read(1), raster.read(2), raster.read(3)
            assert band_ground[0, 3] == (29 + 0) / pixel_size**2  # 0 because no neighbour file
            assert band_not_classified[0, 3] == 2 / pixel_size**2
            assert band_virtual[0, 3] == 0  # no virtual point
        with rasterio.open(outfile_class_raw) as raster:
            band_ground, band_ground_and_virtual, band_virtual = raster.read()
            assert band_ground[0, 3] == 1
            assert band_ground_and_virtual[0, 3] == 1
            assert band_virtual[0, 3] == 0  # no virtual point


def test_main_default_config():
    output_dir = OUTPUT_DIR / "main_default_config"
    outfile_density = output_dir / "density" / "test_data_77050_627755_LA93_IGN69_density.tif"
    outfile_class_raw = output_dir / "class" / "test_data_77050_627755_LA93_IGN69_class_raw.tif"
    with initialize(version_base="1.2", config_path="../configs"):
        cfg = compose(
            config_name="config_metadata",
            overrides=[
                "io.input_filename=test_data_77050_627755_LA93_IGN69.las",
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
            assert band_ground[0, 4] == 11 / 1**2
            assert band_veget_and_bridge[0, 4] == 0  # no veget point, no bridge point
        with rasterio.open(outfile_class_raw) as raster:
            band_ground_and_virtual, band_artefact = raster.read()
            assert band_ground_and_virtual[0, 4] == 1
            assert band_artefact[0, 4] == 0  # no virtual point
