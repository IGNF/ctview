import os
import shutil
from pathlib import Path

import laspy
import numpy as np
import rasterio

import ctview.map_density as map_density

INPUT_LAS = "./data/las/test_data_multiclass_65to66.las"
OUTPUT_DIR = "./tmp/map_density"
EPSG = 2154

INPUT_LAS_50m = "./data/las/test_data_0000_0000_LA93_IGN69_ground.las"
LAS = laspy.read(INPUT_LAS_50m)
INPUT_POINTS = np.vstack((LAS.x, LAS.y, LAS.z)).transpose()
INPUT_CLASSIFS = np.copy(LAS.classification)


def setup_module():
    try:
        shutil.rmtree(OUTPUT_DIR)
    except FileNotFoundError:
        pass
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def test_compute_density():
    origin_x, origin_y = map_density.get_pointcloud_origin(points=INPUT_POINTS, tile_size=50)

    density = map_density.compute_density(INPUT_POINTS, (origin_x, origin_y), 50, 2)

    assert density.shape == (25, 25)


def test_generate_raster_of_density_2():
    output_tif = os.path.join(OUTPUT_DIR, "output_generate_raster_of_density_2.tif")
    map_density.generate_raster_of_density_2(
        input_points=INPUT_POINTS,
        input_classifs=INPUT_CLASSIFS,
        output_tif=output_tif,
        epsg=EPSG,
        tile_size=50,
        pixel_size=2,
    )
    assert os.path.isfile(output_tif)
    with rasterio.open(output_tif) as raster:
        band1 = raster.read(1)
        assert band1[0, 0] == 28 / 2**2  # density = nb_pt / pixel_size **2 = 28/2**2
        assert band1[5, 0] == 1 / 2**2
        assert band1[6, 0] == 0


def test_generate_raster_of_density_2_multiband():
    output_raster_multi = Path(OUTPUT_DIR) / "multiband_raster.tif"
    map_density.generate_raster_of_density_2(
        input_points=INPUT_POINTS,
        input_classifs=INPUT_CLASSIFS,
        classes_by_layer=[[], [125]],
        output_tif=output_raster_multi,
        epsg=EPSG,
        tile_size=50,
        pixel_size=2,
    )
    assert os.path.isfile(output_raster_multi)
    with rasterio.open(output_raster_multi) as raster_multi:
        band1 = raster_multi.read(1)
        assert band1[0, 0] == 28 / 2**2  # density = nb_pt / pixel_size **2 = 28/2**2
        band2 = raster_multi.read(2)
        assert band2[0, 0] == 0  # this band contains no point because none have classification 125
