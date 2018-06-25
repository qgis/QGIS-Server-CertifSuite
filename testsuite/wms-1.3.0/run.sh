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

# run tests
rm -rf $OUTPUTDIR
mkdir -p $OUTPUTDIR
./report.py $OUTPUTDIR bloublo

# clear containers
docker-compose stop
docker-compose rm -f
