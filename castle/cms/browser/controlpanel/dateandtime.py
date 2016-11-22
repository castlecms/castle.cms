from castle.cms.widgets import SelectFieldWidget
from Products.CMFPlone.controlpanel.browser import dateandtime


class DateAndTimeControlPanelForm(dateandtime.DateAndTimeControlPanelForm):

    def updateFields(self):
        super(DateAndTimeControlPanelForm, self).updateFields()
        self.fields['available_timezones'].widgetFactory = SelectFieldWidget


class DateAndTimeControlPanel(dateandtime.DateAndTimeControlPanel):
    form = DateAndTimeControlPanelForm
