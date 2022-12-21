# Autor : ELucon

# IMPORT

    # File
import tools
from map_MNT import hillshade_from_raster, color_MNT_with_cycles
import gen_LUT_X_cycle
    # Library
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
import shutil


def delete_folder(dest_folder: str):
    """Delete the severals folders "LAS", "DTM", "DTM_shade" and "DTM_color" if not exist"""
    # Delete folder "LAS"
    LAS_new_dir = os.path.join(dest_folder, 'LAS')
    if os.path.isdir(LAS_new_dir):
        shutil.rmtree(LAS_new_dir)
    # Delete folder "DTM"
    DTM_brut_new_dir = os.path.join(dest_folder, 'DTM_brut')
    if os.path.isdir(DTM_brut_new_dir):
        shutil.rmtree(DTM_brut_new_dir)
    # Delete folder "DTM_shade"
    DTM_shade_new_dir = os.path.join(dest_folder, 'DTM_shade')
    if os.path.isdir(DTM_shade_new_dir):
        shutil.rmtree(DTM_shade_new_dir)
    # Delete folder "DTM_color"
    DTM_color_new_dir = os.path.join(dest_folder, 'DTM_color')
    if os.path.isdir(DTM_color_new_dir):
        shutil.rmtree(DTM_color_new_dir)

def create_folder(dest_folder: str):
    """Create the severals folders "LAS", "DTM", "DTM_shade" and "DTM_color" if not exist"""
    # Create folder "LAS"
    LAS_new_dir = os.path.join(dest_folder, 'LAS')
    if not os.path.isdir(LAS_new_dir):
        os.makedirs(LAS_new_dir)
    # Create folder "DTM"
    DTM_brut_new_dir = os.path.join(dest_folder, 'DTM_brut')
    if not os.path.isdir(DTM_brut_new_dir):
        os.makedirs(DTM_brut_new_dir)
    # Create folder "DTM_shade"
    DTM_shade_new_dir = os.path.join(dest_folder, 'DTM_shade')
    if not os.path.isdir(DTM_shade_new_dir):
        os.makedirs(DTM_shade_new_dir)
    # Create folder "DTM_color"
    DTM_color_new_dir = os.path.join(dest_folder, 'DTM_color')
    if not os.path.isdir(DTM_color_new_dir):
        os.makedirs(DTM_color_new_dir)




def filter_las_ground(fpath: str, file: str):
    """ Reads the LAS file and filter only grounds from LIDAR.

    Args:
        fpath (str) : directory of projet who contains LIDAR (Ex. "data")
        file (str): name of LIDAR tiles
    """

    information = {}
    information = {
    "pipeline": [
            {
                "type":"readers.las",
                "filename":fpath,
                "override_srs": "EPSG:2154",
                "nosrs": True
            },
            {
                "type":"filters.range",
                "limits":"Classification[2:2],Classification[66:66]"
            }
        ]
    }
    ground = json.dumps(information, sort_keys=True, indent=4)

    pipeline = pdal.Pipeline(ground)
    pipeline.execute()
    return pipeline.arrays[0]

def write_las(input_points, file: str, src: str, name: str):
    """Write a las file
    Args:
        file (str): name of LIDAR tiles
        src (str): directory of work who contains the output files
        """
    print("src : "+src)
    dst = src
    print("dts : "+dst)
    FileOutput = "".join([src, "_".join([file[:-4], f'{name}.las'])])
    print("filename : "+FileOutput)
    pipeline = pdal.Writer.las(filename = FileOutput, a_srs="EPSG:2154").pipeline(input_points)
    pipeline.execute()

    NameFileOutput = "_".join([file[:-4], f'{name}.las'])
    return NameFileOutput

def write_las2(pts):
    information = {}
    information = {
    "pipeline": [
            {
                "type": "writers.las",
                "a_srs": "EPSG:2154",
                # "minor_version": 4,
                # "dataformat_id": 6,
                "filename": FileOutput
            }
        ]
    }
    ground = json.dumps(information, sort_keys=True, indent=4)
    print(ground)
    pipeline = pdal.Pipeline(ground)
    pipeline.execute()


