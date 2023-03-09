# Autor : ELucon

# IMPORT

# File
import ctview.utils_tools as utils_tools
import ctview.utils_pdal as utils_pdal
import ctview.utils_gdal as utils_gdal
from ctview.parameter import dico_param
from ctview.utils_folder import dico_folder
import ctview.gen_LUT_X_cycle as gen_LUT_X_cycle

# Library
import sys
import pdal
from osgeo import gdal
import numpy as np
import subprocess
import startinpy
import os
from sys import argv
from multiprocessing import Pool, cpu_count
import json
import laspy
import math
from tqdm import tqdm
import logging as log
from typing import List

# PARAMETERS

EPSG = dico_param["EPSG"]


def filter_las_classes(input_file: str,
                       output_file: str,
                       spatial_ref: str="EPSG:2154",
                       keep_classes: List=[2, 66]):
    """ Reads the LAS file and filter only grounds from LIDAR.

    Args:
        fileInput (str) : Path to the input lidar file
        spatial_ref (str) : spatial reference to use when reading the las file
        output_file (str): Path to the output file
        keep_classes (List): Classes to keep in the filter (ground + virtual points by default)
    """
    limits = ",".join(f"Classification[{c}:{c}]" for c in keep_classes)
    information = {}
    information = {
    "pipeline": [
            {
                "type":"readers.las",
                "filename": input_file,
                "override_srs": spatial_ref,
                "nosrs": True
            },
            {
                "type":"filters.range",
                "limits": limits
            },
            {
                "type": "writers.las",
                "a_srs": spatial_ref,
                # "minor_version": 4,
                # "dataformat_id": 6,
                "filename": output_file
            }
        ]
    }
    ground = json.dumps(information, sort_keys=True, indent=4)
    log.debug(ground)
    pipeline = pdal.Pipeline(ground)
    pipeline.execute()


def filter_las_ground_virtual(input_dir: str, filename: str):
    """Reads the LAS file and filter only grounds from LIDAR.

    Args:
        input_dir (str) : directory of projet who contains LIDAR (Ex. "data")
        file (str): name of LIDAR tiles
    """
    input_file = os.path.join(input_dir, filename)
    information = {}
    information = {
        "pipeline": [
            {
                "type": "readers.las",
                "filename": input_file,
                "override_srs": f"EPSG:{EPSG}",
                "nosrs": True,
            },
            {
                "type": "filters.range",
                "limits": "Classification[2:2],Classification[66:66]",
            },
        ]
    }
    ground = json.dumps(information, sort_keys=True, indent=4)
    log.debug(f"ground :{ground}")
    pipeline = pdal.Pipeline(ground)
    pipeline.execute()
    return pipeline.arrays[0]


def write_las(input_points, filename: str, output_dir: str, name: str):
    """Write a las file
    Args:
        inputs_points (array) : points cloud
        filename (str): name of LIDAR tiles
        output_dir (str): directory of work who will contains the output files
        name (str) : suffix added to filename
    """
    file_root = os.path.splitext(filename)[0]  # filename without extension

    os.makedirs(output_dir, exist_ok=True)  # create directory LAS/ if not exists

    log.debug(f"output_dir : {output_dir}")
    FileOutput = os.path.join(output_dir, f"{file_root}_{name}.las")

    log.debug(f"filename : {FileOutput}")
    pipeline = pdal.Writer.las(filename=FileOutput, a_srs=f"EPSG:{EPSG}").pipeline(
        input_points
    )
    pipeline.execute()

    return FileOutput


