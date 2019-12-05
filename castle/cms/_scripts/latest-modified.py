from zope.component.hooks import setSite
import argparse


parser = argparse.ArgumentParser(
    description='...')
parser.add_argument('--site-id', dest='site_id', default='Plone')
args, _ = parser.parse_known_args()


if __name__ == '__main__':
    site = app[args.site_id]  # noqa
    setSite(site)

    catalog = site.portal_catalog
    brains = catalog()

    latest_modified = brains[0].modified

    for idx, brain in enumerate(brains):
        try:
            latest_modified = brain.modified if brain.modified > latest_modified else latest_modified  # noqa
        except Exception:
            print('No modified date on brain {path}'.format(path=brain.getPath()))

    print('Content last modified {latest}'.format(latest=latest_modified))
