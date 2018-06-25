#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import uuid
import subprocess
import base64
import time
import os
import shutil
from PIL import Image

GEOSERVER = 'http://cite.demo.opengeo.org:8080/geoserver_wms13/wms'


def run_cmd(cmd):
    print("Running command: " + ''.join(cmd))
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    print(out)
    print(err)
    return out, err


def clean():
    shutil.rmtree(OUTDIR, ignore_errors=True)
    os.makedirs(OUTDIR)


def run_teamengine():
    getcapa = ('{0}?queryable=queryable&basic=basic&recommended=recommended&capabilities-url={1}'
               .format(TEAMENGINE, QGISSERVER_GETCAPABILITIES))
    out, err = run_cmd(['wget', '-O', XML, getcapa])


def get_images(url):
    # build images' names according to the waited format defined in url
    f = ''
    if 'png' in url:
        f = 'png'
    elif 'jpeg' in url:
        f = 'jpeg'

    geoserver_img = '{2}/geoserver_{0}.{1}'.format(uuid.uuid4(), f, OUTDIR)
    qgisserver_img = '{2}/qgisserver_{0}.{1}'.format(uuid.uuid4(), f, OUTDIR)

    # build geoserver url
    geoserver_url = url.replace(QGISSERVER, GEOSERVER)

    # no styles for geoserver
    geoserver_url = geoserver_url.replace('StYlEs=default&', '')
    geoserver_url = geoserver_url.replace('STYLE=default&', '')
    geoserver_url = geoserver_url.replace('StYlEs=&', '')
    geoserver_url = geoserver_url.replace('StYlEs=default,,default,,&', '')
    geoserver_url = geoserver_url.replace('MAP=/home/user/teamengine_wms_130.qgs&', '')

    # no 'all' layers option for geoserver
    all_layers = 'cite:Streams,cite:RoadSegments,cite:Ponds,cite:NamedPlaces,cite:MapNeatline,cite:LakesWithElevation,cite:Lakes,cite:Forests,cite:DividedRoutes,cite:Buildings,cite:BuildingCenters,cite:Bridges,cite:BasicPolygons,cite:Autos'
    geoserver_url = geoserver_url.replace('LaYeRs=teamengine_wms_130', 'layers={}'.format(all_layers))

    # get images from geoserver and qgisserver
    out, err = run_cmd(['wget', '-O', qgisserver_img, url])
    out, err = run_cmd(['wget', '-O', geoserver_img, geoserver_url])

    # log images names with urls
    f = open(LOG, 'a')
    f.write('{} : {}\n'.format(qgisserver_img, url))
    f.write('{} : {}\n'.format(geoserver_img, geoserver_url))
    f.close()

    return [qgisserver_img, geoserver_img]


def html_header():
    return ('<p>\n'
            '  <b style="font-family: Verdana, sans-serif; color: #FF0000;">\n'
            '    Disclaimer:\n'
            '    all images coming from GeoServer should be valid because we\'re using a reference implementation for WMS 1.3.0 (see <a href="https://github.com/opengeospatial/cite/wiki/Reference-Implementations">here</a>). When QGIS supports operations not supported by GeoServer, then there is nothing to compare and this will raise a false failure.\n'
            '  </b>\n'
            '  <br/><br/>\n'
            '  <b style="font-family: Verdana, sans-serif; color: #000000;">\n'
            '    Exhaustive description for WMS 1.3.0 Test Suite: <a href="http://cite.opengeospatial.org/teamengine/about/wms/1.3.0/site/wms-1_3_0-ats.html">http://cite.opengeospatial.org/teamengine/about/wms/1.3.0/site/wms-1_3_0-ats.html</a>\n'
            '  </b>\n'
            '  <br/><br/>\n'
            '  <b style="font-family: Verdana, sans-serif; color: #000000;">\n'
            '    Metadata<br/>\n'
            '  </b>\n'
            '    &ensp;&ensp;&ensp;&ensp;Date: {}<br/>\n'
            '    &ensp;&ensp;&ensp;&ensp;Service: WMS<br/>\n'
            '    &ensp;&ensp;&ensp;&ensp;Version: 1.3.0<br/>\n'
            '    &ensp;&ensp;&ensp;&ensp;Tests: BASIC, QUERYABLE<br/>\n'
            '    &ensp;&ensp;&ensp;&ensp;SHA1: {}<br/>\n'
            '  </ul>\n'
            '</p>\n').format(time.strftime("%Y/%m/%d %H:%M"), HASH)


