from AccessControl.SecurityManagement import newSecurityManager
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from castle.cms.cron.utils import setup_site
from plone import api
from collective.elasticsearch.es import ElasticSearchCatalog
from castle.cms import audit
from castle.cms.utils import ESConnectionFactoryFactory
from collective.elasticsearch.hook import index_batch

from elasticsearch.helpers import bulk
from tendo import singleton

from argparse import ArgumentParser
from json import load
import os
from fnmatch import fnmatch

from datetime import datetime


def get_args():
    parser = ArgumentParser(
        description='Import Audit Logs from file and index in Elasticsearch')
    parser.add_argument('--filepath', dest='filepath', default=None)
    args, _ = parser.parse_known_args()
    return args


def get_all_log_files(root_dir):
    matches = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if fnmatch(file, 'audit_log*.json'):
                matches.append(os.path.join(root, file))
    return matches


def select_file(log_files):
    print('\nHere are some possible log files to choose from:  ')
    for n, file in enumerate(log_files, 1):
            print (str(n) + '  ' + file)
    prompt = '\nEnter the number of the log file you want to import, or enter the filepath. Enter "q" to exit.:  '
    while(True):
        user_input = raw_input(prompt)
        try:
            user_input = int(user_input)
        except:
            pass
        if user_input in range(1, len(log_files) + 1):
            return log_files[user_input - 1]
        elif os.path.isfile(user_input):
            return user_input
        elif user_input in ['N', 'n']:
            return request_filepath()
        elif user_input in ['Q', 'q']:
            return
        else:
            print('\nInvalid input.')


def request_filepath():
    prompt = '\nEnter a filepath to the audit log you want to import. Enter "q" to exit.' 
    while(True):
        user_input = raw_input(prompt)
        if os.path.isfile(user_input):
            return user_input
        elif user_input in ['Q', 'q']:
            return
        else:
            print('\nInvalid input.')


def import_audit_logs(site, args):
    if not args.filepath:
        print('\nNo filepath provided!')
        log_files = get_all_log_files(os.getcwd())
        filepath = request_filepath() if not log_files else select_file(log_files)
        if not filepath:
            print('No filepath provided. Exiting.')
            return        
    
    start_time = datetime.now()
    try:
        with open(filepath, 'r') as file:
            data = load(file)
            audit_log = data['audit_log']
    except:
        print ('Problem reading file.\n')
        raise
    
    try:
        setup_site(site)
        catalog = api.portal.get_tool('portal_catalog')
        es_catalog = ElasticSearchCatalog(catalog)
    except:
        print ('Error setting up ElasticSearchCatalog\n')
        raise

    if not es_catalog.enabled:
        print('Elasticsearch not enabled')
        return
    
    index_names = set(map((lambda x: x['_index']), audit_log))
    es = ESConnectionFactoryFactory()()
    try:
        for index_name in index_names:
            audit._create_index(es, index_name)
    except:
        print ('Error creating index {}'.format(index_name))
        raise

    for entry in audit_log:
        entry.pop('_type', None)

    try:
        entries_indexed, errors = bulk(es_catalog.connection, audit_log, raise_on_error=False)
    except Exception:
        print ('Problem when trying to index log entries.\n')
        raise
    
    end_time = datetime.now()
    elapsed_time = end_time - start_time

    print ('\n{} entries indexed in {}'.format(entries_indexed, elapsed_time))

    if not errors:
        print('\nThere were no errors!')
    elif len(errors) == 1:
        print ('\nThere was 1 error:')
    else:
        print ('\nThere were {} errors'.format((len(errors))))
        
    for error in errors:
        print (error)
  

def run(app):
    singleton.SingleInstance('importauditlog')

    user = app.acl_users.getUser('admin')  # noqa
    newSecurityManager(None, user.__of__(app.acl_users))  # noqa

    for oid in app.objectIds():  # noqa
        obj = app[oid]  # noqa
        if IPloneSiteRoot.providedBy(obj):
            import_audit_logs(obj, get_args())


if __name__ == '__main__':
    run(app)  # noqa
