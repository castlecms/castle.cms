# -*- coding: utf-8 -*-
import unittest


class TestVHM(unittest.TestCase):

    def setUp(self):
        import transaction
        from Testing.makerequest import makerequest
        from Testing.ZopeTestCase.ZopeLite import app
        transaction.begin()
        self.app = makerequest(app())
        if 'virtual_hosting' not in self.app.objectIds():
            # If ZopeLite was imported, we have no default virtual
            # host monster
            from Products.SiteAccess.VirtualHostMonster \
                import manage_addVirtualHostMonster
            manage_addVirtualHostMonster(self.app, 'virtual_hosting')
        self.app.manage_addFolder('folder')
        self.app.folder.manage_addDTMLMethod('doc', '')
        self.app.REQUEST.set('PARENTS', [self.app])
        self.traverse = self.app.REQUEST.traverse

    def tearDown(self):
        import transaction
        transaction.abort()
        self.app._p_jar.close()

    def test_url_with_host_header(self):
        req = self.app.REQUEST
        req.environ['HTTP_HOST'] = 'www.foobar.com'
        self.traverse('/folder/doc')
        self.assertEqual(self.app.REQUEST['ACTUAL_URL'],
                         'http://www.foobar.com/folder/doc')
        self.assertEqual(self.app.folder.doc.absolute_url(),
                         'http://www.foobar.com/folder/doc')

    def test_url_with_scheme_header(self):
        req = self.app.REQUEST
        req.environ['HTTP_X_SCHEME'] = 'https'
        self.traverse('/folder/doc')
        self.assertEqual(self.app.REQUEST['ACTUAL_URL'],
                         'https://foo/folder/doc')
        self.assertEqual(self.app.folder.doc.absolute_url(),
                         'https://foo/folder/doc')

    def test_url_with_scheme_and_host_header(self):
        req = self.app.REQUEST
        req.environ['HTTP_X_SCHEME'] = 'https'
        req.environ['HTTP_HOST'] = 'www.foobar.com'
        self.traverse('/folder/doc')
        self.assertEqual(self.app.REQUEST['ACTUAL_URL'],
                         'https://www.foobar.com/folder/doc')
        self.assertEqual(self.app.folder.doc.absolute_url(),
                         'https://www.foobar.com/folder/doc')
