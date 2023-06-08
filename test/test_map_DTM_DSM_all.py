import os
import shutil
from ctview.map_DTM_DSM import create_mnx_one_las


coordX = 77055
coordY = 627760

input_dir = os.path.join("data", "laz")

input_tilename = f"test_data_{coordX}_{coordY}_LA93_IGN69.laz"

input_filename = os.path.join(input_dir, input_tilename)


tmp_path = os.path.join("data", "labo")

output_dir = tmp_path

expected_output_default_file_1 = os.path.join(output_dir, "tmp_dtm", "buffer", "test_data_77055_627760_LA93_IGN69_buffer.las")
expected_output_default_file_2 = os.path.join(output_dir, "tmp_dtm", "filter", "test_data_77055_627760_LA93_IGN69_filter.las")
expected_output_default_file_3 = os.path.join(output_dir, "DTM", "test_data_77055_627760_LA93_IGN69_interp.tif")


def setup_module(module):
    try:
        shutil.rmtree(tmp_path)

    except (FileNotFoundError):
        pass
    os.mkdir(tmp_path)


def test_create_mnx_one_las():
    create_mnx_one_las(input_file=input_filename,
            output_dir=output_dir,
            config_file=os.path.join("ctview","config_test.json"),
            type_raster="dtm")

    assert os.path.isfile(expected_output_default_file_1)
    assert os.path.isfile(expected_output_default_file_2)
    assert os.path.isfile(expected_output_default_file_3)
