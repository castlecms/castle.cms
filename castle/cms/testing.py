from castle.cms import install
from plone.app.robotframework.testing import PloneRobotFixture
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import MOCK_MAILHOST_FIXTURE
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.testing import z2
from Products.CMFPlone.resources.browser.combine import combine_bundles
from Products.CMFPlone.testing import PRODUCTS_CMFPLONE_ROBOT_REMOTE_LIBRARY_FIXTURE  # noqa
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from zope.configuration import xmlconfig
from zope.globalrequest import clearRequest
from zope.globalrequest import setRequest
from ZPublisher import HTTPResponse

import os


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

    def setUpPloneSite(self, portal):
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


class SeleniumCastleLayer(CastleLayer):
    defaultBases = (z2.ZSERVER_FIXTURE, PLONE_FIXTURE)

    def testSetUp(self):
        # Start up Selenium
        driver = os.environ.get('SELENIUM_DRIVER', '').lower() or 'firefox'
        webdriver = __import__(
            'selenium.webdriver.%s.webdriver' % driver, fromlist=['WebDriver'])
        args = [arg.strip() for arg in
                os.environ.get('SELENIUM_ARGS', '').split()
                if arg.strip()]
        kwargs = {}
        if 'FIREFOX_BINARY' in os.environ:
            log_fi = open('/opt/plone/selenium.log', 'w')
            kwargs['firefox_binary'] = FirefoxBinary(
                os.environ['FIREFOX_BINARY'],
                log_file=log_fi)
        self['selenium'] = webdriver.WebDriver(*args, **kwargs)

    def testTearDown(self):
        self['selenium'].quit()
        del self['selenium']


class CastleRobotLayer(PloneRobotFixture):
    pass


CASTLE_FIXTURE = CastleLayer()
CASTLE_PLONE_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(CASTLE_FIXTURE, MOCK_MAILHOST_FIXTURE),
    name="CastleTesting:Functional")
CASTLE_PLONE_INTEGRATION_TESTING = IntegrationTesting(
    bases=(CASTLE_FIXTURE, MOCK_MAILHOST_FIXTURE),
    name="CastleTesting:Integration")

CASTLE_ROBOT_FIXTURE = CastleRobotLayer()
CASTLE_ROBOT_TESTING = FunctionalTesting(
    bases=(CASTLE_ROBOT_FIXTURE, CASTLE_FIXTURE, MOCK_MAILHOST_FIXTURE, z2.ZSERVER_FIXTURE),
    name="CastleTesting:Robot"
)


SELENIUM_FIXTURE = SeleniumCastleLayer()
SELENIUM_PLONE_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(SELENIUM_FIXTURE, CASTLE_FIXTURE, MOCK_MAILHOST_FIXTURE),
    name="SeleniumTesting:Functional")
