#
# Script to test upgrading from one version of castle/plone to another.
#
# How this works:
#  - read instance script for list of default path modules
#  - download new versions
#  - generate new instance scripts with custom versions
#  - create sites based on different versions
#  - run `upgrade-sites` script
#
import json
import os
import shutil
import stat
import subprocess

import requests


dir_path = os.path.dirname(os.path.realpath(__file__))


DOWNLOAD_LOCATIONS = {
    'castle.cms': 'https://github.com/castlecms/castle.cms/archive/{version}.zip',
    'Products.CMFPlone': 'https://github.com/plone/Products.CMFPlone/archive/{version}.zip',
    'plone.app.upgrade': 'https://github.com/plone/plone.app.upgrade/archive/{version}.zip',
    'mockup': 'https://github.com/plone/mockup/archive/{version}.zip'
}

PACKAGE_DIRECTORY = os.path.join(dir_path, 'packages')
SCRIPTS_DIR = os.path.join(dir_path, 'castle', 'cms', '_scripts')
CREATE_SITE_SCRIPT = os.path.join(SCRIPTS_DIR, 'create-site.py')

TEST_VERSIONS = {
    '2.0.45': {
        'registry': {
            'plone.backend_url': 'foobar.com'
        },
        'packages': {
            'Products.CMFPlone': '5.0.8',
            'mockup': '2.4.1',
            'plone.app.upgrade': '2.0.4'
        }
    },
    '2.1.0': {
        'packages': {
            'Products.CMFPlone': '5.0.8',
            'plone.app.upgrade': '2.0.4',
            'mockup': '2.4.1',
        }
    },
    '2.2.0': {
        'packages': {
            'Products.CMFPlone': '5.0.8',
            'plone.app.upgrade': '2.0.4'
        }
    },
    '2.3.0': {
        'packages': {
            'Products.CMFPlone': '5.0.8',
            'plone.app.upgrade': '2.0.4'
        }
    }
}
PKG_EXTRA = '-py2.7.egg'


def output(txt):
    print('[\033[1;33mCastle Test\033[0m]: {}'.format(txt))


def download_package(name, version, env):
    if not os.path.exists(PACKAGE_DIRECTORY):
        os.mkdir(PACKAGE_DIRECTORY)

    result_filepath = os.path.join(
        PACKAGE_DIRECTORY, '{}-{}'.format(name, version))

    if os.path.exists(result_filepath + PKG_EXTRA):
        # already downloaded...
        return

    filepath = '{}.zip'.format(result_filepath)
    if not os.path.exists(filepath):
        url = DOWNLOAD_LOCATIONS[name].format(version=version)
        output('Downloading {}'.format(url))
        resp = requests.get(url)
        with open(filepath, 'wb') as fi:
            fi.write(resp.content)

    subprocess.check_output([
        'unzip',
        filepath,
        '-d',
        PACKAGE_DIRECTORY
    ])
    os.remove(filepath)

    # copy egg info over...
    original_egg_info = os.path.join(env['packages'][name]['path'], 'EGG-INFO')
    if os.path.exists(original_egg_info):
        new_egg_info = os.path.join(result_filepath, 'EGG-INFO')
        shutil.copytree(original_egg_info, new_egg_info)

    shutil.move(result_filepath, result_filepath + PKG_EXTRA)


def download_packages(env):
    for castle_version, data in TEST_VERSIONS.items():
        versions = data['packages']
        download_package('castle.cms', castle_version, env)
        for name, version in versions.items():
            download_package(name, version, env)


def get_package_environment():
    with open('bin/instance') as fi:
        fidata = fi.read()

    packages = {}
    for line in fidata.splitlines():
        if not line.startswith("  '"):
            continue
        path = line.strip().strip("',")
        path_name = path.split('/')[-1].rsplit('-', 1)[0]
        name, _, version = path_name.partition('-')
        packages[name] = {
            'version': version,
            'line': line,
            'path': path
        }
    return {
        'script': fidata,
        'packages': packages
    }


def get_bins(env):
    for castle_version in TEST_VERSIONS.keys():
        script = munge_py_env(env['script'], castle_version, env)
        yield castle_version, script


def munge_py_env(script, castle_version, env):
    packages = env['packages']
    script = script.replace(
        packages['castle.cms']['line'],
        "  '{}',".format(
            os.path.join(
                PACKAGE_DIRECTORY, 'castle.cms-{}{}'.format(castle_version, PKG_EXTRA))))
    for name, version in TEST_VERSIONS[castle_version]['packages'].items():
        script = script.replace(
            packages[name]['line'],
            "  '{}',".format(
                os.path.join(
                    PACKAGE_DIRECTORY, '{}-{}{}'.format(name, version, PKG_EXTRA))))
    script = script.replace(
        'parts/instance/etc/zope.conf',
        'parts/instance_{}/etc/zope.conf'.format(castle_version))
    return script


def build_instances(env):
    for version, instance_bin in get_bins(env):
        # build bin file
        filepath = 'bin/instance_{}'.format(version)
        with open(filepath, 'w') as fi:
            fi.write(instance_bin)
        st = os.stat(filepath)
        os.chmod(filepath, st.st_mode | stat.S_IEXEC)

        # copy new parts directory
        parts_path = os.path.join('parts', 'instance_{}'.format(version))
        if os.path.exists(parts_path):
            shutil.rmtree(parts_path)
        shutil.copytree('parts/instance', parts_path)

        zope_conf_filepath = os.path.join(parts_path, 'etc', 'zope.conf')
        with open(zope_conf_filepath) as fi:
            zope_conf = fi.read()
        zope_conf = zope_conf.replace('/parts/instance', '/parts/instance_{}'.format(version))
        with open(zope_conf_filepath, 'w') as fi:
            fi.write(zope_conf)

        interp_filepath = os.path.join(parts_path, 'bin', 'interpreter')
        with open(interp_filepath) as fi:
            interp = fi.read()
        interp = munge_py_env(interp, version, env)
        with open(interp_filepath, 'w') as fi:
            fi.write(interp)
        st = os.stat(interp_filepath)
        os.chmod(interp_filepath, st.st_mode | stat.S_IEXEC)


def build_sites(env):
    for version, instance_bin in get_bins(env):
        filepath = 'bin/instance_{}'.format(version)
        output('Creating site for {}'.format(version))
        env = os.environ.copy()
        env.update({
            'REGISTRY_DATA': json.dumps(
                TEST_VERSIONS[version].get('registry', {})
            )
        })
        process = subprocess.Popen([
            filepath,
            'run',
            CREATE_SITE_SCRIPT,
            '--site-id=Castle_{}'.format(version),
            '--delete=true'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        out, err = process.communicate()
        if process.returncode != 0:
            # so we know why we errored out, return output here...
            print(out)
            print(err)
            raise Exception(
                'Invalid status code {}'.format(process.returncode))


def run():
    env = get_package_environment()
    download_packages(env)
    build_instances(env)
    build_sites(env)

    # test running upgrades now
    for version in TEST_VERSIONS.keys():
        output('Run upgrade for {}'.format(version))
        process = subprocess.Popen([
            'bin/upgrade-sites',
            '--site-id=Castle_{}'.format(version),
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = process.communicate()
        if process.returncode != 0:
            print(out)
            print(err)
            raise Exception(
                'Invalid status code {}'.format(process.returncode))
        output('Upgrade successful for {}'.format(version))


if __name__ == '__main__':
    run()
