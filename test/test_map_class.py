import glob
import os
import shutil
from pathlib import Path

import laspy
import numpy as np
import pytest
import rasterio
from hydra import compose, initialize

import ctview.utils_pcd as utils_pcd
import ctview.utils_pdal as utils_pdal
import ctview.utils_raster as utils_raster
from ctview.map_class import (
    add_color_to_raster,
    apply_combination_rules,
    apply_precedence_order,
    compute_binary_class,
    convert_class_array_to_precedence_array,
    create_class_raster_raw_deprecated,
    create_map_class_raster_with_postprocessing_color_and_hillshade,
    fill_gaps_raster,
    generate_class_raster_raw,
    list_original_classes_to_keep,
)

OUTPUT_DIR = os.path.join("tmp", "map_class")
INPUT_DIR = os.path.join("data", "las", "classee")
INPUT_FILENAME = "test_data_77050_627755_LA93_IGN69.las"
TILENAME = os.path.splitext(INPUT_FILENAME)[0]
INPUT_FILE = os.path.join(INPUT_DIR, INPUT_FILENAME)
IN_POINTS = utils_pdal.read_las_file(INPUT_FILE)
LAS = laspy.read(INPUT_FILE)
INPUT_POINTS = np.vstack((LAS.x, LAS.y, LAS.z)).transpose()
INPUT_CLASSIFS = np.copy(LAS.classification)
EPSG = 2154
RASTER_ORIGIN = utils_raster.compute_raster_origin(input_points=INPUT_POINTS, tile_size=50, pixel_size=1)
RASTER_DRIVER = "GTiff"

TILE_COORD_SCALE = 10
TILE_WIDTH = 50
BUFFER_SIZE = 10


def setup_module(module):  # run before the first test
    try:  # Clean folder test if exists
        shutil.rmtree(OUTPUT_DIR)
    except FileNotFoundError:
        pass
    # Create folder test if not exists
    os.makedirs(OUTPUT_DIR)


def test_compute_binary_class():
    origin_x, origin_y = utils_pcd.get_pointcloud_origin(points=INPUT_POINTS, tile_size=50)

    binary_class = compute_binary_class(points=INPUT_POINTS, origin=(origin_x, origin_y), tile_size=50, pixel_size=2)

    assert binary_class.shape == (25, 25)
    assert np.all((binary_class == 0) | (binary_class == 1))
    assert (binary_class[0, :8] == np.array([1, 1, 1, 1, 1, 1, 1, 0])).all()


def test_generate_class_raster_raw():
    output_file = Path(OUTPUT_DIR) / "generate_class_raster_raw" / f"{TILENAME}.tif"
    generate_class_raster_raw(
        input_points=INPUT_POINTS,
        input_classifs=INPUT_CLASSIFS,
        output_tif=str(output_file),
        epsg=EPSG,
        raster_origin=RASTER_ORIGIN,
        class_by_layer=[2, 1, 66],
        tile_size=50,
        pixel_size=1,
        no_data_value=-9999.0,
        raster_driver=RASTER_DRIVER,
    )
    with rasterio.open(output_file) as raster:
        band_ground = raster.read(1)
        band_not_classified = raster.read(2)
        band_virtual = raster.read(3)

        # pixel with 0 point
        assert band_ground[0, 8] == 0
        assert band_not_classified[0, 8] == 0
        assert band_virtual[0, 8] == 0

        # pixel with ground, no not classified, no virtual point
        assert band_ground[0, 7] == 1
        assert band_not_classified[0, 7] == 0
        assert band_virtual[0, 7] == 0

        # pixel with ground, not classified, no virtual point
        assert band_ground[0, 6] == 1
        assert band_not_classified[0, 6] == 1
        assert band_virtual[0, 6] == 0


@pytest.mark.parametrize(
    """rules, priorities,expected_class_by_layer""",
    [
        ([{"CBI": [3, 5], "AGGREG": 35}], [3, 35, 5], [3, 5]),
        ([{"CBI": [3, 5], "AGGREG": 35}], [3, 35, 5, 12, 19], [3, 5, 12, 19]),
    ],
)
def test_list_original_classes_to_keep(rules, priorities, expected_class_by_layer):
    class_by_layer = list_original_classes_to_keep(rules, priorities)
    assert class_by_layer == expected_class_by_layer


parameters = [([{"CBI": [4, 5], "AGGREG": 35}], [3, 35, 5]), ([{"CBI": [3, 5], "AGGREG": 45}], [3, 35, 5])]


@pytest.mark.parametrize(
    """rules, priorities""",
    parameters,
)
def test_list_original_classes_to_keep_value_error(rules, priorities):
    with pytest.raises(ValueError):
        list_original_classes_to_keep(rules, priorities)


