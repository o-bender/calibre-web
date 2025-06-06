# -*- coding: utf-8 -*-

#  This file is part of the Calibre-Web (https://github.com/janeczku/calibre-web)
#    Copyright (C) 2018 lemmsh, cervinko, OzzieIsaacs
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program. If not, see <http://www.gnu.org/licenses/>.

from lxml import etree
import base64


from . import isoLanguages, cover
from .constants import BookMeta

ISBN='/fb:FictionBook/fb:description/fb:publish-info/fb:isbn/text()'
PUBLISHER='/fb:FictionBook/fb:description/fb:publish-info/fb:publisher/text()'
LANG='/fb:FictionBook/fb:description/fb:title-info/fb:lang/text()'
SEQUENCE='/fb:FictionBook/fb:description/fb:title-info/fb:sequence'
DATE='/fb:FictionBook/fb:description/fb:title-info/fb:date/text()'

def get_cover(tmp_file_path, tree, ns) -> str:
    image_id = tree.xpath('/fb:FictionBook/fb:description/fb:title-info/fb:coverpage/fb:image/@l:href', namespaces=ns)
    if not image_id:
        return None

    image_b64 = tree.xpath(f'//*[@id="{image_id[0][1:]}"]/text()', namespaces=ns)
    if not image_b64:
        return None


    img_data = base64.b64decode(image_b64[0])


    return cover.cover_processing(tmp_file_path, img_data, image_id[0].split('.')[1])


def get_description(tree, ns) -> str:
    data = tree.xpath('/fb:FictionBook/fb:description/fb:title-info/fb:annotation', namespaces=ns)
    if data:
        return ''.join(data[0].itertext()).strip()

    data = tree.xpath('/fb:FictionBook/fb:description/fb:publish-info/fb:book-name/text()', namespaces=ns)
    if data:
        return str(data[0]).strip()
    return ''


def get_text(path, tree, ns):
    data = tree.xpath(path, namespaces=ns)
    if data:
        return str(data[0]).strip()

    return ''

def get_attribute(path, tree, ns, key):
    data = tree.xpath(path, namespaces=ns)
    if data:
        return data[0].get(key)

    return ''


def get_fb2_info(tmp_file_path, original_file_extension):
    ns = {
        'fb': 'http://www.gribuser.ru/xml/fictionbook/2.0',
        'l': 'http://www.w3.org/1999/xlink',
    }

    tree = etree.parse(tmp_file_path)

    authors = tree.xpath('/fb:FictionBook/fb:description/fb:title-info/fb:author', namespaces=ns)

    def get_author(element):
        last_name = element.xpath('fb:last-name/text()', namespaces=ns)
        if len(last_name):
            last_name = last_name[0]
        else:
            last_name = ''
        middle_name = element.xpath('fb:middle-name/text()', namespaces=ns)
        if len(middle_name):
            middle_name = middle_name[0]
        else:
            middle_name = ''
        first_name = element.xpath('fb:first-name/text()', namespaces=ns)
        if len(first_name):
            first_name = first_name[0]
        else:
            first_name = ''
        return (first_name + ' '
                + middle_name + ' '
                + last_name)

    author = str(", ".join(map(get_author, authors)))

    title = tree.xpath('/fb:FictionBook/fb:description/fb:title-info/fb:book-title/text()', namespaces=ns)
    if len(title):
        title = str(title[0])
    else:
        title = ''


    return BookMeta(
        file_path=tmp_file_path,
        extension=original_file_extension,
        title=title,
        author=author,
        cover=get_cover(tmp_file_path, tree, ns),
        description=get_description(tree, ns),
        tags="",
        series=get_attribute(SEQUENCE, tree, ns, "name"),
        series_id=get_attribute(SEQUENCE, tree, ns, "number"),
        languages=isoLanguages.get_lang3(get_text(LANG, tree, ns)),
        publisher=get_text(PUBLISHER, tree, ns),
        pubdate=get_text(DATE, tree, ns),
        identifiers=[
            ['isbn', get_text(ISBN, tree, ns)],
        ],
    )
