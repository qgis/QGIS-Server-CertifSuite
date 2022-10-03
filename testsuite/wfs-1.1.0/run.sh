#! /bin/bash

# download data
URL=https://cite.opengeospatial.org/teamengine/about/wms13/1.3.0/site/
OUTPUTDIR=/tmp/certifsuite-wfs110

if [ ! -f data/shapefile/Autos.shp ]
then
  cd data
  wget $URL/data-wms-1.3.0.zip
  unzip data-wms-1.3.0.zip
  rm data-wms-1.3.0.zip
  cd -
fi

if [ ! -f venv/bin/activate ]
then
  virtualenv -p /usr/bin/python3 venv
fi
. venv/bin/activate
pip install -r requirements.txt

# start servers
export COMPOSE_INTERACTIVE_NO_CLI=1
docker-compose up -d
sleep 30

# get metadata
VERSION=$(docker exec -i qgisserver-certifsuite-master sh -c 'cd /root/QGIS/ && git rev-parse --symbolic-full-name --abbrev-ref HEAD')
COMMIT=$(docker exec -i qgisserver-certifsuite-master sh -c 'cd /root/QGIS/ && git rev-parse HEAD')

# run tests
rm -rf $OUTPUTDIR
mkdir -p $OUTPUTDIR

docker exec -i qgisserver-certifsuite-teamengine sh -c 'cd /root/te_base && ./bin/unix/test.sh -source=wfs/1.1.0/ctl/main.ctl -form=/root/params.xml' > /dev/null 2>&1
# docker exec -it qgisserver-certifsuite-teamengine sh -c 'cd /root/te_base && ./bin/unix/viewlog.sh -logdir=/root/te_base/users/root/ -session=s0001'

python3 report.py $OUTPUTDIR $VERSION $COMMIT
curl "http://localhost:8089/qgisserver_master?MAP=/data/teamengine_wfs_110.qgs&SERVICE=WFS&REQUEST=GetCapabilities" > $OUTPUTDIR/getcapabilities.xml
cp logo.png $OUTPUTDIR/

deactivate

# clear containers
docker-compose stop
docker-compose rm -f
