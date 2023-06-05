import os
import ctview.utils_tools as utils_tools
from ctview.parameter import dico_param

RES_DTM = utils_tools.give_name_resolution_raster(dico_param["resolution_DTM"])
RES_DTM_DENS = utils_tools.give_name_resolution_raster(dico_param["resolution_DTM_dens"])
RES_DSM = utils_tools.give_name_resolution_raster(dico_param["resolution_DSM"])

dico_folder = {
    "folder_LAS_ground_virtual": "LAS_filterGrdVirt",
    "folder_DTM_brut": f"DTM{RES_DTM}_brut",
    "folder_DTM_shade": f"DTM{RES_DTM}_shade",
    "folder_DTM_color": f"DTM{RES_DTM}_color",
    "folder_DTM_DENS_brut":  f"DTM_DENS{RES_DTM_DENS}_brut",
    "folder_DTM_DENS_shade": f"DTM_DENS{RES_DTM_DENS}_shade",
    "folder_DSM_brut":  f"DSM{RES_DSM}_brut",
    "folder_DSM_shade": f"DSM{RES_DSM}_shade",
    "folder_intensity": "INTENSITY",
    "folder_interp_table": "TABLE_INTERP",
    "folder_density_value" : "DENS_VAL",
    "folder_density_color" : "DENS_COL",
    "folder_density_final" : "DENS_FINAL",
    "folder_LUT" : "LUT",
    "folder_CC_brut" : "CC_1_brut",
    "folder_CC_brut_color" : "CC_2_bcolor",
    "folder_CC_fillgap" : "CC_3_fg",
    "folder_CC_fillgap_color" : "CC_4_fgcolor",
    "folder_CC_fusion" : "CC_5_fusion",
}


def create_folder(dest_dir: str):
    """Create folders from dictionnary dico_folder if not exist"""
    for folder in dico_folder:
        folder_path = os.path.join(dest_dir, dico_folder[folder])
        os.makedirs(folder_path, exist_ok=True) # create folder if not exist

def add_folder_list_cycles(List: list, folder_base: str, key_base: str):
    """
    Add number of folder that correspond to the number of colorisations with the number of cycles.
    Args :
        List: list of number of cycles per colorisation
        folder: basename of the folders
    """
    for c in List:
        key = f"{key_base}{c}"
        value = f"{folder_base}{c}c"
        dico_folder[key] = value

def delete_empty_folder(dir: str):
    """
    Delete empty folder of dir
    Args :
        dir : directory to be clean
    """
    list_folder = os.listdir(dir)
    for f in list_folder :
        if len(os.listdir(os.path.join(dir,f))) == 0:
            os.rmdir(os.path.join(dir,f))
