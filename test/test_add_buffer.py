import os
import shutil
import test.utils.point_cloud_utils as pcu

import ctview.add_buffer as add_buffer

TMP = "tmp"
COORDX = 77055
COORDY = 627760
TILE_COORD_SCALE = 10
TILE_WIDTH = 50
BUFFER_SIZE = 10
SPATIAL_REFERENCE = "EPSG:2154"

INPUT_DIR_LAS = os.path.join("data", "las")

INPUT_DIR_WITHOUT_BUFFER = os.path.join(INPUT_DIR_LAS, "ground")
INPUT_FILE_WITHOUT_BUFFER = os.path.join(INPUT_DIR_WITHOUT_BUFFER, f"test_data_{COORDX}_{COORDY}_LA93_IGN69.las")

OUTPUT_DIR_BUFFER = os.path.join(TMP, "buffer")
OUTPUT_FILE_WITH_BUFFER = os.path.join(OUTPUT_DIR_BUFFER, f"test_data_{COORDX}_{COORDY}_LA93_IGN69.las")

EXPECTED_OUTPUT_NB_POINTS = 47037


def setup_module(module):
    try:
        shutil.rmtree(TMP)

    except FileNotFoundError:
        pass
    os.mkdir(TMP)
    os.mkdir(OUTPUT_DIR_BUFFER)


def test_run_pdaltools_buffer():
    add_buffer.run_pdaltools_buffer(
        input_dir=INPUT_DIR_WITHOUT_BUFFER,
        tile_filename=INPUT_FILE_WITHOUT_BUFFER,
        output_filename=OUTPUT_FILE_WITH_BUFFER,
        buffer_width=BUFFER_SIZE,
        tile_width=TILE_WIDTH,
        tile_coord_scale=TILE_COORD_SCALE,
        spatial_ref=SPATIAL_REFERENCE,
    )

    assert os.path.isfile(OUTPUT_FILE_WITH_BUFFER)
    assert pcu.get_nb_points(OUTPUT_FILE_WITH_BUFFER) == EXPECTED_OUTPUT_NB_POINTS