def las_prepare_1_file(input_file: str, size: float):
    """Takes the filepath to an input LAS (crop) file and the desired output raster cell size. Reads the LAS file and outputs
    the ground points as a numpy array. Also establishes some
    basic raster parameters:
        - the extents
        - the resolution in coordinates
        - the coordinate location of the relative origin (bottom left)

    Args:
        input_file (str): directory of pointclouds
        fname (str): name of LIDAR tile
        size (int): raster cell size

    Returns:
        extents(array) : extents
        res(list): resolution in coordinates
        origin(list): coordinate location of the relative origin (bottom left)
    """

    # Reads the LAS file and outputs the ground points as a numpy array.
    in_file = laspy.read(input_file)
    header = in_file.header
    log.debug(f'\nheader\n{header}')
    log.debug(f'\nextents = [[header.min[0], header.max[0]], [header.min[1], header.max[1]]]\nextents = {[[header.min[0], header.max[0]], [header.min[1], header.max[1]]]}')
    log.debug(f'\nin_file.x, in_file.y, in_file.z\n{in_file.x}\n{in_file.y}\n{in_file.z}')

    in_np = np.vstack(
        (in_file.x, in_file.y, in_file.z)
    ).transpose()
    log.debug(f'\nin_np : {in_np}')
    # import sys
    # sys.exit(1)
    extents = [[header.min[0], header.max[0]], [header.min[1], header.max[1]]]
    res = [
        math.ceil((extents[0][1] - extents[0][0]) / size),
        math.ceil((extents[1][1] - extents[1][0]) / size),
    ]
    origin = [
        np.mean(extents[0]) - (size / 2) * res[0],
        np.mean(extents[1]) - (size / 2) * res[1],
    ]
    return in_np, res, origin


def run_interpolate(pts, res, origin, size, method):
    """Run interpolation
    Args:
        pts : ground points clouds (for each point, just x-y-z coordinates)
        res(list): resolution in coordinates (1 000 km -> raster carré de 1 000km de côté)
        origin(list): coordinate location of the relative origin (bottom left)
        size (int): raster cell size (1m x 1m OU 5m x 5m)
        method (str) : interpolation method
    Output:
        ras: output raster (/!\ can be full of no-data value)
    """
    ras, success = interpolation(pts, res, origin, size, method)
    log.debug(f'\nsuccess :{success}')

    if not success:
        log.debug(f"type ras without {type(ras)}")
        ras = dico_param["no_data_value"] * np.ones([res[1], res[0]])
        log.debug(f"type ras with {type(ras)}")

        if res[1]==0 and res[0]==0 :
            log.warning("Array is empty ! Your origin las file is probably empty !")
        else :
            log.debug(f"resolution{res,res[1],res[0]}")
            log.debug(f"ras[0][0] apres ajout no data : {ras[0][0]}")
    return ras


def interpolation(pts, res, origin, size, method):
    """Run interpolation
    Args:
        pts : ground points clouds (for each point, just x-y-z coordinates)
        res(list): resolution in coordinates (1 000 km -> raster carré de 1 000km de côté)
        origin(list): coordinate location of the relative origin (bottom left)
        size (int): raster cell size (1m x 1m OU 5m x 5m)
        method (str) : interpolation method
    Output:
        ras: output raster (/!\ can be None)
        can_interpolate (bool): false if there were no points to interpolate
    """

    can_interpolate = pts.size > 0

    if can_interpolate:
        ras = execute_startin(pts, res, origin, size, method)

    else:
        ras = None
        
    return ras, can_interpolate


def execute_startin(pts, res, origin, size, method):
    """Takes the grid parameters and the ground points. Interpolates
    either using the TIN-linear or the Laplace method. Uses a -9999 no-data value.
    Fully based on the startin package (https://startinpy.readthedocs.io/en/latest/api.html)

    Args:
        pts : ground points clouds (for each point, just x-y-z coordinates)
        res(list): resolution in coordinates (1 000 km -> raster carré de 1 000km de côté)
        origin(list): coordinate location of the relative origin (bottom left)
        size (int): raster cell size (1m x 1m OU 5m x 5m)
        method (str) : interpolation method

    Returns:
        ras(list): Z interpolation
    """
    # # Startin
    tin = startinpy.DT()
    tin.insert(pts)  # # Insert each points in the array of points (a 2D array)
    ras = np.zeros(
        [res[1], res[0]]
    )  # # returns a new array of given shape and type, filled with zeros
    # # Interpolate method Laplace or TIN Linear
    if method == "Laplace":

        def interpolant(x, y):
            return tin.interpolate_laplace(x, y)

    elif method == "TINlinear":

        def interpolant(x, y):
            return tin.interpolate_tin_linear(x, y)

    cp = 0
    cp2 = 0
    yi = 0
    # Initialiser la barre de progression
    pbar = tqdm(total=100, desc="Progression interpolation")
    size_res = res[1] * res[0]
    for y in np.arange(origin[1], origin[1] + res[1] * size, size):

        xi = 0
        for x in np.arange(origin[0], origin[0] + res[0] * size, size):

            ch = tin.is_inside_convex_hull(
                x, y
            )  # check is the point [x, y] located inside  the convex hull of the DT
            if ch == False:
                ras[yi, xi] = dico_param["no_data_value"]  # no-data value
            else:
                tri = tin.locate(
                    x, y
                )  # locate the triangle containing the point [x,y]. An error is thrown if it is outside the convex hull

                if (tri.shape != ()) and (0 not in tri):
                    ras[yi, xi] = interpolant(x, y)
                else:
                    ras[yi, xi] = dico_param["no_data_value"]  # no-data value
            xi += 1

        yi += 1

        if (xi * yi * 100 / size_res) in [i for i in range(100)]:
            pbar.update(1)

    pbar.close()
    return ras


