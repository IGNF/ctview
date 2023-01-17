#Autor : ELucon

# IMPORT

    # File
import utils_pdal
import tools
    # Library
import os
import pdal
import argparse
import subprocess
    # Dictionnary
from parameter import dico_param
from check_folder import dico_folder

# PARAMETERS

EPSG = dico_param["EPSG"]
resolution = dico_param["resolution_density"]
extension = dico_param["raster_extension"]
FOLDER_DENS_VALUE = dico_folder["folder_density_value"]
FOLDER_DENS_COLOR = dico_folder["folder_density_color"]

# FONCTION


def generate_raster_of_density_color(
    input_las: str,
    output_dir: str,
):
    """
    Build a raster of density colored.
    Args :
        input_las : las file
        output_dir : output directory
    Return :
        path of the raster of density colored
    """
    input_filename = os.path.basename(input_las)

    # Build raster count point
    raster_name_dens = os.path.join(output_dir, os.path.join(FOLDER_DENS_VALUE,f"{os.path.splitext(input_filename)[0]}_DENS{extension}"))
    #raster_name_dens = os.path.join(output_dir, f"{os.path.splitext(input_filename)[0]}_DENS{extension}")



    pipeline = (
        pdal.Reader.las(filename=input_las)
        | pdal.Writer.gdal(
                        filename = raster_name_dens, 
                        resolution = resolution,
                        output_type = "count"
                        )
    )
    pipeline.execute()

    if False :
        # Transform in density

 
        DENS_bat = os.path.join(output_dir, 'transfom_density.sh')
        DensiteRapSurf = f"{os.path.splitext(out_raster_name)[0]}_25{extension}"

        DENS_fin_flux = open(DENS_bat, "w")

        #Transformation du PointCount en Densite ( avec le rapport de surface de 25m² )
        DENS_fin_flux.write("call gdal_calc --overwrite -a "+out_raster_name+" --outfile="+DensiteRapSurf+" --calc=\"(a/25)\"\n")
        DENS_fin_flux.close()

        #subprocess.call(DENS_bat)

    # Color density

    raster_name_dens_color = os.path.join(output_dir, os.path.join(FOLDER_DENS_COLOR,f"{os.path.splitext(input_filename)[0]}_DENS_COLOR{extension}"))

    tools.color_raster_with_LUT(
        input_raster = raster_name_dens,
        output_raster = raster_name_dens_color,
        LUT = os.path.join("..",os.path.join("LUT","LUT_DENSITY.txt"))
    )

    return raster_name_dens_color


def mutiply_DTM_Density(input_DTM: str, input_dens_raster: str):
    # Mutiply 
    pass



def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-las", "--input_las")
    parser.add_argument('-o', '--output_dir')

    return parser.parse_args()

if __name__=="__main__":

    args = parse_args()
    input_las = args.input_las
    output_dir = args.output_dir

    # Create directory if not exists
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir,FOLDER_DENS_VALUE), exist_ok=True)
    os.makedirs(os.path.join(output_dir,FOLDER_DENS_COLOR), exist_ok=True)

    generate_raster_of_density(input_las = input_las, output_dir=output_dir)
