import os

dico_folder_template = {
    "folder_density_value": "DENS_VAL",
    "folder_density_color": "DENS_COL",
    "folder_LUT": "LUT",
    "folder_CC_brut": "CC_1_brut",
    "folder_CC_brut_color": "CC_2_bcolor",
    "folder_CC_fillgap": "CC_3_fg",
    "folder_CC_fillgap_color": "CC_4_fgcolor",
}


def create_folder(dest_dir: str, dico_fld: dict):
    """Create folders from dictionnary dico_folder if not exist"""
    for folder in dico_fld:
        folder_path = os.path.join(dest_dir, dico_fld[folder])
        os.makedirs(folder_path, exist_ok=True)  # create folder if not exist
