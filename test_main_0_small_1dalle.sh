#!/bin/bash

# PARAMETERS
# paths
INPUT=/var/data/store-lidarhd/developpement/ctview/las/data0
OUTPUT=/var/data/store-lidarhd/developpement/ctview/1_tests_local/test0
# number of file in INPUT
NB_FILE_EXPECTED="1"
# folders
FOLDER_1=ADENS_FINAL
FOLDER_2=ACC_5_fusion_FINAL
FOLDER_3=ADTM_1M_color_FINAL
# folder expected
FOLDER_31=ADTM_1M_color_FINAL1c
FOLDER_32=ADTM_1M_color_FINAL2c
FOLDER_34=ADTM_1M_color_FINAL4c

# COMMAND TO TEST
python -m ctview.main \
-idir $INPUT  \
-odir $OUTPUT \
-ofdens $FOLDER_1 \
-ofcc $FOLDER_2 \
-ofcolor $FOLDER_3 \
-c 1 2 4

# VERIFICATIONS
echo
echo VERIFICATIONS

# verify density
nb_file_folder1=`find $OUTPUT/$FOLDER_1 -maxdepth 1 -type f | wc -l`

if [ "$nb_file_folder1" = "$NB_FILE_EXPECTED" ]; then
    echo "OK : density : number of files : $NB_FILE_EXPECTED expected $nb_file_folder1 obtained."
else
    echo "ERROR : density : number of files : $NB_FILE_EXPECTED expected $nb_file_folder1 obtained."
fi

# verify map of class
nb_file_folder2=`find $OUTPUT/$FOLDER_2 -maxdepth 1 -type f | wc -l`

if [ "$nb_file_folder2" = "$NB_FILE_EXPECTED" ]; then
    echo "OK : CC : number of files : $NB_FILE_EXPECTED expected $nb_file_folder2 obtained."
else
    echo "ERROR : CC : number of files : $NB_FILE_EXPECTED expected $nb_file_folder obtained."
fi

# verify DTM color
nb_file_folder31=`find $OUTPUT/$FOLDER_31 -maxdepth 1 -type f | wc -l`
nb_file_folder32=`find $OUTPUT/$FOLDER_32 -maxdepth 1 -type f | wc -l`
nb_file_folder34=`find $OUTPUT/$FOLDER_34 -maxdepth 1 -type f | wc -l`

if [ "$nb_file_folder31" = "$NB_FILE_EXPECTED" ] && [ "$nb_file_folder32" = "$NB_FILE_EXPECTED" ] && [ "$nb_file_folder34" = "$NB_FILE_EXPECTED" ]; then
    echo "OK : DTM color : number of files : $NB_FILE_EXPECTED expected $nb_file_folder31 obtained."
else
    echo "ERROR : DTM color : number of files : 1c : $NB_FILE_EXPECTED expected $nb_file_folder31 obtained."
    echo "ERROR : DTM color : number of files : 2c : $NB_FILE_EXPECTED expected $nb_file_folder32 obtained."
    echo "ERROR : DTM color : number of files : 4c : $NB_FILE_EXPECTED expected $nb_file_folder34 obtained."
fi

