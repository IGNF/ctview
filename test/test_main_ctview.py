import os

from ctview.main_ctview import get_las_liste

DIR_LAS = os.path.join("data", "las", "2_LAS")
IN_LAS = os.path.join(DIR_LAS, "numero1.las")
ALL_LAS = ["numero2.las", "numero1.las"]
DIR_LAS2 = "/var/data/store-lidarhd/developpement/ctview/las/data0b"
IN_LAS2 = os.path.join(DIR_LAS2, "Semis_2021_0785_6378_LA93_IGN69_light.laz")
DIR_LAS3 = "./data/laz/one_micro_laz"
IN_LAS3 = os.path.join(DIR_LAS3, "Semis_2021_0785_6378_LA93_IGN69_light.laz")


def test_get_las_liste_LAS():
    las_liste, in_dir = get_las_liste(input_las=IN_LAS, input_dir=None)
    assert las_liste == ["numero1.las"]
    assert in_dir == DIR_LAS


def test_get_las_liste_LAS2():
    las_liste, in_dir = get_las_liste(input_las=IN_LAS2, input_dir=None)
    assert las_liste == ["Semis_2021_0785_6378_LA93_IGN69_light.laz"]
    assert in_dir == DIR_LAS2


def test_get_las_liste_LAS3():
    las_liste, in_dir = get_las_liste(input_las=IN_LAS3, input_dir=None)
    assert las_liste == ["Semis_2021_0785_6378_LA93_IGN69_light.laz"]
    assert in_dir == DIR_LAS3


def test_get_las_liste_DIR():
    las_liste, in_dir = get_las_liste(input_las=None, input_dir=DIR_LAS)
    assert set(las_liste) == set(ALL_LAS)
    assert in_dir == DIR_LAS


def test_get_las_liste_DIR2():
    las_liste, in_dir = get_las_liste(input_las=None, input_dir=DIR_LAS2)
    assert set(las_liste) == set(["Semis_2021_0785_6378_LA93_IGN69_light.laz"])
    assert in_dir == DIR_LAS2
