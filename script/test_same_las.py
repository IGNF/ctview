import pdal
import sys
import tools
import utils_pdal

LAS1 = '/home/ELucon/Bureau/ctView/test_raster/DTM_Laplace/DTM/Semis_2021_0843_6521_LA93_IGN69_ground.las'
LAS2 = '/home/ELucon/Bureau/ctView/test_raster/DTM_Laplace/DTM/Semis_2021_0843_6521_LA93_IGN69_ground_interp.las'


def test_same():

    pts1 = tools.read_las(LAS1)
    pts2 = tools.read_las(LAS2)

    info1 = utils_pdal.get_info_from_las(pts1)
    info2 = utils_pdal.get_info_from_las(pts2)

    assert info1 == info2



