#! /bin/bash

# download data
URL=http://cite.opengeospatial.org/teamengine/about/wms/1.3.0/site/
OUTPUTDIR=/tmp/certifsuite-wms130
BRANCH=master

if [ ! -f data/shapefile/Autos.shp ]
then
  cd data
  wget $URL/data-wms-1.3.0.zip
  unzip data-wms-1.3.0.zip
  rm data-wms-1.3.0.zip
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

curl "http://localhost:8089/qgisserver_$BRANCH?MAP=/data/teamengine_wms_130.qgs&SERVICE=WMS&REQUEST=GetCapabilities" > $OUTPUTDIR/getcapabilities.xml

# clear containers
docker-compose stop
docker-compose rm -f
