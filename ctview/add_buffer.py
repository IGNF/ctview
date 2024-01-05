import pdaltools.las_add_buffer


def run_pdaltools_buffer(
    input_dir: str,
    tile_filename: str,
    output_filename: str,
    buffer_width: int = 100,
    tile_width: int = 1000,
    tile_coord_scale: int = 1000,
    spatial_ref: str = "EPSG:2154",
):
    """Merge lidar tiles around the queried tile and crop them in order to add a buffer
    to the tile (usually 100m).
    Args:
        input_dir (str): directory of pointclouds (where you look for neigbors)
        tile_filename (str): full path to the queried LIDAR tile
        output_filename (str) : full path to the saved cropped tile
        buffer_width (int): width of the border to add to the tile (in pixels)
        spatial_ref (str): Spatial reference to use to override the one from input las.
        tile width (int): width of tiles in meters (usually 1000m)
        tile_coord_scale (int) : scale used in the filename to describe coordinates in meters
                (usually 1000m)
        spatial_ref (str) : spatial reference (default EPSG:2154)
    """
    # run buffer
    pdaltools.las_add_buffer.create_las_with_buffer(
        input_dir,
        tile_filename,
        output_filename,
        buffer_width=buffer_width,
        spatial_ref=spatial_ref,
        tile_width=tile_width,
        tile_coord_scale=tile_coord_scale,
    )