def write_geotiff_withbuffer(raster, origin, size, output_file):
    """Writes the interpolated TIN-linear and Laplace rasters
    to disk using the GeoTIFF format with buffer (100 m). The header is based on
    the raster array and a manual definition of the coordinate
    system and an identity affine transform.

    Args:
        raster(array) : Z interpolation
        origin(list): coordinate location of the relative origin (bottom left)
        size (float): raster cell size
        output_file (str) :

    Returns:
        bool: fpath
    """
    import rasterio
    from rasterio.transform import Affine

    transform = Affine.translation(origin[0], origin[1]) * Affine.scale(size, size)
    with rasterio.Env():
        with rasterio.open(
            output_file,
            "w",
            driver="GTiff",
            height=raster.shape[0],
            width=raster.shape[1],
            count=1,
            dtype=rasterio.float32,
            crs=f"EPSG:{EPSG}",
            transform=transform,
        ) as out_file:
            out_file.write(raster.astype(rasterio.float32), 1)
    return output_file


def get_origin(las_input_file: str):
    """
    TODO : improve with pdal.stats instead of using file name
    Returns the North-West coordinates of the las.
    Ex of file name : Semis_2021_0843_6521_LA93_IGN69.laz
    Detail :
        0843 = X coordinate in km
        6521 = Y coordinate in km
        LA93 = system of projection (Lambert93)
        IGN69 = altimetric system

    input :
        las : str : the name of the points cloud file
    output :
        int, int, str, str : X coord in km, Y coord in km, system of projection, altimetric system
    """
    # réécrire plus proprement allant chercher dans les métadonnées
    return (
        int(las_input_file[11:15]),
        int(las_input_file[16:20]),
        str(las_input_file[21:25]),
        str(las_input_file[26:31]),
    )


def hillshade_from_raster(input_raster: str, output_raster: str):
    """Add hillshade to raster"""
    gdal.DEMProcessing(
        destName=output_raster,
        srcDS=input_raster,
        processing="hillshade",
    )


def color_DTM_with_cycles(
    las_input_file: str, output_dir_raster: str, output_dir_LUT: str, raster_DTM_file: str, nb_cycle: int
):
    """Color a raster with a LUT created depending of a choice of cycles

    Argss :
        file_las : str : points cloud
        file_DTM : str : DTM corresponding to the points cloud
        nb_cycle : int : the number of cycle that determine the LUT
    """
    log.info("Generate DTM colorised :")
    log.info("(1/2) Generate LUT.")
    # Create LUT
    LUT = gen_LUT_X_cycle.generate_LUT_X_cycle(
        file_las=las_input_file, file_DTM=raster_DTM_file, nb_cycle=nb_cycle, output_dir_LUT=output_dir_LUT
    )

    # Path DTM colorised
    raster_DTM_color_file = os.path.join(
        output_dir_raster,
        f"{os.path.splitext(las_input_file)[0]}_DTM_hillshade_color{nb_cycle}c.tif",
    )

    log.info("DTM color : " + raster_DTM_color_file)
    log.info("(2/2) Colorise raster.")

    # Colorisation
    utils_gdal.color_raster_with_LUT(
        input_raster=raster_DTM_file,
        output_raster=raster_DTM_color_file,
        LUT=LUT,
    )


def cluster(input_points: str):

    pipeline = pdal.Filter.cluster(
        min_points=3,
        max_points=200,
        tolerance=1,
        is3d=True,
    ).pipeline(input_points)
    pipeline.execute()
    return pipeline.arrays[0]


