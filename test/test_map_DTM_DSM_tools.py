import os
import shutil
from ctview.map_DTM_DSM import create_output_tree


tmp_path = os.path.join("data", "labo", "tools")

output_dir = tmp_path

expected_dir_1 = os.path.join(output_dir, "DTM")
expected_dir_2 = os.path.join(output_dir, "tmp_dtm", "filter")
expected_dir_3 = os.path.join(output_dir, "tmp_dtm", "buffer")
expected_dir_4 = os.path.join(output_dir, "DSM")
expected_dir_5 = os.path.join(output_dir, "tmp_dsm", "filter")
expected_dir_6 = os.path.join(output_dir, "tmp_dsm", "buffer")
expected_dir_7 = os.path.join(output_dir, "DTM_DENS")
expected_dir_8 = os.path.join(output_dir, "tmp_dtm_dens", "filter")
expected_dir_9 = os.path.join(output_dir, "tmp_dtm_dens", "buffer")

def setup_module(module):
    try:
        shutil.rmtree(tmp_path)

    except (FileNotFoundError):
        pass
    os.mkdir(tmp_path)


def test_create_output_tree():
    """Test if all folders are created
    """
    create_output_tree(output_dir=output_dir)

    assert os.path.isdir(expected_dir_1)
    assert os.path.isdir(expected_dir_2)
    assert os.path.isdir(expected_dir_3)
    assert os.path.isdir(expected_dir_4)
    assert os.path.isdir(expected_dir_5)
    assert os.path.isdir(expected_dir_6)
    assert os.path.isdir(expected_dir_7)
    assert os.path.isdir(expected_dir_8)
    assert os.path.isdir(expected_dir_9)
