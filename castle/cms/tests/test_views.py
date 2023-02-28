# -*- coding: utf-8 -*-
from __future__ import division

import unittest
from math import ceil

import six
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import login
from plone.app.testing import setRoles
from plone.formwidget.namedfile.converter import b64encode_file
from plone.namedfile.file import NamedImage
from plone.namedfile.interfaces import INamedFile
from plone.registry.interfaces import IRegistry
from zExceptions import NotFound
from zope.component import getUtility

from castle.cms.browser.files.icon import FaviconView
from castle.cms.browser.files.icon import IconView
from castle.cms.testing import CASTLE_PLONE_INTEGRATION_TESTING


bimage = b'GIF89a=\x00D\x00\xf7\xa8\x00\x9a,3\xff\xc0\xc0\xef\xc0\xc0uXg\xfc\xf9\xf7\x993\x00\xff\xec\xec\xff\xa0\xa0\xe5\xcc\xbf\xcf\x9f\x87\x0f\xef\xef\x7f\x7f\x7f\xef\x0f\x0f\xdf\x1f\x1f\xff&&_\x9f\x9f\xffYY\xbf??5\xa5\xc2\xff\xff\xff\xac\x16\x19\xb2&\x00\xf8\x13\x10\xc2& \xdf`PP\x84\x9b\xf8\x03\x00\xb5\x0b\x0c\xdf\x0f\x00>\x9a\xb5\x87BM\x7f`P\xd2\xa5\x8f\xcc\x19\x00\xa5,\x00\xec\xd9\xcf\xe5\x0c\x00\xeb\t\x00\xff\xd9\xd9\xc7\x0c\x0c\x0f\x0f\x0f\xffyy~MZ\xfb\t\x08\xe5M@\xfb__\xff33\xcf\x90x\xf2\xe5\xdf\xc3\x06\x06\xbf\t\x08\xff\xb3\xb3\xd9\xb2\x9f\xff\x06\x06\xac)\x00\xff\xc6\xc6\x0c\t\x08\xf9\xf2\xef\xc9s`\xb8#\x00\x9f/\x00\xff__\xff\x8c\x8c\xc5\x1c\x00\xdf33\xffpp\xcf\x19\x19\xc0\x13\x10\xbf\x90x\xf7YY\xff\xf6\xf6\xe7??\xd7&&\xefLL2& \xdf\xbf\xaf\xbf\xbf\xbf???\xc5M@cn\x81_\x00\x00___\xcb00\xd8\x13\x00YC8\x80\x80\x80\xf3RRsVH\xc490\x10\x10\x10\x917@\xf2\x06\x00\xcf@@\xca\x86pooo\xa3!&\xc1\x1d\x18\xcf//\x1f\x1f\x1f\xdf\x00\x00\xd2\x16\x00\xcb\x90x\xbf\x1f\x00\x19\x13\x10\xf3\xd0\xd0\xe399&\x1d\x18Yy\x8e\x8f\x8f\x8f\xff\xa9\xa9\xcb\x13\x13\xbf00SF@\xb6& >\x1d\x18\xfb\xdd\xdd@@@\x99\x93\x90\xff\xbc\xbc\x7fPP\xaf\xaf\xaf\xc6VHzsp\x93& \xb7pp\xb3\x86ptPP|pp\xafOO\xd0\xd0\xd0\xef\xef\xefL90\xbc\xa9\xa0o0(\xeb\xb0\xb0\xff\xe0\xe0\xff\xd0\xd0\x870(K0(\xc9|h\x9f__lct\xebFF\xcf\xcf\xcf\xe0\xe0\xe0b& \xff  },(@0(\xa9\x93\x88\xa6|h\x1f\xdf\xdf\xd5\xac\x97\xe2\xc5\xb7\xc7`POOO\x9cyhppp\xff\x80\x80\xff\x96\x96\xd7``\xcc\x99\x7f,\xb0\xcf\xbf\x00\x00\x00\x00\x00\x00\xff\xff\xff\x00\x00\xffff\xff\xff\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00!\xf9\x04\x01\x00\x00\xa8\x00,\x00\x00\x00\x00=\x00D\x00\x00\x08\xff\x00Q\t\x1cH\xb0\xa0\xc1\x83\x08\x13*\\\xc8\xb0\xa1\xc0\x1b\x07\x0c8\x9cHq\xa1\x89\x14\xa72F\xac\xc8\xb1\xa2\t\x1f\x19Cj\x94\xd8\xb1$B\x03\x07D\xaa\x1ci\xb2%*#3V\xcad\xe9\xb2\xa2\x9d 3s\x9e\xdaX\x93!"\x8c:\x83\xf2\xeci\xf0c\xd0\xa3!\x87\x12E\x89\xb4iR\x92.a:\x9d\xfa\xb4\xe5\x0c\x9cT\xb3\xee\x84:\xf1\x06P\xad`\x95*4\n\xb6l\xd5\x84\x06>\x99]\x1b\xb2\xc5\x9c\x83F\xda\xb0\x9d{\xe4\x84\x00\x83W\xe7\xaeM\xe2f\xd4\xa8\xbb\x03\xbd\xea5kE\x88_\xbf\x80\x0fy\x1a\\\xb6\x08\x92\xc3\x87\x01\x070\xe5\x00\x02\xe3\xa9-\x80\xc4\x80\x1cY\xe0dS\x94-_\x0ezd3\xe7\xce\xa8>\x83\x0e=Zf\x92\x13\xa7Gm\x18 \xe1\xaf\xe7\xd5\xb8+\xb7\xceX8\xf6(\xda\xa2D\xd9N\x8d\xbb\xb8n\xc6\x8e}\x8f\xfa\x12<\xf8\xf0\xcf\x11\x1a\x14\x07}|mf\xdf\x00\x9elP\xd1\\\xb8dSaJ\x95\xffz }zu\xadiLs\xa6\xb0&8\x80\x01\xdd\x9f\x9b\x8a ^<\xf9\xe9\xac\xa9:\x82\x1d{\x83\x84\xe6\xef\xc5\xf7\x1d}\xf5\xd9W\x9eq\xa2\x1d\x95\x84a\xb1\xa9\xb0\x01\x00\xdd\x05\xd8\x9c|\x04\x16X\x8a\x02\x0b0\x80\x9f\x0b=\xe8\x94\\l\x1et \n\x00\x10\x02\x08\xdf\x84\x03ZX \x86\x1a\x16W\x03\x87+]\xe7[\x06\x00\x96\xe8\xde\x89\xce\xa5\xa8\xe2\x8a\x19N\xf7b\x87\x19\xa5\x17\x1b\x05\xa3P\x10\xa1\x8d#\xe2X\x9b\x8e;\xf2\xd8"n/\xd6\xd5\xdf\x13\xa2x\x80$\x89\x11\x9e\xd8\x81\x16\x146\xb9#\x8b\xd3\xf9\xe6\xc1\x7f\xa2\x0cp\xe5\x99\x12\xa8\x80\xdad\x15zi!\x98\xab\xf9Ff\x99gvG$g\xdf1\xa0\x80\x9bM\xc2\t\x19\x00\x19p\xd9\x9d\x99G6\xd7Hl\xdf\x99\xc2\xc8\x9e|~\t\x88)~Q@c\x99\xa3\x0cZg\x06\x00\xf8\x96\xa8)\x0c,\xc0h\xa3\x05^\x02\xe9(\x93Rji\x84\xcb)\'\x1fn\x9d~\nj)\xa3\x0e\xffZis\x84\x06\xd7\x81\xaak\xae\xc6\x01\x07\xa0\xb5\xfa*\xac~\xc9z\xaa\x04\x03l\x80+b\xb7\x81V@\x01$\xac\xd6\xe9\xab\xb1\xd2:kpj\x0ep\xe7\xb1\xab\x9aRA\x01!\x14\xd7\xc0\x03\x8dF\x1b\xdc\x00\xd3\x8ar-\xb6\xc8\x12\x07Z\t\x15\xf0:\xdd\xb7n\x8ak\xaa(\x1ddz\xac\x14\x86\x80\x92+~\xf8\xc1\xbb\xa3\xbc\xe4\xae\xe1\x01\xbaR\xfcAG\'\\\xa4\xab\x1a\xbf\xef\x82k\xa1\xbc\x03\xa3\xeb\xd7\x1d\xa4T\xcc\x87\xc2\xc5qP\x02\xc3\xab\xf9+\x9e\xb8OH\xec\xd7\x1bYTL\x8a\x1f~\xa1\x91\xecj"\xd8\xc01n\xfe\x8e\xdaA\x06\xe7\xa2;\t)Q\xb0AJ\x15\\\xa8\xbc2h!\x14\xe0\xee\xcb\xa05\x10\xc6\xa8"s&\x07\n\x13L\xb0sA\x0b\x9b\xa2\x81\x08"h\xf02\x0f\x15\xe0\x964g2\xa8\xd1D\xd3\xa4\xe8\x01\xf5t\x1c\x14`\xc6\xcb\xcbN\x11\xe7\xd6\x87]@\xca\xd7\x8f\x90\xf2\x01\x08#\x10t\x80$\xc5\x99\xc1-\xc7?\x14\xff@\xc6\xdal\x8f\xe2\x04)b0\xb1\t)}\x84\x12J&\x04\x05\x02\xc5\x18\xb8\xd9P\xc0\x0f\x1c\x93`5h\x81_\xb0H(j\x98\xacD( \xc0`P\xc5\x8f\x83\xa6\xc1\xb6;l1\x9d\x06\x1bk\x9d4\x18:(\x1e\n\x15&sR\xb7A9\xc0Q\xf1 \x18X\x00Z\xdf<\x84\xa0:h$H^\x1cgC\\\xa0\xdc\x10\x9a\xc8\xae8\x11gdQ\x07\x01\x07!\x10\n\x11W| {\xef\xa6\x90\xb0m\x01"T B\x01<\xa8\xed\xba_X|pE\x1e\xa7\xc9\xe0D\x19\xce\xcb\xbe\x04\xf5\x08\x11\x80@\x02\xf1+\xce}\t!\xecP\xc1\x0ed\xb8\xdc\xf9\x86\xa0\x88\x8aQA\x06\x90\xc1\x02\xfc\xf2G\x83\x1c4\xc4~\xf8\xcb\x1f\xf7^v\x98D\x98\x0c\x07\xca\x1b\xc5\x05\xba\x90\xbfP`Bt\x14\x81`\x07\'\xc8/\xbf\xc8@\toC\x01)\x9c\x00\xbb\x0e\xd2\xcd$"\x94\xa0\xef\xf0\xe3\x978\xe0l\x02^ \x05\x07\xf3\x97\x00\x04\xd0\xaf%1t\xde\x0b|X\xb0\x820\x8db\x0f\xa4`\xc2\x04\x16@\x8a\x0e\xce\x8f(\x02\t\xa2\xec\x86X\xc4\xb5\x15"\x898\xc4A\xfc\x1a\x08\xc5\x82HQqT\xc4\xdc("A\n<\x08\x02\x05\x94\x90\x1d\r@\xd8E\x83|1\x14T\xbc\x80\x0e>@\n\x14\x88An\xa0\xbb]\x1b\x13\xf2F\xd9Y\xc2dg\xe8\xe1\x1e\x1d\xd2\xc7P\xa0\x10\x07\x84\xf8\xe1 \x1fx\xbf\xfc\x11\xa1\x12\x90XdG\x82\xb8FI\x02q\t/\xb4\xa4&[\x12\x10\x00;'  # noqa E:501
# bimage default size is 61 X 68


