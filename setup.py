# -*- coding: utf-8 -*-

import os

from setuptools import setup
from setuptools import find_packages


def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()


setup(
    name='castle.cms',
    version='2.0.11',
    description='Castle CMS Plone distribution main package',
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
        "Framework :: Plone :: 5.1"
    ],
    author='Nathan Van Gheem',
    author_email='nathan.vangheem@wildcardcorp.com',
    url='https://github.com/castlecms/castle.cms',
    license='GPL2',
    packages=find_packages(exclude=['ez_setup']),
    namespace_packages=['castle'],
    install_requires=[
        'Products.CMFPlone',
        'Products.CMFPlacefulWorkflow',
        'plone.app.caching',
        'plone.app.dexterity',
        'plone.app.iterate',
        'plone.app.upgrade',
        'castle.theme',
        'setuptools',
        'collective.elasticsearch',
        'collective.celery',
        'requests',
        'requests_oauthlib',
        'plone.app.mosaic',
        'plone.api',
        'redis',
        'z3c.unconfigure',
        'collective.documentviewer',
        'python-dateutil',
        'boto',
        'google-api-python-client',
        'pyopenssl',
        'phonenumbers',
        'html2text',
        'z3c.jbot',
        'pycountry',
        'tendo',
        'plone.app.blocks>=10.0.0'
    ],
    extras_require={
        'test': [
            'selenium',
            'plone.app.testing',
            'responses',
            'mock',
            'argon2_cffi'
        ],
        'development': [
            'zest.releaser',
            'check-manifest',
        ],
        'profile': [
            'collective.profiler'
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
      """,
    include_package_data=True,
    zip_safe=False,
)