def name_folder_DTM_dens():
    """Assign folder name from dictionnary"""
    folder_DXM_brut = dico_folder["folder_DTM_DENS_brut"]
    folder_DXM_shade = dico_folder["folder_DTM_DENS_shade"]
    return folder_DXM_brut, folder_DXM_shade


def name_folder_DSM():
    """Assign folder name from dictionnary"""
    folder_DXM_brut = dico_folder["folder_DSM_brut"]
    folder_DXM_shade = dico_folder["folder_DSM_shade"]
    return folder_DXM_brut, folder_DXM_shade


def name_folder_DTM():
    """Assign folder name from dictionnary"""
    folder_DXM_brut = dico_folder["folder_DTM_brut"]
    folder_DXM_shade = dico_folder["folder_DTM_shade"]
    return folder_DXM_brut, folder_DXM_shade


def create_map_one_las(
    input_las: str, output_dir: str, interpMETHOD: str, list_c: list, type_raster: str
):
    """
    Create a DTM with Laplace or Linear method of interpolation. This function create a brut DTM, a shade DTM and a colored shade DTM.
    Args :
        input_las: las file
        output_dir: output directory
        interpMETHOD : method of interpolation (Laplace or TINLinear)
        list_c: liste of number of cycles for each DTM colored. This list allows to create several DTM with differents colorisations.
    """

    # Paramètres
    size = dico_param[f"resolution_{type_raster}"]  # meter = resolution from raster
    _size = utils_tools.give_name_resolution_raster(size)

    DXM = type_raster
    if type_raster == "DTM_dens":
        DXM = "DTM"
        folder_DXM_brut = name_folder_DTM_dens()
        log.info(f"{type_raster} (brut) at resolution {size} meter(s)\n")
    elif type_raster == "DSM":
        folder_DXM_brut, folder_DXM_shade = name_folder_DSM()
        log.info(f"{type_raster} (brut, shade) at resolution {size} meter(s)\n")
    elif type_raster == "DTM":
        folder_DXM_brut, folder_DXM_shade, folder_DXM_color = name_folder_DTM()
        log.info(f"{type_raster} (brut, shade, color) at resolution {size} meter(s)\n")
    else :
        raise ValueError("Function create_map_one_las Parameter type_raster. Must be \"DTM\", \"DSM\" or \"DTM_dens\"")

    # Get directory
    input_dir = os.path.dirname(input_las)
    # Get filename with extension
    input_las_name = os.path.basename(input_las)
    # Get filename without extension
    input_las_name_without_ext = os.path.splitext(input_las_name)[0]

    # Fichier de sortie DXM brut
    out_dtm_raster = f"{output_dir}{input_las_name}_{DXM}.tif"

    # # Extraction infos du las
    # origin_x, origin_y, ProjSystem, AltiSystem = get_origin(input_las_name)

    # log.info(f"Dalle name : {input_las_name}")

    # log.info(f"North-West X coordinate : {origin_x} km")
    # log.info(f"North-West Y coordinate : {origin_y} km")
    # log.info(f"System of projection : {ProjSystem}")
    # log.info(f"Altimetric system : {AltiSystem}")

    if DXM == "DTM" :

        log.info("Filtering ground and virtual points...")
        # Filtre les points sol de classif 2 et 66
        ground_pts = filter_las_ground_virtual(input_dir=input_dir, filename=input_las_name)

        log.info("Build las filtered...")
        # LAS points sol non interpolés
        FileLasGround = write_las(
            input_points=ground_pts,
            filename=input_las_name,
            output_dir=os.path.join(output_dir, dico_folder["folder_LAS_ground_virtual"]),
            name="ground",
        )

        FileToInterpolate = FileLasGround

    else : # DXM == DSM

        FileToInterpolate = input_las

    log.info(f"Interpolation method : {interpMETHOD}")

    log.info(f"Re-sampling : resolution {size} meter...")
    # Extraction coord points cloud
    log.debug(f"input : {FileToInterpolate}")
    pts_calc, res_calc, origin_calc = las_prepare_1_file(
        input_file=FileToInterpolate, size=size
    )

    log.debug(f"Points cloud {pts_calc}")
    log.debug(f"Resolution in coordinates : {res_calc}")
    log.debug(f"Loc of the relative origin : {origin_calc}")

    log.info("Begin Interpolation...")
    # Interpolation using Laplace or tin linear method
    resolution = res_calc  # résolution en coordonnées (correspond à la taille de la grille de coordonnées pour avoir la résolution indiquée dans le paramètre "size")
    origine = origin_calc
    ras = run_interpolate(
        pts=pts_calc, res=resolution, origin=origine, size=size, method=interpMETHOD
    )
    log.info("End interpolation.")

    log.debug("Interpolation table : ")
    log.debug(type(ras))
    log.debug(ras)

    # Write interpolation table in a text file
    fileRas = os.path.join(
        output_dir,
        dico_folder["folder_interp_table"],
        f"ras_{os.path.splitext(input_las_name)[0]}.txt"
        )  
    
    utils_tools.write_interp_table(
        output_filename=fileRas, 
        table_interp=ras
        )

    log.debug(f"All in :{fileRas}")

    log.info(f"Build {DXM} brut...")

    raster_dtm_interp = write_geotiff_withbuffer(
        raster=ras,
        origin=origine,
        size=size,
        output_file=os.path.join(
            output_dir, 
            folder_DXM_brut,
            f"{os.path.splitext(input_las_name)[0]}_{DXM}{_size}_{interpMETHOD}.tif",
        ),
    )

    log.debug(raster_dtm_interp)

    if type_raster == "DTM_dens" : # not hillshade DTM for density map 

        return raster_dtm_interp # DTM brut for density 

    else : # Add hillshade

        log.info(f"Build {DXM} hillshade...")

        dtm_file = raster_dtm_interp
        raster_dtm_hs = os.path.join(
            output_dir, 
            folder_DXM_shade,
            f"{os.path.splitext(input_las_name)[0]}_{DXM}{_size}_hillshade.tif",
        )
        hillshade_from_raster(
            input_raster=dtm_file,
            output_raster=raster_dtm_hs,
        )

        log.debug(os.path.join(output_dir, raster_dtm_hs))

    # Add color

    if type_raster == "DTM" : # color only DTM for map class fusion

        log.info("Build DTM hillshade color")

        cpt = 1

        for cycle in list_c:

            log.info(f"{cpt}/{len(list_c)}...")

            color_DTM_with_cycles(
                las_input_file=input_las_name,
                output_dir_raster=os.path.join(output_dir,folder_DXM_color),
                output_dir_LUT=os.path.join(output_dir,dico_folder["folder_LUT"]),
                raster_DTM_file=raster_dtm_hs,
                nb_cycle=cycle,
            )

            cpt += 1

    log.info(f"End {type_raster}.\n")

    return raster_dtm_hs # DTM/DSM with hillshade


