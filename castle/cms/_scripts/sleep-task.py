import logging
import os

from AccessControl.SecurityManagement import newSecurityManager
from plone import api
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from tendo import singleton
from zope.component.hooks import setSite

from castle.cms.gelf import GELFHandler


logger = logging.getLogger("Plone")


SCHEMA_VERSION = "1"
SCHEMA_TYPE = "UserGroupMatrix"
APP_NAME = "castle.cms"
gelflogger = logging.getLogger(SCHEMA_TYPE)
gelfhandler = GELFHandler()
gelfformatter = logging.Formatter("%(asctime)s %(name)s [%(levelname)s] %(message)s")
gelfhandler.setFormatter(gelfformatter)
gelflogger.addHandler(gelfhandler)

def run(app):
    
    user = app.acl_users.getUser('admin')
    newSecurityManager(None, user.__of__(app.acl_users))

    from castle.cms.tasks.sleep import add
    add.delay(2, 2)
    import pdb; pdb.set_trace()


def setup_and_run():
    conf_path = os.getenv("ZOPE_CONF_PATH", "parts/instance/zope.conf")
    if conf_path is None or not os.path.exists(conf_path):
        raise Exception('Could not find zope.conf at {}'.format(conf_path))

    from Zope2 import configure
    configure(conf_path)
    import Zope2
    app = Zope2.app()
    from Testing.ZopeTestCase.utils import makerequest
    app = makerequest(app)
    app.REQUEST['PARENTS'] = [app]
    from zope.globalrequest import setRequest
    setRequest(app.REQUEST)
    from AccessControl.SpecialUsers import system as user
    from AccessControl.SecurityManagement import newSecurityManager
    newSecurityManager(None, user)

    run(app)


if __name__ == '__main__':
    run(app)  # noqa: F821
