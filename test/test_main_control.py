import os
import shutil
from pathlib import Path

from hydra import compose, initialize
from osgeo import gdal

from ctview.main_control import main

gdal.UseExceptions()

INPUT_DIR_SMALL = Path("data") / "las" / "ground"
INPUT_FILENAME_SMALL1 = "test_data_77055_627755_LA93_IGN69.laz"
INPUT_FILENAME_SMALL2 = "test_data_77055_627760_LA93_IGN69.laz"


OUTPUT_DIR = Path("tmp") / "main_control"


def setup_module(module):
    try:
        shutil.rmtree(OUTPUT_DIR)
    except FileNotFoundError:
        pass
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def test_main_control_default():
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
