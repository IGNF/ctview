import os
import shutil
from ctview.map_DTM_DSM import run_mnx_interpolation
import test.utils.raster_utils as ru
import ctview.utils_tools as utools


coordX = 77055
coordY = 627760
tile_coord_scale = 10
tile_width = 50
pixel_size = 0.5


input_dir = os.path.join("data", "laz")
input_basename = f"test_data_{coordX}_{coordY}_LA93_IGN69.laz"
input_filename = os.path.join(input_dir, input_basename)

tmp_path = os.path.join("data", "labo")

output_dir = os.path.join(tmp_path, "interpolation")

config_file = os.path.join("ctview", "config.json")
config_dict = utools.convert_json_into_dico(config_file)

config_dict["tile_geometry"]["tile_coord_scale"] = tile_coord_scale
config_dict["tile_geometry"]["tile_width"] = tile_width
config_dict["tile_geometry"]["pixel_size"] = pixel_size

expected_xmin = coordX * tile_coord_scale - pixel_size/2
expected_ymax = coordY * tile_coord_scale  + pixel_size/2
expected_raster_bounds = (expected_xmin, expected_ymax - tile_width), (expected_xmin + tile_width, expected_ymax)

expected_output_default_file = os.path.join(output_dir, "test_data_77055_627760_LA93_IGN69_50CM_Laplace.tif")


def setup_module(module):
    try:
        shutil.rmtree(tmp_path)

    except (FileNotFoundError):
        pass
    os.mkdir(tmp_path)
    os.mkdir(output_dir)


def test_run_mnx_interpolation():
    """Verif interpolation create a file with suffix size (50CM) and interpolation method (Laplace)
    """
    if os.path.isfile(expected_output_default_file):
        os.remove(expected_output_default_file)

    run_mnx_interpolation(input_file=input_filename, output_raster=expected_output_default_file, config=config_dict)

    assert os.path.isfile(expected_output_default_file)

    raster_bounds = ru.get_tif_extent(expected_output_default_file)
    assert ru.allclose_mm(raster_bounds, expected_raster_bounds)

