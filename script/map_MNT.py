# Autor : ELucon


# IMPORT

import pdal
from osgeo import gdal
import tools
import utils_gdal
import numpy
import subprocess



# FONCTION

def build_dtm_from_points(
    points, output_dtm: str, epsg: int, dtm_type: str, resolution: float
):
    """build a dtm from points - dtm_type (min, max, mean)"""
    pipeline = pdal.Writer.gdal(
        filename=output_dtm,
        resolution=resolution,
        output_type=dtm_type,
        where="(Classification == 2 || Classification == 66)",
        data_type="Float32",
    ).pipeline(points)
    pipeline.execute()
    utils_gdal.add_epsg_to_raster(output_dtm, epsg)


def build_dtm_from_las(
    input_las: str, output_dtm: str, epsg: int, dtm_type: str, resolution: float
):
    """build a dtm from las - dtm_type (min, max, mean)"""
    points_ini = tools.read_las(input_las)
    return build_dtm_from_points(points_ini, output_dtm, epsg, dtm_type, resolution)


def hillshade_from_raster(
    input_raster: str, output_raster: str
):
    """Add hillshade to raster"""
    gdal.DEMProcessing(
        destName=output_raster,
        srcDS=input_raster,
        processing = "hillshade",
        )




def create_LUT_X_cycles(
    cycle: int
):


def color_MNT_with_cycles(
    input_raster: str, output_raster: str, nb_cycle: int
):


# TEST

if __name__ == "__main__":

    import sys
    # Pour tester ce fichier de création de raster colorisé par classe après une interpolation
    in_las = sys.argv[1:][0]

    # Fichier de sortie
    out_dtm_raster = f"../test_raster/DTM/{in_las[7:-4]}_DTM.tif"

    # Paramètres
    EPSG = 2154
    DTM_TYPE = "all"
    RESOLUTION = 1 #mètres

    # Création
    build_dtm_from_las(
        input_las = in_las,
        output_dtm = out_dtm_raster,
        epsg = EPSG,
        dtm_type = DTM_TYPE,
        resolution = RESOLUTION,
    )

    # Ajout ombrage
    in_file = out_dtm_raster
    out_file = f"../test_raster/DTM/{in_las[7:-4]}_DTM_hillshade.tif"
    hillshade_from_raster(
        input_raster = in_file,
        output_raster = out_file,
    )
