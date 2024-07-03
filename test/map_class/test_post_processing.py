import os
import shutil
from pathlib import Path

import rasterio
from osgeo import gdal

from ctview.map_class.post_processing import add_color_to_raster, fill_gaps_raster

gdal.UseExceptions()

OUTPUT_DIR = os.path.join("tmp", "map_class", "post_processing")
INPUT_DIR = os.path.join("data", "las", "classee")
INPUT_FILENAME = "test_data_77050_627755_LA93_IGN69.las"
TILENAME = os.path.splitext(INPUT_FILENAME)[0]
RASTER_DRIVER = "GTiff"


def setup_module(module):  # run before the first test
    try:  # Clean folder test if exists
        shutil.rmtree(OUTPUT_DIR)
    except FileNotFoundError:
        pass
    # Create folder test if not exists
    os.makedirs(OUTPUT_DIR)


def test_fill_gaps_raster():
    input_file = Path("data") / "raster" / "class_raw" / f"{TILENAME}.tif"
    output_file = Path(OUTPUT_DIR) / "fill_gaps_raster" / f"{TILENAME}.tif"
    fill_gaps_raster(
        in_raster=input_file,
        output_file=output_file,
        raster_driver=RASTER_DRIVER,
    )
    with rasterio.open(output_file) as raster:
        band_max = raster.read(1)
        assert band_max[6, 17] == -9999.0  # gap not filled
        assert band_max[0, 8] != -9999.0  # gap filled
        assert band_max[0, 10] == 2  # max (band_G) kept from input raster
        assert band_max[17, 14] == 65  # max (band_G) kept from input raster


def test_add_color_to_raster():
    input_file = Path("data") / "raster" / "class_fill_gaps" / f"{TILENAME}.tif"
    output_file = Path(OUTPUT_DIR) / "add_color_to_raster" / f"{TILENAME}.tif"
    add_color_to_raster(
        in_raster=input_file,
        output_file=output_file,
        LUT=os.path.join("LUT", "LUT_CLASS.txt"),
    )
    with rasterio.open(output_file) as raster:
        band_R = raster.read(1)
        band_G = raster.read(2)
        band_B = raster.read(3)

        assert band_R[6, 17] == 255  # nodata -> color not defined in LUT => white
        assert band_G[6, 17] == 255  # nodata -> color not defined in LUT => white
        assert band_B[6, 17] == 255  # nodata -> color not defined in LUT => white

        assert band_R[0, 10] == 255  # sol (classe 2) -> color defined in LUT
        assert band_G[0, 10] == 128  # sol (classe 2) -> color defined in LUT
        assert band_B[0, 10] == 0  # sol (classe 2) -> color defined in LUT

        assert band_R[17, 14] == 64  # artefact (classe 65) -> color defined in LUT
        assert band_G[17, 14] == 0  # artefact (classe 65) -> color defined in LUT
        assert band_B[17, 14] == 128  # artefact (classe 65) -> color defined in LUT
