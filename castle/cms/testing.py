import re

import transaction
from castle.cms import install
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import MOCK_MAILHOST_FIXTURE
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import applyProfile
from plone.app.testing.bbb import PloneTestCase
from plone.testing import z2
from Products.CMFPlone.resources.browser.combine import combine_bundles
from zope.configuration import xmlconfig
from zope.globalrequest import clearRequest
from zope.globalrequest import setRequest
from ZPublisher import HTTPResponse


class CastleLayer(PloneSandboxLayer):
    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Fix subrequest not fallbacking to wrong encoding in test environment:
        HTTPResponse.default_encoding = 'utf-8'

        import plone.app.contenttypes
        self.loadZCML(package=plone.app.contenttypes)

        import castle.cms
        import castle.cms.tests
        xmlconfig.file('configure.zcml',
                       castle.cms,
                       context=configurationContext)
        xmlconfig.file('configure.zcml',
                       castle.cms.tests,
                       context=configurationContext)

    def setUpPloneSite(self, portal, retried=False):
        # Configure five.globalrequest
        portal.REQUEST['PARENTS'] = [portal.__parent__]
        setRequest(portal.REQUEST)

        # Install into Plone site using portal_setup
        applyProfile(portal, 'plone.app.contenttypes:default')
        applyProfile(portal, 'plone.app.mosaic:default')
        applyProfile(portal, 'castle.cms:default')
        portal.portal_workflow.setDefaultChain('simple_publication_workflow')
        install.tiles(portal, portal.REQUEST)
        combine_bundles(portal)
        transaction.commit()

        # Clear globalrequest
        clearRequest()


CASTLE_FIXTURE = CastleLayer()
CASTLE_PLONE_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(CASTLE_FIXTURE, MOCK_MAILHOST_FIXTURE),
    name="CastleTesting:Functional")
CASTLE_PLONE_INTEGRATION_TESTING = IntegrationTesting(
    bases=(CASTLE_FIXTURE, MOCK_MAILHOST_FIXTURE),
    name="CastleTesting:Integration")


CASTLE_ROBOT_TESTING = FunctionalTesting(
    bases=(CASTLE_FIXTURE, REMOTE_LIBRARY_BUNDLE_FIXTURE, z2.ZSERVER_FIXTURE),
    name="CastleTesting:Robot"
)


class ResponseWrapper:
    '''Decorates a response object with additional introspective methods.'''

    _bodyre = re.compile('\r\n\r\n(.*)', re.MULTILINE | re.DOTALL)

    def __init__(self, response, outstream, path):
        self._response = response
        self._outstream = outstream
        self._path = path

    def __getattr__(self, name):
        return getattr(self._response, name)

    @property
    def output(self):
        '''Returns the complete output, headers and all.'''
        return self._outstream.getvalue()

    @property
    def body(self):
        '''Returns the page body, i.e. the output par headers.'''
        body = self._bodyre.search(self.getOutput())
        if body is not None:
            body = body.group(1)
        return body

    @property
    def path(self):
        '''Returns the path used by the request.'''
        return self._path

    @property
    def status_code(self):
        return self._response.getStatus()

    def getHeader(self, name):
        '''Returns the value of a response header.'''
        return self.headers.get(name.lower())

    def getCookie(self, name):
        '''Returns a response cookie.'''
        return self.cookies.get(name)


class BaseTest(PloneTestCase):
    layer = CASTLE_PLONE_FUNCTIONAL_TESTING

    def setUp(self):
        super().setUp()
        self.portal = self.layer['portal']
        self.request = self.layer['request']
