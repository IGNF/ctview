import os
import shutil

from ctview.map_DTM_DSM import hillshade_from_raster

# TEST FILE
DATA_DIR_RASTER = os.path.join("data","raster")
RASTER_DTM_BRUT = "test_data_0000_0000_LA93_IGN69_ground_DTM_1M_Laplace.tif"

# PATH TO FOLDER TEST
TEST_DIR = os.path.join("data","labo")

def setup_module(module): # run before the first test
    try : # Clean folder test if exists
        shutil.rmtree(TEST_DIR)
    except (FileNotFoundError):
        pass
    # Create folder test if not exists
    os.makedirs(TEST_DIR)


def teardown_module(module): # run after the last test
    try : # Clean folder test if exists
        shutil.rmtree(TEST_DIR)
    except (FileNotFoundError):
        pass


def test_hillshade_from_raster():
    """
    Verify :
        - .tif is created
    """
    input_raster = os.path.join(DATA_DIR_RASTER, RASTER_DTM_BRUT)
    output_raster = os.path.join(TEST_DIR,RASTER_DTM_BRUT)
    hillshade_from_raster(input_raster, output_raster)
    assert os.path.exists(output_raster)
