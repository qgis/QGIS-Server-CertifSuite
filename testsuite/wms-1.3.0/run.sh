#! /bin/bash

# download data
URL=http://cite.opengeospatial.org/teamengine/about/wms/1.3.0/site/
OUTPUTDIR=/tmp/certifsuite-wms130

if [ ! -f data/shapefile/Autos.shp ]
then
  cd data
  wget $URL/data-wms-1.3.0.zip
  unzip data-wms-1.3.0.zip
  rm data-wms-1.3.0.zip
  cd -
fi

# start servers
docker-compose up -d
sleep 30

# get metadata
VERSION=$(docker exec -it qgisserver-certifsuite-master sh -c 'cd /root/QGIS/ && git rev-parse --symbolic-full-name --abbrev-ref HEAD')
COMMIT=$(docker exec -it qgisserver-certifsuite-master sh -c 'cd /root/QGIS/ && git rev-parse HEAD')

# run tests
rm -rf $OUTPUTDIR
mkdir -p $OUTPUTDIR
python3 report.py $OUTPUTDIR $VERSION $COMMIT

# clear containers
docker-compose stop
docker-compose rm -f