def test_apply_combination_rules():
    input_array = np.array([[[1, 0], [0, 0]], [[1, 1], [0, 0]]])
    class_by_layer = [3, 5]
    rules = [
        {"CBI": [3, 5], "AGGREG": 35},
    ]
    array_rules, class_by_layer_rules = apply_combination_rules(input_array, class_by_layer, rules)
    assert np.array_equal(array_rules, np.array([[[1, 0], [0, 0]], [[1, 1], [0, 0]], [[1, 0], [0, 0]]]))
    assert class_by_layer_rules == [3, 5, 35]


def test_apply_precedence_order():
    input_array = np.array([[[1, 0], [0, 0]], [[1, 1], [0, 0]], [[1, 0], [1, 0]]])
    class_by_layer = [3, 5, 35]
    priorities = [3, 35, 5]
    array_rules_priorities = apply_precedence_order(input_array, class_by_layer, priorities)
    assert np.array_equal(array_rules_priorities, np.array([[3, 5], [35, 0]]))


parameters = [
    (
        np.array([[[1, 0], [0, 0]], [[0, 1], [0, 0]], [[0, 0], [1, 0]], [[0, 0], [0, 1]]]),
        [12, 6, 5, 8],
        [12, 6, 5, 8],
        (2, 2),
        np.array([[12, 6], [5, 8]]),  # Standard use case
    ),
    (np.array([[[1, 0], [0, 0]]]), [12, 6], [], (2, 2), np.array([[0, 0], [0, 0]])),  # Case without priorities
    (
        np.array([[[1, 0], [0, 0]], [[1, 0], [0, 0]]]),
        [12],
        [],
        (2, 2),
        np.array([[0, 0], [0, 0]]),
    ),  # Case 1 class and without priorities
]


@pytest.mark.parametrize(
    """input_array, class_by_layer,priorities, expected_shape, expected_array""",
    parameters,
)
def test_convert_class_array_to_precedence_array(
    input_array, class_by_layer, priorities, expected_shape, expected_array
):
    output_array = convert_class_array_to_precedence_array(
        input_array=input_array, class_by_layer=class_by_layer, priorities=priorities
    )
    assert output_array.shape == expected_shape
    assert np.array_equal(output_array, expected_array)


def test_convert_class_array_to_precedence_array_with_rules():
    output_array = convert_class_array_to_precedence_array(
        input_array=np.array([[[1, 1], [0, 1]], [[1, 1], [1, 0]], [[1, 1], [1, 1]]]),
        class_by_layer=[12, 8, 5, 6],
        rules=[{"CBI": [12, 8], "AGGREG": 128}, {"CBI": [5, 6], "AGGREG": 45}],
        priorities=[128, 6, 5, 8],
    )
    assert output_array.shape == (2, 2)
    assert np.array_equal(output_array, np.array([[128, 128], [5, 5]]))


def test_generate_class_raster_flatten():
    output_dir = Path(OUTPUT_DIR) / "generate_class_raster_flatten"
    input_array = generate_class_raster_raw(
        input_points=INPUT_POINTS,
        input_classifs=INPUT_CLASSIFS,
        output_tif=str(output_dir / "raw" / f"{TILENAME}.tif"),
        epsg=EPSG,
        raster_origin=RASTER_ORIGIN,
        class_by_layer=[2, 1, 66],
        tile_size=50,
        pixel_size=1,
        no_data_value=-9999.0,
        raster_driver=RASTER_DRIVER,
    )
    output_dir_flatten = output_dir / "flatten"
    output_dir_flatten.mkdir(exist_ok=True)

    flatten_array = convert_class_array_to_precedence_array(
        input_array=input_array,
        class_by_layer=[2, 1, 66],
        rules=[],
        priorities=[2, 1, 66],
    )
    utils_raster.write_single_band_raster_to_file(
        input_array=flatten_array,
        raster_origin=RASTER_ORIGIN,
        output_tif=str(output_dir_flatten / f"{TILENAME}.tif"),
    )
    assert os.path.isfile(str(output_dir_flatten / f"{TILENAME}.tif"))
    with rasterio.Env():
        with rasterio.open(str(output_dir_flatten / f"{TILENAME}.tif")) as raster:
            unique_band = raster.read(1)
            assert unique_band[0, 3] == 2
            assert unique_band[0, 9] == 0
            assert unique_band[8, 15] == 1


