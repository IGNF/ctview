import os
import shutil
import test.utils.raster_utils as ru

from hydra import compose, initialize

from ctview.map_DTM_DSM import run_mnx_interpolation

COORDX = 77055
COORDY = 627760
TILE_COORD_SCALE = 10
TILE_WIDTH = 50
PIXEL_SIZE = 0.5
BUFFER_SIZE = 10


INPUT_DIR = os.path.join("data", "laz")
INPUT_BASENAME = f"test_data_{COORDX}_{COORDY}_LA93_IGN69.laz"
INPUT_FILENAME = os.path.join(INPUT_DIR, INPUT_BASENAME)

OUTPUT_DIR = os.path.join("tmp", "interpolation")

EXPECTED_XMIN = COORDX * TILE_COORD_SCALE - PIXEL_SIZE / 2
EXPECTED_YMAX = COORDY * TILE_COORD_SCALE + PIXEL_SIZE / 2
EXPECTED_RASTER_BOUNDS = (EXPECTED_XMIN, EXPECTED_YMAX - TILE_WIDTH), (EXPECTED_XMIN + TILE_WIDTH, EXPECTED_YMAX)

EXPECTED_OUTPUT_DEFAULT_FILE = os.path.join(OUTPUT_DIR, "test_data_77055_627760_LA93_IGN69_50CM_Laplace.tif")


def setup_module(module):
    try:
        shutil.rmtree(OUTPUT_DIR)

    except FileNotFoundError:
        pass
    os.mkdir(OUTPUT_DIR)


def test_run_mnx_interpolation():
    """Verif interpolation create a file with suffix size (50CM)"""
    with initialize(version_base="1.2", config_path="../configs"):
        # config is relative to a module
        cfg = compose(
            config_name="config_ctview",
            overrides=[
                f"mnx_dtm.tile_geometry.tile_coord_scale={TILE_COORD_SCALE}",
                f"mnx_dtm.tile_geometry.tile_width={TILE_WIDTH}",
                f"mnx_dtm.buffer.size={BUFFER_SIZE}",
                f"mnx_dtm.tile_geometry.pixel_size={PIXEL_SIZE}",
            ],
        )

    run_mnx_interpolation(input_file=INPUT_FILENAME, output_raster=EXPECTED_OUTPUT_DEFAULT_FILE, config=cfg.mnx_dtm)

    assert os.path.isfile(EXPECTED_OUTPUT_DEFAULT_FILE)

    raster_bounds = ru.get_tif_extent(EXPECTED_OUTPUT_DEFAULT_FILE)
    assert ru.allclose_mm(raster_bounds, EXPECTED_RASTER_BOUNDS)
