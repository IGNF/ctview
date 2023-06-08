import numpy as np
import os
import shutil

from ctview.utils_tools import write_interp_table, remove_1_pixel, convert_json_into_dico

TEST_DIR = os.path.join("data", "labo")
dir_filename = os.path.join(TEST_DIR, "table.txt")
table_interpolation = np.ones((2, 3))

path_json_config = os.path.join("ctview","config.json")

maxX = 30
minX = 0
maxY = 60
minY = 0
res = 5
new_maxX_expected = 25
new_maxY_expected = 55


def setup_module(module):  # run before the first test
    try:  # Clean folder test if exists
        shutil.rmtree(TEST_DIR)
    except (FileNotFoundError):
        pass
    # Create folder test if not exists
    os.makedirs(TEST_DIR)


def teardown_module(module):  # run after the last test
    try:  # Clean folder test if exists
        shutil.rmtree(TEST_DIR)
    except (FileNotFoundError):
        pass


def test_write_interp_table():
    """Test is fuction write_interp_table create a text file"""
    write_interp_table(output_filename=dir_filename, table_interp=table_interpolation)
    assert os.path.exists(dir_filename)


def test_remove_1_pixel():
    """Test if boundaries change with a given resolution"""
    bound = ([minX, maxX],[minY,maxY])
    new_bounds = remove_1_pixel(bound,res)
    assert new_bounds == ([minX,new_maxX_expected],[minY,new_maxY_expected])



def test_convert_json_into_dico():
    """Test if type of return is a dictionnary"""
    dico = convert_json_into_dico(config_file=path_json_config)
    assert isinstance(dico, dict) # assert type
    assert dico['tile_geometry']['no_data_value']==-9999 # assert architecture
    assert dico['io']['spatial_reference']=='EPSG:2154' # assert architecture