def create_map_one_las_DTM(
    input_las: str, output_dir: str, interpMETHOD: str, list_c: list, type_raster: str="DTM"
):
    """
    Create a DTM with Laplace or Linear method of interpolation. This function create a brut DTM, a shade DTM and a colored shade DTM.
    Args :
        input_las: las file
        output_dir: output directory
        interpMETHOD : method of interpolation (Laplace or TINLinear)
        list_c: liste of number of cycles for each DTM colored. This list allows to create several DTM with differents colorisations.
    """

        # Get directory
    input_dir = os.path.dirname(input_las)
    # Get filename with extension
    input_las_name = os.path.basename(input_las)
    # Get filename without extension
    input_las_name_without_ext = os.path.splitext(input_las_name)[0]

    # Paramètres
    size = dico_param[f"resolution_{type_raster}"]  # meter = resolution from raster
    _size = utils_tools.give_name_resolution_raster(size)

    DXM = type_raster
    if type_raster == "DTM":
        folder_DXM_brut, folder_DXM_shade = name_folder_DTM()
        log.info(f"\n{type_raster} (brut, shade, color) at resolution {size} meter(s) : {input_las_name}\n")
    else :
        raise ValueError("Function create_map_one_las Parameter type_raster. Must be \"DTM\", \"DSM\" or \"DTM_dens\"")
    
    # Fichier de sortie DXM brut
    out_dtm_raster = f"{output_dir}{input_las_name}_{DXM}.tif"

    # # Extraction infos du las
    # origin_x, origin_y, ProjSystem, AltiSystem = get_origin(input_las_name)

    # log.info(f"Dalle name : {input_las_name}")

    # log.info(f"North-West X coordinate : {origin_x} km")
    # log.info(f"North-West Y coordinate : {origin_y} km")
    # log.info(f"System of projection : {ProjSystem}")
    # log.info(f"Altimetric system : {AltiSystem}")

    ## Get resolution and origin from initial las file
    _, res_initial, origin_initial = las_prepare_1_file(
        input_file=os.path.join(input_dir,input_las_name), size=size
    )

    log.info("Filtering ground and virtual points...")
    # Filtre les points sol de classif 2 et 66

    FileToInterpolate = os.path.join(output_dir, dico_folder["folder_LAS_ground_virtual"], f"{input_las_name_without_ext}_ground.las")

    filter_las_classes(input_file=os.path.join(input_dir,input_las_name),
                       output_file=FileToInterpolate)

    log.info(f"Interpolation method : {interpMETHOD}")

    log.info(f"Re-sampling : resolution {size} meter...")
    # Extraction coord points cloud
    log.debug(f"input : {FileToInterpolate}")
    pts_calc, _, _ = las_prepare_1_file(
        input_file=FileToInterpolate, size=size
    )

    log.info(f"Points cloud {pts_calc}")
    log.info(f"Resolution in coordinates : {res_initial}")
    log.info(f"Loc of the relative origin : {origin_initial}")
    log.info(f'size :{size}')

    log.info("Begin Interpolation...")
    # Interpolation using Laplace or tin linear method
    resolution = res_initial  # résolution en coordonnées (correspond à la taille de la grille de coordonnées pour avoir la résolution indiquée dans le paramètre "size")
    origine = origin_initial
    ras = run_interpolate(
        pts=pts_calc, res=resolution, origin=origine, size=size, method=interpMETHOD
    )
    log.info("End interpolation.")

    log.debug("Interpolation table : ")
    log.debug(type(ras))
    log.debug(ras)

    # Write interpolation table in a text file
    fileRas = os.path.join(
        output_dir,
        dico_folder["folder_interp_table"],
        f"ras_{os.path.splitext(input_las_name)[0]}.txt"
        )  
    
    utils_tools.write_interp_table(
        output_filename=fileRas, 
        table_interp=ras
        )

    log.debug(f"All in :{fileRas}")

    log.info(f"Build {DXM} brut...")

    raster_dtm_interp = write_geotiff_withbuffer(
        raster=ras,
        origin=origine,
        size=size,
        output_file=os.path.join(
            output_dir, 
            folder_DXM_brut,
            f"{os.path.splitext(input_las_name)[0]}_{DXM}{_size}_{interpMETHOD}.tif",
        ),
    )

    log.debug(raster_dtm_interp)

    # Add hillshade

    log.info(f"Build {DXM} hillshade...")

    dtm_file = raster_dtm_interp
    raster_dtm_hs = os.path.join(
        output_dir, 
        folder_DXM_shade,
        f"{os.path.splitext(input_las_name)[0]}_{DXM}{_size}_hillshade.tif",
    )
    hillshade_from_raster(
        input_raster=dtm_file,
        output_raster=raster_dtm_hs,
    )

    log.debug(os.path.join(output_dir, raster_dtm_hs))

    # Add color
    # color only DTM for map class fusion

    log.info("Build DTM hillshade color")

    cpt = 1

    for cycle in list_c:

        log.info(f"{cpt}/{len(list_c)}...")

        folder_DXM_color = dico_folder[f"folder_DTM_color{cycle}"]

        color_DTM_with_cycles(
            las_input_file=input_las_name,
            output_dir_raster=os.path.join(output_dir,folder_DXM_color),
            output_dir_LUT=os.path.join(output_dir,dico_folder["folder_LUT"]),
            raster_DTM_file=raster_dtm_hs,
            nb_cycle=cycle,
        )

        cpt += 1

    log.info(f"End {type_raster}.\n")

    return raster_dtm_hs # DTM with hillshade