def test_create_class_raster_raw_deprecated():
    output_file = Path(OUTPUT_DIR) / "create_class_raster_raw" / f"{TILENAME}.tif"
    create_class_raster_raw_deprecated(
        in_points=IN_POINTS, output_file=str(output_file), res=1, raster_driver=RASTER_DRIVER, no_data_value=-9999.0
    )
    with rasterio.open(output_file) as raster:
        band_min = raster.read(1)
        band_max = raster.read(2)
        band_mean = raster.read(3)
        band_idw = raster.read(4)
        band_count = raster.read(5)
        band_stdev = raster.read(6)

        assert band_min[6, 17] == -9999.0
        assert band_max[6, 17] == -9999.0
        assert band_mean[6, 17] == -9999.0
        assert band_idw[6, 17] == -9999.0
        assert band_count[6, 17] == 0  # pixel with 0 point
        assert band_stdev[6, 17] == -9999.0

        assert band_min[0, 8] == -9999.0
        assert band_max[0, 8] == -9999.0
        assert band_mean[0, 8] == -9999.0
        assert band_idw[0, 8] == -9999.0
        assert band_count[0, 8] == 0  # pixel with 0 point
        assert band_stdev[0, 8] == -9999.0

        assert band_min[0, 10] == 2
        assert band_max[0, 10] == 2
        assert band_mean[0, 10] == 2
        assert band_idw[0, 10] == 2
        assert band_count[0, 10] == 1  # pixel with one single point (class 2)
        assert band_stdev[0, 10] == 0

        assert band_min[17, 14] == 1
        assert band_max[17, 14] == 65
        assert round(band_mean[17, 14], 4) == 2.9375
        assert round(band_idw[17, 14], 4) == 4.6058
        assert band_count[17, 14] == 64  # pixel with 64 points and at least class 1 and 65
        assert round(band_stdev[17, 14], 4) == 7.8220


def test_fill_gaps_raster():
    input_file = Path("data") / "raster" / "class_raw" / f"{TILENAME}.tif"
    output_file = Path(OUTPUT_DIR) / "fill_gaps_raster" / f"{TILENAME}.tif"
    fill_gaps_raster(
        in_raster=input_file,
        output_file=output_file,
        raster_driver=RASTER_DRIVER,
    )
    with rasterio.open(output_file) as raster:
        band_max = raster.read(1)
        assert band_max[6, 17] == -9999.0  # gap not filled
        assert band_max[0, 8] != -9999.0  # gap filled
        assert band_max[0, 10] == 2  # max (band_G) kept from input raster
        assert band_max[17, 14] == 65  # max (band_G) kept from input raster


def test_add_color_to_raster():
    input_file = Path("data") / "raster" / "class_fill_gaps" / f"{TILENAME}.tif"
    output_file = Path(OUTPUT_DIR) / "add_color_to_raster" / f"{TILENAME}.tif"
    add_color_to_raster(
        in_raster=input_file,
        output_file=output_file,
        LUT=os.path.join("LUT", "LUT_CLASS.txt"),
    )
    with rasterio.open(output_file) as raster:
        band_R = raster.read(1)
        band_G = raster.read(2)
        band_B = raster.read(3)

        assert band_R[6, 17] == 255  # nodata -> color not defined in LUT => white
        assert band_G[6, 17] == 255  # nodata -> color not defined in LUT => white
        assert band_B[6, 17] == 255  # nodata -> color not defined in LUT => white

        assert band_R[0, 10] == 255  # sol (classe 2) -> color defined in LUT
        assert band_G[0, 10] == 128  # sol (classe 2) -> color defined in LUT
        assert band_B[0, 10] == 0  # sol (classe 2) -> color defined in LUT

        assert band_R[17, 14] == 64  # artefact (classe 65) -> color defined in LUT
        assert band_G[17, 14] == 0  # artefact (classe 65) -> color defined in LUT
        assert band_B[17, 14] == 128  # artefact (classe 65) -> color defined in LUT


def test_create_map_class_raster_with_postprocessing_color_and_hillshade_default():
    output_dir = Path(OUTPUT_DIR) / "create_map_class_raster_with_postprocessing_color_and_hillshade_default"
    las_bounds = utils_pdal.get_bounds_from_las(INPUT_FILE)
    with initialize(version_base="1.2", config_path="../configs"):
        cfg = compose(
            config_name="config_ctview",
            overrides=[
                f"io.output_dir={output_dir}",
                f"io.tile_geometry.tile_coord_scale={TILE_COORD_SCALE}",
                f"io.tile_geometry.tile_width={TILE_WIDTH}",
                f"buffer.size={BUFFER_SIZE}",
            ],
        )
    create_map_class_raster_with_postprocessing_color_and_hillshade(
        INPUT_FILE, TILENAME, cfg.class_map, cfg.io, las_bounds
    )
    assert os.listdir(output_dir) == ["CLASS_FINAL"]
    assert not glob.glob("tmp/tmp_class*")
    with rasterio.Env():
        with rasterio.open(Path(output_dir) / "CLASS_FINAL" / f"{TILENAME}_fusion_DSM_class.tif") as raster:
            band_R = raster.read(1)
            band_G = raster.read(2)
            band_B = raster.read(3)
            assert band_R[0, 0] is not None
            assert band_G[0, 0] is not None
            assert band_B[0, 0] is not None
            assert raster.res == (0.5, 0.5)


