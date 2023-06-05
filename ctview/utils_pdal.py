import pdal
import tempfile
from pathlib import Path

# from ctclass import utils_geometry, utils_gdal

def write_las_simple(input_points, output_las):
    """Write a las file"""
    pipeline = pdal.Writer.las(filename=output_las).pipeline(input_points)
    pipeline.execute()


def write_raster(input_points, output_raster, dim,):
    """
    Generate a raster.
    input_points : input
    output_raster : output
    dim : dimension
    """
    pipeline = pdal.Writer.gdal(
        filename=output_raster,
        resolution=0.5,
        dimension=dim,
    ).pipeline(input_points)
    pipeline.execute()


def write_raster_z(input_points, output_raster):
    """Generate a raster"""
    pipeline = pdal.Writer.gdal(
        filename=output_raster, resolution=0.5, dimension="Z"
    ).pipeline(input_points)
    pipeline.execute()


def write_raster_class(input_points, output_raster, res):
    """Generate a raster"""
    pipeline = pdal.Writer.gdal(
        filename=output_raster,
        resolution=res,
        dimension="Classification",
        gdaldriver="GTiff",
    ).pipeline(input_points)
    pipeline.execute()


def filter_las(points, classif):
    """Filter with the classification classif"""
    classif = f"Classification[{classif}:{classif}]"  # classif 6 = batiments
    pipeline = (
        pdal.Filter.range(limits=classif).pipeline(points)
        | pdal.Filter.hag_nn()
        | pdal.Filter.range(limits=classif)
    )
    pipeline.execute()
    return pipeline.arrays[0]


def filter_las_version2(lasFile, outFile):
    fpath = lasFile
    FileOutput = outFile
    information = {}
    information = {
        "pipeline": [
            {
                "type": "readers.las",
                "filename": fpath,
                "override_srs": "EPSG:2154",
                "nosrs": True,
            },
            {
                "type": "filters.range",
                "limits": "Classification[2:2],Classification[66:66]",
            },
            {
                "type": "writers.las",
                "a_srs": "EPSG:2154",
                # "minor_version": 4,
                # "dataformat_id": 6,
                "filename": FileOutput,
            },
        ]
    }
    ground = json.dumps(information, sort_keys=True, indent=4)
    print(ground)
    pipeline = pdal.Pipeline(ground)
    pipeline.execute()


def color_points_by_class(input_points):
    "Color las points by class."
    #   classif = "Classification[6:6]"  # classif 6 = batiments
    pipeline = pdal.Filter.colorinterp(
        ramp="pestel_shades",
        mad="true",
        k="1.8",
        dimension="Z",
    ).pipeline(input_points)
    pipeline.execute()
    return pipeline.arrays[0]


def read_las_file(input_las: str):
    """Read a las file and put it in an array"""
    pipeline = pdal.Pipeline() | pdal.Reader.las(filename=input_las)
    pipeline.execute()
    return pipeline.arrays[0]


def get_info_from_las(points):
    """get info from a las to put it in an array"""
    pipeline = pdal.Filter.stats().pipeline(points)
    pipeline.execute()
    return pipeline.metadata

def get_bounds_from_las(in_las: str):
    """get bounds=([minx,maxx],[miny,maxy]) from las file"""
    metadata = get_info_from_las(read_las_file(in_las))
    xmin = metadata["metadata"]["filters.stats"]["bbox"]["native"]["bbox"]["minx"]
    xmax = metadata["metadata"]["filters.stats"]["bbox"]["native"]["bbox"]["maxx"]
    ymin = metadata["metadata"]["filters.stats"]["bbox"]["native"]["bbox"]["miny"]
    ymax = metadata["metadata"]["filters.stats"]["bbox"]["native"]["bbox"]["maxy"]
    return ([xmin, xmax], [ymin, ymax])


