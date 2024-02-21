import os
import shutil
from pathlib import Path

import rasterio
from hydra import compose, initialize
from pdaltools.las_add_buffer import create_las_with_buffer

import ctview.map_DXM as map_DXM

# GENERAL
OUTPUT_DIR = Path("tmp") / "map_DXM"
COORDX = 77055
COORDY = 627760
TILE_COORD_SCALE = 10
TILE_WIDTH = 50
SPATIAL_REFERENCE = "EPSG:2154"

INPUT_DIR_LAZ = os.path.join("data", "laz")
INPUT_DIR_LAS = os.path.join("data", "las")
INPUT_DIR_RASTER = os.path.join("data", "raster")


INPUT_FILENAME = f"test_data_{COORDX}_{COORDY}_LA93_IGN69.laz"
TILENAME = os.path.splitext(INPUT_FILENAME)[0]
INPUT_FILE = os.path.join(INPUT_DIR_LAZ, INPUT_FILENAME)

with initialize(version_base="1.2", config_path="../configs"):
    # config is relative to a module
    CONFIG_2 = compose(
        config_name="config_ctview",
        overrides=[
            f"io.tile_geometry.tile_coord_scale={TILE_COORD_SCALE}",
            f"io.tile_geometry.tile_width={TILE_WIDTH}",
        ],
    )

EXPECTED_DTM_INTERP = os.path.join("DTM", "test_data_77055_627760_LA93_IGN69_interp.tif")
EXPECTED_DTM_HILLSHADE = os.path.join("tmp_dtm", "hillshade", "test_data_77055_627760_LA93_IGN69_hillshade.tif")
EXPECTED_DTM_COLORED = [
    os.path.join("DTM", "color", "1cycle", "test_data_77055_627760_LA93_IGN69_DTM_hillshade_color1c.tif"),
    os.path.join("DTM", "color", "4cycles", "test_data_77055_627760_LA93_IGN69_DTM_hillshade_color4c.tif"),
]


EXPECTED_DSM_INTERP = os.path.join("DSM", "test_data_77055_627760_LA93_IGN69_interp.tif")
EXPECTED_DSM_HILLSHADE = os.path.join("tmp_dsm", "hillshade", "test_data_77055_627760_LA93_IGN69_hillshade.tif")
EXPECTED_COLOR_MAP_WITH_HILLSHADE = os.path.join("CC_6_fusion", "test_data_77055_627760_LA93_IGN69_color_map.tif")

EXPECTED_DTM_DENS_INTERP = os.path.join("DTM_DENS", "test_data_77055_627760_LA93_IGN69_interp.tif")
EXPECTED_DTM_DENS_HILLSHADE = os.path.join(
    "tmp_dtm_dens", "hillshade", "test_data_77055_627760_LA93_IGN69_hillshade.tif"
)
EXPECTED_DENS_WITH_HILLSHADE = os.path.join("DENS_FINAL", "test_data_77055_627760_LA93_IGN69_DENS.tif")


def setup_module(module):
    try:
        shutil.rmtree(OUTPUT_DIR)

    except FileNotFoundError:
        pass
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def test_create_raw_DXM_default_pixelsize():
    """
    Verify :
        - .tif are created
        - output is the raster hillshaded
    """
    output_dir = os.path.join(OUTPUT_DIR, "create_raw_DXM_default_pixelsize")
    raster_dxm_raw = os.path.join(
        output_dir,
        CONFIG_2.dtm.intermediate_dirs.dxm_raw,
        f"{TILENAME}_interp{CONFIG_2.io.extension}",
    )
    os.makedirs(os.path.dirname(raster_dxm_raw))
    map_DXM.create_raw_dxm(
        input_file=INPUT_FILE,
        output_dxm=raster_dxm_raw,
        pixel_size=CONFIG_2.dtm.pixel_size,
        keep_classes=CONFIG_2.dtm.keep_classes,
        dxm_interpolation=CONFIG_2.dtm.dxm_interpolation,
        config_io=CONFIG_2.io,
    )

    assert os.path.isfile(os.path.join(output_dir, EXPECTED_DTM_INTERP))
    assert raster_dxm_raw == os.path.join(output_dir, EXPECTED_DTM_INTERP)


