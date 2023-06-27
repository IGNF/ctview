import pytest
import os
import shutil

from ctview import _version as ctview_version

# PARAMETERS
# version
VERSION=ctview_version.__version__
# input folders
FOLDER_1="ADENS_FINAL"
FOLDER_2="ACC_5_fusion_FINAL"
FOLDER_3="ADTM_1M_color_FINAL"
# folders expected
FOLDER_31="DTM/color/1cycle"
FOLDER_32="DTM/color/2cycles"
FOLDER_34="DTM/color/4cycles"

# test 1 : small dalle with and without docker
INPUT_1="/var/data/store-lidarhd/developpement/ctview/las/data0"
OUTPUT_1="/var/data/store-lidarhd/developpement/ctview/1_tests_local/test0"
OUTPUT_1bis="/var/data/store-lidarhd/developpement/ctview/2_tests_local_docker/test0"
NB_FILE_EXPECTED_1=1

# test 2 : dalle with water
INPUT_2="/var/data/store-lidarhd/developpement/ctview/las/data0b"
OUTPUT_2="/var/data/store-lidarhd/developpement/ctview/1_tests_local/test0b"
OUTPUT_2bis="/var/data/store-lidarhd/developpement/ctview/2_tests_local_docker/test0b"
NB_FILE_EXPECTED_2=1

# test 3 : big dalle docker
INPUT_3="/var/data/store-lidarhd/developpement/ctview/las/data1"
OUTPUT_3="/var/data/store-lidarhd/developpement/ctview/1_tests_local/test1"
OUTPUT_3bis="/var/data/store-lidarhd/developpement/ctview/2_tests_local_docker/test1"
NB_FILE_EXPECTED_3=1

# test 4 : big 4 dalles docker
INPUT_4="/var/data/store-lidarhd/developpement/ctview/las/data3"
OUTPUT_4="/var/data/store-lidarhd/developpement/ctview/1_tests_local/test3"
OUTPUT_4bis="/var/data/store-lidarhd/developpement/ctview/2_tests_local_docker/test3"
NB_FILE_EXPECTED_4=4


def setup_module(module): # run before the first test
    try : # Clean folder test if exists
        shutil.rmtree("/var/data/store-lidarhd/developpement/ctview/1_tests_local")
        shutil.rmtree("/var/data/store-lidarhd/developpement/ctview/2_tests_local_docker")
    except (FileNotFoundError):
        pass


# def teardown_module(module): # run after the last test
#     try : # Clean folder test if exists
#         shutil.rmtree("/var/data/store-lidarhd/developpement/ctview/1_tests_local")
#         shutil.rmtree("/var/data/store-lidarhd/developpement/ctview/2_tests_local_docker")
#     except (FileNotFoundError):
#         pass


def assert_output_folders_contains_expected_number_of_file(output: str, nb_raster_expected: int, water:bool=False):
    """
    Verify :
        - good number of raster created on final folders
        - exception for density when there is a lot of water
    """
    # good number of raster created
    path = os.path.join(output,FOLDER_1)
    if not water :
        assert len(os.listdir(path)) == nb_raster_expected
    else :
        assert not os.path.exists(path)
    for folder in [FOLDER_2, FOLDER_31, FOLDER_32, FOLDER_34]:
      path = os.path.join(output, folder)
      assert len(os.listdir(path)) == nb_raster_expected

def execute_test_end_to_end(input: str, output: str, nb_raster_expected: int, water:bool=False):
    """
    Verify :
        - good number of raster created on final folders without docker
    """
    os.system(f"""
    python -m ctview.main \
    -idir {input}  \
    -odir {output} \
    -ofdens {FOLDER_1} \
    -ofcc {FOLDER_2} \
    -ofcolor {FOLDER_3} \
    -c 1 2 4
    """)

    assert_output_folders_contains_expected_number_of_file(output=output, nb_raster_expected=nb_raster_expected, water=water)


def execute_test_end_to_end_docker(input: str, output: str, nb_raster_expected: int, water:bool=False):
    """
    Verify :
        - good number of raster created on final folders with docker
    """
    os.system(f"""
    docker run --rm \
    -v {input}:/input \
    -v {output}:/output \
    lidar_hd/ct_view:{VERSION} \
    python -m ctview.main \
    -idir /input \
    -odir /output \
    -ofdens {FOLDER_1} \
    -ofcc {FOLDER_2} \
    -ofcolor {FOLDER_3} \
    -c 1 2 4
    """)

    assert_output_folders_contains_expected_number_of_file(output=output, nb_raster_expected=nb_raster_expected, water=water)


def test_execute_end_to_end_quick():
    # 1/1 small 1 dalle
    execute_test_end_to_end(input=INPUT_1, output=OUTPUT_1, nb_raster_expected=NB_FILE_EXPECTED_1)
    # execute_test_end_to_end_docker(input=INPUT_1, output=OUTPUT_1bis, nb_raster_expected=NB_FILE_EXPECTED_1)


@pytest.mark.slow
def test_execute_end_to_end_slow():
    # 1/3 water 1 dalle
    execute_test_end_to_end(input=INPUT_2, output=OUTPUT_2, nb_raster_expected=NB_FILE_EXPECTED_2, water=True)
    execute_test_end_to_end_docker(input=INPUT_2, output=OUTPUT_2bis, nb_raster_expected=NB_FILE_EXPECTED_2, water=True)
    # 2/3 big 1 dalle
    execute_test_end_to_end(input=INPUT_3, output=OUTPUT_3, nb_raster_expected=NB_FILE_EXPECTED_3)
    execute_test_end_to_end_docker(input=INPUT_3, output=OUTPUT_3bis, nb_raster_expected=NB_FILE_EXPECTED_3)
    # 3/3 big 4 dalles
    execute_test_end_to_end(input=INPUT_4, output=OUTPUT_4, nb_raster_expected=NB_FILE_EXPECTED_4)
    execute_test_end_to_end_docker(input=INPUT_4, output=OUTPUT_4bis, nb_raster_expected=NB_FILE_EXPECTED_4)
