docker run --rm \
-v /var/data/store-lidarhd/developpement/ctview/las/data3:/input \
-v /var/data/store-lidarhd/developpement/ctview/tests_local_docker/test3:/output \
lidar_hd/ct_view \
python -m ctview.main -idir /input -odir /output
