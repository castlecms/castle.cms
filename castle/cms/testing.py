import base64
import json
import re
import sys
import unittest
from cStringIO import StringIO

import transaction
from castle.cms import install
from plone.app.robotframework import AutoLogin
from plone.app.robotframework import RemoteLibraryLayer
from plone.app.robotframework.content import Content
from plone.app.robotframework.genericsetup import GenericSetup
from plone.app.robotframework.i18n import I18N
from plone.app.robotframework.mailhost import MockMailHost
from plone.app.robotframework.quickinstaller import QuickInstaller
from plone.app.robotframework.server import Zope2ServerRemote
from plone.app.robotframework.users import Users
from plone.app.testing import MOCK_MAILHOST_FIXTURE
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import applyProfile
# from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
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

        # Clear globalrequest
        clearRequest()


CASTLE_FIXTURE = CastleLayer()
CASTLE_PLONE_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(CASTLE_FIXTURE, MOCK_MAILHOST_FIXTURE),
    name="CastleTesting:Functional")
CASTLE_PLONE_INTEGRATION_TESTING = IntegrationTesting(
    bases=(CASTLE_FIXTURE, MOCK_MAILHOST_FIXTURE),
    name="CastleTesting:Integration")


CASTLE_BUNDLE_FIXTURE = RemoteLibraryLayer(
    bases=(PLONE_FIXTURE,),
    libraries=(
        AutoLogin,
        QuickInstaller,
        GenericSetup,
        Content,
        Users,
        I18N,
        MockMailHost,
        Zope2ServerRemote,
    ),
    name="CastleBundleRobot:RobotRemote",
)


CASTLE_ROBOT_TESTING = RemoteLibraryLayer(
    bases=(CASTLE_FIXTURE, z2.ZSERVER_FIXTURE, CASTLE_BUNDLE_FIXTURE),
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


class BaseTest(unittest.TestCase):
    layer = CASTLE_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']

    def publish(self, path, basic=None, env=None, extra=None,
                request_method='GET', content=None, handle_errors=True,
                username=None, password=None):
        """
        Mostly pulled from Testing.functional
        """
        from ZPublisher.Request import Request
        from ZPublisher.Response import Response
        from ZPublisher.Publish import publish_module

        transaction.commit()

        if env is None:
            env = {}
        if extra is None:
            extra = {}

        env['SERVER_NAME'] = self.request['SERVER_NAME']
        env['SERVER_PORT'] = self.request['SERVER_PORT']
        env['REQUEST_METHOD'] = request_method

        p = path.split('?')
        if len(p) == 1:
            env['PATH_INFO'] = p[0]
        elif len(p) == 2:
            [env['PATH_INFO'], env['QUERY_STRING']] = p
        else:
            raise TypeError('')

        if basic:
            env['HTTP_AUTHORIZATION'] = "Basic %s" % base64.encodestring(basic)
        elif username is not None and password is not None:
            env['HTTP_AUTHORIZATION'] = "Basic %s" % base64.encodestring('{}:{}'.format(
                username, password
            ))

        stdin = StringIO()
        if content is not None:
            if type(content) in (list, dict):
                content = json.dumps(content)
            stdin.write(content)
            stdin.seek(0)

        outstream = StringIO()
        response = Response(stdout=outstream, stderr=sys.stderr)
        request = Request(stdin, env, response)
        if extra:
            # Needed on Plone 3 when adding things to the path in a querystring
            # is not enough.
            for key, value in extra.items():
                request[key] = value

        publish_module('Zope2',
                       debug=not handle_errors,
                       request=request,
                       response=response)

        return ResponseWrapper(response, outstream, path)
