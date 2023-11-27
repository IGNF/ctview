import os
import shutil

from ctview.map_DTM_DSM import create_output_tree

tmp_path = os.path.join("data", "labo", "tools")

output_dir = tmp_path

expected_dtm_dir = os.path.join(output_dir, "DTM")
expected_dtm_filter_dir = os.path.join(output_dir, "tmp_dtm", "filter")
expected_dtm_buffer_dir = os.path.join(output_dir, "tmp_dtm", "buffer")
expected_dtm_hillshade_dir = os.path.join(output_dir, "tmp_dtm", "hillshade")
expected_dtm_color_dir = os.path.join(output_dir, "DTM", "color")
expected_dsm_dir = os.path.join(output_dir, "DSM")
expected_dsm_filter_dir = os.path.join(output_dir, "tmp_dsm", "filter")
expected_dsm_buffer_dir = os.path.join(output_dir, "tmp_dsm", "buffer")
expected_dsm_hillshade_dir = os.path.join(output_dir, "tmp_dsm", "hillshade")
expected_dtm_dens_dir = os.path.join(output_dir, "DTM_DENS")
expected_dtm_dens_filter_dir = os.path.join(output_dir, "tmp_dtm_dens", "filter")
expected_dtm_dens_buffer_dir = os.path.join(output_dir, "tmp_dtm_dens", "buffer")
expected_dtm_dens_hillshade_dir = os.path.join(output_dir, "tmp_dtm_dens", "hillshade")


def setup_module(module):
    try:
        shutil.rmtree(tmp_path)

    except FileNotFoundError:
        pass
    os.mkdir(tmp_path)


def test_create_output_tree():
    """Test if all folders are created"""
    create_output_tree(output_dir=output_dir)

    assert os.path.isdir(expected_dtm_dir)
    assert os.path.isdir(expected_dtm_filter_dir)
    assert os.path.isdir(expected_dtm_buffer_dir)
    assert os.path.isdir(expected_dtm_hillshade_dir)
    assert os.path.isdir(expected_dtm_color_dir)
    assert os.path.isdir(expected_dsm_dir)
    assert os.path.isdir(expected_dsm_filter_dir)
    assert os.path.isdir(expected_dsm_buffer_dir)
    assert os.path.isdir(expected_dsm_hillshade_dir)
    assert os.path.isdir(expected_dtm_dens_dir)
    assert os.path.isdir(expected_dtm_dens_filter_dir)
    assert os.path.isdir(expected_dtm_dens_buffer_dir)
    assert os.path.isdir(expected_dtm_dens_hillshade_dir)
