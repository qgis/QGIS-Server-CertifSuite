#! /bin/bash

URL=http://cite.opengeospatial.org/teamengine/about/wms/1.3.0/site/
OUTPUTDIR=/tmp/certifsuite-ogcapif
BRANCH=master

if [ ! -f data/QGIS-Training-Data/exercise_data/qgis-server-tutorial-data/world3.qgs ]
then
  cd data
  git clone https://github.com/qgis/QGIS-Training-Data
  cd -
fi

# start servers
export COMPOSE_INTERACTIVE_NO_CLI=1
docker-compose up -d
sleep 30

# get metadata
VERSION=$(docker exec -i qgisserver-certifsuite-$BRANCH sh -c 'cd /root/QGIS/ && git rev-parse --symbolic-full-name --abbrev-ref HEAD')
COMMIT=$(docker exec -i qgisserver-certifsuite-$BRANCH sh -c 'cd /root/QGIS/ && git rev-parse HEAD')

# run tests
rm -rf $OUTPUTDIR
mkdir -p $OUTPUTDIR
python3 report.py $OUTPUTDIR $VERSION $BRANCH $COMMIT

# clear containers
docker-compose stop
docker-compose rm -f
