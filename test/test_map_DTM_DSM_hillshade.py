import os
import shutil

from ctview.map_DTM_DSM import add_hillshade_one_raster

input_dir = os.path.join("data", "raster")

input_rastername = "test_data_77055_627760_LA93_IGN69_interp.tif"

input_raster = os.path.join(input_dir, input_rastername)


tmp_path = os.path.join("data", "labo")

expected_output_default_file = os.path.join(tmp_path, "test_data_77055_627760_LA93_IGN69_hillshade.tif")


def setup_module(module):
    try:
        shutil.rmtree(tmp_path)

    except FileNotFoundError:
        pass
    os.mkdir(tmp_path)


def test_add_hillshade_one_raster():
    """
    Verify :
        - .tif is created
    """
    assert os.path.isfile(input_raster)
    add_hillshade_one_raster(input_raster=input_raster, output_raster=expected_output_default_file)

    assert os.path.isfile(expected_output_default_file)
