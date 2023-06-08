import os
import shutil
from ctview.map_DTM_DSM import run_pdaltools_buffer
import test.utils.point_cloud_utils as pcu


coordX = 77055
coordY = 627760


input_dir = os.path.join("data", "laz", "ground")

tmp_path = os.path.join("data", "labo")

expected_output_nb_points = 47037


input_filename = os.path.join(input_dir, f"test_data_{coordX}_{coordY}_LA93_IGN69.las")

output_dir = os.path.join(tmp_path,  "buffer")

output_default_file = os.path.join(output_dir, f"test_data_{coordX}_{coordY}_LA93_IGN69.las")


def setup_module(module):
    try:
        shutil.rmtree(tmp_path)

    except (FileNotFoundError):
        pass
    os.mkdir(tmp_path)
    os.mkdir(output_dir)


def test_run_pdaltools_buffer():

    run_pdaltools_buffer(input_dir=input_dir, tile_filename=input_filename, output_filename=output_default_file,
                    buffer_width=10,
                    tile_width=50,
                    tile_coord_scale=10)
    
    assert os.path.isfile(output_default_file)
    assert pcu.get_nb_points(output_default_file) == expected_output_nb_points
