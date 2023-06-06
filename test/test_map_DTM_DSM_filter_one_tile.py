from produit_derive_lidar import filter_one_tile
from ctview.map_DTM_DSM import run_mnx_filter_one_tile
import os
import pytest
import shutil
import test.utils.point_cloud_utils as pcu
from hydra import initialize, compose


coordX = 77055
coordY = 627760

tmp_path = os.path.join("data", "labo")

expected_output_nb_points_ground = 22343
expected_output_nb_points_building = 14908


output_dir = os.path.join(tmp_path,  "ground")

output_default_file = os.path.join(output_dir, f"test_data_{coordX}_{coordY}_LA93_IGN69.laz")
output_las_file = os.path.join(output_dir,f"test_data_{coordX}_{coordY}_LA93_IGN69.las")


def setup_module(module):
    try:
        shutil.rmtree(output_dir)

    except (FileNotFoundError):
        pass
    os.mkdir(output_dir)


def test_filter_one_tile():
    '''
    Test call to run_filter_on_tile from library produit_derive_lidar.
    '''
    with initialize(version_base="1.2", config_path="../configs"):
        # config is relative to a module
        cfg = compose(config_name="config",
                      overrides=["io=test", "+tile_geometry=test",
                                 f"filter=default_test"])

    filter_one_tile.run_filter_on_tile(cfg)
    assert os.path.isfile(output_default_file)
    assert pcu.get_nb_points(output_default_file) == expected_output_nb_points_ground


def test_filter_one_tile_building_class():
    '''
    Test call to run_filter_on_tile from library produit_derive_lidar,
    with modification of class config.
    '''
    with initialize(version_base="1.2", config_path="../configs"):
        # config is relative to a module
        cfg = compose(config_name="config",
                      overrides=["io=test", "+tile_geometry=test",
                                 f"io.output_dir={output_dir}",
                                  f"filter.keep_classes=[6]"])
    filter_one_tile.run_filter_on_tile(cfg)
    assert os.path.isfile(output_default_file)
    assert pcu.get_nb_points(output_default_file) == expected_output_nb_points_building


def test_filter_one_tile_force_output():
    '''
    Test call to run_filter_on_tile from library produit_derive_lidar,
    with modification of output config.
    '''
    with initialize(version_base="1.2", config_path="../configs"):
        # config is relative to a module
        cfg = compose(config_name="config",
                        overrides=["io=test", "+tile_geometry=test",
                                    f"io.output_dir={output_dir}",
                                    f"filter=default_test",
                                    "io.forced_intermediate_ext=las"])
    filter_one_tile.run_filter_on_tile(cfg)
    assert os.path.isfile(output_las_file)
    assert pcu.get_nb_points(output_las_file) == expected_output_nb_points_ground


def test_run_mnx_filter_one_tile():
    '''
    Test of fonction run_mnx_filter_one_tile from library produit_derive_lidar.
    '''
    run_mnx_filter_one_tile(
                        output_dir=output_dir,
                        io_yaml_file='test',
                        tile_geometry_yaml_file='test',
                        filter_yaml_file='default_test')
    
    assert os.path.isfile(output_default_file)
    assert pcu.get_nb_points(output_default_file) == expected_output_nb_points_ground


def test_run_mnx_filter_one_tile_building_class():
    '''
    Test of fonction run_mnx_filter_one_tile from library produit_derive_lidar,
    with modification of class config.
    '''
    run_mnx_filter_one_tile(
                        output_dir=output_dir,
                        io_yaml_file='test',
                        tile_geometry_yaml_file='test',
                        filter_yaml_file='building_test')
    
    assert os.path.isfile(output_default_file)
    assert pcu.get_nb_points(output_default_file) == expected_output_nb_points_building


def test_run_mnx_filter_one_tile_force_output():
    '''
    Test of fonction run_mnx_filter_one_tile from library produit_derive_lidar,
    with modification of output config.
    '''
    run_mnx_filter_one_tile(
                        output_dir=output_dir,
                        io_yaml_file='test',
                        tile_geometry_yaml_file='test',
                        filter_yaml_file='default_test',
                        forced_intermediate_ext='laz')
    
    assert os.path.isfile(output_default_file)
    assert pcu.get_nb_points(output_default_file) == expected_output_nb_points_ground


# TODO : when change spatial_reference with a tile in EPSG:2194, this could raise an error
# def test_run_mnx_filter_one_tile_spatial_reference():
#     '''
#     Test of fonction run_mnx_filter_one_tile from library produit_derive_lidar.
#     '''
#     run_mnx_filter_one_tile(
#                         output_dir=output_dir,
#                         io_yaml_file='test',
#                         tile_geometry_yaml_file='test',
#                         filter_yaml_file='default_test',
#                         spatial_reference='EPSG:3689')
    
#     assert os.path.isfile(output_default_file)
#     assert pcu.get_nb_points(output_default_file) == expected_output_nb_points_ground


# def test_run_mnx_filter_las_classes():
#     '''
#     Test call to filter_las_classes from library produit_derive_lidar.
#     '''

#     assert 0==0