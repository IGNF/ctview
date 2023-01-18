# Autor : ELucon

# IMPORT

# File
import tools
import utils_gdal
import gen_LUT_X_cycle

# Library
import pdal
from osgeo import gdal
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


def hillshade_from_raster(input_raster: str, output_raster: str):
    """Add hillshade to raster"""
    gdal.DEMProcessing(
        destName=output_raster,
        srcDS=input_raster,
        processing="hillshade",
    )


def color_MNT_with_cycles(file_las: str, file_MNT: str, nb_cycle: int, verbose=False):
    """Color a raster with a LUT created depending of a choice of cycles
    file_las : str : points cloud
    file_MNT : str : MNT corresponding to the points cloud
    nb_cycle : int : the number of cycle that determine the LUT
    """

    if verbose:
        print("Generate MNT colorised :")
        print("(1/2) Generate LUT.")
    # Create LUT
    LUT = gen_LUT_X_cycle.generate_LUT_X_cycle(
        file_las=file_las, file_MNT=file_MNT, nb_cycle=nb_cycle, verbose=verbose
    )

    # Path MNT colorised
    file_MNT_color = (
        f"../test_raster/DTM/{file_las[-31:-4]}_DTM_hillshade_color{nb_cycle}c.tif"
    )

    if verbose:
        print("(2/2) Colorise raster.")

    # Colorisation
    tools.color_raster_with_LUT(
        input_raster=file_MNT,
        output_raster=file_MNT_color,
        LUT=LUT,
    )


def generate_DTM_hs_color(verbose=False):
    """Generate a DTM with hillshade and colorisation configurable."""

    import sys

    # Pour tester ce fichier de création de raster colorisé par classe après une interpolation
    in_las = sys.argv[1:][0]

    # Fichier de sortie
    out_dtm_raster = f"../test_raster/DTM/{in_las[-31:-4]}_DTM.tif"

    # Paramètres
    EPSG = 2154
    DTM_TYPE = "all"
    RESOLUTION = 1  # mètres

    # Création
    if verbose:
        print("Build DTM brut...")

    build_dtm_from_las(
        input_las=in_las,
        output_dtm=out_dtm_raster,
        epsg=EPSG,
        dtm_type=DTM_TYPE,
        resolution=RESOLUTION,
    )

    if verbose:
        print("Success.\n")

    # Ajout ombrage
    if verbose:
        print("Add hillshade...")

    dtm_file = out_dtm_raster
    dtm_hs_file = f"../test_raster/DTM/{in_las[-31:-4]}_DTM_hillshade.tif"
    hillshade_from_raster(
        input_raster=dtm_file,
        output_raster=dtm_hs_file,
    )

    if verbose:
        print("Success.\n")

    # Colorisation
    if verbose:
        print("Add color...")

    nb_raster_color = int(input("How many raster colorised ? : "))

    for i in range(nb_raster_color):

        cycle = int(input(f"Raster {i+1}/{nb_raster_color} : how many cycles ? : "))

        if verbose:
            print(f"Build raster {i+1}/{nb_raster_color}...")

        color_MNT_with_cycles(
            file_las=in_las, file_MNT=dtm_hs_file, nb_cycle=cycle, verbose=verbose
        )

        if verbose:
            print("Success.\n")

    if verbose:
        print("End.")


# TEST

if __name__ == "__main__":

    generate_DTM_hs_color(verbose=True)
