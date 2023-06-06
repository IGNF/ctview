import os
import shutil
import numpy as np
from ctview.parameter import dico_param

from ctview.map_DTM_DSM import (
    filter_las_ground_virtual,
    write_las,
    las_prepare_1_file,
    execute_startin,
    write_geotiff_withbuffer,
    get_origin,
    hillshade_from_raster,
    interpolation,
    run_interpolate
)

from ctview.utils_pdal import get_class_min_max_from_las, get_info_from_las, read_las_file

NoDataValue = dico_param["no_data_value"]

# from utils_pdal import get_stats_from_las

# TEST FILE
DATA_DIR_LAS = os.path.join("data","las")
LAS_CLASS_65_TO_66 = "test_data_multiclass_65to66.las"
LAS_CLASS_2 = "test_data_class_2.las"
LAS_CLASS_6 = "test_data_class_6.las"
LAS_EMPTY = "test_data_empty.las"
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


def test_1_filter_las_ground_virtual(INPUT_DIR=DATA_DIR_LAS, filename=LAS_CLASS_6):
    """
    Input :
        las_file with points where classif in [6]
    Verify :
        - output is an array
        - no remaining points with classif != 2
    """
    # Application of the filter
    out_filter_ground = filter_las_ground_virtual(input_dir=DATA_DIR_LAS, filename=filename)
    # Check Classif of each point
    for p in out_filter_ground:
        assert p[8] == 2  # Classification==2

    assert isinstance(out_filter_ground, np.ndarray)  # type is array


def test_2_filter_las_ground_virtual(INPUT_DIR=DATA_DIR_LAS, filename=LAS_CLASS_65_TO_66):
    """
    Input :
        las_file with points where classif in [65:66]
    Verify :
        - output is an array
        - no remaining points with classif != 66
    """
    # Application of the filter
    out_filter_ground = filter_las_ground_virtual(input_dir=DATA_DIR_LAS, filename=filename)
    # Check Classif of each point
    for p in out_filter_ground:
        assert p[8] == 66  # Classification==66

    assert isinstance(out_filter_ground, np.ndarray)  # type is array


def test_write_las():
    """
    Test function write_las
    Verify :
        - file is created
        - extension is las
    """
    input_file = os.path.join(DATA_DIR_LAS , LAS_CLASS_6)
    input_points = read_las_file(
        input_las=input_file
    )  # fct tested in test_utils_pdal.py

    filename = "Stand_ardd_Name_File_Test_IGN69.laz"
    output_filename = write_las(
        input_points=input_points, filename=filename, output_dir=TEST_DIR, name=""
    )

    assert os.path.exists(output_filename)  # file created
    assert os.path.splitext(output_filename)[1] == ".las"  # extension is las


def test_las_prepare_1_file():
    """
    Verify :
        - type and size
    """
    input_file = os.path.join(DATA_DIR_LAS , LAS_CLASS_6)
    size = 1.0

    pts, resolution, origin = las_prepare_1_file(input_file=input_file, size=size)

    assert isinstance(pts, np.ndarray)  # type is array
    assert (
        isinstance(resolution, list) and len(resolution) == 2
    )  # type is list and len==2
    assert isinstance(origin, list) and len(resolution) == 2  # type is list and len==2


def execute_test_mnt(method: str):
    """
    Verify :
        - return an array
    """
    input_file = os.path.join(DATA_DIR_LAS , LAS_CLASS_2)
    size = 1.0

    pts_to_interpol, resolution, origin = las_prepare_1_file(
        input_file=input_file, size=size
    )

    ras = execute_startin(
        pts=pts_to_interpol, res=resolution, origin=origin, size=1.0, method=method
    )
    assert isinstance(ras, np.ndarray)  # type is array


def test_execute_startin():
    execute_test_mnt("Laplace")


def test_execute_startin_2():
    execute_test_mnt("TINlinear")


def execute_test_write_geotiff_withbuffer(method: str):
    """
    Verify :
        - .tif is created
    """
    input_file = os.path.join(DATA_DIR_LAS , LAS_CLASS_2)
    size = 1.0

    pts_to_interpol, resolution, origin = las_prepare_1_file(
        input_file=input_file, size=size
    )

    ras = execute_startin(
        pts=pts_to_interpol, res=resolution, origin=origin, size=1.0, method=method
    )

    raster_dtm_interp = write_geotiff_withbuffer(
        raster=ras,
        origin=origin,
        size=size,
        output_file=os.path.join(
            TEST_DIR,
            f"{os.path.splitext(LAS_CLASS_2)[0]}_{method}.tif",
        ),
    )
    assert os.path.exists(raster_dtm_interp)


