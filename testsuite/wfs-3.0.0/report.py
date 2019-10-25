#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import subprocess
import datetime
import os
import shutil


def run_cmd(cmd):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    return out, err


def clean(outdir):
    shutil.rmtree(outdir, ignore_errors=True)
    os.makedirs(outdir)


def run_teamengine(xml, teamengine_url, getcapabilities_url):
    getcapa = ('{0}?iut={1}'
               .format(teamengine_url, getcapabilities_url))
    out, err = run_cmd(['wget', '-O', xml, getcapa])


def generate_html(xml, html, version, commit):
    out, err = run_cmd(['xmlstarlet', 'tr', 'tohtml.xsl', xml])
    out = out.decode("utf-8")

    report_out = ''

    for line in out.splitlines(keepends=True):
        # clear line
        line = line.replace('&quot;', '"')
        line = line.replace('&amp;', '&')

        # date
        date_tag = '{{TEMPLATE_DATE}}'
        if date_tag in line:
            format = '%Y-%m-%d %H:%M:%S'
            date = datetime.datetime.now().strftime(format)
            line = date

        # version
        version_tag = '{{TEMPLATE_VERSION}}'
        if version_tag in line:
            line = line.replace(version_tag, version)

        # commit
        commit_tag = '{{TEMPLATE_COMMIT}}'
        if commit_tag in line:
            commit_link = 'https://github.com/qgis/QGIS/commit/{}'.format(commit)
            commit_link_tag = '%7BTEMPLATE_COMMIT_LINK%7D'
            line = line.replace(commit_link_tag, commit_link)
            line = line.replace(commit_tag, commit)

        report_out += line

    f = open(html, 'w')
    f.write(report_out)
    f.close()


if __name__ == '__main__':
    descr = 'Generate HTML report'
    parser = argparse.ArgumentParser(description=descr)
    parser.add_argument('outdir', metavar='outdir', type=str,
                        help='Output directory')
    parser.add_argument('version', metavar='version', type=str,
                        help='QGIS Version')
    parser.add_argument('branch', metavar='branch', type=str,
                        help='QGIS Branch')
    parser.add_argument('hash', metavar='hash', type=str, help='QGIS Hash')
    args = parser.parse_args()

    teamengine_url = 'http://localhost:8090/teamengine/rest/suites/wfs30/run'
    qgisserver_url = 'http://nginx/qgisserver_{}/wfs3'.format(args.branch)
    getcapabilities_url = ('{}?MAP=/data/teamengine_wms_130.qgs'
                           .format(qgisserver_url))

    outdir = args.outdir
    xml = '{}/report.xml'.format(outdir)
    html = '{}/report.html'.format(outdir)
    log = '{}/log.txt'.format(outdir)

    clean(outdir)
    run_teamengine(xml, teamengine_url, getcapabilities_url)
    generate_html(xml, html, args.version, args.hash)
    shutil.copy('style.css', outdir)
    shutil.copy('logo.png', outdir)