def create_map_one_las_DSM(
    input_las: str, output_dir: str, interpMETHOD: str, type_raster: str="DSM"
):
    """
    Create a DSM with Laplace or Linear method of interpolation. This function create a brut DSM and a shade DSM.
    Args :
        input_las: las file
        output_dir: output directory
        interpMETHOD : method of interpolation (Laplace or TINLinear)
    """

    # Get directory
    input_dir = os.path.dirname(input_las)
    # Get filename with extension
    input_las_name = os.path.basename(input_las)
    # Get filename without extension
    input_las_name_without_ext = os.path.splitext(input_las_name)[0]

    # Paramètres
    size = dico_param[f"resolution_{type_raster}"]  # meter = resolution from raster
    _size = utils_tools.give_name_resolution_raster(size)

    DXM = type_raster
    if type_raster == "DSM":
        folder_DXM_brut, folder_DXM_shade = name_folder_DSM()
        log.info(f"\n{type_raster} (brut, shade) at resolution {size} meter(s) : {input_las_name}\n")
    else :
        raise ValueError("Function create_map_one_las Parameter type_raster. Must be \"DTM\", \"DSM\" or \"DTM_dens\"")

    # Fichier de sortie DXM brut
    out_dtm_raster = f"{output_dir}{input_las_name}_{DXM}.tif"

    # # Extraction infos du las
    # origin_x, origin_y, ProjSystem, AltiSystem = get_origin(input_las_name)

    # log.info(f"Dalle name : {input_las_name}")

    # log.info(f"North-West X coordinate : {origin_x} km")
    # log.info(f"North-West Y coordinate : {origin_y} km")
    # log.info(f"System of projection : {ProjSystem}")
    # log.info(f"Altimetric system : {AltiSystem}")

    # No filtering for DSM
    FileToInterpolate = input_las

    log.info(f"Interpolation method : {interpMETHOD}")

    log.info(f"Re-sampling : resolution {size} meter...")
    # Extraction coord points cloud
    log.debug(f"input : {FileToInterpolate}")
    pts_calc, res_calc, origin_calc = las_prepare_1_file(
        input_file=FileToInterpolate, size=size
    )

    log.debug(f"Points cloud {pts_calc}")
    log.debug(f"Resolution in coordinates : {res_calc}")
    log.debug(f"Loc of the relative origin : {origin_calc}")

    log.info("Begin Interpolation...")
    # Interpolation using Laplace or tin linear method
    resolution = res_calc  # résolution en coordonnées (correspond à la taille de la grille de coordonnées pour avoir la résolution indiquée dans le paramètre "size")
    origine = origin_calc
    ras = run_interpolate(
        pts=pts_calc, res=resolution, origin=origine, size=size, method=interpMETHOD
    )
    log.info("End interpolation.")

    log.debug("Interpolation table : ")
    log.debug(type(ras))
    log.debug(ras)

    # Write interpolation table in a text file
    fileRas = os.path.join(
        output_dir,
        dico_folder["folder_interp_table"],
        f"ras_{os.path.splitext(input_las_name)[0]}.txt"
        )  
    
    utils_tools.write_interp_table(
        output_filename=fileRas, 
        table_interp=ras
        )

    log.debug(f"All in :{fileRas}")

    log.info(f"Build {DXM} brut...")

    raster_dtm_interp = write_geotiff_withbuffer(
        raster=ras,
        origin=origine,
        size=size,
        output_file=os.path.join(
            output_dir, 
            folder_DXM_brut,
            f"{os.path.splitext(input_las_name)[0]}_{DXM}{_size}_{interpMETHOD}.tif",
        ),
    )

    log.debug(raster_dtm_interp)

    # Add hillshade

    log.info(f"Build {DXM} hillshade...")

    dtm_file = raster_dtm_interp
    raster_dtm_hs = os.path.join(
        output_dir, 
        folder_DXM_shade,
        f"{os.path.splitext(input_las_name)[0]}_{DXM}{_size}_hillshade.tif",
    )
    hillshade_from_raster(
        input_raster=dtm_file,
        output_raster=raster_dtm_hs,
    )

    log.debug(os.path.join(output_dir, raster_dtm_hs))


    log.info(f"End {type_raster}.\n")

    return raster_dtm_hs # DSM with hillshade


