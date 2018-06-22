#! /bin/bash

BASEDIR=$(dirname "$0")
docker build ${BASEDIR} -t qgisserver-certifsuite/teamengine-4
