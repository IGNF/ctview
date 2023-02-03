# construit lidar_hd/ct_view
PROJECT_NAME=lidar_hd/ct_view
VERSION=`cat ../VERSION.md`

docker build -t $PROJECT_NAME -f Dockerfile .
docker tag $PROJECT_NAME $PROJECT_NAME:$VERSION
