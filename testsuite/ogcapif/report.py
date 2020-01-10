#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import argparse
import datetime
import subprocess
import xml.etree.ElementTree as ET

COLOR_PASSED="#006600"
COLOR_SKIPPED="#ffa500"
COLOR_FAILED="#e60000"

class Class(object):

    def __init__(self, name):
        self.name = name.split('.')[-1]
        self.link = "https://opengeospatial.github.io/ets-wfs30/apidocs/{}".format(name.replace('.', '/'))
        self.description = "Test the {} class according to the API described <a href=\"{}\">here</a>.".format(self.name, self.link)
        self.methods = []
        self.id = self.name

    @property
    def status(self):

        passed = True
        for m in self.methods:
            passed &= m.passed

        if passed:
            return "Passed"
        else:
            return "Fail"

    @property
    def color(self):
        if self.status == "Passed":
            return COLOR_PASSED
        else:
            return COLOR_FAILED

    def toc(self):
        href = ('<a href="#{}">{}</a><b style="font-family: Verdana, '
                'sans-serif; color: {};"> {}</b>'
               ).format(self.id, self.name, self.color, self.status)

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

    def body(self):

        body_methods = ""
        for m in self.methods:
            body_methods += m.body(self.name, self.link)

        result = ('<b style="font-family: Verdana, sans-serif; '
                  'color: {};"> {}</b>'
        ).format(self.color, self.status)

        subtests = ''
        if self.methods:
            subtests = ('<p><h4>Executed tests</h4>'
                        '<ul>\n')
            for m in self.methods:
                subtests += ('<li>'
                             '<a name="{}">{}</a><b style="font-family: '
                             'Verdana, sans-serif; color: {};"> {}</b>'
                             '</li>').format(m.id, m.name, m.color, m.status)
            subtests += "</ul>"

        body = ('<div class="test">\n'
        '<h2><a name="{}">test: {}</a></h2>'
        '<p><h4>Assertion</h4>{}</p>'
        '<p><h4>Test result</h4>{}</p>'
        '{}'
        '{}'
        '</div>\n'
        ).format(self.name, self.name, self.description, result, subtests, body_methods)

        return body


class Method(object):

    def __init__(self, name, status, description, exception, message):
        self.name = name
        self.exception = exception
        self.message = message
        self.description = description
        self.id = self.name

        self.status = "Passed"
        if status == "FAIL":
            self.status = "Failed"
        elif status == "SKIP":
            self.status = "Skipped"

    @property
    def passed(self):
        if self.status == 'FAIL':
            return False
        else:
            return True

    @property
    def color(self):
        if self.status == "Passed":
            return COLOR_PASSED
        elif self.status == "Skipped":
            return COLOR_SKIPPED
        else:
            return COLOR_FAILED

    def toc(self):
        href = ('<a href="#{}">{}</a><b style="font-family: Verdana, '
                'sans-serif; color: {};"> {}</b>'
               ).format(self.id, self.name, self.color, self.status)

        toc = ('<ul>\n'
           '  <li>\n'
           '    {0}\n'
           '  </li>\n'
           '</ul>').format(href)

        return toc

    def body(self, classname, link):
        result = ('<b style="font-family: Verdana, sans-serif; '
                  'color: {};"> {}</b>'
        ).format(self.color, self.status)

        description = self.description
        if not description:
            description = "Test {}.{} method.".format(classname, self.name)

        reporter = "There is nothing to report."
        if self.status != "Passed":
            reporter = "{}: {}".format(self.exception, self.message)

        body = ('<div class="test">\n'
        '<h2><a name="{}">test: {}.{}</a></h2>'
        '<p><h4>Assertion</h4>{}</p>'
        '<p><h4>Test result</h4>{}</p>'
        '<p><h4>Message</h4>{}</p>'
        '</div>\n'
        ).format("id", classname, self.name, description, result, reporter)

        return body

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
            return COLOR_PASSED
        else:
            return COLOR_FAILED


class Body(object):

    def __init__(self, toc):
        self.toc = toc

    def body(self):

        body = ''

        for cl in self.toc.classes:
            body += cl.body()

        return body


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
            description = ''
            if 'description' in ch.attrib:
                description = ch.attrib['description']

            exception = ""
            message = ""
            for cc in ch:
                if 'exception' in cc.tag:
                    exception = cc.attrib['class']
                    for ccc in cc:
                        if 'message' in ccc.tag:
                            message = ccc.text

            m = Method(ch.attrib['name'], ch.attrib['status'], description, exception, message)
            cl.methods.append(m)
        classes.append(cl)

    toc = Toc(classes)
    body = Body(toc)

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
                body_tag = '{{TEMPLATE_BODY}}'
                if body_tag in line:
                    line = body.body()

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

    teamengine_url = 'http://localhost:8090/teamengine/rest/suites/ogcapi-features-1.0/run'
    qgisserver_url = 'http://nginx/qgisserver_{}/wfs3'.format(args.branch)

    outdir = args.outdir
    xml = '{}/report.xml'.format(outdir)
    html = '{}/report.html'.format(outdir)
    log = '{}/log.txt'.format(outdir)

    clean(outdir)
    run_teamengine(xml, teamengine_url, qgisserver_url)
    generate_html(xml, outdir, args.version, args.hash)
    shutil.copy('style.css', outdir)
    shutil.copy('logo.png', outdir)
