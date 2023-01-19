import fnmatch
import re
import os
import tempfile
import geojson

from osgeo import gdal, osr, ogr

# import lidarutils.geometry_utils as gu
# import lidarutils.gdal_utils as lu_gdal_utils


def add_epsg_to_raster(raster: str, epsg: int):
    """add epsg to raster"""
    gdal_image = gdal.Open(raster)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(epsg)
    gdal_image.SetProjection(srs.ExportToWkt())


def build_vrt(
    vrt: str, input_images_dir: str, format_image: str, epsg: int, force_if_exists: bool
):
    """build a vrt if non exists"""
    if not force_if_exists and os.path.exists(vrt):
        return

    # scan des fichiers
    images = []
    reobj = re.compile(fnmatch.translate("*." + format_image), re.IGNORECASE)
    for file in os.listdir(input_images_dir):
        if reobj.match(file):
            add_epsg_to_raster(input_images_dir + "/" + file, epsg)
            images.append(input_images_dir + "/" + file)

    vrt_options = gdal.BuildVRTOptions(resampleAlg="bilinear", addAlpha=False)
    my_vrt = gdal.BuildVRT(vrt, images, options=vrt_options)
    my_vrt = None


# def extract_from_vrt(in_vrt: str, out_put_image: str, bbox: gu.Bbox):
#     """extract part of DTM"""
#     gdal.Translate(
#         out_put_image, in_vrt, projWin=[bbox.xmin, bbox.ymax, bbox.xmax, bbox.ymin]
#     )


def get_box_from_image(input_raster: str):
    """get image bbox"""
    src = gdal.Open(input_raster)
    ulx, x_res, _, uly, _, y_res = src.GetGeoTransform()
    lrx = ulx + (src.RasterXSize * x_res)
    lry = uly + (src.RasterYSize * y_res)
    return gu.Bbox(ulx, lrx, lry, uly)


def rasterise(
    image_out: str, geo: str, image_ref_georef: str, type: gdal, options=None
):
    """rasterise a geometry"""
    data_src = gdal.Open(image_ref_georef)
    drv_tiff = gdal.GetDriverByName("GTiff")
    ds_out = drv_tiff.Create(
        image_out, data_src.RasterXSize, data_src.RasterYSize, 1, type
    )
    ds_out.SetGeoTransform(data_src.GetGeoTransform())
    if geo is not None and os.path.exists(geo):
        source_ds = ogr.Open(geo)
        source_layer = source_ds.GetLayer()
        if options:
            gdal.RasterizeLayer(ds_out, [1], source_layer, options=options)
        else:
            gdal.RasterizeLayer(ds_out, [1], source_layer, None)
    data_src, ds_out = None, None


def polygonize_and_add_field_name(raster_unvalide: str, epsg: int, field_name: str):
    unvalide_area = []
    out_json_density_ground = tempfile.NamedTemporaryFile(
        suffix="_polygonize_and_add_field_name.json"
    )
    lu_gdal_utils.gdal_polygonize(raster_unvalide, out_json_density_ground.name, epsg)
    with open(out_json_density_ground.name) as file:
        geo_json = geojson.load(file)
        features = geo_json["features"]
        for fea in features:
            fea["properties"]["type erreur"] = field_name
            unvalide_area.append(fea)
    return unvalide_area
