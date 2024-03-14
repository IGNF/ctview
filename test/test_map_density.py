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

import ctview.map_density as map_density

INPUT_DIR = Path("data") / "las"
OUTPUT_DIR = Path("tmp") / "map_density"
EPSG = 2154

INPUT_FILENAME_50M = "test_data_0000_0000_LA93_IGN69_ground.las"

INPUT_LAS_50m = Path(INPUT_DIR) / INPUT_FILENAME_50M
LAS = laspy.read(INPUT_LAS_50m)
INPUT_POINTS = np.vstack((LAS.x, LAS.y, LAS.z)).transpose()
INPUT_CLASSIFS = np.copy(LAS.classification)


def setup_module():
    try:
        shutil.rmtree(OUTPUT_DIR)
    except FileNotFoundError:
        pass
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def test_compute_density():
    origin_x, origin_y = utils_pcd.get_pointcloud_origin(points=INPUT_POINTS, tile_size=50)

    density = map_density.compute_density(INPUT_POINTS, (origin_x, origin_y), 50, 2)

    assert density.shape == (25, 25)


def test_generate_raster_of_density():
    output_tif = Path(OUTPUT_DIR) / "output_generate_raster_of_density_2.tif"
    map_density.generate_raster_of_density(
        input_points=INPUT_POINTS,
        input_classifs=INPUT_CLASSIFS,
        output_tif=output_tif,
        epsg=EPSG,
        tile_size=50,
        pixel_size=2,
        raster_driver="GTiff",
    )
    assert os.path.isfile(output_tif)
    with rasterio.open(output_tif) as raster:
        band1 = raster.read(1)
        assert band1[0, 0] == 28 / 2**2  # density = nb_pt / pixel_size **2 = 28/2**2
        assert band1[5, 0] == 1 / 2**2
        assert band1[6, 0] == 0


def test_generate_raster_of_density_multiband():
    output_raster_multi = Path(OUTPUT_DIR) / "multiband_raster.tif"
    map_density.generate_raster_of_density(
        input_points=INPUT_POINTS,
        input_classifs=INPUT_CLASSIFS,
        classes_by_layer=[[], [125]],
        output_tif=output_raster_multi,
        epsg=EPSG,
        tile_size=50,
        pixel_size=2,
        raster_driver="GTiff",
    )
    assert os.path.isfile(output_raster_multi)
    with rasterio.open(output_raster_multi) as raster_multi:
        band1 = raster_multi.read(1)
        assert band1[0, 0] == 28 / 2**2  # density = nb_pt / pixel_size **2 = 28/2**2
        band2 = raster_multi.read(2)
        assert band2[0, 0] == 0  # this band contains no point because none have classification 125


def test_generate_raster_of_density_raster_driver():
    output_raster = Path(OUTPUT_DIR) / "output_generate_raster_of_density_2.gpkg"
    map_density.generate_raster_of_density(
        input_points=INPUT_POINTS,
        input_classifs=INPUT_CLASSIFS,
        output_tif=output_raster,
        epsg=EPSG,
        tile_size=50,
        pixel_size=2,
        raster_driver="GPKG",
    )
    assert os.path.isfile(output_raster)
    with rasterio.open(output_raster) as raster:
        band1 = raster.read(1)
        assert band1[0, 0] == 28 / 2**2  # density = nb_pt / pixel_size **2 = 28/2**2
        assert band1[5, 0] == 1 / 2**2
        assert band1[6, 0] == 0


def test_generate_raster_of_density_single_list():
    output_tif = Path(OUTPUT_DIR) / "output_generate_raster_of_density_2.tif"
    with pytest.raises(TypeError):
        map_density.generate_raster_of_density(
            input_points=INPUT_POINTS,
            input_classifs=INPUT_CLASSIFS,
            output_tif=output_tif,
            classes_by_layer=[2, 3],
            epsg=EPSG,
            tile_size=50,
            pixel_size=2,
            raster_driver="GTiff",
        )


def test_create_density_raster_with_color_and_hillshade_default():
    input_dir = Path("data") / "las" / "ground"
    input_filename = "test_data_77055_627755_LA93_IGN69.las"
    input_tilename = os.path.splitext(input_filename)[0]
    tile_width = 50
    tile_coord_scale = 10
    pixel_size = 2
    buffer_size = 10
    output_dir = OUTPUT_DIR / "create_density_raster_with_color_and_hillshade_default"
    input_tilename = os.path.splitext(input_filename)[0]
    with initialize(version_base="1.2", config_path="../configs"):
        # config is relative to a module
        cfg = compose(
            config_name="config_ctview",
            overrides=[
                f"io.input_filename={input_filename}",
                f"io.input_dir={input_dir}",
                f"io.output_dir={output_dir}",
                f"io.tile_geometry.tile_coord_scale={tile_coord_scale}",
                f"io.tile_geometry.tile_width={tile_width}",
                f"buffer.size={buffer_size}",
                f"density.pixel_size={pixel_size}",
            ],
        )
    map_density.create_density_raster_with_color_and_hillshade(
        os.path.join(input_dir, input_filename), input_tilename, cfg.density, cfg.io, cfg.buffer.size
    )
    assert os.listdir(output_dir) == ["DENS_FINAL"]
    assert not glob.glob("tmp/tmp_density*")
    with rasterio.Env():
        with rasterio.open(Path(output_dir) / "DENS_FINAL" / f"{input_tilename}_DENS.tif") as raster:
            data = raster.read()
            assert data.shape[0] == 3
            assert data.shape[1] == tile_width / pixel_size
            assert data.shape[2] == tile_width / pixel_size
            for ii in range(3):
                assert np.any(data[ii, :, :])