def execute_startin(pts, res, origin, size):
    """Takes the grid parameters and the ground points. Interpolates
    either using the TIN-linear method. Uses a -9999 no-data value. 
    Fully based on the startin package (https://startinpy.readthedocs.io/en/latest/api.html)

    Args:
        pts : ground points clouds (for each point, just x-y-z coordinates)
        res(list): resolution in coordinates (1 000 km -> raster carré de 1 000km de côté)
        origin(list): coordinate location of the relative origin (bottom left)
        size (int): raster cell size (1m x 1m OR 5m x 5m)

    Returns:
        ras(list): Z interpolation (array de zeros et de 1)
    """

    # # Startin 
    tin = startinpy.DT(); tin.insert(pts) # # Insert each points in the array of points (a 2D array)
    ras = np.zeros([res[1], res[0]]) # # returns a new array of given shape and type, filled with zeros
    # # Interpolate method TIN Linear
    def interpolant(x, y): return tin.interpolate_tin_linear(x, y)

    yi = 0
    for y in np.arange(origin[1], origin[1] + res[1] * size, size):
        xi = 0
        for x in np.arange(origin[0], origin[0] + res[0] * size, size):
            ch = tin.is_inside_convex_hull(x, y) # check is the point [x, y] located inside  the convex hull of the DT
            if ch == False:
                ras[yi, xi] = -9999 # no-data value
            else:
                tri = tin.locate(x, y) # locate the triangle containing the point [x,y]. An error is thrown if it is outside the convex hull
                #print("tri", tri, type(tri))
                if tri != np.array([]) and 0 not in tri:
                    ras[yi, xi] = interpolant(x, y)
                else: ras[yi, xi] = -9999 # no-data value
            xi += 1
        yi += 1
    return ras


def write_geotiff_withbuffer(raster, origin, size, fpath):
    """Writes the interpolated TIN-linear rasters
    to disk using the GeoTIFF format with buffer (100 m). The header is based on
    the raster array and a manual definition of the coordinate
    system and an identity affine transform.

    Args:
        raster(array) : Z interpolation
        origin(list): coordinate location of the relative origin (bottom left)
        size (float): raster cell size
        fpath(str): target folder

    Returns:
        bool: fpath
    """
    import rasterio
    from rasterio.transform import Affine
    transform = (Affine.translation(origin[0], origin[1])
                 * Affine.scale(size, size))
    with rasterio.Env():
        with rasterio.open(fpath, 'w', driver = 'GTiff',
                           height = raster.shape[0],
                           width = raster.shape[1],
                           count = 1,
                           dtype = rasterio.float32,
                           crs='EPSG:2154',
                           transform = transform
                           ) as out_file:
            out_file.write(raster.astype(rasterio.float32), 1)
    return fpath

def get_origin(las: str):
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
    # réécrire plus proprement en allant chercher dans les métadonnées   
    return int(las[11:15]), int(las[16:20]), str(las[21:25]), str(las[26:31])

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


def las_prepare_1_file(target_file: str, src: str, fname: str, size: float):
    """Takes the filepath to an input LAS (crop) file and the desired output raster cell size. Reads the LAS file and outputs
    the ground points as a numpy array. Also establishes some
    basic raster parameters:
        - the extents
        - the resolution in coordinates
        - the coordinate location of the relative origin (bottom left)

    Args:
        target_folder (str): directory of pointclouds
        src (str): directory folder for saving the outputs
        fname (str): name of LIDAR tile
        size (int): raster cell size
    
    Returns:
        extents(array) : extents
        res(list): resolution in coordinates
        origin(list): coordinate location of the relative origin (bottom left)
    """
    # Parameters
    Fileoutput = target_file
    # Reads the LAS file and outputs the ground points as a numpy array.
    in_file = laspy.read(Fileoutput)
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
    


def color_MNT_with_cycles(
    file_las: str,
    scr: str,
    file_MNT: str,
    nb_cycle: int,
    verbose=False
):
    """Color a raster with a LUT created depending of a choice of cycles

    Args :
        file_las : str : points cloud
        file_MNT : str : MNT corresponding to the points cloud
        nb_cycle : int : the number of cycle that determine the LUT
    """

    if verbose :
        print("Generate MNT colorised :")
        print("(1/2) Generate LUT.")
    # Create LUT
    LUT = gen_LUT_X_cycle.generate_LUT_X_cycle(
        file_las=file_las,
        file_MNT=file_MNT,
        nb_cycle=nb_cycle,
        verbose=verbose
    )

    # Path MNT colorised
    file_MNT_color = f'{scr}{file_las[:-4]}_DTM_hillshade_color{nb_cycle}c.tif'


    if verbose :
        print("(2/2) Colorise raster.")

    # Colorisation
    tools.color_raster_with_LUT(
        input_raster = file_MNT,
        output_raster = file_MNT_color,
        LUT = LUT,
    )


