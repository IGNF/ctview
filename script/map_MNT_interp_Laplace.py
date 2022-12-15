# Autor : ELucon

# IMPORT

    # File
import tools
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


def main():    
    # Create the severals folder if not exists
    create_folder(argv[2])
    if 3 <= len(argv) <= 7: start_pool(*argv[1:])
    else: print("Error: Incorrect number of arguments passed. Returning.")

def create_folder(dest_folder: str):
    """Create the severals folders "DTM" and "_tmp" if not exist"""
    # Create folder "DTM"
    DTM_new_dir = os.path.join(dest_folder, 'DTM')
    if not os.path.isdir(DTM_new_dir):
        os.makedirs(DTM_new_dir)
    # Create folder "_tmp"
    tmp_new_dir = os.path.join(dest_folder, '_tmp')
    if not os.path.isdir(tmp_new_dir):
        os.makedirs(tmp_new_dir)

def start_pool(target_folder, src, filetype = 'las', postprocess = 0,
               size = 1, method = 'startin-Laplace'):
    """Assembles and executes the multiprocessing pool.
    The interpolation variants/export formats are handled
    by the worker function (ip_worker(mapped)).
    """
    fnames = listPointclouds(target_folder, filetype)
    cores = cpu_count()
    print(f"Found {cores} logical cores in this PC")
    num_threads = cores -1
    if CPU_LIMIT > 0 and num_threads > CPU_LIMIT:
        print(f"Limit CPU usage to {CPU_LIMIT} cores due to env var CPU_LIMIT")
        num_threads = CPU_LIMIT
    print("\nStarting interpolation pool of processes on the {}".format(
        num_threads) + " logical cores.\n")

    if len(fnames) == 0:
        print("Error: No file names were input. Returning."); return
    pre_map, processno = [], len(fnames)
    for i in range(processno):
        pre_map.append([src, int(postprocess), float(size),
                            target_folder, fnames[i].strip('\n'), method, filetype])
    p = Pool(cores -1)
    p.map(ip_worker, pre_map)
    p.close(); p.join()
    print("\nAll workers have returned.")




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
    print(ground)
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
    dst = str("DTM".join([src, '/']))
    print("dts : "+dst)
    FileOutput = "".join([dst, "_".join([file[:-4], f'{name}.las'])])
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
    either using the TIN-linear or the Laplace method. Uses a -9999 no-data value. 
    Fully based on the startin package (https://startinpy.readthedocs.io/en/latest/api.html)

    Args:
        pts : ground points clouds
        res(list): resolution in coordinates (1m x 1m OU 5m x 5m)
        origin(list): coordinate location of the relative origin (bottom left)
        size (int): raster cell size (1 000 km -> raster carré de 1 000km de côté)

    Returns:
        ras(list): Z interpolation
    """

    # # Startin 
    tin = startinpy.DT(); tin.insert(pts) # # Insert each points in the array of points (a 2D array)
    ras = np.zeros([res[1], res[0]]) # # returns a new array of given shape and type, filled with zeros
    # # Interpolate method
    method == 'startin-Laplace'
    def interpolant(x, y): return tin.interpolate_laplace(x, y)

    yi = 0
    for y in np.arange(origin[1], origin[1] + res[1] * size, size):
        xi = 0
        for x in np.arange(origin[0], origin[0] + res[0] * size, size):
            ch = tin.is_inside_convex_hull(x, y) # check is the point [x, y] located inside  the convex hull of the DT
            if ch == False:
                ras[yi, xi] = -9999 # no-data value
            else:
                tri = tin.locate(x, y) # locate the triangle containing the point [x,y]. An error is thrown if it is outside the convex hull
                if tri != [] and 0 not in tri:
                    ras[yi, xi] = interpolant(x, y)
                else: ras[yi, xi] = -9999 # no-data value
            xi += 1
        yi += 1
    return ras


def write_geotiff_withbuffer(raster, origin, size, fpath):
    """Writes the interpolated TIN-linear and Laplace rasters
    to disk using the GeoTIFF format with buffer (100 m). The header is based on
    the raster array and a manual definition of the coordinate
    system and an identity affine transform.

    Args:
        raster(array) : Z interpolation
        origin(list): coordinate location of the relative origin (bottom left)
        size (float): raster cell size
        fpath(str): target folder "_tmp"

    Returns:
        bool: If the output "DTM" in the folder "_tmp" is okay or not
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
    # réécrire plus proprement en considérant ce qu'il y a entre chaque _ (tiret du 8)    
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
    """Severals steps :
        1- Merge LIDAR tiles
        2- Crop tiles 
        3- Takes the filepath to an input LAS (crop) file and the desired output raster cell size. Reads the LAS file and outputs
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
    # STEP 3 : Reads the LAS file and outputs the ground points as a numpy array.
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
    

def do(verbose=False):

    import sys

    # Paramètres
    size = 1000 #km
    _size = give_name_resolution_raster(size)

    # Pour tester ce fichier de création de raster colorisé par classe après une interpolation
    in_las = sys.argv[1:][0]
    # Dossier dans lequel seront créés les fichiers
    path_workfolder = sys.argv[1:][1]

    in_las_name = in_las[-35:]



    # Fichier de sortie MNT brut
    out_dtm_raster = f"{path_workfolder}{in_las_name}_DTM.tif"

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
    FileLasGround = write_las(input_points=ground_pts, file=in_las_name , src=path_workfolder, name="ground")



    if verbose :
        print("\nInterpolation méthode de Laplace...")

    if verbose :
        print("\n           Extraction liste des coordonnées du nuage de points...")
    # Extraction coord nuage de points
    extents_calc, res_calc, origin_calc = las_prepare_1_file(target_file=in_las, src=path_workfolder, fname=in_las_name, size=1000)
    if verbose :
        print(f"Extents {extents_calc}")
        print(f"Resolution in coordinates {res_calc}")
        print(f"Loc of the relative origin {origin_calc}")



    if verbose :
        print("\n           Interpolation...")
    # Interpole avec la méthode de Laplace
    resolution = 1.0 # in meters
    origine = [origin_x, origin_y]
    size = 10000 # taille du raster (raster cell size) 1000km
    ras = execute_startin(pts=extents_calc, res=resolution, origin=origine, size=size)
    print(ras)

    if verbose :
        print("Build raster...")
    

    write_geotiff_withbuffer(raster=ras, origin=origine, size=size, fpath=in_las + _size + '_Laplace.tif')

    if verbose :
        print("Build las...")
    # LAS points sol interpolés
    write_las(input_points=ground_pts, file=in_las_name ,src=path_workfolder, name="ground_interp")


    if verbose :
        print("End.")

if __name__ == '__main__':
    
    do(True)