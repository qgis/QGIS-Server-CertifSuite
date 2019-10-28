#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import argparse
import datetime
import subprocess
import xml.etree.ElementTree as ET


class Class(object):

    def __init__(self, name):
        self.name = name.split('.')[-1]
        self.link = "https://opengeospatial.github.io/ets-wfs30/apidocs/{}".format(name.replace('.', '/'))
        self.methods = []

    def dump(self):
        print("Class: ")
        print("  - name: {}".format(self.name))
        print("  - link: {}".format(self.link))
        print("  - passed: {}".format(self.status()))

        for m in self.methods:
            m.dump()

    def status(self):

        passed = True
        for m in self.methods:
            passed &= m.passed()

        if passed:
            return "Passed"
        else:
            return "Fail"

    def color(self):
        if self.status() == "Passed":
            return "#006600"
        else:
            return "#e60000"

    def toc(self):
        href = ('<a href="#">{}</a><b style="font-family: Verdana, '
                'sans-serif; color: {};"> {}</b>'
               ).format(self.name, self.color(), self.status())

        t = ''
        for m in self.methods:
            t += m.toc()

        toc = ('<ul>\n'
           '  <li>\n'
           '    {0}\n'
           '    {1}\n'
           '  </li>\n'
           '</ul>').format(href, t)

        return toc


class Method(object):

    def __init__(self, name, status):
        self.name = name

        self.status = "Passed"
        if status == "FAIL":
            self.status = "Failed"
        elif status == "SKIP":
            self.status = "Skipped"

    def dump(self):
        print("    - {}: {}".format(self.name, self.status))

    def passed(self):
        if self.status == 'FAIL':
            return False
        else:
            return True

    def color(self):
        if self.status == "Passed":
            return "#006600"
        elif self.status == "Skipped":
            return "#ffa500"
        else:
            return "#e60000"

    def toc(self):
        href = ('<a href="#">{}</a><b style="font-family: Verdana, '
                'sans-serif; color: {};"> {}</b>'
               ).format(self.name, self.color(), self.status)

        toc = ('<ul>\n'
           '  <li>\n'
           '    {0}\n'
           '  </li>\n'
           '</ul>').format(href)

        return toc


class Toc(object):

    def __init__(self, classes):
        self.classes = classes

    def toc(self):
        toc = ''

        for cl in self.classes:
            toc += cl.toc()

        return toc

    def status(self):

        status = "Passed"

        for cl in self.classes:
            if cl.status != "Passed":
                status = "Failed"

        return status

    def color(self):
        if self.status() == "Passed":
            return "#006600"
        else:
            return "#e60000"


def run_cmd(cmd):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    out, err = p.communicate()
    return out, err


def clean(outdir):
    shutil.rmtree(outdir, ignore_errors=True)
    os.makedirs(outdir)


def run_teamengine(xml, teamengine_url, getcapabilities_url):
    getcapa = ('{0}?iut={1}'
               .format(teamengine_url, getcapabilities_url))
    out, err = run_cmd('wget --header="Accept: application/xml" -O {} {}'.format(xml, getcapa))


def generate_html(xml, outdir, version, commit):
    # parse xml
    tree = ET.parse(xml)
    tests = tree.find('suite').find('test')

    classes = []
    for test in tests:
        cl = Class(test.attrib['name'])
        for ch in test:
            m = Method(ch.attrib['name'], ch.attrib['status'])
            cl.methods.append(m)
        classes.append(cl)

    toc = Toc(classes)

    # generate html
    outpath = os.path.join(outdir, 'report.html')
    with open('template.html', 'r') as infile:
        with open(outpath, 'w') as outfile:
            for line in infile:
                # date
                date_tag = '{{TEMPLATE_DATE}}'
                if date_tag in line:
                    format = '%Y-%m-%d %H:%M:%S'
                    date = datetime.datetime.now().strftime(format)
                    line = date

                # overall result
                color_tag = '{{TEMPLATE_RESULT_COLOR}}'
                status_tag = '{{TEMPLATE_RESULT_STATUS}}'
                if color_tag in line:
                    line = line.replace(color_tag, toc.color())
                    line = line.replace(status_tag, toc.status())

                # version
                version_tag = '{{TEMPLATE_VERSION}}'
                if version_tag in line:
                    line = line.replace(version_tag, version)

                # commit
                commit_tag = '{{TEMPLATE_COMMIT}}'
                if commit_tag in line:
                    line = line.replace(commit_tag, commit)

                # toc
                toc_tag = '{{TEMPLATE_TOC}}'
                if toc_tag in line:
                    line = toc.toc()

                # # body
                # body_tag = '{{TEMPLATE_BODY}}'
                # if body_tag in line:
                #     line = cont

                outfile.write(line)


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

    # clean(outdir)
    # run_teamengine(xml, teamengine_url, getcapabilities_url)
    generate_html(xml, outdir, args.version, args.hash)
    shutil.copy('style.css', outdir)
    shutil.copy('logo.png', outdir)
