from ctview.main import get_las_liste
import os
import pytest

DIR_LAS = os.path.join("data","las","2_LAS")
IN_LAS = os.path.join(DIR_LAS,"numero1.las")
ALL_LAS = ["numero2.las","numero1.las"]

def test_get_las_liste_LAS():
    las_liste, in_dir = get_las_liste(input_las=IN_LAS, input_dir=None)
    assert las_liste == ["numero1.las"]
    assert in_dir == DIR_LAS

def test_get_las_liste_DIR():
    las_liste, in_dir = get_las_liste(input_las=None, input_dir=DIR_LAS)
    assert set(las_liste) == set(ALL_LAS)
    assert in_dir == DIR_LAS