class TestSiteIcon(unittest.TestCase):

    layer = CASTLE_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ('Member', 'Manager'))
        registry = getUtility(IRegistry)
        registry['plone.site_icon'] = b64encode_file('foobar.gif', bimage)
        self.view = IconView(self.portal, self.request)

    def get_icon_size(self):
        return self.view._getFile().getImageSize()

    def test_IconView_getFile_returns_NamedImage(self):
        self.assertTrue(
            isinstance(self.view._getFile(), NamedImage)
        )

    def test_get_site_icon_does_not_raise_overflow_error(self):
        self.request.form.update({
            'scale': '-3284239847329'
        })
        self.assertRaises(NotFound, self.view._getFile)

    def test_get_site_icon_raises_404(self):
        self.request.form.update({
            'scale': '555'
        })
        self.assertRaises(NotFound, self.view._getFile)

    def test_get_site_icon(self):
        self.request.form.update({
            'scale': '180'
        })
        result = self.view._getFile()
        self.assertTrue(INamedFile.providedBy(result))

    def test_get_site_icon_default_size(self):
        self.assertEqual(
            self.get_icon_size(),
            (61, 68),
        )

    def test_get_site_icon_downscales(self):
        allowed_downscaled_sizes = (
            16,
            32,
        )
        for size in allowed_downscaled_sizes:
            self.request.form.update({
                'scale': str(size),
            })
            scaled_size = int(ceil(size * 61 / 68))
            self.assertEqual(
                self.get_icon_size(),
                (scaled_size, size),
            )

    def test_get_site_icon_does_not_upscale(self):
        allowed_upscaled_sizes = (
            '150',
            '180',
            '192',
            '512',
        )
        for size in allowed_upscaled_sizes:
            self.request.form.update({
                'scale': size,
            })
            self.assertEqual(
                self.get_icon_size(),
                (61, 68),
            )

    def test_IconView_maintains_filename(self):
        filename = self.view.filename
        self.assertIsNotNone(filename)
        self.assertEqual(filename, 'icon.png')

    def test_IconView_filename_is_unicode(self):
        self.assertTrue(
            isinstance(self.view.filename, six.text_type)
        )


class TestFavicon(unittest.TestCase):

    layer = CASTLE_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ('Member', 'Manager'))
        registry = getUtility(IRegistry)
        registry['plone.site_icon'] = b64encode_file('foobar.gif', bimage)
        self.view = FaviconView(self.portal, self.request)

    def test_FaviconView_getFile_returns_NamedImage(self):
        self.assertTrue(
            isinstance(self.view._getFile(), NamedImage)
        )

    def test_FaviconView_maintains_filename(self):
        filename = self.view.filename
        self.assertIsNotNone(filename)
        self.assertEqual(filename, 'favicon.ico')

    def test_FaviconView_filename_is_unicode(self):
        self.assertTrue(
            isinstance(self.view.filename, six.text_type)
        )
