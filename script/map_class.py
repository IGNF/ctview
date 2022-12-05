#Autor : ELucon

#IMPORT

import pdal
from osgeo import gdal
import tools
import utils_gdal
from osgeo_utils import gdal_fillnodata
from typing import Optional
from numbers import Real




#FONCTION

def fill_gaps(input_raster):
    """
    NO FONKTIONIERT
    Fill selected raster regions by interpolation from the edges.
    This algorithm will interpolate values for all designated nodata pixels.
    The default mask band used is the one returned by GDALGetMaskBand(hTargetBand).
    """
    opened_raster = gdal.OpenEx(input_raster)
    band_raster = gdal.Dataset.GetRasterBand(opened_raster, 1)
    mask_band_raster = gdal.Band.GetMaskBand(band_raster)

    gdal.FillNodata(
        targetBand=band_raster,
        maskBand=mask_band_raster,
        maxSearchDist=2,
        smoothingIterations=0,
    )




def fill_no_data(src_raster: Optional[str] = None, dst_raster: Optional[str] = None, max_Search_Distance: Real = 100):
    """Fill gap in the data.
    input_raster : raster to fill
    output_raster : raster with no gap
    max_Search_Distance : maximum distance (in pixel) that the algorithm will search out for values to interpolate.
    """
    gdal_fillnodata.gdal_fillnodata(
        src_filename=src_raster,
        band_number=2,
        dst_filename=dst_raster,
        driver_name='GTiff',
        creation_options=None,
        quiet=True,
        mask='default',
        max_distance=max_Search_Distance,
        smoothing_iterations=0,
        options=None,
    )






# TEST

if __name__ == "__main__":

    import sys
    # Pour tester ce fichier de création de raster colorisé par classe après une interpolation
    in_las = sys.argv[1:][0]
    # Read las
    in_points = tools.read_las(in_las)

    # Write raster
    output_raster = f'../test_raster/{in_las[7:-4]}_raster.tif'
    tools.write_raster_class(in_points, output_raster)

    # Fill gaps
    fillgap_raster = f'../test_raster/{in_las[7:-4]}_raster_fillgap.tif'
    #fillgap_color_raster = fill_gaps(color_raster)
    fill_no_data(
        src_raster=output_raster,
        dst_raster=fillgap_raster,
        max_Search_Distance=100,

    )

    # Color fill gaps
    color_fillgap_raster = f'../test_raster/{in_las[7:-4]}_raster_fillgap_color.tif'
    tools.color_raster_by_class_2(
        input_raster=fillgap_raster,
        output_raster=color_fillgap_raster,
        )

    # Color fill
    color_raster = f'../test_raster/{in_las[7:-4]}_raster_color_.tif'
    tools.color_raster_by_class_2(
        input_raster=output_raster,
        output_raster=color_raster,
        )


    # # Color qui marche pas
    # colorinterp_raster = f'../test_raster/raster2_colorinterp_{in_las[7:-4]}.tif'
    # colorinterp_points = tools.color_points_by_class(in_points)
    # tools.write_raster_class(colorinterp_points, colorinterp_raster)

    # # Info
    # metadata = utils_gdal.get_info_from_las(in_points)
    # print(metadata)

    # # Color
    # color_points = tools.color_points_by_class(in_points)
    # # Write raster
    # output_raster_color = f'../test_raster/raster_color{in_las[7:-4]}.tif'
    # tools.write_raster(color_points, output_raster_color)
    # output_raster = f'../test_raster/raster_{in_las[7:-4]}.tif'
    # tools.write_raster(in_points, output_raster)




