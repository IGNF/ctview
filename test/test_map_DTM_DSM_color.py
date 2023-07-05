import os
import shutil
import ctview.utils_tools as utils_tools
from ctview.utils_folder import dico_folder_template, add_folder_list_cycles
from ctview.map_DTM_DSM import (create_output_tree,
                                color_raster_dtm_hillshade_with_LUT)

# input
input_dir = os.path.join("data", "laz")
input_tilename = "test_data_77055_627760_LA93_IGN69.laz"
input_filename = os.path.join(input_dir, input_tilename)
input_raster = os.path.join("data", "raster", "test_data_77055_627760_LA93_IGN69_interp.tif")

# output
tmp_path = os.path.join("data", "labo")
tmp_path_LUT = os.path.join(tmp_path, "LUT")

# expected
expected_dtm_color_1cycle_file = os.path.join(tmp_path, "DTM", "color", "1cycle", "test_data_77055_627760_LA93_IGN69_DTM_hillshade_color1c.tif")
expected_dtm_color_5cycles_file = os.path.join(tmp_path, "DTM", "color", "5cycles", "test_data_77055_627760_LA93_IGN69_DTM_hillshade_color5c.tif")

# preparation
list_cycles = [1,5]
dico_folder = dico_folder_template.copy()

new_dico = add_folder_list_cycles(List=list_cycles, folder_base=dico_folder["folder_DTM_color"], key_base="folder_DTM_color", dico_fld=dico_folder_template)

def setup_module(module):
    try:
        shutil.rmtree(tmp_path)

    except (FileNotFoundError):
        pass
    os.mkdir(tmp_path)
    os.mkdir(tmp_path_LUT)


def test_color_raster_dtm_hillshade_with_LUT():
    """
    Verify :
        - tifs is created
    """
    color_raster_dtm_hillshade_with_LUT(input_initial_basename=input_tilename,
                        input_raster=input_raster,
                        output_dir=tmp_path,
                        list_c=list_cycles,
                        dico_fld=new_dico)
    assert os.path.exists(expected_dtm_color_1cycle_file)
    assert os.path.exists(expected_dtm_color_5cycles_file)