import csv
import json
import os
from datetime import datetime
from io import BytesIO

import sqlalchemy.exc
from castle.cms import linkreporter
from castle.cms.linkreporter import Link
from castle.cms.linkreporter import Url
from Products.Five import BrowserView


class LinksControlPanel(BrowserView):

    label = 'Link report'
    description = 'Report on crawled site links'

    page_size = 20
    _broken_count = None
    _page = None

    def __call__(self):
        self.session = linkreporter.get_session()
        if 'links_of' in self.request.form:
            links = []
            for link in self.session.query(Link).filter(
                    Link.site_id == self.context.getId(),
                    Link.url_to == self.request.form['links_of']).limit(50):
                links.append(link.url_from)
            self.request.response.setHeader('Content-type', 'application/json')
            resp = json.dumps(links)
        elif self.request.form.get('export') == 'true':
            resp = self.csv_export()
        else:
            resp = super(LinksControlPanel, self).__call__()
        self.session.close()
        return resp

    @property
    def configured(self):
        return os.environ.get('LINK_REPORT_DB', 'sqlite://') != 'sqlite://'

    def csv_export(self):
        output = BytesIO()
        writer = csv.writer(output)

        writer.writerow(['URL', 'From URL', 'Status code', 'Checked', 'Redirected url'])
        last = None
        count = 0
        for link, url in self.session.query(Link, Url.url).join(
                Url, Url.url == Link.url_to).filter(
                    Link.site_id == self.context.getId(),
                    Url.last_checked_date > datetime(1985, 1, 1),
                    ~Url.status_code.in_([200, 999, 429, 524]),
                ).order_by(Url.url):

            if last != link.url_to:
                if count > 25:
                    writer.writerow(
                        [last, '- Truncated {} entries...'.format(count - 25)])
                last = link.url_to
                count = 0
            count += 1
            if count <= 25:
                writer.writerow([
                    link.url_to,
                    link.url_from,
                    linkreporter.status_codes_info.get(
                        link._url_to.status_code, link._url_to.status_code),
                    link._url_to.last_checked_date.isoformat(),
                    link._url_from.final_url or ''
                ])

        writer.writerow([])
        writer.writerow([])
        writer.writerow([])

        for name, value in self.get_summary().items():
            if name not in ('errors',):
                writer.writerow([name, value, ''])

        resp = self.request.response
        resp.setHeader('Content-Disposition', 'attachment; filename=broken-links.csv')
        resp.setHeader('Content-Type', 'text/csv')
        output.seek(0)
        return output.read()

    def get_broken_query(self):
        return self.session.query(Link, Url.url).join(
            Url, Link.url_to == Url.url).filter(
                Link.site_id == self.context.getId(),
                ~Url.status_code.in_([-1, 200, 999, 429, 524])
        )

    @property
    def broken_count(self):
        if self._broken_count is not None:
            return self._broken_count

        query = self.get_broken_query()
        try:
            self._broken_count = query.count()
        except sqlalchemy.exc.OperationalError as ex:
            if 'no such table' in ex.message:
                linkreporter.init()
                self._broken_count = query.count()
            raise
        return self._broken_count

    @property
    def page(self):
        try:
            return int(self.request.form.get('page', '0'))
        except Exception:
            return 0

    def get_summary(self):
        try:
            return {
                'links': '{:,}'.format(self.session.query(Link).filter(
                    Link.site_id == self.context.getId()
                ).count()),
                'urls': '{:,}'.format(self.session.query(Url, Link.url_to).join(
                    Link, Link.url_to == Url.url).filter(
                        Link.site_id == self.context.getId()
                    ).distinct(Url.url).count()),
                'unchecked': '{:,}'.format(self.session.query(Url, Link.url_to).join(
                    Link, Link.url_to == Url.url).filter(
                        Link.site_id == self.context.getId(),
                        Url.status_code == -1,
                        Url.parse_error == None  # noqa
                    ).count()),
                'errors': '{:,}'.format(self.session.query(Url, Link.url_to).join(
                    Link, Link.url_to == Url.url).filter(
                        Link.site_id == self.context.getId(),
                        Url.status_code.in_([-2, -200, -599, -301]),
                        Url.parse_error != None
                    ).count()),
                'broken': '{:,}'.format(self.broken_count),
            }
        except sqlalchemy.exc.OperationalError as ex:
            if 'no such table' in ex.message:
                linkreporter.init()
                return self.get_summary()
            raise

    def get_broken(self):
        offset = self.page * self.page_size
        items = [l[0] for l in self.get_broken_query().order_by(
                 Url.last_checked_date.desc()).offset(offset).limit(self.page_size)]
        return {
            'items': items,
            'total': self.broken_count
        }
