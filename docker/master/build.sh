#! /bin/sh

BASEDIR=$(dirname "$0")
docker build ${BASEDIR} -t qgisserver-certifsuite/master-prepare
docker run --name certifsuite-master-build --rm --privileged -d -it qgisserver-certifsuite/master-prepare /bin/bash
docker exec certifsuite-master-build sh /root/qgis.sh
docker commit --change='CMD ["sh", "/root/cmd.sh"]' certifsuite-master-build qgisserver-certifsuite/master
docker stop certifsuite-master-build
sleep 5
docker rmi qgisserver-certifsuite/master-prepare