def test_write_geotiff_withbuffer():
    execute_test_write_geotiff_withbuffer("Laplace")


def test_write_geotiff_withbuffer():
    execute_test_write_geotiff_withbuffer("TINlinear")


def test_get_origin():
    """
    Verify :
        - .tif is created
    """
    xcoord, ycoord, projection, sys_alti = get_origin("Semis_2021_0939_6537_LA93_IGN69.laz")
    assert xcoord == 939
    assert ycoord == 6537
    assert projection == "LA93"
    assert sys_alti == "IGN69"

def test_hillshade_from_raster():
    """
    Verify :
        - .tif is created
    """
    input_raster = os.path.join(DATA_DIR_RASTER, RASTER_DTM_BRUT)
    output_raster = os.path.join(TEST_DIR,RASTER_DTM_BRUT)
    hillshade_from_raster(input_raster, output_raster)
    assert os.path.exists(output_raster)

def execute_test_interpolate(input_file):
    """
    Verify :
        - can_interp is a boolean
        - ras is None when there is no points to interpolate
    """
    size=1
    method="Laplace"
    points, resolution, origin = las_prepare_1_file(input_file=input_file, size=size)
    ras, can_interp = interpolation(pts=points, res=resolution, origin=origin, size=size, method=method)
    assert isinstance(can_interp, bool)
    if not can_interp :
        assert ras is None
    return ras, can_interp

def test_interpolate():
    """
    Test 2 file : one with interpolation and one without
    """
    # Las avec points de classe 2 ie avec interpolation
    _, success = execute_test_interpolate(input_file=os.path.join(DATA_DIR_LAS, LAS_CLASS_2))
    assert success
    # Las sans aucun point (donc sans points de classe 2 ni 66 ie sans interpolation)
    rasNone, fail = execute_test_interpolate(input_file=os.path.join(DATA_DIR_LAS, LAS_EMPTY))
    assert not fail
    assert rasNone is None

def execute_test_run_interpolate(input_file):
    """
    Verify :
        - ras is numpy array
    """
    # param
    size=1
    method="Laplace"
    # prepare
    points, resolution, origin = las_prepare_1_file(input_file=input_file, size=size)
    # run function to test
    ras_to_evaluate = run_interpolate(pts=points, res=resolution, origin=origin, size=size, method=method)
    # control
    assert isinstance(ras_to_evaluate, np.ndarray)

def execute_test_run_interpolate_with_filtering(input_file):
    print(input_file)
    # filtering
    input_file_filtered = os.path.join(TEST_DIR,os.path.basename(input_file))
    filter_las_classes(input_file=input_file, output_file=input_file_filtered)
    # run interpolate
    # param
    size=1
    method="Laplace"
    # prepare
    _, resolution, origin = las_prepare_1_file(input_file=input_file, size=size)
    points, _, _ = las_prepare_1_file(input_file=input_file_filtered, size=size)
    # run function to test
    ras_to_evaluate = run_interpolate(pts=points, res=resolution, origin=origin, size=size, method=method)
    # control
    assert isinstance(ras_to_evaluate, np.ndarray)

    return ras_to_evaluate

def test_run_interpolate():
    """
    Test execute_test_run_interpolate on 2 files : one with interpolation and one without
    """
    # Las avec points de classe 2 ie avec interpolation
    execute_test_run_interpolate(input_file=os.path.join(DATA_DIR_LAS, LAS_CLASS_2))
    # Las sans aucun point (donc sans points de classe 2 ni 66 ie sans interpolation)
    execute_test_run_interpolate(input_file=os.path.join(DATA_DIR_LAS, LAS_EMPTY))
    # Las avec que points classe 6 et avec filtre => no data attendu
    ras = execute_test_run_interpolate_with_filtering(input_file=os.path.join(DATA_DIR_LAS, LAS_CLASS_6))
    
    for line in ras :
        for element in line :
            assert element == NoDataValue