# Autor : ELucon

# IMPORT

# File
import utils_pdal

# Library


# FONCTION


def generate_raster_of_density(input_las: str):
    """
    Build a raster with ground points only (class 2)
    input_las : origin points cloud
    """

    # Filter ground points
    pip1 = utils_gdal.get_ground_points_only(input_las=input_las)
    pip1.execute()
    filter_points = pip1.array[0]

    # Build raster

    # Transform in density

    # Color density

    # Mutiply