def test_create_map_class_raster_with_postprocessing_color_and_hillshade_and_intermediate_files():
    output_dir = (
        Path(OUTPUT_DIR) / "create_map_class_raster_with_postprocessing_color_and_hillshade_and_intermediate_files"
    )
    las_bounds = utils_pdal.get_bounds_from_las(INPUT_FILE)
    with initialize(version_base="1.2", config_path="../configs"):
        # config is relative to a module
        cfg = compose(
            config_name="config_ctview",
            overrides=[
                f"io.output_dir={output_dir}",
                f"io.tile_geometry.tile_coord_scale={TILE_COORD_SCALE}",
                f"io.tile_geometry.tile_width={TILE_WIDTH}",
                f"buffer.size={BUFFER_SIZE}",
                "class_map.intermediate_dirs.CC_raw=CC_1_raw",
                "class_map.intermediate_dirs.CC_raw_color=CC_2_bcolor",
                "class_map.intermediate_dirs.CC_fillgap=CC_3_fg",
                "class_map.intermediate_dirs.CC_fillgap_color=CC_4_fgcolor",
                "class_map.intermediate_dirs.CC_crop=CC_5_crop",
                "class_map.intermediate_dirs.dxm_raw=DSM_VAL",
                "class_map.intermediate_dirs.dxm_hillshade=DSM_HS",
            ],
        )
    create_map_class_raster_with_postprocessing_color_and_hillshade(
        INPUT_FILE, TILENAME, cfg.class_map, cfg.io, las_bounds
    )
    assert set(os.listdir(output_dir)) == {
        "CC_1_raw",
        "CC_2_bcolor",
        "CC_3_fg",
        "CC_4_fgcolor",
        "CC_5_crop",
        "CLASS_FINAL",
        "DSM_VAL",
        "DSM_HS",
    }

    with rasterio.Env():
        with rasterio.open(Path(output_dir) / "CC_4_fgcolor" / f"{TILENAME}_fillgap_color.tif") as raster:
            band_R = raster.read(1)
            band_G = raster.read(2)
            band_B = raster.read(3)
            assert band_R[0, 0] == 255  # ground point
            assert band_G[0, 0] == 128
            assert band_B[0, 0] == 0
            assert raster.res == (0.5, 0.5)

        with rasterio.open(Path(output_dir) / "CLASS_FINAL" / f"{TILENAME}_fusion_DSM_class.tif") as raster:
            band_R = raster.read(1)
            band_G = raster.read(2)
            band_B = raster.read(3)
            assert band_R[0, 0] is not None
            assert band_G[0, 0] is not None
            assert band_B[0, 0] is not None
            assert raster.res == (0.5, 0.5)


def test_main():
    execute_main_default()
    execute_main_change_pixel_size()


def execute_main_default():
    output_dir = Path(OUTPUT_DIR) / "execute_main_default"
    os.system(
        f"""
        python -m ctview.map_class \
        io.input_filename={INPUT_FILENAME} \
        io.input_dir={INPUT_DIR} \
        io.output_dir={output_dir} \
        io.tile_geometry.tile_coord_scale={TILE_COORD_SCALE} \
        io.tile_geometry.tile_width={TILE_WIDTH} \
        """
    )
    with rasterio.Env():
        with rasterio.open(Path(output_dir) / "CLASS_FINAL" / f"{TILENAME}_fusion_DSM_class.tif") as raster:
            band_R = raster.read(1)
            band_G = raster.read(2)
            band_B = raster.read(3)
            assert band_R[0, 0] is not None
            assert band_G[0, 0] is not None
            assert band_B[0, 0] is not None
            assert raster.res == (0.5, 0.5)


def execute_main_change_pixel_size():
    output_dir = Path(OUTPUT_DIR) / "execute_main_change_pixel_size"
    os.system(
        f"""
    python -m ctview.map_class \
    io.input_filename={INPUT_FILENAME} \
    io.input_dir={INPUT_DIR} \
    io.output_dir={output_dir} \
    io.tile_geometry.tile_coord_scale={TILE_COORD_SCALE} \
    io.tile_geometry.tile_width={TILE_WIDTH} \
    class_map.pixel_size=5 \
    """
    )
    with rasterio.Env():
        with rasterio.open(Path(output_dir) / "CLASS_FINAL" / f"{TILENAME}_fusion_DSM_class.tif") as raster:
            band_R = raster.read(1)
            band_G = raster.read(2)
            band_B = raster.read(3)
            assert band_R[0, 0] is not None
            assert band_G[0, 0] is not None
            assert band_B[0, 0] is not None
            assert raster.res == (5, 5)
