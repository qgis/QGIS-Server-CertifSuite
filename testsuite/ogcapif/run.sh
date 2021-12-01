#! /bin/bash

OUTPUTDIR=/tmp/certifsuite-ogcapif
BRANCH=master

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
if [ ! -f data/QGIS-Training-Data/exercise_data/qgis-server-tutorial-data/world.qgs ]
then
  mkdir -p data
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
. venv/bin/activate
./pyogctest/pyogctest.py -p 8087 -n ogcapif_qgis -s ogcapif -v -u http://$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' qgisserver-certifsuite-nginx)/qgisserver -f html -o $OUTPUTDIR/ -c $COMMIT -b $VERSION
deactivate
mv $OUTPUTDIR/pyogctest_ogcapif.html $OUTPUTDIR/report.html

# clear containers
docker-compose stop
docker-compose rm -f
