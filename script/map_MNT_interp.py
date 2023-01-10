# Autor : ELucon

# IMPORT

    # File
import tools
import utils_pdal
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
from map_MNT import hillshade_from_raster, color_MNT_with_cycles
import gen_LUT_X_cycle
import shutil
from tqdm import tqdm

def delete_folder(dest_dir: str):
    """Delete the severals folders "LAS", "DTM", "DTM_shade" and "DTM_color" if not exist"""
    # Delete folder "LAS"
    LAS_new_dir = os.path.join(dest_dir, 'LAS')
    if os.path.isdir(LAS_new_dir):
        shutil.rmtree(LAS_new_dir)
    # Delete folder "DTM"
    DTM_brut_new_dir = os.path.join(dest_dir, 'DTM_brut')
    if os.path.isdir(DTM_brut_new_dir):
        shutil.rmtree(DTM_brut_new_dir)
    # Delete folder "DTM_shade"
    DTM_shade_new_dir = os.path.join(dest_dir, 'DTM_shade')
    if os.path.isdir(DTM_shade_new_dir):
        shutil.rmtree(DTM_shade_new_dir)
    # Delete folder "DTM_color"
    DTM_color_new_dir = os.path.join(dest_dir, 'DTM_color')
    if os.path.isdir(DTM_color_new_dir):
        shutil.rmtree(DTM_color_new_dir)

def create_folder(dest_dir: str):
    """Create the severals folders "LAS", "DTM", "DTM_shade" and "DTM_color" if not exist"""
    # Create folder "LAS"
    LAS_new_dir = os.path.join(dest_dir, 'LAS')
    if not os.path.isdir(LAS_new_dir):
        os.makedirs(LAS_new_dir)
    # Create folder "DTM"
    DTM_brut_new_dir = os.path.join(dest_dir, 'DTM_brut')
    if not os.path.isdir(DTM_brut_new_dir):
        os.makedirs(DTM_brut_new_dir)
    # Create folder "DTM_shade"
    DTM_shade_new_dir = os.path.join(dest_dir, 'DTM_shade')
    if not os.path.isdir(DTM_shade_new_dir):
        os.makedirs(DTM_shade_new_dir)
    # Create folder "DTM_color"
    DTM_color_new_dir = os.path.join(dest_dir, 'DTM_color')
    if not os.path.isdir(DTM_color_new_dir):
        os.makedirs(DTM_color_new_dir)





