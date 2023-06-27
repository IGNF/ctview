import os
import shutil
import ctview.utils_tools as utils_tools
from ctview.map_DTM_DSM import (create_mnx_one_las,
                                create_dxm_with_hillshade_one_las_XM,
                                create_dtm_with_hillshade_one_las_5M,
                                create_dtm_with_hillshade_one_las_1M,
                                create_dsm_with_hillshade_one_las_50CM
                                )

# choice tile
coordX = 77055
coordY = 627760

# config
config_file = os.path.join("ctview","config_test.json")
config_dict = utils_tools.convert_json_into_dico(config_file)

# input
input_dir = os.path.join("data", "laz")
input_tilename = f"test_data_{coordX}_{coordY}_LA93_IGN69.laz"
input_filename = os.path.join(input_dir, input_tilename)

# output
tmp_path = os.path.join("data", "labo")
output_dir = os.path.join(tmp_path, "mnx")
output_dir_2 = os.path.join(tmp_path, "mnx_hs")
output_dir_3 = os.path.join(tmp_path, "mnt_mns_mntdens_hs")

# expected
expected_output_default_file_1 = os.path.join("tmp_dtm", "buffer", "test_data_77055_627760_LA93_IGN69_buffer.las")
expected_output_default_file_2 = os.path.join("tmp_dtm", "filter", "test_data_77055_627760_LA93_IGN69_filter.las")
expected_output_default_file_3 = os.path.join("DTM", "test_data_77055_627760_LA93_IGN69_interp.tif")
expected_output_default_file_4 = os.path.join("tmp_dtm", "hillshade", "test_data_77055_627760_LA93_IGN69_hillshade.tif")

expected_output_default_file_5 = os.path.join("tmp_dsm", "buffer", "test_data_77055_627760_LA93_IGN69_buffer.las")
expected_output_default_file_6 = os.path.join("tmp_dsm", "filter", "test_data_77055_627760_LA93_IGN69_filter.las")
expected_output_default_file_7 = os.path.join("DSM", "test_data_77055_627760_LA93_IGN69_interp.tif")
expected_output_default_file_8 = os.path.join("tmp_dsm", "hillshade", "test_data_77055_627760_LA93_IGN69_hillshade.tif")

expected_output_default_file_9 = os.path.join("tmp_dtm_dens", "buffer", "test_data_77055_627760_LA93_IGN69_buffer.las")
expected_output_default_file_10 = os.path.join("tmp_dtm_dens", "filter", "test_data_77055_627760_LA93_IGN69_filter.las")
expected_output_default_file_11 = os.path.join("DTM_DENS", "test_data_77055_627760_LA93_IGN69_interp.tif")
expected_output_default_file_12 = os.path.join("tmp_dtm_dens", "hillshade", "test_data_77055_627760_LA93_IGN69_hillshade.tif")


def setup_module(module):
    try:
        shutil.rmtree(tmp_path)

    except (FileNotFoundError):
        pass
    os.mkdir(tmp_path)


def test_create_mnx_one_las():
    """
    Verify :
        - every 4 tifs are created
        - output is the raster hillshaded
    """
    output_raster = create_mnx_one_las(input_file=input_filename,
            output_dir=output_dir,
            config_dict=config_dict,
            type_raster="dtm")

    assert os.path.isfile(os.path.join(output_dir, expected_output_default_file_1))
    assert os.path.isfile(os.path.join(output_dir, expected_output_default_file_2))
    assert os.path.isfile(os.path.join(output_dir, expected_output_default_file_3))
    assert os.path.isfile(os.path.join(output_dir, expected_output_default_file_4))
    assert output_raster == os.path.join(output_dir, expected_output_default_file_4)


def test_create_DTM_with_hillshade_one_las_default_pixelsize():
    """
    Verify :
        - .tif are created
        - output is the raster hillshaded
    """
    output_raster = create_dxm_with_hillshade_one_las_XM(input_file=input_filename, 
                                output_dir=output_dir_2,
                                config_file=os.path.join("ctview","config_test.json"),
                                type_raster="dtm")

    assert os.path.isfile(os.path.join(output_dir_2, expected_output_default_file_1))
    assert os.path.isfile(os.path.join(output_dir_2, expected_output_default_file_2))
    assert os.path.isfile(os.path.join(output_dir_2, expected_output_default_file_3))
    assert os.path.isfile(os.path.join(output_dir_2, expected_output_default_file_4))
    assert output_raster == os.path.join(output_dir_2, expected_output_default_file_4)


def test_create_DSM_with_hillshade_one_las_default_pixelsize():
    """
    Verify :
        - .tif are created
        - output is the raster hillshaded
    """
    output_raster = create_dxm_with_hillshade_one_las_XM(input_file=input_filename, 
                                output_dir=output_dir_2,
                                config_file=os.path.join("ctview","config_test.json"),
                                type_raster="dsm")

    assert os.path.isfile(os.path.join(output_dir_2, expected_output_default_file_5))
    assert os.path.isfile(os.path.join(output_dir_2, expected_output_default_file_6))
    assert os.path.isfile(os.path.join(output_dir_2, expected_output_default_file_7))
    assert os.path.isfile(os.path.join(output_dir_2, expected_output_default_file_8))
    assert output_raster == os.path.join(output_dir_2, expected_output_default_file_8)


def test_create_dtm_with_hillshade_one_las_5M_pixelsize():
    """
    Verify :
        - .tif are created
        - output is the raster hillshaded
    """
    output_raster = create_dtm_with_hillshade_one_las_5M(input_file=input_filename, 
                                output_dir=output_dir_3)

    assert os.path.isfile(os.path.join(output_dir_3, expected_output_default_file_9))
    assert os.path.isfile(os.path.join(output_dir_3, expected_output_default_file_10))
    assert os.path.isfile(os.path.join(output_dir_3, expected_output_default_file_11))
    assert os.path.isfile(os.path.join(output_dir_3, expected_output_default_file_12))
    assert output_raster == os.path.join(output_dir_3, expected_output_default_file_12)


def test_create_dtm_with_hillshade_one_las_1M_pixelsize():
    """
    Verify :
        - .tif are created
        - output is the raster hillshaded
    """
    output_raster = create_dtm_with_hillshade_one_las_1M(input_file=input_filename, 
                                output_dir=output_dir_3)

    assert os.path.isfile(os.path.join(output_dir_3, expected_output_default_file_1))
    assert os.path.isfile(os.path.join(output_dir_3, expected_output_default_file_2))
    assert os.path.isfile(os.path.join(output_dir_3, expected_output_default_file_3))
    assert os.path.isfile(os.path.join(output_dir_3, expected_output_default_file_4))
    assert output_raster == os.path.join(output_dir_3, expected_output_default_file_4)

    
def test_create_dsm_with_hillshade_one_las_50CM_pixelsize():
    """
    Verify :
        - .tif are created
        - output is the raster hillshaded
    """
    output_raster = create_dsm_with_hillshade_one_las_50CM(input_file=input_filename, 
                                output_dir=output_dir_3)

    assert os.path.isfile(os.path.join(output_dir_3, expected_output_default_file_5))
    assert os.path.isfile(os.path.join(output_dir_3, expected_output_default_file_6))
    assert os.path.isfile(os.path.join(output_dir_3, expected_output_default_file_7))
    assert os.path.isfile(os.path.join(output_dir_3, expected_output_default_file_8))
    assert output_raster == os.path.join(output_dir_3, expected_output_default_file_8)