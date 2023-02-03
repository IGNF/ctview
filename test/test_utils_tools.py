import numpy as np
import os
import shutil

from ctview.utils_tools import write_interp_table, remove_1_pixel

TEST_DIR = os.path.join("data", "labo")
dir_filename = os.path.join(TEST_DIR, "table.txt")
table_interpolation = np.ones((2, 3))

maxX = 30
minX = 0
maxY = 60
minY = 0
res = 5
new_maxX_expected = 25
new_maxY_expected = 55


def setUpModule():  # run before the first test
    try:  # Clean folder test if exists
        shutil.rmtree(TEST_DIR)
    except (FileNotFoundError):
        pass
    # Create folder test if not exists
    os.makedirs(TEST_DIR)


def tearDownModule():  # run after the last test
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
