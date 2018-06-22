#! /usr/bin/env bash

BASEDIR=$(dirname $(realpath -s $0))

cd ${BASEDIR}/master && sh build.sh
cd ${BASEDIR}/teamengine-4 && sh build.sh