def test_create_colored_dxm_with_hillshade_dtm_1m():
    """
    Verify :
        - all .tif are created
        - pixel size is 1m
    """
    output_dir = os.path.join(OUTPUT_DIR, "create_colored_dxm_with_hillshade_dtm_1m")
    conf_dtm = CONFIG_2.dtm.copy()
    conf_dtm.color.cycles_DTM_colored = [1, 4]
    conf_io = CONFIG_2.io.copy()
    conf_io.output_dir = output_dir
    map_DXM.create_colored_dxm_with_hillshade(
        input_las=INPUT_FILE, tilename=TILENAME, config_dtm=conf_dtm, config_io=conf_io
    )

    assert os.path.isfile(os.path.join(output_dir, EXPECTED_DTM_INTERP))
    assert os.path.isfile(os.path.join(output_dir, EXPECTED_DTM_HILLSHADE))
    for p in EXPECTED_DTM_COLORED:
        assert os.path.isfile(os.path.join(output_dir, p))
        with rasterio.open(os.path.join(output_dir, p)) as raster:
            assert raster.res == (1, 1)


def test_add_dxm_hillshade_to_raster_dsm_50cm():
    """
    Verify :
        - all .tif are created
        - pixel size = 50cm
    """
    output_dir = os.path.join(OUTPUT_DIR, "add_dxm_hillshade_to_raster_dsm_50cm")
    input_raster = os.path.join(INPUT_DIR_RASTER, f"test_data_{COORDX}_{COORDY}_LA93_IGN69_COLOR_MAP_50cm.tif")
    output_raster = os.path.join(
        output_dir,
        CONFIG_2.class_map.output_subdir,
        f"{TILENAME}_color_map{CONFIG_2.io.extension}",
    )
    raster_dxm_raw = os.path.join(
        output_dir,
        CONFIG_2.class_map.intermediate_dirs.dxm_raw,
        f"{TILENAME}_interp{CONFIG_2.io.extension}",
    )
    raster_dxm_hillshade = os.path.join(
        output_dir,
        CONFIG_2.class_map.intermediate_dirs.dxm_hillshade,
        f"{TILENAME}_hillshade{CONFIG_2.io.extension}",
    )

    map_DXM.add_dxm_hillshade_to_raster(
        input_raster=input_raster,
        input_pointcloud=INPUT_FILE,
        output_raster=output_raster,
        pixel_size=0.5,
        keep_classes=CONFIG_2.class_map.keep_classes,
        dxm_interpolation=CONFIG_2.class_map.dxm_interpolation,
        output_dxm_raw=raster_dxm_raw,
        output_dxm_hillshade=raster_dxm_hillshade,
        hillshade_calc=CONFIG_2.class_map.hillshade_calc,
        config_io=CONFIG_2.io,
    )

    assert os.path.isfile(os.path.join(output_dir, EXPECTED_DSM_INTERP))
    assert os.path.isfile(os.path.join(output_dir, EXPECTED_DSM_HILLSHADE))
    assert output_raster == os.path.join(output_dir, EXPECTED_COLOR_MAP_WITH_HILLSHADE)
    assert os.path.isfile(os.path.join(output_dir, EXPECTED_COLOR_MAP_WITH_HILLSHADE))
    with rasterio.open(output_raster) as raster:
        assert raster.res == (0.5, 0.5)


