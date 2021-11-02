# -*- coding: utf-8 -*-

import os

from setuptools import setup
from setuptools import find_packages


def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()


setup(
    name='castle.cms',
    description='CastleCMS Plone distribution main package',
    long_description_content_type='text/x-rst',
    version='3.0.0b12.dev0',
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



        # castle
        'castle.theme>=1.0.6',

        # add-ons
        'collective.documentviewer>=5.0.4',
        'collective.elasticsearch>=4.0.0',
        'collective.celery>=1.1.4',

        # python
        'boto3>=1.9.222',
        'google-api-python-client>=1.4.2<2',
        'requests>=2.7.0<3',
        'requests_oauthlib>=0.5.0<1',
        'oauth2client>=1.5.1<2',
        'redis>=2.10.5<3',
        'setuptools',
        'python-dateutil',
        'pyopenssl',
        'phonenumbers',
        'html2text',
        'pycountry',
        'tendo',
        'pylru',
        'sqlalchemy',

        # misc
        'z3c.unconfigure',
        'z3c.jbot',
    ],
    extras_require={
        'test': [
            'plone.app.testing',
            'responses',
            'mock',
            'argon2_cffi',
            'plone.app.robotframework',
            'moto',
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
      upgrade-elasticsearch-in-place = castle.cms.cron:upgrade_elasticsearch_in_place
      send-forced-publish-alert = castle.cms.cron:forced_publish_alert
      castle-crawler = castle.cms.cron:crawler
      clean-drafts = castle.cms.cron:clean_drafts
      upgrade-sites = castle.cms.cron:upgrade_sites
      link-report = castle.cms.cron:link_report
      """,
    include_package_data=True,
    zip_safe=False,
)