def html_table_images(img_qgisserver, img_geoserver):
    s = img_qgisserver.split('.')
    html = None

    if len(s) > 1:
        format = s[1]

        if format == 'png':
            i0 = base64.b64encode(open(img_qgisserver,'rb').read()).decode('utf-8')
            i1 = base64.b64encode(open(img_geoserver,'rb').read()).decode('utf-8')
        else:
            try:
                im = Image.open(img_qgisserver)
                im.save('/tmp/i0.png')
            except OSError:
                pass
            i0 = base64.b64encode(open('/tmp/i0.png','rb').read()).decode('utf-8')

            try:
                im = Image.open(img_geoserver)
                im.save('/tmp/i1.png')
            except OSError:
                pass
            i1 = base64.b64encode(open('/tmp/i1.png', 'rb').read()).decode('utf-8')

        i0_tag = ('<img src="data:image/{0};base64,{1}" align="center"/>'
                  .format(format, i0))
        i1_tag = ('<img src="data:image/{0};base64,{1}" align="center"/>'
                  .format(format, i1))

        html = ('<b>Images</b>'
                '<br/>'
                '<br/>'
                '<em>QGIS Server</em>'
                '<br/>'
                '<br/>'
                '<br/>'
                '{0}'
                '<br/>'
                '<br/>'
                '<br/>'
                '<em>Geo Server</em>'
                '<br/>'
                '<br/>'
                '<br/>'
                '{1}'
                '<br/>'
                '<br/>'
                '<br/>'
                .format(i0_tag, i1_tag))

    return html


def generate_html():
    out, err = run_cmd(['xmlstarlet', 'tr', 'tohtml.xsl', XML])
    out = out.decode("utf-8")

    next = False
    header = False
    url = ""
    seek = 0
    report_out = ""

    for l in out.splitlines(keepends=True):
        # clean line
        l = l.replace('&quot;', '"')
        l = l.replace('&amp;', '&')

        # extract URL for GetMap and GetLegendGraphic requests
        if next:
            l = l.replace(' ', '')
            if 'GetMap' in l or 'GetLegendGraphic' in l:
                url = l
                seek = 0

        if header:
            seek += 1
            if seek == 2:
                seek = 0
                header = False
                report_out += html_header()

        # add images into html report
        if url:
            seek += 1
            if seek == 5:
                imgs = get_images(url)
                url = ''
                html = html_table_images(imgs[0], imgs[1])
                if html:
                    report_out += html
                seek = 0

        # we should extract an url at the next line (or not)
        if 'URL' in l:
            next = True
        else:
            next = False

        if 'Test execution report' in l:
            header = True
        else:
            header = False

        report_out += l

    f = open(HTML, 'w')
    f.write(report_out)
    f.close()


if __name__ == '__main__':
    descr = 'Generate HTML report'
    parser = argparse.ArgumentParser(description=descr)
    parser.add_argument('outdir', metavar='outdir', type=str, help='Output directory')
    parser.add_argument('hash', metavar='hash', type=str, help='QGIS Hash')
    args = parser.parse_args()

    TEAMENGINE = 'http://localhost:8081/teamengine/rest/suites/wms/1.22/run'
    QGISSERVER = 'http://nginx/qgisserver_master'
    QGISSERVER_GETCAPABILITIES = ('{}?REQUEST=GetCapabilities%26SERVICE=WMS'
                                  '%26VERSION=1.3.0%26'
                                  'MAP=/data/teamengine_wms_130.qgs'
                                  .format(QGISSERVER))

    OUTDIR = args.outdir
    XML = '{}/report.xml'.format(OUTDIR)
    HTML = '{}/report.html'.format(OUTDIR)
    LOG = '{}/log.txt'.format(OUTDIR)

    HASH = args.hash

    clean()
    run_teamengine()
    generate_html()
