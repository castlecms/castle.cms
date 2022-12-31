import logging
import math
import os
import Queue
import threading
import time
import traceback
import urlparse
from datetime import datetime
from datetime import timedelta

import requests
import requests.exceptions
from requests.packages.urllib3.exceptions import InsecureRequestWarning

import sqlalchemy.exc
from lxml import html
from pylru import lrudecorator
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker


requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

engine = create_engine(os.environ.get('LINK_REPORT_DB', 'sqlite://'))
Base = declarative_base()

logger = logging.getLogger('castle.cms')
USER_AGENT = 'Castle CMS/2.0'


requests.utils.default_headers().update({
    'User-Agent': USER_AGENT
})

_ignored = [
    'javascript:',
    'mailto:',
    'data:',
    'https://twitter.com/intent/tweet',
    'https://www.facebook.com/sharer/sharer.php',
    'http://www.addthis.com',
    'http://www.captcha.net',
    'https://supervisord.org',
    'http://pinterest.com',
    'http://www.facebook.com/sharer',
    'http://reddit.com/submit',
    'http://digg.com/submit',
    'http://www.stumbleupon.com/submit',
    'http://www.linkedin.com/shareArticle',
    'https://plus.google.com/share',
    'http://twitter.com/intent'
]
_ignored_views = ['@@search']
_local = threading.local()


class Url(Base):
    __tablename__ = 'urls'

    url = Column(String, primary_key=True, index=True)
    last_checked_date = Column(DateTime, index=True)
    added_date = Column(DateTime)
    status_code = Column(Integer, index=True)
    content_type = Column(String, nullable=True)
    content_length = Column(String, nullable=True)
    parse_error = Column(String, nullable=True)
    ssl_verified = Column(Boolean, default=True)
    final_url = Column(String, nullable=True, index=True)


class Link(Base):
    __tablename__ = 'links'

    site_id = Column(String, primary_key=True, index=True)
    url_to = Column(String, ForeignKey(Url.url), primary_key=True, index=True)
    url_from = Column(String, ForeignKey(Url.url), primary_key=True, index=True)
    last_found = Column(DateTime)

    _url_to = relationship("Url", foreign_keys=[url_to])
    _url_from = relationship("Url", foreign_keys=[url_from])


def init():
    Base.metadata.create_all(engine)


def get_session():
    if not hasattr(_local, 'session'):
        Session = sessionmaker(bind=engine)
        _local.session = Session()
    return _local.session


_worker_queue = Queue.Queue()
_consumer_queue = Queue.Queue()
_exiting = threading.Event()


def parse_url_worker():
    while True:
        try:
            url = _worker_queue.get(timeout=0.5)
        except Queue.Empty:
            if _exiting.is_set():
                return
            continue

        _worker_queue.task_done()
        try:
            resp = requests.get(
                url, allow_redirects=True, timeout=10,
                stream=True, verify=False, headers={
                    'User-Agent': USER_AGENT
                })
        except Exception as ex:
            resp = ex
        _consumer_queue.put((url, resp))


_exception_status_codes = {
    requests.exceptions.ConnectionError: -2,
    requests.exceptions.ConnectTimeout: -599,
    requests.exceptions.TooManyRedirects: -301
}

status_codes_info = {
    -2: 'Unknown connection error',
    -200: 'nodename nor servname provided, or not known',
    -599: 'Connection timeout',
    -301: 'Too many redirects'
}