def create_map_one_las_DTM_dens(
    input_las: str, output_dir: str, interpMETHOD: str, type_raster: str="DTM_dens"
):
    """
    Create a DTM with Laplace or Linear method of interpolation. This function create a brut DTM and a shade DTM.
    Args :
        input_las: las file
        output_dir: output directory
        interpMETHOD : method of interpolation (Laplace or TINLinear)
    """

    # Get directory
    input_dir = os.path.dirname(input_las)
    # Get filename with extension
    input_las_name = os.path.basename(input_las)
    # Get filename without extension
    input_las_name_without_ext = os.path.splitext(input_las_name)[0]

    # Paramètres
    size = dico_param[f"resolution_{type_raster}"]  # meter = resolution from raster
    _size = utils_tools.give_name_resolution_raster(size)

    DXM = type_raster
    if type_raster == "DTM_dens":
        DXM = "DTM"
        folder_DXM_brut, folder_DXM_shade = name_folder_DTM_dens()
        log.info(f"\n{type_raster} (brut) at resolution {size} meter(s) : {input_las_name}\n")
    else :
        raise ValueError("Function create_map_one_las Parameter type_raster. Must be \"DTM\", \"DSM\" or \"DTM_dens\"")

    # Fichier de sortie DXM brut
    out_dtm_raster = f"{output_dir}{input_las_name}_{DXM}.tif"

    # # Extraction infos du las
    # origin_x, origin_y, ProjSystem, AltiSystem = get_origin(input_las_name)

    # log.info(f"Dalle name : {input_las_name}")

    # log.info(f"North-West X coordinate : {origin_x} km")
    # log.info(f"North-West Y coordinate : {origin_y} km")
    # log.info(f"System of projection : {ProjSystem}")
    # log.info(f"Altimetric system : {AltiSystem}")

    ## Get resolution and origin from initial las file
    _, res_initial, origin_initial = las_prepare_1_file(
        input_file=os.path.join(input_dir,input_las_name), size=size
    )

    log.info("Filtering ground and virtual points...")
    # Filtre les points sol de classif 2 et 66

    FileToInterpolate = os.path.join(output_dir, dico_folder["folder_LAS_ground_virtual"], f"{input_las_name_without_ext}_ground.las")

    filter_las_classes(input_file=os.path.join(input_dir,input_las_name),
                       output_file=FileToInterpolate)

    log.info(f"Interpolation method : {interpMETHOD}")

    log.info(f"Re-sampling : resolution {size} meter...")
    # Extraction coord points cloud
    log.debug(f"input : {FileToInterpolate}")
    pts_calc, _, _ = las_prepare_1_file(
        input_file=FileToInterpolate, size=size
    )

    log.info(f"Points cloud {pts_calc}")
    log.info(f"Resolution in coordinates : {res_initial}")
    log.info(f"Loc of the relative origin : {origin_initial}")
    log.info(f'size :{size}')

    log.info("Begin Interpolation...")
    # Interpolation using Laplace or tin linear method
    resolution = res_initial  # résolution en coordonnées (correspond à la taille de la grille de coordonnées pour avoir la résolution indiquée dans le paramètre "size")
    origine = origin_initial
    ras = run_interpolate(
        pts=pts_calc, res=resolution, origin=origine, size=size, method=interpMETHOD
    )
    log.info("End interpolation.")

    log.debug("Interpolation table : ")
    log.debug(type(ras))
    log.debug(ras)

    # Write interpolation table in a text file
    fileRas = os.path.join(
        output_dir,
        dico_folder["folder_interp_table"],
        f"ras_{os.path.splitext(input_las_name)[0]}.txt"
        )  
    
    utils_tools.write_interp_table(
        output_filename=fileRas, 
        table_interp=ras
        )

    log.debug(f"All in :{fileRas}")

    log.info(f"Build {DXM} brut...")

    raster_dtm_interp = write_geotiff_withbuffer(
        raster=ras,
        origin=origine,
        size=size,
        output_file=os.path.join(
            output_dir, 
            folder_DXM_brut,
            f"{os.path.splitext(input_las_name)[0]}_{DXM}{_size}_{interpMETHOD}.tif",
        ),
    )

    log.debug(raster_dtm_interp)

    # Add hillshade

    log.info(f"Build {DXM} hillshade...")

    dtm_file = raster_dtm_interp
    raster_dtm_hs = os.path.join(
        output_dir, 
        folder_DXM_shade,
        f"{os.path.splitext(input_las_name)[0]}_{DXM}{_size}_hillshade.tif",
    )
    hillshade_from_raster(
        input_raster=dtm_file,
        output_raster=raster_dtm_hs,
    )

    log.debug(os.path.join(output_dir, raster_dtm_hs))

    log.info(f"End {type_raster}.\n")

    return raster_dtm_hs # DTM with hillshade


if __name__ == "__main__":

    main()