def get_class_min_max_from_las(points):
    """
    Get minimum and maximum classification of a points cloud.
    """
    # Which class in OUT_FILTER_GROUND ?
    # Get Classification dictionnary
    dico_metadata = get_info_from_las(points)  # !!! an other function is used !!!

    list_statistic = dico_metadata["metadata"]["filters.stats"]["statistic"]

    indice = -1  # indice will be be the indice that show the researched dictionnary
    for i in range(len(list_statistic)):
        if list_statistic[i]["name"] == "Classification":
            indice = i
            break
    if indice == -1:
        print("AlgoError : classification dictionnary not found")
    # Classification dictionnary is list_statistic[indice]
    minClass = list_statistic[indice]["minimum"]
    maxClass = list_statistic[indice]["maximum"]
    return minClass, maxClass


def assign_classification(points):
    """assign classification to the entire las"""
    pipeline = pdal.Filter.assign(value="Classification = 0").pipeline(points)
    pipeline.execute()
    return pipeline.arrays[0]


def tab_class_to_str_pdal_class(class_filtre: [int]):
    """Build a string list for range filter classification"""
    tab_class = ""
    for c in class_filtre:
        tab_class += "Classification[" + str(c) + ":" + str(c) + "],"
    return tab_class[:-1]


def range_classification_points(points_ini, class_filtre: [int]):
    """range points with some class"""
    pipeline = pdal.Filter.range(
        limits=tab_class_to_str_pdal_class(class_filtre)
    ).pipeline(points_ini)
    pipeline.execute()
    return pipeline.arrays[0]


def get_geom_non_open_ground(input_las: str):
    """Calcul geometry of non open area"""
    tab_ground_class = [
        1,
        2,
        17,
        66,
    ]  # classe d'objets au sol [unclassified, ground, ponts, points virtuel]
    tab_non_ground_class = []
    for i in range(1, 255):
        if i not in tab_ground_class:
            tab_non_ground_class.append(i)

    pipeline_non_ground = pdal.Reader.las(filename=input_las) | pdal.Filter.range(
        limits=tab_class_to_str_pdal_class(tab_non_ground_class)
    )
    pipeline_non_ground.execute()
    return calc_boundary(pipeline_non_ground.arrays[0], 1)


def get_ground_points_pipeline(input_las: str):
    """get ground or non classified with a height lower than 0.5"""
    tab_ground_class = [1, 2, 17, 66]
    pipeline = (
        pdal.Reader.las(filename=input_las)
        | pdal.Filter.range(limits=tab_class_to_str_pdal_class(tab_ground_class))
        | pdal.Filter.hag_nn()
        | pdal.Filter.range(limits="HeightAboveGround[0:0.5]")
    )
    return pipeline


def get_ground_points_only(input_las: str):
    """get ground or non classified with a height lower than 0.5"""
    tab_ground_class = [2]
    pipeline = (
        pdal.Reader.las(filename=input_las)
        | pdal.Filter.range(limits=tab_class_to_str_pdal_class(tab_ground_class))
        | pdal.Filter.hag_nn()
        | pdal.Filter.range(limits="HeightAboveGround[0:0.5]")
    )
    return pipeline


def build_dtm_from_points(
    points, output_dtm: str, epsg: int, dtm_type: str, resolution: float
):
    """build a dtm from points - dtm_type (min, max, mean)"""
    pipeline = pdal.Writer.gdal(
        filename=output_dtm,
        resolution=resolution,
        output_type=dtm_type,
        where="(Classification == 2 || Classification == 66)",
        data_type="Float32",
    ).pipeline(points)
    pipeline.execute()
    utils_gdal.add_epsg_to_raster(output_dtm, epsg)


def build_dtm_from_las(
    input_las: str, output_dtm: str, epsg: int, dtm_type: str, resolution: float
):
    """build a dtm from las - dtm_type (min, max, mean)"""
    points_ini = read_las_file(input_las)
    return build_dtm_from_points(points_ini, output_dtm, epsg, dtm_type, resolution)
