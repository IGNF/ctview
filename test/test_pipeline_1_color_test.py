import pdal

FILENAME = 'LAS/pont_route_OK.las'
RESULT_FILENAME = "LAS_create/Result_color.las"
RASTER_FILNAME = "raster/Result_raster.tif"
DICO = 'dico/ramp.txt'
RASTERGDAL_NAME = "raster/Result_rastergdal.png"


COLOR1 = 'heat_map'
COLOR2 = 'blue_hue'

def read_las(file_las):
    """Read a las file and put it in an array"""
    pipeline = pdal.Pipeline() | pdal.Reader.las(filename=file_las)
    pipeline.execute()
    return pipeline.arrays[0]


def filter_las(points):
    classif = "Classification[6:6]"  # classif 6 = batiments
    pipeline = (
        pdal.Filter.range(limits=classif).pipeline(points)
        | pdal.Filter.hag_nn()
        | pdal.Filter.range(limits=classif)
    )
    pipeline.execute()
    return pipeline.arrays[0]


def filter_color_interp(points):
 #   classif = "Classification[6:6]"  # classif 6 = batiments
    pipeline = (
        pdal.Filter.colorinterp(ramp=COLOR2).pipeline(points)
    )
    pipeline.execute()
    return pipeline.arrays[0]

    
def filter_color(points):
 #   classif = "Classification[6:6]"  # classif 6 = batiments
    pipeline5 = (
        pdal.Filter.colorization(raster=TIFF_FILNAME).pipeline(points)
    )
    pipeline5.execute()
    return pipeline5.arrays[0]    


def write_raster(points):
    print('begin write_raster')
    pipeline = pdal.Writer.gdal(
        resolution=1.0,
        filename=RASTER_NAME,
        #output_type="mean",
        #where=f"Classification={2}",
        )
    
    print('execute')
    pipeline.execute()
    print('end write_raster')


def write(points):
    print("enter")
    class_choice = 2
    pipeline = (
        pdal.Writer.las(filename=RESULT_FILENAME, extra_dims="all").pipeline(points)


        | pdal.Writer.gdal(
        resolution=0.5,
        filename=RASTERGDAL_NAME,
        #output_type="mean",
        #where=f"Classification={1}",
        )
        )
    print("interm")
    pipeline.execute()
    print("out")

if __name__ == "__main__":

    

    points = read_las(FILENAME)
    print(points[0])
    filt_points = filter_color_interp(points)
    write(filt_points)
 #   filtered_points = filter_las(points)
 #   write(filtered_points)
