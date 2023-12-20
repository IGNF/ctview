PROJECT_NAME=lidar_hd/ct_view
docker rmi -f `docker images | grep ${PROJECT_NAME} | tr -s ' ' | cut -d ' ' -f 3`