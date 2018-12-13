from castle.cms.tiles.base import BaseTile
from castle.cms.utils import parse_query_from_data
from castle.cms.widgets import QueryFieldWidget
from datetime import timedelta
from plone.autoform import directives as form
from plone.event.utils import is_datetime
from plone.event.utils import pydt
from plone.event.recurrence import recurrence_sequence_ical as recurrences
from Products.CMFCore.utils import getToolByName
from zope import schema
from zope.interface import Interface

import json


def format_date(dt):
    if is_datetime(dt):
        return dt.isoformat()
    else:
        try:
            return dt.ISO8601()
        except Exception:
            pass


class CalendarTile(BaseTile):

    def get_query(self):
        parsed = parse_query_from_data(self.data, self.context)
        parsed['sort_order'] = 'reverse'
        return parsed

    def results(self):
        catalog = getToolByName(self.context, 'portal_catalog')
        return catalog(**self.get_query())[:self.data.get('limit', 250) or 250]

    def json_config(self):
        events = []
        for brain in self.results():
            event = {
                'title': brain.Title,
                'url': brain.getURL()
            }
            if brain.portal_type == 'Event':
                event.update({
                    'start': brain.start and format_date(brain.start),
                    'end': brain.end and format_date(brain.end)
                })

                if hasattr(brain, 'recurrence') and brain.recurrence is not None:
                    time_delta = brain.end - brain.start
                    recurring_events = recurrences(brain.start, brain.recurrence)
                    for new_event in recurring_events:
                        if new_event != brain.start:  # skip the actual event
                            events.append({
                                'title': brain.Title,
                                'url': brain.getURL(),
                                'start': format_date(new_event),
                                'end': format_date(new_event + time_delta)
                            })

            else:
                event['start'] = format_date(brain.effective)
                if brain.expires and brain.expires.year() != 2499:
                    event['end'] = format_date(brain.expires)
                else:
                    event['end'] = format_date(pydt(brain.effective) + timedelta(hours=1))
            events.append(event)

        return json.dumps({
            'header': {
                'left': 'prev,next today',
                'center': 'title',
                'right': 'month,agendaWeek,agendaDay'
            },
            'events': events
        })


class ICalendarTileSchema(Interface):

    form.widget(query=QueryFieldWidget)
    query = schema.List(
        title=u'Base query',
        description=u"This query can be customized base on user selection",
        value_type=schema.Dict(value_type=schema.Field(),
                               key_type=schema.TextLine()),
        required=False,
        default=[{
            u'i': u'portal_type',
            u'v': [u'Event'],
            u'o': u'plone.app.querystring.operation.selection.any'}]
    )

    sort_on = schema.TextLine(
        title=u'Sort on',
        description=u"Sort on this index",
        required=False,
    )

    sort_reversed = schema.Bool(
        title=u'Reversed order',
        description=u'Sort the results in reversed order',
        required=False,
    )

    limit = schema.Int(
        title=u'Limit',
        description=u'Limit Search Results',
        required=False,
        default=250,
        min=1,
    )
