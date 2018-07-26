#! /bin/sh

echo "Remove docker images for master"
echo "------------------------------"
docker rmi qgisserver-certifsuite/master

echo "Build new docker image for master"
echo "---------------------------------"
cd docker/master && sh build.sh && cd -

echo "Run OGC tests for WMS 1.3.0"
echo "---------------------------"
cd wms-1.3.0/ && sh run.sh && cd -

echo "Run OGC tests for WFS 1.1.0"
echo "---------------------------"
cd wfs-1.1.0/ && sh run.sh && cd -
