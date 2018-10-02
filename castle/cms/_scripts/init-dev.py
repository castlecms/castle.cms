from castle.cms._scripts.utils import get_module_dir
from castle.cms.cron.utils import get_sites
from castle.cms.cron.utils import setup_site
from plone.registry.interfaces import IRegistry
from Products.CMFPlone.interfaces import IBundleRegistry
from Products.CMFPlone.interfaces import IResourceRegistry
from zope.component import getUtility

import castle.cms
import json
import os
import Products.CMFPlone


DIR = os.path.dirname(os.path.realpath(__file__))
WORK_DIR = os.path.join(os.getcwd(), 'devtools')


if not os.path.exists(WORK_DIR):
    os.mkdir(WORK_DIR)


def jdump(data):
    return json.dumps(data, sort_keys=True,
                      indent=4, separators=(',', ': '))


def add_quotes(ss):
    return '"' + ss + '"'


SCRIPT_DIR = os.path.join(get_module_dir(castle.cms), '_scripts')
CMFPlone_DIR = get_module_dir(Products.CMFPlone)

webpack_aliases = {}
bundles_config = {}


for site in get_sites(app):  # noqa
    setup_site(site)
    os.environ['SITE_ID'] = site.getId()
    break


registry = getUtility(IRegistry)
bundles = registry.collectionOfInterface(
    IBundleRegistry, prefix="plone.bundles", check=False)
resources = registry.collectionOfInterface(
    IResourceRegistry, prefix="plone.resources", check=False)


with open(os.path.join(SCRIPT_DIR, 'templates/watchable-grunt.js')) as fi:
    tmpl = fi.read()
    with open('watchable-grunt.js', 'w') as output:
        output.write(tmpl % {
            'castle': os.path.join(get_module_dir(castle.cms), 'static')
        })


with open(os.path.join(SCRIPT_DIR, 'templates/package.json')) as fi:
    tmpl = fi.read()
    with open('package.json', 'w') as output:
        output.write(tmpl)


with open(os.path.join(SCRIPT_DIR, 'templates/Makefile')) as fi:
    tmpl = fi.read()
    with open('Makefile', 'w') as output:
        output.write(tmpl)


with open(os.path.join(SCRIPT_DIR, 'templates/watch-run.py')) as fi:
    tmpl = fi.read()
    with open('watch-run.py', 'w') as output:
        output.write(tmpl)


print('generate original grunt file')

with open(os.path.join(CMFPlone_DIR, '_scripts/_generate_gruntfile.py')) as fi:
    code = fi.read()
    exec(code, globals(), locals())
# __import__('Products.CMFPlone._scripts._generate_gruntfile',
#            globals(), locals())