class Reporter(object):

    batch_size = 20
    running = True

    def __init__(self, site, recheck_delay=60 * 60 * 24 * 7):
        self.site = site
        self.recheck_delay = recheck_delay
        self.session = get_session()
        self.base = site.portal_registry['plone.public_url']
        if self.base:
            self.base = self.base.rstrip('/')
        self.done = 0
        self.error = 0
        self.queued = 0
        self.found = 0
        self.threads = []
        self.cache = {}

    def join(self):
        _exiting.set()
        self.running = False
        for thread in self.threads:
            thread.join()

    def get_next(self, limit=1):
        now = datetime.utcnow()
        relative = now - timedelta(seconds=self.recheck_delay)
        result = self.session.query(Url, Link.url_to).join(
            Link, Link.url_to == Url.url).filter(
                Url.last_checked_date < relative,
                Link.site_id == self.site.getId()
            ).order_by(Url.last_checked_date).limit(limit)
        return [r[0] for r in result]

    @property
    def valid(self):
        if not self.base:
            return False
        return True

    def __call__(self):
        if not self.valid:
            return

        for _ in range(int(math.ceil(self.batch_size / 3))):
            thread = threading.Thread(target=parse_url_worker)
            thread.start()
            self.threads.append(thread)

        try:
            # just make sure db is set up
            self.get_next()
        except sqlalchemy.exc.OperationalError as ex:
            if 'no such table' in ex.message:
                init()
            else:
                raise

        self.add_link(self.base, self.base)

        while self.running:
            if self.consume() == 0:
                break

        # attempt to retry errors... just once
        self.session.query(Url).filter(
            Url.status_code.in_([-1, -2, 400, 403, 401, 429])).update(
            {'last_checked_date': datetime(1984, 1, 1)},
            synchronize_session=False)
        self.session.expunge_all()

        while self.running:
            if self.consume() == 0:
                break

        self.join()
        while _consumer_queue.qsize() > 0:
            url, resp = _consumer_queue.get()
            if url in self.cache:
                url = self.cache.pop(url)
                self.check_url(url, resp)

    def consume(self):
        urls = self.get_next(self.batch_size)

        for url in urls:
            self.cache[url.url] = url
            _worker_queue.put(url.url)

        while _worker_queue.qsize() > int(math.ceil(self.batch_size / 4)):
            # let it work while we keep moving
            time.sleep(0.1)

        while _consumer_queue.qsize() > 0:
            url, resp = _consumer_queue.get()
            if url in self.cache:
                url = self.cache.pop(url)
                self.check_url(url, resp)
            _consumer_queue.task_done()
        return len(urls)

    def handle_error(self, request, exception):
        return exception

    def check_url(self, url, resp):
        self.done += 1
        if self.done % 500 == 0:
            # clear cache every so often
            self.session.expire_all()

        if isinstance(resp, Exception):
            self.error += 1
            logger.error(
                'Error processing url: {}\n{}'.format(url.url, resp))
            self.update_url(url, None, exception=resp)
        else:
            logger.info('({}/{}/{}/{}): Processing ({}) {}'.format(
                self.found, self.queued, self.done, self.error,
                resp.status_code, url.url))
            if resp.status_code == 429:
                # slow it down since we're getting limited...
                time.sleep(0.2)
            try:
                override_status_code = None
                if '/acl_users/' in resp.url or '?came_from=' in resp.url:
                    override_status_code = 403
                elif resp.status_code == 200:
                    if (resp.url.startswith(self.base) and
                            'html' in resp.headers.get('Content-Type', '')):
                        self.parse_response(resp, url.url)

                self.update_url(url, resp,
                                override_status_code=override_status_code)
            except Exception:
                logger.error('Could not update url {}'.format(url.url), exc_info=True)
            finally:
                resp.close()

    def update_url(self, url, resp=None, exception=None, override_status_code=None):
        url.last_checked_date = datetime.utcnow()
        final_url = None
        if resp is not None:
            url.status_code = override_status_code or resp.status_code
            url.content_type = resp.headers.get('Content-Type')
            url.content_length = resp.headers.get('Content-Length')
            url.parse_error = None
            if url.url != resp.url:
                final_url = resp.url
        else:
            status_code = _exception_status_codes.get(type(exception), -1)
            if status_code == -2:
                if status_codes_info[-200] in str(exception):
                    status_code = -200
            url.status_code = status_code
            url.content_type = None
            url.content_length = None
            url.parse_error = traceback.format_exc(exception)
        url.final_url = final_url
        try:
            self.session.add(url)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    def parse_response(self, resp, from_url):
        base = resp.url
        dom = html.fromstring(resp.content)
        base_tag = dom.cssselect('base')
        if len(base_tag) > 0:
            base_tag = base_tag[0]
            base = base_tag.attrib('href')
            if not base.startswith('http://') and not base.startswith('https://'):
                base = urlparse.urljoin(resp.url, base)

        for anchor in dom.cssselect('a,img'):
            if 'href' not in anchor.attrib and 'src' not in anchor:
                continue
            url = anchor.attrib.get('href', anchor.attrib.get('src'))
            url = url.split('#')[0]
            if not url:
                continue
            if not url.startswith('http://') and not url.startswith('https://'):
                # make absolute url
                url = urlparse.urljoin(base, url)

            drop = False
            for ignore in _ignored:
                if url.startswith(ignore):
                    drop = True
                    break
            for view in _ignored_views:
                if url.endswith(view):
                    drop = True
                    break
            if drop:
                continue

            if not url.startswith('http://') and not url.startswith('https://'):
                logger.warning('Invalid url: {}'.format(url))
                continue

            self.add_link(url, from_url)

    @lrudecorator(5000)
    def add_url(self, url):
        error = False
        try:
            self.session.identity_map[(Url, (url,))]
            # no key error, we already have object, ignore
        except KeyError:
            url_ob = Url(
                url=url,
                last_checked_date=datetime(1984, 1, 1),
                added_date=datetime.utcnow(),
                status_code=-1
            )
            try:
                self.session.add(url_ob)
                self.session.commit()
                self.queued += 1
            except sqlalchemy.exc.IntegrityError:
                # we're okay if we already have a link object in db!
                error = True
            except Exception:
                error = True
                logger.error('Unhandled error updating url object', exc_info=True)
                raise
            finally:
                if error:
                    self.session.rollback()

    @lrudecorator(5000)
    def add_link(self, url, from_url):
        if '/acl_users/' in url or '?came_from=' in url:
            # ignore parsing these guys
            return

        if url[0] == '/':
            # make full url
            url = urlparse.urljoin(from_url, url)

        url = url.rstrip('/')
        self.add_url(url)

        error = False
        try:
            link_ob = Link(
                site_id=self.site.getId(),
                url_to=url,
                url_from=from_url,
                last_found=datetime.utcnow()
            )
            self.session.add(link_ob)
            self.session.commit()
            self.found += 1
        except sqlalchemy.exc.IntegrityError:
            self.session.rollback()
            link_ob = self.session.query(Link).filter(
                Link.site_id == self.site.getId(),
                Link.url_to == url,
                Link.url_from == from_url
            ).first()
            link_ob.last_found = datetime.utcnow()
            self.session.add(link_ob)
            try:
                self.session.commit()
            except Exception:
                logger.error('Error commit link object', exc_info=True)
                error = True
        except Exception:
            error = True
            logger.error('Unhandled error updating link object', exc_info=True)
            raise
        finally:
            if error:
                self.session.rollback()
