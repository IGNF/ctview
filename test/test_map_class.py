import numpy as np
import os
import ctview.utils_pdal as utils_pdal
import shutil

from ctview.map_class import step1_create_raster_brut, step2_create_raster_fillgap, step3_color_raster

# Test files
TEST_DIR = os.path.join("data","labo")
DATA = os.path.join("data","las", "test_data_0000_0000_LA93_IGN69_ground.las")
IN_POINTS = utils_pdal.read_las_file(DATA) # tested 
FILENAME = "toto"
VERBOSE = "tata"


# Attempted
PATH1_EXPECTED = os.path.join(TEST_DIR,"toto_raster.tif")
PATH2_EXPECTED = os.path.join(TEST_DIR,"toto_raster_fillgap.tif")
PATH3_EXPECTED = os.path.join(TEST_DIR,"toto_tata.tif")


def setUpModule(): # run before the first test
    try : # Clean folder test if exists
        shutil.rmtree(TEST_DIR)
    except (FileNotFoundError):
        pass
    # Create folder test if not exists
    os.makedirs(TEST_DIR)


def tearDownModule(): # run after the last test
    try : # Clean folder test if exists
        shutil.rmtree(TEST_DIR)
    except (FileNotFoundError):
        pass


def test_step1_create_raster_brut():
    raster = step1_create_raster_brut(in_points=IN_POINTS,output_dir=TEST_DIR, filename=FILENAME, res=1, i=1)
    assert raster == PATH1_EXPECTED # good output filename
    assert os.path.exists(PATH1_EXPECTED) # file exists


def test_step2_create_raster_fillgap():
    raster_brut = step1_create_raster_brut(in_points=IN_POINTS,output_dir=TEST_DIR, filename=FILENAME, res=1, i=1)
    raster_fillgap = step2_create_raster_fillgap(in_raster=raster_brut, output_dir=TEST_DIR, filename=FILENAME, i=1)
    assert raster_fillgap == PATH2_EXPECTED # good output filename
    assert os.path.exists(PATH2_EXPECTED) # file exists


def test_step3_color_raster():
    raster_brut = step1_create_raster_brut(in_points=IN_POINTS,output_dir=TEST_DIR, filename=FILENAME, res=1, i=1)
    raster_color = step3_color_raster(in_raster=raster_brut, output_dir=TEST_DIR,filename=FILENAME,verbose=VERBOSE,i=1)
    assert raster_color == PATH3_EXPECTED # good output filename
    assert os.path.exists(PATH3_EXPECTED) # file exists

