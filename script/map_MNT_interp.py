# Autor : ELucon

# IMPORT

    # File
import tools
import utils_pdal
from parameter import dico_param
from check_folder import dico_folder
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
import gen_LUT_X_cycle
from tqdm import tqdm
import logging as log

# PARAMETERS

EPSG = dico_param["EPSG"]



def filter_las_ground(input_dir: str, filename: str):
    """ Reads the LAS file and filter only grounds from LIDAR.

    Args:
        input_dir (str) : directory of projet who contains LIDAR (Ex. "data")
        file (str): name of LIDAR tiles
    """
    input_file = os.path.join(input_dir, filename)
    information = {}
    information = {
    "pipeline": [
            {
                "type":"readers.las",
                "filename":input_file,
                "override_srs": f"EPSG:{EPSG}",
                "nosrs": True
            },
            {
                "type":"filters.range",
                "limits":"Classification[2:2],Classification[66:66]"
            }
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
    file_root = os.path.splitext(filename)[0] #filename without extension

    dst = os.path.join(output_dir, dico_folder["folder_LAS_ground"])

    os.makedirs(dst, exist_ok=True) # create directory LAS/ if not exists

    log.debug("dst : "+dst)
    FileOutput = os.path.join(dst, f'{file_root}_{name}.las')
    
    log.debug("filename : "+FileOutput)
    pipeline = pdal.Writer.las(filename = FileOutput, a_srs=f"EPSG:{EPSG}").pipeline(input_points)
    pipeline.execute()

    return FileOutput

def write_las2(pts):
    information = {}
    information = {
    "pipeline": [
            {
                "type": "writers.las",
                "a_srs": f"EPSG:{EPSG}",
                # "minor_version": 4,
                # "dataformat_id": 6,
                "filename": FileOutput
            }
        ]
    }
    ground = json.dumps(information, sort_keys=True, indent=4)
    log.info(ground)
    pipeline = pdal.Pipeline(ground)
    pipeline.execute()

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
    in_np = np.vstack((in_file.classification,
                           in_file.x, in_file.y, in_file.z)).transpose()
    in_np = in_np[in_np[:,0] == 2].copy()[:,1:]
    extents = [[header.min[0], header.max[0]],
               [header.min[1], header.max[1]]]
    res = [math.ceil((extents[0][1] - extents[0][0]) / size),
           math.ceil((extents[1][1] - extents[1][0]) / size)]
    origin = [np.mean(extents[0]) - (size / 2) * res[0],
              np.mean(extents[1]) - (size / 2) * res[1]]
    return in_np, res, origin

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
    tin = startinpy.DT(); tin.insert(pts) # # Insert each points in the array of points (a 2D array)
    ras = np.zeros([res[1], res[0]]) # # returns a new array of given shape and type, filled with zeros
    # # Interpolate method Laplace or TIN Linear
    if method == "Laplace" :
        def interpolant(x, y): return tin.interpolate_laplace(x, y)
    elif method == "TINlinear":
        def interpolant(x, y): return tin.interpolate_tin_linear(x, y)
    cp = 0
    cp2 = 0
    yi = 0
    # Initialiser la barre de progression
    pbar = tqdm(total=100, desc="Progression interpolation")
    size_res = res[1]*res[0]
    for y in np.arange(origin[1], origin[1] + res[1] * size, size):
        # print("y",y, "size", size)
        # print("arange",len(np.arange(origin[1], origin[1] + res[1] * size, size)),np.arange(origin[1], origin[1] + res[1] * size, size))
        xi = 0
        for x in np.arange(origin[0], origin[0] + res[0] * size, size):
            # print("x",x, "size", size)
            # print("arange",len(np.arange(origin[0], origin[0] + res[0] * size, size)),np.arange(origin[0], origin[0] + res[0] * size, size))
            # print("[x,y]", x, y)
            ch = tin.is_inside_convex_hull(x, y) # check is the point [x, y] located inside  the convex hull of the DT
            if ch == False:
                ras[yi, xi] = -9999 # no-data value
            else:
                tri = tin.locate(x, y) # locate the triangle containing the point [x,y]. An error is thrown if it is outside the convex hull
                # print("\n\nTRI",tri)


                if (tri.shape!=()) and (0 not in tri):
                    ras[yi, xi] = interpolant(x, y)
                else: 
                    ras[yi, xi] = -9999 # no-data value
            xi += 1
            
        yi += 1
        
        if (xi*yi * 100 / size_res) in [i for i in range(100)] :
            pbar.update( 1 )
        # print(xi*yi * 100 / size_res )


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
    transform = (Affine.translation(origin[0], origin[1])
                 * Affine.scale(size, size))
    with rasterio.Env():
        with rasterio.open(output_file, 'w', driver = 'GTiff',
                           height = raster.shape[0],
                           width = raster.shape[1],
                           count = 1,
                           dtype = rasterio.float32,
                           crs=f"EPSG:{EPSG}",
                           transform = transform
                           ) as out_file:
            out_file.write(raster.astype(rasterio.float32), 1)
    return output_file

def get_origin(las_input_file: str):
    """
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
    return int(las_input_file[11:15]), int(las_input_file[16:20]), str(las_input_file[21:25]), str(las_input_file[26:31])

def give_name_resolution_raster(size):
    """
    Give a resolution from raster

    Args:
        size (int): raster cell size

    Return:
        _size(str): resolution from raster for output's name
    """
    if float(size) == 1.0:
        _size = str('_1M')
    elif float(size) == 0.5:
        _size = str('_50CM')
    elif float(size) == 5.0:
        _size = str('_5M')
    else:
        _size = str(size)
    return _size


def hillshade_from_raster(
    input_raster: str, output_raster: str
):
    """Add hillshade to raster"""
    gdal.DEMProcessing(
        destName=output_raster,
        srcDS=input_raster,
        processing = "hillshade",
        )
    


def color_MNT_with_cycles(
    las_input_file: str,
    output_dir: str,
    raster_MNT_file: str,
    nb_cycle: int
):
    """Color a raster with a LUT created depending of a choice of cycles

    Argss :
        file_las : str : points cloud
        file_MNT : str : MNT corresponding to the points cloud
        nb_cycle : int : the number of cycle that determine the LUT
    """

    
    log.info("Generate MNT colorised :")
    log.info("(1/2) Generate LUT.")
    # Create LUT
    LUT = gen_LUT_X_cycle.generate_LUT_X_cycle(
        file_las=las_input_file,
        file_MNT=raster_MNT_file,
        nb_cycle=nb_cycle
    )

    # Path MNT colorised
    raster_MNT_color_file = os.path.join(os.path.join(output_dir,'DTM_color'),f'{las_input_file[:-4]}_DTM_hillshade_color{nb_cycle}c.tif')


    
    log.info("MNT color : "+raster_MNT_color_file)
    log.info("(2/2) Colorise raster.")

    # Colorisation
    tools.color_raster_with_LUT(
        input_raster = raster_MNT_file,
        output_raster = raster_MNT_color_file,
        LUT = LUT,
    )


def create_map_one_las(input_las: str, output_dir: str, interpMETHOD: str, list_c : list):
    """
    Create a DTM with Laplace or Linear method of interpolation. This function create a brut DTM, a shade DTM and a colored shade DTM.
    Args :
        input_las: las file
        output_dir: output directory
        interpMETHOD : method of interpolation (Laplace or TINLinear)
        list_c: liste of number of cycles for each DTM colored. This list allows to create several DTM with differents colorisations.
    """

    log.basicConfig(level=log.INFO)

    # Paramètres
    size = dico_param["resolution_MNT"] # meter = resolution from raster
    _size = give_name_resolution_raster(size)


    # Complete path (exemple : "data" become "data/")
    output_dir = os.path.join(output_dir,"")



    # Get directory
    input_dir = os.path.dirname(input_las)
    input_dir = utils_pdal.parent(input_las)
    # Get filename without extension
    input_las_name = os.path.basename(input_las)
    input_las_name = f"{utils_pdal.stem(input_las)}.la{input_las[-1]}"




    # Fichier de sortie MNT brut
    out_dtm_raster = f"{output_dir}{input_las_name}_DTM.tif"

    # # Extraction infos du las
    # origin_x, origin_y, ProjSystem, AltiSystem = get_origin(input_las_name)

    # 
    # log.info(f"Dalle name : {input_las_name}")

    # log.info(f"North-West X coordinate : {origin_x} km")
    # log.info(f"North-West Y coordinate : {origin_y} km")
    # log.info(f"System of projection : {ProjSystem}")
    # log.info(f"Altimetric system : {AltiSystem}")

    
    log.info("Filtering ground and virtual points...")
    # Filtre les points sol de classif 2 et 66
    # tools.filter_las_version2(las,las_pts_ground)
    ground_pts = filter_las_ground(
        input_dir = input_dir,
        filename = input_las_name)

    
    log.info("Build las filtered...")
    # LAS points sol non interpolés
    FileLasGround = write_las(input_points=ground_pts, filename=input_las_name , output_dir=output_dir, name="ground")



    
    log.info(f"Interpolation method : {interpMETHOD}")

    
    log.info(f"Re-sampling : resolution {size} meter...")
    # Extraction coord points cloud
    log.debug(f"input : {FileLasGround}")
    extents_calc, res_calc, origin_calc = las_prepare_1_file(input_file=FileLasGround, size=size)
    
    log.debug(f"Extents {extents_calc}")
    log.debug(f"Resolution in coordinates : {res_calc}")
    log.debug(f"Loc of the relative origin : {origin_calc}")



    
    log.info("Begin Interpolation...")
    # Interpolation using Laplace or tin linear method
    resolution = res_calc # résolution en coordonnées (correspond à la taille de la grille de coordonnées pour avoir la résolution indiquée dans le paramètre "size")
    origine = origin_calc
    ras = execute_startin(pts=extents_calc, res=resolution, origin=origine, size=size, method=interpMETHOD)
    log.info("End interpolation.")

    
    log.debug("Tableau d'interpolation : ")
    log.debug(ras)

    log.info("Build DTM brut...")
    
    raster_dtm_interp = write_geotiff_withbuffer(raster=ras, origin=origine, size=size, output_file= os.path.join(os.path.join(output_dir, "DTM_brut"), input_las_name[:-4] + _size + f'_{interpMETHOD}.tif') )
  
    log.debug(os.path.join(output_dir, raster_dtm_interp))


    # Add hillshade
    
    log.info("Build DTM hillshade...")

    dtm_file = raster_dtm_interp
    dtm_hs_file = os.path.join(os.path.join(output_dir,"DTM_shade"),f"{input_las_name[:-4]}_DTM{_size}_hillshade.tif")
    hillshade_from_raster(
        input_raster = dtm_file,
        output_raster = dtm_hs_file,
    )

    log.debug(os.path.join(output_dir, dtm_hs_file))

    # Add color
    
    log.info("Build DTM hillshade color")

    cpt = 1

    for cycle in list_c :
        
        
        log.info(f"{cpt}/{len(list_c)}...")

        color_MNT_with_cycles(
        las_input_file=input_las_name,
        output_dir=output_dir,
        raster_MNT_file=dtm_hs_file,
        nb_cycle=cycle
        )

        cpt += 1

    log.debug("End DTM.")

if __name__ == '__main__':
    
    main()