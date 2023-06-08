import os
import shutil
from ctview.map_DTM_DSM import run_mnx_filter_las_classes
import test.utils.point_cloud_utils as pcu


coordX = 77055
coordY = 627760

tmp_path = os.path.join("data", "labo")

expected_output_nb_points_ground = 22343
expected_output_nb_points_building = 14908


output_dir = os.path.join(tmp_path,  "ground")

output_default_file = os.path.join(output_dir, f"test_data_{coordX}_{coordY}_LA93_IGN69.laz")
output_las_file = os.path.join(output_dir,f"test_data_{coordX}_{coordY}_LA93_IGN69.las")


def setup_module():
    try:
        shutil.rmtree(tmp_path)

    except (FileNotFoundError):
        pass
    os.mkdir(tmp_path)
    os.mkdir(output_dir)


def test_run_mnx_filter_las_classes():
    '''
    Test call to filter_las_classes from library produit_derive_lidar.
    '''
    setup_module()
    run_mnx_filter_las_classes(
                        input_file="./data/laz/test_data_77055_627760_LA93_IGN69.laz",
                        output_file=output_default_file,
                        spatial_reference='EPSG:2154',
                        keep_classes=[2, 66])
    assert os.path.isfile(output_default_file)
    assert pcu.get_nb_points(output_default_file) == expected_output_nb_points_ground


def test_run_mnx_filter_las_classes_building_class():
    '''
    Test call to filter_las_classes from library produit_derive_lidar,
    with modification of class config.
    '''
    setup_module()
    run_mnx_filter_las_classes(
                        input_file="./data/laz/test_data_77055_627760_LA93_IGN69.laz",
                        output_file=output_default_file,
                        spatial_reference='EPSG:2154',
                        keep_classes=[6])
    assert os.path.isfile(output_default_file)
    assert pcu.get_nb_points(output_default_file) == expected_output_nb_points_building


def test_run_mnx_filter_las_classes_false_spatial_reference():
    '''
    Test call to filter_las_classes from library produit_derive_lidar,
    with modification of spatial reference.
    This must raise a RuntimeError
    '''
    setup_module()
    try : 
        run_mnx_filter_las_classes(
                        input_file="./data/laz/test_data_77055_627760_LA93_IGN69.laz",
                        output_file=output_default_file,
                        spatial_reference='EPSG:9999',
                        keep_classes=[2, 66])
        assert 0
    except RuntimeError:
        assert 1
