# construit lidar_hd/ct_view
PROJECT_NAME=lidar_hd/ct_view
VERSION=`cd .. && python -m ctview._version`

docker build --no-cache -t $PROJECT_NAME -f Dockerfile .
docker tag $PROJECT_NAME $PROJECT_NAME:$VERSION