def main(verbose=False):

    import sys

    # Paramètres
    size = 1.0 # mètres = resolution from raster
    _size = give_name_resolution_raster(size)

    # Pour tester ce fichier de création de raster colorisé par classe après une interpolation
    in_las = sys.argv[1:][0]
    # Dossier dans lequel seront créés les fichiers
    path_workfolder = sys.argv[1:][1]

    # Delete the severals folder LAS, DTM, DTM_shade and DTM_color if not exists
    delete_folder(path_workfolder)
    # Create the severals folder LAS, DTM, DTM_shade and DTM_color if not exists
    create_folder(path_workfolder)

    in_las_name = in_las[-35:]



    # Fichier de sortie MNT brut
    out_dtm_raster = f"{path_workfolder}DTM_brut/{in_las_name}_DTM.tif"

    # Extraction infos du las
    origin_x, origin_y, ProjSystem, AltiSystem = get_origin(in_las_name)

    if verbose :
        print(f"Dalle name : {in_las_name}")

        print(f"North-West X coordinate : {origin_x} km")
        print(f"North-West Y coordinate : {origin_y} km")
        print(f"System of projection : {ProjSystem}")
        print(f"Altimetric system : {AltiSystem}")

    if verbose :
        print("\nFiltrage points sol et virtuels...")
    # Filtre les points sol de classif 2 et 66
    # tools.filter_las_version2(las,las_pts_ground)
    ground_pts = filter_las_ground(
        fpath = in_las, 
        file = in_las_name)

    if verbose :
        print("Build las...")
    # LAS points sol non interpolés
    FileLasGround = write_las(input_points=ground_pts, file=in_las_name , src=f"{path_workfolder}LAS/", name="ground")



    if verbose :
        print("\nInterpolation méthode de TIN Linéaire...")

    if verbose :
        print("\n           Extraction liste des coordonnées du nuage de points...")
    # Extraction coord nuage de points
    extents_calc, res_calc, origin_calc = las_prepare_1_file(target_file=in_las, src=path_workfolder, fname=in_las_name, size=size)
    if verbose :
        print(f"\nExtents {extents_calc}")
        print(f"Resolution in coordinates : {res_calc} m,m")
        print(f"Localisation of the relative origin : {origin_calc} m,m")



    if verbose :
        print("\n           Interpolation...")
    # Interpole avec la méthode de TIN Linéaire
    resolution = res_calc # résolution en coordonnées (correspond à la taille de la grille de coordonnées pour avoir la résolution indiquée dans le paramètre "size")
    origine = origin_calc
    ras = execute_startin(pts=extents_calc, res=resolution, origin=origine, size=size)
    

    if verbose :
        print("\nTableau d'interpolation : ")
        print(ras)
        print("\nBuild raster...")
    
    raster_dtm_interp = write_geotiff_withbuffer(raster=ras, origin=origine, size=size, fpath=path_workfolder + "DTM_brut/" + in_las_name[:-4] + _size + '_TINlinear.tif')

    if verbose :
        print(f"{path_workfolder}{_size}_TINlinear.tif")
        print("\nBuild las...")
    # LAS points sol interpolés
    las_dtm_interp = write_las(input_points=ground_pts, file=in_las_name ,src=f"{path_workfolder}LAS/", name="ground_interp")


    # Ajout ombrage
    if verbose :
        print("\nAdd hillshade...")
        print(raster_dtm_interp)
        print("\n")

    dtm_file = raster_dtm_interp
    dtm_hs_file = f"{path_workfolder}DTM_shade/{in_las_name[:-4]}_DTM_hillshade.tif"
    hillshade_from_raster(
        input_raster = dtm_file,
        output_raster = dtm_hs_file,
    )

    if verbose :
        print("Success.\n")

    # Colorisation
    if verbose :
        print("Add color...")
        
    nb_raster_color = int(input("How many raster colorised ? : "))

    for i in range(nb_raster_color) :

        cycle = int(input(f"Raster {i+1}/{nb_raster_color} : how many cycles ? : "))
        
        if verbose :
            print(f"Build raster {i+1}/{nb_raster_color}...")

        color_MNT_with_cycles(
        file_las=in_las_name,
        scr=f"{path_workfolder}DTM_color/",
        file_MNT=dtm_hs_file,
        nb_cycle=cycle,
        verbose=verbose
        )

        if verbose :
            print("Success.\n")

    if verbose :
        print("End.")

if __name__ == '__main__':
    
    main(True)