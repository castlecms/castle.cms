from castle.cms._scripts.utils import get_js_resource_object
from castle.cms._scripts.utils import get_module_dir
from castle.cms._scripts.utils import get_url_resource_object
from castle.cms._scripts.utils import recursive_resources
from castle.cms._scripts.utils import remove_extension
from castle.cms._scripts.utils import resource_to_path, get_resource_object
from castle.cms.cron.utils import get_sites
from castle.cms.cron.utils import setup_site
from plone.registry.interfaces import IRegistry
from Products.CMFPlone.interfaces import IBundleRegistry
from Products.CMFPlone.interfaces import IResourceRegistry
from zope.component import getUtility

import castle.cms
import json
import mockup
import os
import plone.app.mosaic
import plone.app.portlets
import plonetheme.barceloneta
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


for rkey, resource in resources.items():
    js_object = get_js_resource_object(site, resource)
    if js_object:
        webpack_aliases[rkey] = remove_extension(resource_to_path(js_object))
    url_object = get_url_resource_object(site, resource)
    if url_object:
        fs_path = resource_to_path(url_object)
        webpack_aliases[rkey + '-url'] = fs_path
        webpack_aliases.update(recursive_resources(rkey + '-url', fs_path))
    for css in resource.css:
        css_obj = get_resource_object(site, css)
        if css_obj:
            if '.less' in css:
                webpack_aliases[rkey + '.less'] = resource_to_path(css_obj)
            else:
                webpack_aliases[rkey + '.css'] = resource_to_path(css_obj)


for bkey, bundle in bundles.items():
    if bundle.compile:
        js_requires = []
        css_requires = []
        build_filename = os.path.join(WORK_DIR, '{}-build.js'.format(bkey))
        less_build_filename = os.path.join(
            WORK_DIR, '{}-build.less'.format(bkey))
        for resource_key in bundle.resources:
            js_object = get_js_resource_object(site, resources[resource_key])
            if js_object:
                bfilepath = resource_to_path(js_object)
                js_requires.append(bfilepath)
            for css in resources[resource_key].css:
                css_obj = get_resource_object(site, css)
                css_requires.append(resource_to_path(css_obj))
        bundles_config[bkey] = build_filename
        with open(build_filename, 'w') as fi:
            fi.write('\n'.join(['require("' + f + '");' for f in js_requires]))
        with open(less_build_filename, 'w') as fi:
            fi.write('@import "{}/variables.less";\n'.format(WORK_DIR))
            for css_require in css_requires:
                # the less plugin doesn't like absolute paths? wahhhhh?
                parts = css_require.split('/')
                filename = parts[-1]
                alias_name = '{}-{}-dir'.format(
                    bkey, filename.replace('.', '-'))
                webpack_aliases[alias_name] = '/'.join(parts[:-1])
                fi.write('@import "{}/{}";\n'.format(
                    webpack_aliases[alias_name], filename))


webpack_aliases.update({
    'webpack-build': WORK_DIR,
    'bower': os.path.join(CMFPlone_DIR, 'static/components'),
    'mockup': os.path.join(get_module_dir(mockup), 'patterns'),
    'plone': os.path.join(CMFPlone_DIR, 'static'),
    'mockup-less': os.path.join(get_module_dir(mockup), 'less')
})
webpack_config_data = {
    'cmfplone': CMFPlone_DIR,
    'static': os.path.join(CMFPlone_DIR, 'static'),
    'bower': os.path.join(CMFPlone_DIR, 'static/components'),
    'mockup': get_module_dir(mockup),
    'mosaic': get_module_dir(plone.app.mosaic),
    'barceloneta': get_module_dir(plonetheme.barceloneta),
    'castle': os.path.join(get_module_dir(castle.cms), 'static'),
    'aliases': jdump(webpack_aliases)
}
less_config = {
    'globalVars': {
        'bowerPath': add_quotes(webpack_aliases['bower'] + '/'),
        'mockupPath': add_quotes(webpack_aliases['mockup']),
        'staticPath': add_quotes(webpack_aliases['plone']),
        'fontsPrefix': add_quotes(webpack_aliases['plone'] + '/fonts/'),
        'mockuplessPath': add_quotes(webpack_aliases['mockup-less'])
    }
}

with open(os.path.join(SCRIPT_DIR, 'templates/variables.less')) as fi:
    tmpl = fi.read()
    with open(os.path.join(WORK_DIR, 'variables.less'), 'w') as output:
        output.write(tmpl % webpack_aliases)


with open(os.path.join(SCRIPT_DIR, 'templates/webpack.globals.js')) as fi:
    tmpl = fi.read()
    with open(os.path.join(WORK_DIR, 'webpack.globals.js'), 'w') as output:
        output.write(tmpl % webpack_config_data)


with open(os.path.join(SCRIPT_DIR, 'templates/watchable-grunt.js')) as fi:
    tmpl = fi.read()
    with open('watchable-grunt.js', 'w') as output:
        output.write(tmpl % webpack_config_data)


with open(os.path.join(SCRIPT_DIR, 'templates/webpack.config.js')) as fi:
    tmpl = fi.read()
    with open('webpack.config.js', 'w') as output:
        output.write(tmpl % {
            'bundles_config': jdump(bundles_config),
            'bundles_keys': jdump(bundles_config.keys()),
            'common': 'common',

            # XXX not currently used
            'less_globals': jdump(less_config),
            'output': jdump({
                "pathinfo": True,
                "path": os.path.join(get_module_dir(castle.cms), 'static'),
                "filename": '[name]-compiled.min.js',
                "sourceMapFilename": '[name].map'
            })
        })


with open(os.path.join(SCRIPT_DIR, 'templates/package.json')) as fi:
    tmpl = fi.read()
    with open('package.json', 'w') as output:
        output.write(tmpl)


with open(os.path.join(SCRIPT_DIR, 'templates/Makefile')) as fi:
    tmpl = fi.read()
    with open('Makefile', 'w') as output:
        output.write(tmpl)

print('generate original grunt file')

with open(os.path.join(CMFPlone_DIR, '_scripts/_generate_gruntfile.py')) as fi:
    code = fi.read()
    exec(code, globals(), locals())
# __import__('Products.CMFPlone._scripts._generate_gruntfile',
#            globals(), locals())
