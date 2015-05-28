#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import Counter
from errno import ENOENT
from stat import S_IFDIR, S_IFREG
from sys import argv, exit
import os
import re

from fuse import FUSE, FuseOSError, Operations
from lxml import etree


if not hasattr(__builtins__, 'bytes'):
    bytes = str


def _to_xpath(path):
    """Return an xpath query corresponding to the filesystem path.

    >>> _to_xpath('/node1/node2')
    "/*[local-name() = 'node1']/*[local-name() = 'node2']"
    >>> _to_xpath('/node[4]')
    "/*[local-name() = 'node'][4]"

    A trailing slash in the path will add an astrisk to the xpath query
    so that it will find a node's children, similar to a directory
    listing.

    >>> _to_xpath('/node/')
    "/*[local-name() = 'node']/*"

    Only slashes will return a query that lists elements in the top level.

    >>> _to_xpath('/')
    '/*'
    >>> _to_xpath('//')
    '/*'
    """

    # If the path ends with a slash we want to generate a query that
    # gives us a listing.  In that case we'll add an asterisk at the
    # end.
    listing = (path[-1] == '/')

    path = path.strip('/')
    if not path:
        return '/*'

    components = []
    for name in path.split('/'):
        # Extract into name and index if possible, e.g.
        # tagname[42] -> name='tagname' index='[42]'
        # tagname     -> name='tagname' index=None
        name, index = re.match(r'(.*?)(\[\d+\])?$', name).groups()
        components.append("*[local-name() = '{}']{}".format(name, index or ''))

    if listing:
        components.append('*')

    return '/' + '/'.join(components)


class XmlFs(Operations):
    def __init__(self, filename):
        with open(filename) as f:
            self.file_contents = f.read()
        self.root = etree.fromstring(self.file_contents)
        self.stat = os.stat(filename)
        self.fd = 0

    def _query(self, path):
        return self.root.xpath(_to_xpath(path))

    def _all_tags(self, path):
        """Return generator iterating through all tags under path."""
        for child in self.root.xpath(_to_xpath(path + '/')):
            yield child.xpath('local-name()')

    def _fileattr(self, size):
        return dict(st_mode=(S_IFREG | 420),  # octal: 644
                    st_nlink=1, st_size=size,
                    st_ctime=self.stat.st_ctime,
                    st_mtime=self.stat.st_mtime,
                    st_atime=self.stat.st_atime)

    def _dirattr(self, links):
        return dict(st_mode=(S_IFDIR | 493),  # octal: 755
                    st_nlink=links, st_size=0,
                    st_ctime=self.stat.st_ctime,
                    st_mtime=self.stat.st_mtime,
                    st_atime=self.stat.st_atime)

    def _get_contents(self, path):
        path = path[:-10]  # Remove '/#contents'
        if path == '':
            return self.file_contents
        else:
            return etree.tostring(self._query(path)[0])

    def getattr(self, path, fh=None):
        if path.endswith('/#contents'):
            size = len(self._get_contents(path))
            return self._fileattr(size)

        if not self._query(path):
            raise FuseOSError(ENOENT)

        num_subtags = sum(1 for _ in self._all_tags(path))
        links = num_subtags + 3  # 3 is for ., .., and #contents
        return self._dirattr(links)

    def open(self, path, flags):
        self.fd += 1
        return self.fd

    def read(self, path, size, offset, fh):
        return bytes(self._get_contents(path)[offset:offset + size])

    def readdir(self, path, fh):
        dirs = []
        for tag, count in Counter(self._all_tags(path)).items():
            if count == 1:
                dirs.append(tag)
            else:
                dirs.extend("{}[{}]".format(tag, i + 1) for i in range(count))
        return ['.', '..', '#contents'] + dirs

    def statfs(self, path):
        return dict(f_bsize=512, f_blocks=4096, f_bavail=2048)


if __name__ == '__main__':
    if len(argv) != 3:
        print('usage: {} <xml-file> <mountpoint>'.format(argv[0]))
        exit(1)

    FUSE(XmlFs(filename=argv[1]), mountpoint=argv[2], foreground=True)
