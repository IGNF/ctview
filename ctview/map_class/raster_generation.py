import logging as log
import os
import tempfile
from collections.abc import Iterable
from typing import Tuple

import hydra
import numpy as np
from omegaconf import DictConfig
from osgeo import gdal

from ctview import clip_raster, map_DXM, utils_pdal, utils_raster
from ctview.map_class.classes_mapping import (
    check_and_list_original_classes_to_keep,
    compute_binary_class,
    convert_class_array_to_precedence_array,
    create_class_raster_raw_deprecated,
)
from ctview.map_class.post_processing import add_color_to_raster, fill_gaps_raster


def generate_class_raster_raw(
    input_points: np.array,
    input_classifs: np.array,
    output_tif: str,
    epsg: int | str,
    raster_origin: tuple,
    class_by_layer: list = [],
    tile_width: int = 1000,
    pixel_size: float = 1,
    no_data_value: int = -9999,
    raster_driver: str = "GTiff",
):
    """Generate a (multilayer) raster of class for the classes in `class_by_layer`.

    The output has one layer per value in the class_by_layer list.
    Each layer contains a class map for the classes listed in its correspondig list of
    values in class_by_layer.
    Eg, if class_by_layer = [1, 3]:
    * the first layer contains the class map for class 1 only,
    * the second layer contains the class map for class 3 only,

    Args:
        input_points (np.array): numpy array with the input points
        input_classifs (np.array): numpy array with classifications of the input points
        output_tif (str): path to the output file
        epsg (int): spatial reference of the output file
        raster_origin (tuple): origin of the output raster
        class_by_layer (list, optional): class to display on each layer. Defaults to [].
        tile_width (int, optional): size ot the raster tile in meters. Defaults to 1000.
        pixel_size (float, optional): pixel size of the output raster. Defaults to 1.
        no_data_value (int, optional): No data value of the output. Defaults to -9999.
        raster_driver (str): raster_driver (str): One of GDAL raster drivers formats
        (cf. https://gdal.org/drivers/raster/index.html#raster-drivers). Defaults to "GTiff"
    Returns:
        raster_raw (np.array): binary multilayer raster of class
    """
    os.makedirs(os.path.dirname(output_tif), exist_ok=True)
    if not isinstance(class_by_layer, Iterable):
        raise TypeError(
            "In generate_class_raster_raw, class_by_layer is expected to be a list, "
            f"got {type(class_by_layer)} instead)"
        )
    if not np.all([isinstance(item, int) for item in class_by_layer]):
        raise TypeError(
            "In generate_class_raster_raw, classes_by_layer is expected to be a list of integers, "
            f"got {class_by_layer} instead)"
        )
    class_list_by_layer = [[class_one_layer] for class_one_layer in class_by_layer]
    raster_raw = utils_raster.generate_raster_raw(
        input_points=input_points,
        input_classifs=input_classifs,
        output_tif=output_tif,
        epsg=epsg,
        raster_origin=raster_origin,
        fn=compute_binary_class,
        classes_by_layer=class_list_by_layer,
        tile_width=tile_width,
        pixel_size=pixel_size,
        no_data_value=no_data_value,
        raster_driver=raster_driver,
    )

    return raster_raw


