from ctview import utils_gdal
import os
import pytest

RASTER = os.path.join("data","raster","test_data_0000_0000_LA93_IGN69_ground.tif")

upper_left_x_expected = 770500.000
upper_left_y_expected = 6277551.000
lower_right_x_expected = 770551.000
lower_right_y_expected = 6277500.000

minx_expected = 770500.000
maxx_expected = 770551.000
miny_expected = 6277500.000
maxy_expected = 6277551.000


def test_get_raster_corner_coord():
    """Extract corners coordinates from a raster"""
    (ulx,uly,lrx,lry) = utils_gdal.get_raster_corner_coord(in_raster=RASTER)
    assert ulx == upper_left_x_expected
    assert uly == upper_left_y_expected
    assert lrx == lower_right_x_expected
    assert lry == lower_right_y_expected

def test_transform_CornerCoord_to_Bounds():
    """Re-arrange corners coordinates like ([minx,maxx],[miny,maxy])"""
    ccoord = utils_gdal.get_raster_corner_coord(in_raster=RASTER)
    ([minx,maxx],[miny,maxy]) = utils_gdal.transform_CornerCoord_to_Bounds(corner_coord=ccoord)
    assert minx == minx_expected
    assert maxx == maxx_expected
    assert miny == miny_expected
    assert maxy == maxy_expected

