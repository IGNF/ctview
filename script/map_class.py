#Autor : ELucon

#IMPORT

# Library
import pdal
import tools
import sys
import logging as log
import os

from osgeo import gdal
from typing import Optional
from numbers import Real


# Library intern
import utils_gdal
from osgeo_utils import gdal_fillnodata





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




def fill_no_data(src_raster: Optional[str] = None, dst_raster: Optional[str] = None, max_Search_Distance: Real = 2):
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


def main():

    # Pour tester ce fichier de création de raster colorisé par classe après une interpolation

    try :
        # Pour tester ce fichier de création de raster colorisé par classe après une interpolation
        input_las = sys.argv[1:][0]
        # Dossier dans lequel seront créés les fichiers
        output_dir = sys.argv[1:][1]

    except IndexError :
        log.critical("IndexError : Wrong number of argument : 2 expected (las path, destination folder)")
        sys.exit()

    # Clean folder
    for filename in os.listdir(output_dir):
        os.remove(os.path.join(output_dir, filename))

    input_las_name = os.path.basename(input_las)
    input_las_name_without_extension = os.path.splitext(input_las_name)[0]    # Read las
    in_points = tools.read_las(input_las)

    # Write raster
    output_raster = os.path.join(output_dir,f'{input_las_name_without_extension}_raster.tif')
    tools.write_raster_class(in_points, output_raster)

    # Fill gaps
    fillgap_raster = os.path.join(output_dir,f'{input_las_name_without_extension}_raster_fillgap.tif')
   
    fill_no_data(
        src_raster=output_raster,
        dst_raster=fillgap_raster,
        max_Search_Distance=2, #modif 10/01/2023

    )

    # Color fill gaps
    color_fillgap_raster = os.path.join(output_dir,f'{input_las_name_without_extension}_raster_fillgap_color.tif')
    tools.color_raster_by_class_2(
        input_raster=fillgap_raster,
        output_raster=color_fillgap_raster,
        )
    print(color_fillgap_raster)
    # Color fill
    color_raster = os.path.join(output_dir,f'{input_las_name_without_extension}_raster_color_.tif')
    tools.color_raster_by_class_2(
        input_raster=output_raster,
        output_raster=color_raster,
        )




if __name__ == "__main__":

    main()





