import os
import argparse
import sys
import subprocess
import Zope2
import glob
from Testing.ZopeTestCase.utils import makerequest
from zope.globalrequest import setRequest
from AccessControl.SpecialUsers import system as user
from AccessControl.SecurityManagement import newSecurityManager
from zope.dottedname.resolve import resolve

parser = argparse.ArgumentParser(description='Run a script')
parser.add_argument('--instance', dest='instance',
                    help='path to instance executable. If not provided, '
                         'will look in bin this was executed from for '
                         'instance or client1')
parser.add_argument('--site-id', dest='siteid',
                    help='Some scripts care about site id')

this_dir = os.path.dirname(os.path.realpath(__file__))


def script_runner(script, argv=sys.argv):
    args, _ = parser.parse_known_args()
    instance = args.instance
    if not instance:
        # look for it, get bin directory, search for plone instance
        bin_path = os.path.sep.join(
            os.path.abspath(sys.argv[0]).split(os.path.sep)[:-1])
        files = os.listdir(bin_path)
        if 'instance' in files:
            instance = os.path.join(bin_path, 'instance')
        elif 'client1' in files:
            instance = os.path.join(bin_path, 'client1')
    if not instance:
        print("Could not find plone instance to run command against.")
        sys.exit()
    if script[0] != '/':
        script_path = os.path.join(this_dir, script)
    else:
        script_path = script
    cmd = [instance, 'run', script_path]

    print('Running command: %s' % ' '.join(cmd))
    subprocess.check_call(cmd, env=os.environ)


def lookup_path_generator():
    cwd = os.getcwd()
    lookup_paths = glob.glob('/opt/plone/parts/*/etc/zope.conf')
    lookup_paths += glob.glob(os.path.join(cwd, 'parts/*/etc/zope.conf'))
    return lookup_paths


def run_it(module):
    conf_path = None
    lookup_paths = lookup_path_generator()
    for path in lookup_paths:
        if os.path.exists(path):
            conf_path = path
            break
    if conf_path is None:
        raise Exception('Could not find zope.conf in {}'.format(lookup_paths))

    Zope2.configure(conf_path)
    app = Zope2.app()
    app = makerequest(app)
    app.REQUEST['PARENTS'] = [app]
    setRequest(app.REQUEST)
    newSecurityManager(None, user)

    mod = resolve('castle.cms.cron.' + module)
    mod.run(app)


def social_counts(argv=sys.argv):
    return run_it('_social_counts')


def clean_users(argv=sys.argv):
    return run_it('_clean_users')


def archive_content(argv=sys.argv):
    return run_it('_archive_content')


def ga_popularity(argv=sys.argv):
    return run_it('_popularity')


def empty_trash(argv=sys.argv):
    return run_it('_empty_trash')


def twitter_monitor(argv=sys.argv):
    return run_it('_twitter_monitor')


def reindex_es(argv=sys.argv):
    return run_it('_reindex_es')


def upgrade_elasticsearch_in_place(argv=sys.argv):
    return run_it('_upgrade_elasticsearch_in_place')


def forced_publish_alert(argv=sys.argv):
    return run_it('_forced_publish_alert')


def crawler(argv=sys.argv):
    return run_it('_crawler')


def clean_drafts(argv=sys.argv):
    return run_it('_clean_drafts')


def upgrade_sites(argv=sys.argv):
    return run_it('_upgrade_sites')


def link_report(argv=sys.argv):
    return run_it('_link_report')
