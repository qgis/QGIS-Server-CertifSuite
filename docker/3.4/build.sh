#! /bin/sh

BASEDIR=$(dirname "$0")
docker build ${BASEDIR} -t qgisserver-certifsuite/3.4-prepare
docker run --name certifsuite-3.4-build --rm --privileged -d -it qgisserver-certifsuite/3.4-prepare /bin/bash
docker exec certifsuite-3.4-build sh /root/qgis.sh
docker commit --change='CMD ["sh", "/root/cmd.sh"]' certifsuite-3.4-build qgisserver-certifsuite/3.4
docker stop certifsuite-3.4-build
sleep 5
docker rmi qgisserver-certifsuite/3.4-prepare