def test_add_dxm_hillshade_to_raster_density_5m():
    """
    Verify :
        - .tif are created
        - pixel size = 5 meters
    """
    output_dir = os.path.join(OUTPUT_DIR, "add_dxm_hillshade_to_raster_density_5m")
    input_raster = os.path.join(INPUT_DIR_RASTER, f"test_data_{COORDX}_{COORDY}_LA93_IGN69_DENS_COLOR_5m.tif")
    output_raster = os.path.join(
        output_dir,
        CONFIG_2.density.output_subdir,
        f"{TILENAME}_DENS{CONFIG_2.io.extension}",
    )
    raster_dxm_raw = os.path.join(
        output_dir,
        CONFIG_2.density.intermediate_dirs.dxm_raw,
        f"{TILENAME}_interp{CONFIG_2.io.extension}",
    )
    raster_dxm_hillshade = os.path.join(
        output_dir,
        CONFIG_2.density.intermediate_dirs.dxm_hillshade,
        f"{TILENAME}_hillshade{CONFIG_2.io.extension}",
    )
    map_DXM.add_dxm_hillshade_to_raster(
        input_raster=input_raster,
        input_pointcloud=INPUT_FILE,
        output_raster=output_raster,
        pixel_size=5,
        keep_classes=CONFIG_2.density.keep_classes,
        dxm_interpolation=CONFIG_2.density.dxm_interpolation,
        output_dxm_raw=raster_dxm_raw,
        output_dxm_hillshade=raster_dxm_hillshade,
        hillshade_calc=CONFIG_2.density.hillshade_calc,
        config_io=CONFIG_2.io,
    )

    assert os.path.isfile(os.path.join(output_dir, EXPECTED_DTM_DENS_INTERP))
    assert os.path.isfile(os.path.join(output_dir, EXPECTED_DTM_DENS_HILLSHADE))
    assert output_raster == os.path.join(output_dir, EXPECTED_DENS_WITH_HILLSHADE)
    assert os.path.isfile(os.path.join(output_dir, EXPECTED_DENS_WITH_HILLSHADE))
    with rasterio.open(output_raster) as raster:
        assert raster.res == (5, 5)


def test_create_colored_dxm_with_hillshade():
    input_dir = Path("data") / "las" / "ground"
    input_filename = "test_data_77055_627755_LA93_IGN69.las"
    input_tilename = os.path.splitext(input_filename)[0]
    tile_width = 50
    tile_coord_scale = 10
    buffer_size = 10
    output_dir = OUTPUT_DIR / "main_create_colored_dxm_with_hillshade"
    las_with_buffer = output_dir / "buffer" / input_filename
    las_with_buffer.parent.mkdir(parents=True, exist_ok=True)
    with initialize(version_base="1.2", config_path="../configs"):
        # config is relative to a module
        cfg = compose(
            config_name="config_ctview",
            overrides=[
                f"io.input_filename={input_filename}",
                f"io.input_dir={input_dir}",
                f"io.output_dir={output_dir}",
                "dtm.color.cycles_DTM_colored=[1,4]",
                f"io.tile_geometry.tile_coord_scale={tile_coord_scale}",
                f"io.tile_geometry.tile_width={tile_width}",
                f"buffer.size={buffer_size}",
                f"dtm.pixel_size={1}",
            ],
        )
    create_las_with_buffer(
        input_dir=str(input_dir),
        tile_filename=os.path.join(input_dir, input_filename),
        output_filename=str(las_with_buffer),
        buffer_width=cfg.buffer.size,
        spatial_ref=cfg.io.spatial_reference,
        tile_width=cfg.io.tile_geometry.tile_width,
        tile_coord_scale=cfg.io.tile_geometry.tile_coord_scale,
    )

    map_DXM.create_colored_dxm_with_hillshade(str(las_with_buffer), input_tilename, cfg.dtm, cfg.io)
    with rasterio.Env():
        with rasterio.open(
            Path(output_dir) / "DTM" / "color" / "1cycle" / f"{input_tilename}_DTM_hillshade_color1c.tif"
        ) as raster:
            band1 = raster.read(1)
            band2 = raster.read(2)
            band3 = raster.read(3)
            assert band1[8, 8] == 255
            assert band2[8, 8] == 147
            assert band3[8, 8] == 0
            assert raster.res == (1, 1)
        with rasterio.open(
            Path(output_dir) / "DTM" / "color" / "4cycles" / f"{input_tilename}_DTM_hillshade_color4c.tif"
        ) as raster:
            band1 = raster.read(1)
            band2 = raster.read(2)
            band3 = raster.read(3)
            assert band1[8, 8] == 205
            assert band2[8, 8] == 103
            assert band3[8, 8] == 0
            assert raster.res == (1, 1)
