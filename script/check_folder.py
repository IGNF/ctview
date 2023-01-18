import os
import shutil

dico_folder = {
    "folder_LAS_ground": "LAS_ground",
    "folder_DTM_brut": "DTM_brut",
    "folder_DTM_shade": "DTM_shade",
    "folder_DTM_color": "DTM_color",
    "folder_intensity": "INTENSITY",
}


def delete_folder(dest_dir: str):
    """Delete folders from dictionnary dico_folder if exist"""
    for folder in dico_folder:
        folder_path = os.path.join(dest_dir, dico_folder[folder])
        if os.path.isdir(folder_path):  # if exist
            shutil.rmtree(folder_path)  # delete


def create_folder(dest_dir: str):
    """Create folders from dictionnary dico_folder if not exist"""
    for folder in dico_folder:
        folder_path = os.path.join(dest_dir, dico_folder[folder])
        os.makedirs(folder_path, exist_ok=True)  # create folder if not exist
