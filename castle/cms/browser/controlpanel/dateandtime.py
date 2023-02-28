from Products.CMFPlone.controlpanel.browser import dateandtime

from castle.cms.widgets import SelectFieldWidget


class DateAndTimeControlPanelForm(dateandtime.DateAndTimeControlPanelForm):

    def updateFields(self):
        super(DateAndTimeControlPanelForm, self).updateFields()
        self.fields['available_timezones'].widgetFactory = SelectFieldWidget


class DateAndTimeControlPanel(dateandtime.DateAndTimeControlPanel):
    form = DateAndTimeControlPanelForm
