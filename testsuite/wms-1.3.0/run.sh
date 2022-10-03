#! /bin/bash
BRANCH=master
OUTPUTDIR=/tmp/certifsuite-wms130

# install pyogctest
if [ ! -f pyogctest/setup.py ]
then
  git clone https://github.com/pblottiere/pyogctest
  virtualenv -p /usr/bin/python3 venv
  . venv/bin/activate
  pip install -e pyogctest/
  deactivate
fi

# download data
if [ ! -f data/shapefile/Autos.shp ]
then
  . venv/bin/activate
  ./pyogctest/pyogctest.py -s wms130 -w
  deactivate
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
. venv/bin/activate
./pyogctest/pyogctest.py -p 8087 -n wms-130_qgis -s wms130 -v -u http://$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' qgisserver-certifsuite-nginx)/qgisserver -f html -o $OUTPUTDIR/ -c $COMMIT -b $VERSION
deactivate
mv $OUTPUTDIR/teamengine.html $OUTPUTDIR/report.html

curl "http://$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' qgisserver-certifsuite-nginx)/qgisserver?SERVICE=WMS&REQUEST=GetCapabilities" > $OUTPUTDIR/getcapabilities.xml

# clear containers
docker-compose stop
docker-compose rm -f