def generate_class_raster(
    input_points: np.array,
    input_classifs: np.array,
    tilename: str,
    output_dir: str,
    config_class: DictConfig,
    config_io: DictConfig,
    config_geometry: DictConfig,
    raster_origin: tuple,
) -> str:
    """Generate a single band classification raster.
    Each pixel represents the classification of the points contained in this pixel using :
    - combination rules to create new classification values for specific combinations of classes
        (eg. class 56 when both class 5 and 6 are in the same pixel)
    - a precedence list to choose which class to show when several classes are in the same pixel
    The combination rules and precedence list are in `config_class`

    Args:
        input_points (np.array): numpy array with the input points
        input_classifs (np.array): numpy array with classifications of the input points
        tilename (str): tilename used to generate the output filename
        output_dir (str): output full path
        config_class (Dictconfig): configuration dict for the classification such as :
        {
            pixel_size: 1
            CBI_rules:
                - {"CBI": [5,6],"AGGREG": 56}
                - {"CBI": [5,17],"AGGREG": 57}
                - {"CBI": [2,6],"AGGREG": 26}
        }
        precedence_classes: [56,26,6,17,5,57,2]
        intermediate_dirs:  # pour chaque intermediate_dirs, si null, le dossier n'est pas créé
            class_binary: null  # exemple: tmp/binary
            class_precedence: null}
            Cf `class_map` section in `configs/config_metadata.yaml`
        config_io (DictConfig):  hydra configuration with the general io parameters
            eg.  {
            input_filename: null
            input_dir: null
            output_dir: null
            spatial_reference: 2154
            no_data_value: -9999
            extension: .tif
            raster_driver: "GTiff"
            }
            Cf `io` section in `configs/config_metadata.yaml`

        config_geometry (DictConfig): hydra configuration with the tile geometry parameters, such as:
        {
            tile_coord_scale: 1000  # meters
            tile_width: 1000  # meters
        }
        Cf `tile_geometry` section in `configs/config_metadata.yaml`
        raster_origin (tuple): origin of the raster (top left corner of the upper left pixel)

    Returns:
        str: full path to the output class raster
    """
    log.info("\nCreate class map")
    inter_dirs = config_class.intermediate_dirs
    ext = config_io.extension

    classes_in_las = set(input_classifs)
    class_by_layer = check_and_list_original_classes_to_keep(
        classes_in_las, config_class.CBI_rules, config_class.precedence_classes, config_class.ignored_classes
    )

    with tempfile.TemporaryDirectory(prefix="tmp_class_map", dir="tmp") as tmpdir:
        if inter_dirs.class_binary:
            raster_class_map_binary = os.path.join(output_dir, inter_dirs.class_binary, f"{tilename}_class_raw{ext}")
        else:
            raster_class_map_binary = os.path.join(tmpdir, f"{tilename}_class_raw{ext}")

        raster_class_map = os.path.join(output_dir, f"{tilename}_class{ext}")

        os.makedirs(os.path.dirname(raster_class_map_binary), exist_ok=True)
        os.makedirs(os.path.dirname(raster_class_map), exist_ok=True)

        class_raw = generate_class_raster_raw(
            input_points=input_points,
            input_classifs=input_classifs,
            output_tif=raster_class_map_binary,
            epsg=config_io.spatial_reference,
            raster_origin=raster_origin,
            class_by_layer=class_by_layer,
            tile_width=config_geometry.tile_width,
            pixel_size=config_class.pixel_size,
            no_data_value=config_io.no_data_value,
            raster_driver=config_io.raster_driver,
        )

        flatten_array = convert_class_array_to_precedence_array(
            input_array=class_raw,
            class_by_layer=class_by_layer,
            rules=config_class.CBI_rules,
            priorities=config_class.precedence_classes,
        )

        utils_raster.write_single_band_raster_to_file(
            input_array=flatten_array,
            raster_origin=raster_origin,
            output_tif=raster_class_map,
            pixel_size=config_class.pixel_size,
            epsg=config_io.spatial_reference,
            raster_driver=config_io.raster_driver,
            colormap=config_class.colormap,
        )

        return raster_class_map


def generate_pretty_class_raster_from_single_band_raster(
    input_raster: str,
    input_las: str,
    tilename: str,
    output_dir: str,
    config_class: DictConfig,
    config_io: DictConfig,
):
    """Use single band classification raster (with colors in the metadata) and
    las file to generate a classification raster for visualization purpose
    with colors from input_raster and hillshade computed from a digital surface model

    Args:
        input_raster (str): path to the input single band classification model
        input_las (str): path to the input las file
        tilename (str): tilename (used to generate the output file name)
        output_dir (str): path to the output directory
        config_class (DictConfig): configuration dict for the class map
        It must contain:
        {
          # the output raster size (should be coherent with the pixel size of input_raster)
          pixel_size: 0.5
          # The filter parameters to choose the points to use in the DSM
          dxm_filter:
              dimension: Classification
              keep_values: [2, 3, 4, 5, 6, 9, 17, 64, 66, 67]
          # The operation used to mix DSM hillshade and colored
          # A: input_colored raster
          # B: hillshade DSM
          hillshade_calc: "0.95*A*(0.2+0.6*(B/255))"
            }
        config_io (DictConfig): _description_
    """
    ext = config_io.extension
    with tempfile.TemporaryDirectory(prefix="tmp_class_map", dir="tmp") as tmpdir:
        colored_tmp_file = os.path.join(tmpdir, f"{tilename}_colored{ext}")
        dxm_raw_tmp_file = os.path.join(tmpdir, f"{tilename}_dxm_raw{ext}")
        dxm_hillshade_tmp_file = os.path.join(tmpdir, f"{tilename}_dxm_hillshade{ext}")

        ds = gdal.Open(input_raster)
        ds = gdal.Translate(colored_tmp_file, ds, rgbExpand="rgb")  # Use colors in metadata
        ds = None  # close file
        output_raster = os.path.join(output_dir, f"{tilename}_class_pretty{ext}")
        map_DXM.add_dxm_hillshade_to_raster(
            input_raster=colored_tmp_file,
            input_pointcloud=str(input_las),
            output_raster=output_raster,
            pixel_size=config_class.pixel_size,
            dxm_filter_dimension=config_class.dxm_filter.dimension,
            dxm_filter_keep_values=config_class.dxm_filter.keep_values,
            output_dxm_raw=dxm_raw_tmp_file,
            output_dxm_hillshade=dxm_hillshade_tmp_file,
            hillshade_calc=config_class.hillshade_calc,
            config_io=config_io,
        )