def filter_las_ground(input_dir: str, filename: str):
    """ Reads the LAS file and filter only grounds from LIDAR.

    Args:
        input_dir (str) : directory of projet who contains LIDAR (Ex. "data")
        file (str): name of LIDAR tiles
    """
    if input_dir[len(input_dir)-1]=="/":
        input_file = "".join([input_dir, filename])
    else :
        input_file = "/".join([input_dir, filename])
    information = {}
    information = {
    "pipeline": [
            {
                "type":"readers.las",
                "filename":input_file,
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
    #print(ground)
    pipeline = pdal.Pipeline(ground)
    pipeline.execute()
    return pipeline.arrays[0]

def write_las(input_points, filename: str, output_dir: str, name: str, verbose=False):
    """Write a las file
    Args:
        inputs_points (array) : points cloud
        filename (str): name of LIDAR tiles
        output_dir (str): directory of work who will contains the output files
        name (str) : suffix added to filename
        """
    dst = str("LAS".join([output_dir, '/']))

    if not os.path.exists(dst):
        os.makedirs(dst) # create directory /LAS if not exists

    if verbose :
        print("dst : "+dst)
    FileOutput = "".join([dst, "_".join([filename[:-4], f'{name}.las'])])
    if verbose :
        print("filename : "+FileOutput)
    pipeline = pdal.Writer.las(filename = FileOutput, a_srs="EPSG:2154").pipeline(input_points)
    pipeline.execute()

    NameFileOutput = "_".join([filename[:-4], f'{name}.las'])
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
        fpath(str): target folder "_tmp"

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
                           crs='EPSG:2154',
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



    


def color_MNT_with_cycles(
    las_input_file: str,
    output_dir: str,
    raster_MNT_file: str,
    nb_cycle: int,
    verbose=False
):
    """Color a raster with a LUT created depending of a choice of cycles

    Argss :
        file_las : str : points cloud
        file_MNT : str : MNT corresponding to the points cloud
        nb_cycle : int : the number of cycle that determine the LUT
    """

    if verbose :
        print("Generate MNT colorised :")
        print("(1/2) Generate LUT.")
    # Create LUT
    LUT = gen_LUT_X_cycle.generate_LUT_X_cycle(
        file_las=las_input_file,
        file_MNT=raster_MNT_file,
        nb_cycle=nb_cycle,
        verbose=verbose
    )

    # Path MNT colorised
    raster_MNT_color_file = f'{output_dir}/DTM_color/{las_input_file[:-4]}_DTM_hillshade_color{nb_cycle}c.tif'


    if verbose :
        print("MNT color : "+raster_MNT_color_file)
        print("(2/2) Colorise raster.")

    # Colorisation
    tools.color_raster_with_LUT(
        input_raster = raster_MNT_file,
        output_raster = raster_MNT_color_file,
        LUT = LUT,
    )


def main(verbose=False):

    import sys

    # Paramètres
    size = 1.0 # mètres = resolution from raster
    _size = give_name_resolution_raster(size)

    try :
        # Pour tester ce fichier de création de raster colorisé par classe après une interpolation
        input_las = sys.argv[1:][0]
        # Dossier dans lequel seront créés les fichiers
        output_dir = sys.argv[1:][1]
        # Choice of interpolation method : Laplace or TINlinear
        interpMETHOD = sys.argv[1:][2].lower()
        if interpMETHOD == "laplace":
            interpMETHOD = "Laplace"
        elif interpMETHOD =="tinlinear":
            interpMETHOD = "TINlinear"
        else :
            print("Wrong interpolation method : choose between Laplace method and TINlinear method")
            sys.exit()
    except IndexError :
        print("IndexError : Wrong number of argument : 3 expected (las path, destination folder, interpolation method)")
        sys.exit()

    # Complete path
    if output_dir[len(output_dir)-1] != '/' :
        output_dir = output_dir + '/'

    # Delete the severals folder LAS, DTM, DTM_shade and DTM_color if not exists
    delete_folder(output_dir)
    # Create the severals folder LAS, DTM, DTM_shade and DTM_color if not exists
    create_folder(output_dir)

    # Get directory
    input_dir = input_las[:-35]
    input_dir = utils_pdal.parent(input_las)
    # Get filename without extension
    input_las_name = input_las[-35:]
    input_las_name = f"{utils_pdal.stem(input_las)}.la{input_las[-1]}"




    # Fichier de sortie MNT brut
    out_dtm_raster = f"{output_dir}{input_las_name}_DTM.tif"

    # # Extraction infos du las
    # origin_x, origin_y, ProjSystem, AltiSystem = get_origin(input_las_name)

    # if verbose :
    #     print(f"Dalle name : {input_las_name}")

    #     print(f"North-West X coordinate : {origin_x} km")
    #     print(f"North-West Y coordinate : {origin_y} km")
    #     print(f"System of projection : {ProjSystem}")
    #     print(f"Altimetric system : {AltiSystem}")

    if verbose :
        print("\nFiltrage points sol et virtuels...")
    # Filtre les points sol de classif 2 et 66
    # tools.filter_las_version2(las,las_pts_ground)
    ground_pts = filter_las_ground(
        input_dir = input_dir,
        filename = input_las_name)

    if verbose :
        print("Build las...")
    # LAS points sol non interpolés
    FileLasGround = write_las(input_points=ground_pts, filename=input_las_name , output_dir=output_dir, name="ground", verbose=verbose)



    if verbose :
        print(f"\nInterpolation méthode de {interpMETHOD}...")

    if verbose :
        print("\n           Extraction liste des coordonnées du nuage de points...")
    # Extraction coord nuage de points
    extents_calc, res_calc, origin_calc = las_prepare_1_file(input_file=input_las, size=size)
    if verbose :
        print(f"\nExtents {extents_calc}")
        print(f"Resolution in coordinates : {res_calc}")
        print(f"Loc of the relative origin : {origin_calc}")



    if verbose :
        print("\n           Interpolation...")
    # Interpole avec la méthode de Laplace ou tin linéaire
    resolution = res_calc # résolution en coordonnées (correspond à la taille de la grille de coordonnées pour avoir la résolution indiquée dans le paramètre "size")
    origine = origin_calc
    ras = execute_startin(pts=extents_calc, res=resolution, origin=origine, size=size, method=interpMETHOD)
    

    if verbose :
        print("\nTableau d'interpolation : ")

        
        fileRas = f"{output_dir}ras.txt"

        print("\nWrite in " + fileRas)

        fileR = open(fileRas, "w")

        l,c = ras.shape
        s = ''
        for i in range(l):
            ligne = ""
            for j in range(c):
                ELEMENTras = ras[i,j]
                ligne += f"{round(ELEMENTras,5) : >20}"
            s += ligne
            s += '\n'  

        fileR.write(s)
        fileR.close()

        print("End write.")
        print("\n numpy.array post-interpolation")
        print(ras)
        print("\nBuild raster ie DTM brut...")
    
    raster_dtm_interp = write_geotiff_withbuffer(raster=ras, origin=origine, size=size, output_file=output_dir + "DTM_brut/" + input_las_name[:-4] + _size + f'_{interpMETHOD}.tif')

    if verbose :
        print(f"{output_dir}{_size}_{interpMETHOD}.tif")
        print("\nBuild las...")
    # LAS points sol interpolés
    las_dtm_interp = write_las(input_points=ground_pts, filename=input_las_name ,output_dir=output_dir, name="ground_interp", verbose=verbose)


    # Ajout ombrage
    if verbose :
        print("\nAdd hillshade...")
        print(raster_dtm_interp)
        print("\n")

    dtm_file = raster_dtm_interp
    dtm_hs_file = f"{output_dir}/DTM_shade/{input_las_name[:-4]}_DTM_hillshade.tif"
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
        las_input_file=input_las_name,
        output_dir=output_dir,
        raster_MNT_file=dtm_hs_file,
        nb_cycle=cycle,
        verbose=verbose
        )

        if verbose :
            print("Success.\n")

    if verbose :
        print("End.")

if __name__ == '__main__':
    
    main(True)

    OTHER   = "../../data/data_simple/solo/pont_route_OK.las"