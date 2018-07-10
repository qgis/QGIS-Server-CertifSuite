#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import datetime
import os
import shutil
import docker


class Node(object):

    def __init__(self, line):
        self.level = 0

        for c in line:
            if c == ' ':
                self.level += 1
            else:
                break

        line = line[self.level:]
        self.level = int(self.level / 3)

        parts = line.split(' ')
        self.name = parts[1]
        self.id = parts[4].replace('(', '').replace(')', '')
        self.status = parts[5].replace('\n', '')

        self.color = '#e60000'
        if self.status == 'Passed':
            self.color = '#006600'

        self.message = ''
        self.method = 'get'
        self.url = ''

        self.childs = []
        self.__build_body()

    def __build_body(self):
        cont = container('qgisserver-certifsuite/teamengine-4')
        cmd = ('./bin/unix/viewlog.sh -logdir=/root/te_base/users/root/ {}'
               ).format(self.id)
        workdir = '/root/te_base'

        res = cont.exec_run(cmd, workdir=workdir)[1].decode('utf-8')
        self.body = res

        blocs = []
        bloc = ''
        for line in res.split('\n'):
            bloc += line + '\n'

            if not line:
                blocs.append(bloc)
                bloc = ''

        for bloc in blocs:
            if 'Assertion' in bloc:
                bloc = bloc.replace('Assertion: ', '')
                self.assertion = bloc

            if 'Request' in bloc:
                self.method = 'get'

                for line in bloc.split('\n'):
                    if 'URL' in line:
                        url = line.replace('   URL: ', '')
                        self.url = url.replace('&', '&<br>')
                        break

            if 'Response from parser' in bloc:
                for line in bloc.split('\n')[3:]:
                    self.message += line + '\n'

    def content(self):
        result = ('<b style="font-family: Verdana, sans-serif; '
                  'color: {};"> {}</b>'
                  ).format(self.color, self.status)

        subtests = ''
        if self.childs:
            subtests = ('<p><h4>Executed tests</h4>'
                        '<ul>\n')
            for c in self.childs:
                subtests += ('<li>'
                             '<a href="">{}</a><b style="font-family: '
                             'Verdana, sans-serif; color: {};"> {}</b>'
                             '</li>').format(c.name, c.color, c.status)

        request = ''
        if self.url and not self.childs:
            request = ('<p><h4>Submitted request</h4><pre>\n'
                       '<b><em>Method</em></b>\n'
                       'get\n\n'
                       '<b><em>URL</em></b>\n'
                       '{}'
                       '</pre></p>\n'
                       .format(self.url))

        message = ''
        if self.message and not self.childs and self.status == 'Failed':
            message = ('<p><h4>Message</h4>'
                       '<pre>'
                       '{}'
                       '</pre></p>'
                       ).format(self.message)

        body = ('<div class="test">\n'
                '<h2><a name="">test: {}</a></h2>'
                '<p><h4>Assertion</h4>{}</p>'
                '<p><h4>Test result</h4>{}</p>'
                '{}'
                '{}'
                '{}'
                '</div>\n'
                ).format(self.name, self.assertion, result, subtests,
                         request, message)

        return body

    def toc(self):
        toc = ''
        for c in self.childs:
            toc += c.toc()

        href = ('<a href="">{}</a><b style="font-family: Verdana, '
                'sans-serif; color: {};"> {}</b>'
                ).format(self.name, self.color, self.status)

        toc = ('<ul>\n'
               '  <li>\n'
               '    {0}\n'
               '    {1}\n'
               '  </li>\n'
               '</ul>').format(href, toc)

        return toc


def container(image):
    cont = None
    client = docker.from_env()

    for c in client.containers.list():
        if c.attrs['Config']['Image'] == image:
            cont = c

    return cont


def generate_html(outdir, version, commit):

    # get log from docker container
    cont = container('qgisserver-certifsuite/teamengine-4')

    cmd = './bin/unix/viewlog.sh -logdir=/root/te_base/users/root/ -session=s0001'
    workdir = '/root/te_base'
    res = cont.exec_run(cmd, workdir=workdir)[1].decode('utf-8')

    # build a tree
    nodes = []
    for line in res.split('\n'):
        if not line:
            continue

        node = Node(str(line))
        nodes.append(node)

    # hierarchical sort
    for i in range(len(nodes)-1, -1, -1):
        level = nodes[i].level

        for j in range(i, -1, -1):
            if nodes[j].level == level - 1:
                nodes[j].childs.insert(0, nodes[i])
                break

    # body
    cont = ''
    for node in nodes:
        cont += node.content()

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

                # date
                color_tag = '{{TEMPLATE_RESULT_COLOR}}'
                status_tag = '{{TEMPLATE_RESULT_STATUS}}'
                if color_tag in line:
                    line = line.replace(color_tag, nodes[0].color)
                    line = line.replace(status_tag, str(nodes[0].status))

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
                    line = nodes[0].toc()

                # body
                body_tag = '{{TEMPLATE_BODY}}'
                if body_tag in line:
                    line = cont

                outfile.write(line)


def clean(outdir):
    shutil.rmtree(outdir, ignore_errors=True)
    os.makedirs(outdir)


if __name__ == '__main__':
    descr = 'Generate HTML report'
    parser = argparse.ArgumentParser(description=descr)
    parser.add_argument('outdir', metavar='outdir', type=str,
                        help='Output directory')
    parser.add_argument('version', metavar='version', type=str,
                        help='QGIS Version')
    parser.add_argument('hash', metavar='hash', type=str, help='QGIS Hash')
    args = parser.parse_args()

    clean(args.outdir)
    generate_html(args.outdir, args.version, args.hash)
    shutil.copy('style.css', args.outdir)