def create_map_class_raster_with_postprocessing_color_and_hillshade(
    input_las: str,
    tilename: str,
    config_class: DictConfig | dict,
    config_io: DictConfig | dict,
    output_bounds: Tuple,
):
    """Create a raster of class with post processing steps:
    * fill gaps with a method of gdal
    * colorisation
    * mix with a hillshade that comes from an elevation model

    Args:
        input_las (str): path to the input las file
        tilename (str): tilename used to generate the output filename
        config_class (DictConfig | dict):  hydra configuration with the class map parameters
        eg. {
          pixel_size: 0.5  # pixel size of the output raster
          dxm_filter:  # filter used to generate dsm, the dsm is used to generate hillshade
              dimension: Classification
              keep_values: [1, 2, 3, 4, 5, 6, 9, 17, 64, 65, 66, 67, 202]
          lut_filename: LUT_CLASS.txt  # filename for the lut that colorizes the classification map
          output_subdir: CC_6_fusion  # folder name for the final class map output
          hillshade_calc: "254*((A*(0.5*(B/255)+0.25))>254)+(A*(0.5*(B/255)+0.25))*((A*(0.5*(B/255)+0.25))<=254)"
          # formula used to mix the classification map with its hillshade
          intermediate_dirs:  # paths to the saved intermediate results
              CC_raw: CC_1_raw
              CC_raw_color: CC_2_bcolor
              CC_fillgap: CC_3_fg
              CC_fillgap_color: CC_4_fgcolor
              CC_crop: CC_5_crop
              dxm_raw: "DSM"
              dxm_hillshade: "tmp_dsm/hillshade"

        }
        config_io (DictConfig | dict): hydra configuration with the general io parameters
        eg.  {
            input_filename: null
            input_dir: null
            output_dir: null
            spatial_reference: EPSG:2154
            lut_folder: LUT
            extension: .tif
            raster_driver: GTiff
            no_data_value: -9999
            tile_geometry:
                tile_coord_scale: 1000
                tile_width: 1000
            }
        output_bounds (Tuple): bounds of the output raster file ([minx,maxx],[miny, maxy]).
            Should correspond to the las input file before adding any buffer
    """
    log.basicConfig(level=log.INFO, format="%(message)s")

    # File names
    input_las_name = os.path.basename(input_las)
    in_points = utils_pdal.read_las_file(input_las)

    log.info(f"\nMAP OF CLASS : file : {input_las_name}")

    # Output_folder_names
    out_dir = config_io.output_dir
    inter_dirs = config_class.intermediate_dirs
    ext = config_io.extension

    with tempfile.TemporaryDirectory(prefix="tmp_class", dir="tmp") as tmpdir:
        if inter_dirs.CC_raw:
            raster_raw = os.path.join(out_dir, inter_dirs.CC_raw, f"{tilename}_raw{ext}")
        else:
            raster_raw = os.path.join(tmpdir, f"{tilename}_raw{ext}")
        if inter_dirs.CC_raw_color:
            raster_raw_color = os.path.join(out_dir, inter_dirs.CC_raw_color, f"{tilename}_raw_color{ext}")

        if inter_dirs.CC_fillgap:
            raster_fillgap = os.path.join(out_dir, inter_dirs.CC_fillgap, f"{tilename}_fillgap{ext}")
        else:
            raster_fillgap = os.path.join(tmpdir, f"{tilename}_fillgap{ext}")
        if inter_dirs.CC_fillgap_color:
            raster_fg_color = os.path.join(out_dir, inter_dirs.CC_fillgap_color, f"{tilename}_fillgap_color{ext}")
        else:
            raster_fg_color = os.path.join(tmpdir, f"{tilename}_fillgaps_color{ext}")
        if inter_dirs.CC_crop:
            raster_fg_color_clip = os.path.join(out_dir, inter_dirs.CC_crop, f"{tilename}_fillgap_color_clip{ext}")
        else:
            raster_fg_color_clip = os.path.join(tmpdir, f"{tilename}_fillgap_color_clip{ext}")

        if inter_dirs.dxm_raw:
            raster_class_map_dxm_raw = os.path.join(out_dir, inter_dirs.dxm_raw, f"{tilename}_interp{ext}")
        else:
            raster_class_map_dxm_raw = os.path.join(tmpdir, f"{tilename}_interp{ext}")
        if inter_dirs.dxm_hillshade:
            raster_class_map_dxm_hs = os.path.join(out_dir, inter_dirs.dxm_hillshade, f"{tilename}_hillshade{ext}")
        else:
            raster_class_map_dxm_hs = os.path.join(tmpdir, f"{tilename}_hillshade{ext}")

        raster_class_map = os.path.join(out_dir, config_class.output_subdir, f"{tilename}_fusion_DSM_class{ext}")
        os.makedirs(os.path.dirname(raster_class_map), exist_ok=True)

        log.info("Step 1 : Write raster raw")
        create_class_raster_raw_deprecated(
            in_points=in_points,
            output_file=raster_raw,
            res=config_class.pixel_size,
            raster_driver=config_io.raster_driver,
            no_data_value=config_io.no_data_value,
        )

        if inter_dirs["CC_raw_color"]:
            log.info("Step 1.5 : Write raster raw colorized")
            add_color_to_raster(
                in_raster=raster_raw,
                output_file=raster_raw_color,
                LUT=os.path.join(config_io.lut_folder, config_class.lut_filename),
            )

        log.info("Step 2 : Write raster with fillgap")
        fill_gaps_raster(
            in_raster=raster_raw,
            output_file=raster_fillgap,
            raster_driver=config_io.raster_driver,
        )

        log.info("Step 2 : Write raster with fillgap and color")
        add_color_to_raster(
            in_raster=raster_fillgap,
            output_file=raster_fg_color,
            LUT=os.path.join(config_io.lut_folder, config_class.lut_filename),
        )
        log.info("Step 3 : Write raster with fillgap, color + clipped at the right bounds")
        clip_raster.clip_raster(
            input_raster=raster_fg_color,
            output_raster=raster_fg_color_clip,
            bounds=output_bounds,
            raster_driver=config_io.raster_driver,
        )

        map_DXM.add_dxm_hillshade_to_raster(
            input_raster=raster_fg_color_clip,
            input_pointcloud=str(input_las),
            output_raster=raster_class_map,
            pixel_size=config_class.pixel_size,
            dxm_filter_dimension=config_class.dxm_filter.dimension,
            dxm_filter_keep_values=config_class.dxm_filter.keep_values,
            output_dxm_raw=raster_class_map_dxm_raw,
            output_dxm_hillshade=raster_class_map_dxm_hs,
            hillshade_calc=config_class.hillshade_calc,
            config_io=config_io,
        )


@hydra.main(config_path="../../configs/", config_name="config_ctview.yaml", version_base="1.2")
def main(config: DictConfig):
    log.basicConfig(level=log.INFO, format="%(message)s")
    initial_las_file = os.path.join(config.io.input_dir, config.io.input_filename)
    las_bounds = utils_pdal.get_bounds_from_las(initial_las_file)
    os.makedirs(config.io.output_dir, exist_ok=True)
    create_map_class_raster_with_postprocessing_color_and_hillshade(
        input_las=initial_las_file,
        tilename=os.path.splitext(os.path.basename(initial_las_file))[0],
        config_class=config.class_map,
        config_io=config.io,
        output_bounds=las_bounds,
    )
    log.info("END.")


if __name__ == "__main__":
    gdal.UseExceptions()
    main()
