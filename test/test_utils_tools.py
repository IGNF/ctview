import numpy as np
import os
import shutil

from ctview.utils_tools import convert_json_into_dico

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



def test_convert_json_into_dico():
    """Test if type of return is a dictionnary"""
    dico = convert_json_into_dico(config_file=path_json_config)
    assert isinstance(dico, dict) # assert type
    assert dico['tile_geometry']['no_data_value']==-9999 # assert architecture
    assert dico['io']['spatial_reference']=='EPSG:2154' # assert architecture