def test_create_density_raster_with_color_and_hillshade_and_intermediate_files():
    input_dir = Path("data") / "las" / "ground"
    input_filename = "test_data_77055_627755_LA93_IGN69.las"
    input_tilename = os.path.splitext(input_filename)[0]
    tile_width = 50
    tile_coord_scale = 10
    pixel_size = 2
    buffer_size = 10
    output_dir = OUTPUT_DIR / "create_density_raster_with_color_and_hillshade_and_intermediate"
    input_tilename = os.path.splitext(input_filename)[0]
    with initialize(version_base="1.2", config_path="../configs"):
        # config is relative to a module
        cfg = compose(
            config_name="config_ctview",
            overrides=[
                f"io.input_filename={input_filename}",
                f"io.input_dir={input_dir}",
                f"io.output_dir={output_dir}",
                f"io.tile_geometry.tile_coord_scale={tile_coord_scale}",
                f"io.tile_geometry.tile_width={tile_width}",
                f"buffer.size={buffer_size}",
                f"density.pixel_size={pixel_size}",
                "density.intermediate_dirs.density_values=DENS_VAL",
                "density.intermediate_dirs.density_color=DENS_COL",
                "density.intermediate_dirs.dxm_raw=DENS_DTM",
                "density.intermediate_dirs.dxm_hillshade=DENS_HS",
            ],
        )
    map_density.create_density_raster_with_color_and_hillshade(
        os.path.join(input_dir, input_filename), input_tilename, cfg.density, cfg.io, cfg.buffer.size
    )
    for folder in ["DENS_FINAL", "DENS_VAL", "DENS_COL", "DENS_DTM", "DENS_HS"]:
        assert len(os.listdir(os.path.join(output_dir, folder))) == 1


def test_create_density_raster_with_color_and_hillshade_multiple_layers():
    input_dir = Path("data") / "las" / "ground"
    input_filename = "test_data_77055_627755_LA93_IGN69.las"
    input_tilename = os.path.splitext(input_filename)[0]
    tile_width = 50
    tile_coord_scale = 10
    pixel_size = 2
    buffer_size = 10
    output_dir = OUTPUT_DIR / "create_density_raster_with_color_and_hillshade"
    input_tilename = os.path.splitext(input_filename)[0]
    with initialize(version_base="1.2", config_path="../configs"):
        # config is relative to a module
        cfg = compose(
            config_name="config_ctview",
            overrides=[
                f"io.input_filename={input_filename}",
                f"io.input_dir={input_dir}",
                f"io.output_dir={output_dir}",
                f"io.tile_geometry.tile_coord_scale={tile_coord_scale}",
                f"io.tile_geometry.tile_width={tile_width}",
                f"buffer.size={buffer_size}",
                f"density.pixel_size={pixel_size}",
                "density.keep_classes=[[1, 2]]",
            ],
        )
    with pytest.raises(TypeError):
        map_density.create_density_raster_with_color_and_hillshade(
            os.path.join(input_dir, input_filename), input_tilename, cfg.density, cfg.io, cfg.buffer.size
        )


def test_create_density_raster_with_color_and_hillshade_empty():
    """Test that the create_density_raster_with_color_and_hillshade function
    creates a black tif when there is no points with the requested classes"""
    input_dir_water = Path("data") / "laz" / "water"
    input_filename_water = "Semis_2021_0785_6378_LA93_IGN69_water.laz"
    tile_width = 1000
    tile_coord_scale = 1000
    buffer_size = 10
    pixel_size = 1
    output_dir = OUTPUT_DIR / "create_density_raster_with_color_and_hillshade_empty"
    input_tilename = os.path.splitext(input_filename_water)[0]
    with initialize(version_base="1.2", config_path="../configs"):
        # config is relative to a module
        cfg = compose(
            config_name="config_ctview",
            overrides=[
                f"io.input_filename={input_filename_water}",
                f"io.input_dir={input_dir_water}",
                f"io.output_dir={output_dir}",
                f"io.tile_geometry.tile_coord_scale={tile_coord_scale}",
                f"io.tile_geometry.tile_width={tile_width}",
                f"buffer.size={buffer_size}",
                f"density.pixel_size={pixel_size}",
            ],
        )
    map_density.create_density_raster_with_color_and_hillshade(
        os.path.join(input_dir_water, input_filename_water), input_tilename, cfg.density, cfg.io, cfg.buffer.size
    )
    with rasterio.Env():
        with rasterio.open(Path(output_dir) / "DENS_FINAL" / f"{input_tilename}_DENS.tif") as raster:
            data = raster.read()
            assert data.shape[0] == 3
            assert data.shape[1] == tile_width / pixel_size
            assert data.shape[2] == tile_width / pixel_size
            assert np.all(data == 255)  # default nodata value of gdal_calc with input Byte data
