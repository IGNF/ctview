import os
import ctview.tools as tools
from ctview.parameter import dico_param

RES_DTM = tools.give_name_resolution_raster(dico_param["resolution_DTM"])
RES_DTM_DENS = tools.give_name_resolution_raster(dico_param["resolution_DTM_dens"])
RES_DSM = tools.give_name_resolution_raster(dico_param["resolution_DSM"])

dico_folder = {
    "folder_LAS_ground_virtual": "LAS_filterGrdVirt",
    "folder_DTM_brut": f"DTM{RES_DTM}_brut",
    "folder_DTM_shade": f"DTM{RES_DTM}_shade",
    "folder_DTM_color": f"DTM{RES_DTM}_color",
    "folder_DTM_DENS_brut":  f"DTM_DENS{RES_DTM_DENS}_brut",
    "folder_DSM_brut":  f"DSM{RES_DSM}_brut",
    "folder_DSM_shade": f"DSM{RES_DSM}_shade",
    "folder_intensity": "INTENSITY",
    "folder_interp_table": "TABLE_INTERP",
    "folder_density_value" : "DENS_VAL",
    "folder_density_color" : "DENS_COL",
    "folder_density_final" : "DENS_FINAL"
}


def create_folder(dest_dir: str):
    """Create folders from dictionnary dico_folder if not exist"""
    for folder in dico_folder:
        folder_path = os.path.join(dest_dir, dico_folder[folder])
        os.makedirs(folder_path, exist_ok=True) # create folder if not exist
