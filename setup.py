# -*- coding: utf-8 -*-

import os

from setuptools import setup
from setuptools import find_packages


def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames), 'r').read()


setup(
    name='castle.cms',
    description='CastleCMS Plone distribution main package',
    long_description_content_type='text/x-rst',
    version='2.5.4.dev0',
    long_description='%s\n%s' % (
        read('README.rst'),
        read('HISTORY.rst')
    ),
    keywords="plone cms castle",
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Framework :: Plone :: 5.0",
        "Framework :: Plone",
        "Framework :: Plone :: 5.1",
        "Framework :: CastleCMS",
        "Framework :: CastleCMS :: Theme"
    ],
    author='Wildcard Corp',
    author_email='info@wildcardcorp.com',
    url='https://github.com/castlecms/castle.cms',
    license='GPL2',
    packages=find_packages(exclude=['ez_setup']),
    namespace_packages=['castle'],
    install_requires=[
        # plone packages
        'Products.CMFPlone>=5.2.0.dev0',
        'plone.app.upgrade>=2.0.17',
        'plone.app.mosaic>=2.0.0.dev24',
        'plone.app.blocks>=10.0.0',
        'Products.PloneKeywordManager>=2.2.1',
        'z3c.relationfield>=0.7.1.dev0',
        'plone.app.standardtiles>=2.0.0.dev0',

        'Products.CMFPlacefulWorkflow',
        'plone.app.caching',
        'plone.app.dexterity',
        'plone.app.iterate',
        'plone.api',
        'plone.app.drafts>=1.1.3',
        'zope.globalrequest',

        # castle
        'castle.theme>=1.0.4',

        # add-ons
        'collective.documentviewer>=5.0.4',
        'collective.elasticsearch>=2.0.5<3',
        'collective.celery>=1.1.4',

        # python
        'boto>=2.38.0<3',
        'google-api-python-client>=1.4.2<2',
        'redis>=2.10.3<3',
        'requests>=2.7.0<3',
        'requests_oauthlib>=0.5.0<1',
        'oauth2client>=1.5.1<2',
        'redis>=2.10.5<3',
        'setuptools',
        'python-dateutil',
        'boto',
        'pyopenssl',
        'phonenumbers',
        'html2text',
        'pycountry>18.12.8',
        'tendo',
        'pylru',
        'sqlalchemy',

        # misc
        'z3c.unconfigure',
        'z3c.jbot'
    ],
    extras_require={
        'test': [
            'plone.app.testing',
            'responses',
            'mock',
            'argon2_cffi',
            'plone.app.robotframework>0.9.16',
            'robotframework-debuglibrary',
            'plone.app.testing',
            'zope.testing',
        ],
        'development': [
            'zest.releaser',
            'check-manifest',
        ],
        'profile': [
            'collective.profiler'
        ],
        'forms': [
            'collective.easyform [recaptcha]'
        ]
    },
    entry_points="""
      # -*- Entry points: -*-

      [z3c.autoinclude.plugin]
      target = plone

      [celery_tasks]
      castle = castle.cms.tasks

      [console_scripts]
      clean-plone-users = castle.cms.cron:clean_users
      social-counts = castle.cms.cron:social_counts
      archive-content = castle.cms.cron:archive_content
      content-popularity = castle.cms.cron:ga_popularity
      empty-trash = castle.cms.cron:empty_trash
      twitter-monitor = castle.cms.cron:twitter_monitor
      reindex-elasticsearch = castle.cms.cron:reindex_es
      send-forced-publish-alert = castle.cms.cron:forced_publish_alert
      castle-crawler = castle.cms.cron:crawler
      clean-drafts = castle.cms.cron:clean_drafts
      upgrade-sites = castle.cms.cron:upgrade_sites
      link-report = castle.cms.cron:link_report

      [zodbupdate.decode]
      decodes = castle.cms:zodbupdate_decode_dict
      """,
    include_package_data=True,
    zip_safe=False,
)
