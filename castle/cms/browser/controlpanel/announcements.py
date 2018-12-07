from Acquisition import aq_inner
from castle.cms import texting
from castle.cms import subscribe
from castle.cms.browser.utils import Utils
from castle.cms.constants import ALL_SUBSCRIBERS
from castle.cms.interfaces import IAnnouncementData
from castle.cms.tasks import send_email
from castle.cms.tasks import send_email_to_subscribers
from castle.cms.widgets import AjaxSelectFieldWidget
from castle.cms.widgets import SelectFieldWidget, TinyMCETextFieldWidget
from plone import api
from plone.app.registry.browser import controlpanel
from plone.app.textfield import RichText
from plone.app.textfield.value import RichTextValue
from plone.autoform import directives
from plone.autoform.form import AutoExtensibleForm
from plone.outputfilters import apply_filters
from plone.outputfilters.interfaces import IFilter
from plone.registry.interfaces import IRegistry
from plone.supermodel import model
from Products.CMFPlone.utils import safe_unicode
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form import button
from z3c.form import form
from z3c.form.browser.file import FileWidget
from z3c.form.interfaces import WidgetActionExecutionError
from zope import schema
from zope.component import getAdapters
from zope.component import getUtility
from zope.interface import Invalid
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm

reg_key = 'castle.subscriber_categories'


class AnnouncementsControlPanelForm(controlpanel.RegistryEditForm):
    schema = IAnnouncementData
    schema_prefix = 'castle'
    id = "AnnouncementsControlPanel"
    label = u"Announcements"
    description = ""

    def updateFields(self):
        super(AnnouncementsControlPanelForm, self).updateFields()
        self.fields['site_announcement'].widgetFactory = TinyMCETextFieldWidget


class ISendEmailUsersForm(model.Schema):
    subject = schema.ASCIILine(
        title=u'Subject')

    send_from = schema.TextLine(
        title=u'Custom FROM address',
        required=False,
    )

    directives.widget(
        'send_to_groups',
        AjaxSelectFieldWidget,
        vocabulary='plone.app.vocabularies.Groups'
    )

    send_to_groups = schema.List(
        title=u'Send to groups',
        value_type=schema.Choice(
            vocabulary='plone.app.vocabularies.Groups'
        ),
        required=False
    )

    directives.widget(
        'send_to_users',
        AjaxSelectFieldWidget,
        vocabulary='plone.app.vocabularies.Users'
    )

    send_to_users = schema.List(
        title=u'Send to users',
        value_type=schema.Choice(
            vocabulary='plone.app.vocabularies.Users'
        ),
        required=False
    )

    send_to_custom = schema.List(
        title=u'To(additional)',
        description=u'Additional email addresses, one per line, to '
                    u'send emails to.',
        value_type=schema.TextLine(),
        required=False
    )

    body = RichText(
        title=u'Body',
        description=u'Message body',
        default_mime_type='text/html',
        output_mime_type='text/html',
        allowed_mime_types=('text/html',),
        required=True)


class SendEmailUsersForm(AutoExtensibleForm, form.Form):
    schema = ISendEmailUsersForm

    ignoreContext = True

    @button.buttonAndHandler(u'Send', name='send')
    def handle_send(self, action):
        data, errors = self.extractData()
        if not errors:
            addresses = data['send_to_custom'] or []
            for group in data['send_to_groups'] or []:
                for user in api.user.get_users(groupname=group):
                    email = user.getProperty('email')
                    if email:
                        addresses.append(email)
            for username in data['send_to_users'] or []:
                user = api.user.get(username=username)
                if user:
                    email = user.getProperty('email')
                    if email:
                        addresses.append(email)

            try:
                sender = data['send_from']
            except Exception:
                sender = None

            utils = Utils(self.context, self.request)
            public_url = utils.get_public_url()
            html = data['body'].output

            filters = [f for _, f in getAdapters((self.context, self.request), IFilter)]
            html = apply_filters(filters, html)
            html = html.replace(self.context.absolute_url(), public_url.encode('utf8'))

            send_email.delay(list(set(addresses)), data['subject'], html=html, sender=sender)
            self.request.response.redirect('%s/@@announcements-controlpanel' % (
                self.context.absolute_url()))


class ISendEmailSubscribersForm(model.Schema):
    subject = schema.ASCIILine(
        title=u'Subject')

    directives.widget('send_to_categories', SelectFieldWidget)
    send_to_categories = schema.List(
        title=u'Send to categories',
        required=False,
        value_type=schema.Choice(
            vocabulary='castle.cms.vocabularies.EmailCategories'
        )
    )

    send_from = schema.TextLine(
        title=u'Custom FROM address',
        required=False,
    )

    body = RichText(
        title=u'Body',
        description=u'Message body',
        default_mime_type='text/html',
        output_mime_type='text/html',
        allowed_mime_types=('text/html',),
        required=True,
        default=RichTextValue(
            u'<p></p><p></p>'
            u'<p><a href="{{change_url}}">Change your subscription settings</a></p>'
            u'<p><a href="{{unsubscribe_url}}">Unsubscribe from these messages</a></p>',
            'text/html', 'text/html'))


class SendEmailSubscribersForm(AutoExtensibleForm, form.Form):
    schema = ISendEmailSubscribersForm

    ignoreContext = True

    @button.buttonAndHandler(u'Send', name='send2')
    def handle_send2(self, action):
        data, errors = self.extractData()
        if not errors:
            utils = Utils(self.context, self.request)
            public_url = utils.get_public_url()
            html = data['body'].output

            filters = [f for _, f in getAdapters((self.context, self.request), IFilter)]
            html = apply_filters(filters, html)
            html = html.replace(self.context.absolute_url(), public_url.encode('utf8'))

            categories = set()
            if 'form.widgets.send_to_categories' in self.request.form:
                categories = set(data['send_to_categories'])

            sender = None
            if 'form.widgets.send_from' in self.request.form:
                sender = data['send_from']

            send_email_to_subscribers.delay(data['subject'], html=html, categories=categories, sender=sender)

            api.portal.show_message(
                'Sending emails', request=self.request, type='info')
            self.request.response.redirect('%s/@@announcements-controlpanel' % (
                self.context.absolute_url()))


class ISendTextForm(model.Schema):

    text = schema.Text(
        title=u'Text message')


class SendTextForm(AutoExtensibleForm, form.Form):

    schema = ISendTextForm

    ignoreContext = True

    @button.buttonAndHandler(u'Send', name='text')
    def handle_text(self, action):
        data, errors = self.extractData()
        if not errors:
            texting.send(data['text'], ALL_SUBSCRIBERS)
            api.portal.show_message(
                'Text message sent', request=self.request, type='info')
            self.request.response.redirect('%s/@@announcements-controlpanel' % (
                self.context.absolute_url()))


class IExportSubscribersForm(model.Schema):
    directives.widget('export_categories', SelectFieldWidget)
    export_categories = schema.List(
        title=u'Subscribers to export',
        description=u'Leave Empty For All Subscribers',
        required=False,
        value_type=schema.Choice(
            vocabulary='castle.cms.vocabularies.EmailCategories'
        )
    )


class ExportSubscribersForm(AutoExtensibleForm, form.Form):
    schema = IExportSubscribersForm

    ignoreContext = True

    @button.buttonAndHandler(u'Export', name='export')
    def handle_export(self, action):
        data, errors = self.extractData()
        if not errors:
            response = self.request.response
            cd = 'attachment; filename=subscribers.csv'
            response.setHeader('Content-Disposition', cd)
            fields = ['name', 'email', 'phone_number', 'phone_number_confirmed',
                      'confirmed', 'code', 'created', 'captcha', 'categories']
            responsebody = ','.join(fields)
            categories = set()
            if 'form.widgets.export_categories' in self.request.form:
                if data['export_categories'] not in (None, ''):
                    categories = set(data['export_categories'])
            check_categories = (categories is not None and len(categories) != 0)
            for subscriber in subscribe.all():
                if check_categories:
                    if ('categories' in subscriber and len(subscriber['categories']) > 0):
                        if len(categories.intersection(subscriber['categories'])) == 0:
                            continue
                row = []
                for key in fields:
                    if subscriber.get(key) is None:
                        row.append('')
                    elif isinstance(subscriber.get(key), list):
                        row.append('"' + ';'.join(subscriber.get(key)) + '"')
                    else:
                        row.append(str(subscriber.get(key)))
                responsebody += '\n' + ','.join(row)
            response.setBody(responsebody, lock=True)


class IImportSubscribersForm(model.Schema):
    directives.widget('csv_upload', FileWidget)
    csv_upload = schema.ASCII(
        title=u"Import subscribers",
        description=u"Upload CSV file to import",
        required=False
    )


class ImportSubscribersForm(AutoExtensibleForm, form.Form):
    schema = IImportSubscribersForm

    ignoreContext = True

    @button.buttonAndHandler(u'Import', name='import')
    def handle_export(self, action):
        data, errors = self.extractData()
        if not errors:
            lines = data['csv_upload'].split('\n')
            columns = lines[0].split(',')
            categoryindex = columns.index('categories')
            emailindex = columns.index('email')
            for line in lines[1:]:
                cols = line.split(',')
                if len(cols) <= 1:
                    continue
                subscriber = {
                    'categories': map(safe_unicode, cols[categoryindex].strip('"').split(';')),
                    'email': cols[emailindex]
                }
                match = subscribe.get_subscriber(subscriber['email'])
                if match is not None:
                    for cat in subscriber['categories']:
                        if cat not in match['categories']:
                            match['categories'].append(cat)
                else:
                    for index, col in enumerate(cols):
                        if(index == categoryindex):
                            continue
                        if col == '':
                            subscriber[columns[index]] = None
                        elif col == 'True' or col == 'False':
                            subscriber[columns[index]] = col == 'True'
                        else:
                            try:
                                subscriber[columns[index]] = float(col)
                            except ValueError:
                                subscriber[columns[index]] = col
                    subscribe.register(subscriber['email'], subscriber)
                allcategories = api.portal.get_registry_record(reg_key)
                for cat in subscriber['categories']:
                    if cat not in allcategories:
                        allcategories.append(cat)
                api.portal.set_registry_record(reg_key, allcategories)


class IMergeCategoriesForm(model.Schema):
    directives.widget('rename_merge_categories', SelectFieldWidget)
    rename_merge_categories = schema.List(
        title=u'Categories to Rename or Merge',
        required=True,
        value_type=schema.Choice(
            vocabulary='castle.cms.vocabularies.EmailCategories'
        )
    )
    new_category_name = schema.TextLine(
        title=u"New Category Name",
        required=True
    )


class MergeCategoriesForm(AutoExtensibleForm, form.Form):
    schema = IMergeCategoriesForm

    ignoreContext = True

    @button.buttonAndHandler(u'Rename/Merge', name='merge')
    def handle_merge(self, action):
        data, errors = self.extractData()
        if not errors:
            allcategories = api.portal.get_registry_record(reg_key)
            categories = set()
            newname = u''
            if 'form.widgets.rename_merge_categories' in self.request.form:
                if data['rename_merge_categories'] not in (None, ''):
                    categories = set(data['rename_merge_categories'])
            if 'form.widgets.new_category_name' in self.request.form:
                newname = data['new_category_name'].split(';')[0]
            if len(categories) > 0 and len(newname) > 0:
                if newname in allcategories and newname not in categories:
                    raise WidgetActionExecutionError(
                        'new_category_name',
                        Invalid(
                            u"That category name is already in use"
                        )
                    )
                    return
                for category in categories:
                    allcategories.remove(category)
                allcategories.append(newname)
                api.portal.set_registry_record(reg_key, allcategories)
                for subscriber in subscribe.all():
                    if ('categories' in subscriber and len(subscriber['categories']) > 0):
                        if len(categories.intersection(subscriber['categories'])) > 0:
                            subcat = subscriber['categories']
                            for category in categories:
                                if category in subcat:
                                    subcat.remove(category)
                            subcat.append(newname)
                            subscriber['categories'] = subcat
                self.widgets['new_category_name'].value = u''
                self.widgets['rename_merge_categories'].value = u''


class IDeleteCategoriesForm(model.Schema):
    directives.widget('delete_categories', SelectFieldWidget)
    delete_categories = schema.List(
        title=u'Categories to Delete',
        required=True,
        value_type=schema.Choice(
            vocabulary='castle.cms.vocabularies.EmailCategories'
        )
    )
    force_delete = schema.Bool(
        title=u'Force Delete',
        description=u'Delete category even if there are accounts still subscribed to it',
        default=False,
    )


class DeleteCategoriesForm(AutoExtensibleForm, form.Form):
    schema = IDeleteCategoriesForm

    ignoreContext = True

    @button.buttonAndHandler(u'Delete Categories', name='delete')
    def handle_delete(self, action):
        data, errors = self.extractData()
        if not errors:
            allcategories = api.portal.get_registry_record(reg_key)
            categories = set()
            if 'form.widgets.delete_categories' in self.request.form:
                if data['delete_categories'] not in (None, ''):
                    categories = set(data['delete_categories'])
            force_delete = 'form.widgets.force_delete' in self.request.form
            if len(categories) > 0:
                badcategories = []
                for category in categories:
                    existing_subscribers = False
                    for subscriber in subscribe.all():
                        if ('categories' in subscriber and len(subscriber['categories']) > 0):
                            if len(categories.intersection(subscriber['categories'])) > 0:
                                subcat = subscriber['categories']
                                for category in categories:
                                    if category in subcat:
                                        existing_subscribers = True
                                        if force_delete:
                                            subcat.remove(category)
                                subscriber['categories'] = subcat
                    if force_delete or not existing_subscribers:
                        allcategories.remove(category)
                    else:
                        badcategories.append(category)
                api.portal.set_registry_record(reg_key, allcategories)
                self.widgets['delete_categories'].value = ';'.join(badcategories)
                if len(badcategories) > 0:
                    raise WidgetActionExecutionError(
                        'delete_categories',
                        Invalid(
                            u'These category(s) still have subscribers. '
                            u'Select "Force Delete" if you want to unsubscribe them.'
                        )
                    )


class IAddCategoryForm(model.Schema):
    add_categories = schema.TextLine(
        title=u'New category',
        description=u'Add multiple categories at once by separating them with semicolons',
        required=True
    )


class AddCategoryForm(AutoExtensibleForm, form.Form):
    schema = IAddCategoryForm

    ignoreContext = True

    @button.buttonAndHandler(u'Add Category', name='addcat')
    def handle_addcat(self, action):
        data, errors = self.extractData()
        if not errors:
            allcategories = api.portal.get_registry_record(reg_key)
            categories = set()
            if 'add_categories' in data:
                if data['add_categories'] not in (None, ''):
                    categories = set(data['add_categories'].split(';'))
            if len(categories) > 0:
                badcategories = []
                for category in categories:
                    category = category.strip()
                    if len(category) > 0 and category not in allcategories:
                        allcategories.append(category)
                    else:
                        badcategories.append(category)
                api.portal.set_registry_record(reg_key, allcategories)
                self.widgets['add_categories'].value = ';'.join(badcategories)
                if len(badcategories) > 0:
                    raise WidgetActionExecutionError(
                        'add_categories',
                        Invalid(
                            u"That category name is already in use"
                        )
                    )


class AnnouncementsControlPanel(controlpanel.ControlPanelFormWrapper):
    form = AnnouncementsControlPanelForm
    index = ViewPageTemplateFile('templates/announcements.pt')

    hasTexting = False

    def __init__(self, context, request):
        super(AnnouncementsControlPanel, self).__init__(context, request)
        self.email_form = SendEmailUsersForm(aq_inner(context), request)
        self.email_subscribers_form = SendEmailSubscribersForm(aq_inner(context), request)
        self.text_subscribers_form = SendTextForm(aq_inner(context), request)
        self.export_subscribers_form = ExportSubscribersForm(aq_inner(context), request)
        self.import_subscribers_form = ImportSubscribersForm(aq_inner(context), request)
        self.merge_categories_form = MergeCategoriesForm(aq_inner(context), request)
        self.delete_categories_form = DeleteCategoriesForm(aq_inner(context), request)
        self.add_category_form = AddCategoryForm(aq_inner(context), request)

    def get_sub_count(self):
        self.categories = api.portal.get_registry_record(reg_key)
        self.sub_count = {}
        for category in self.categories:
            self.sub_count[category] = 0
        self.invalid_category = 0
        for subscriber in subscribe.all():
            if ('categories' in subscriber and len(subscriber['categories']) > 0):
                subcat = subscriber['categories']
                for category in subcat:
                    if category in self.categories:
                        self.sub_count[category] += 1
                    else:
                        self.invalid_category += 1

    def update_terms(self):
        category_vocab_terms = []
        for category in self.categories:
            category_vocab_terms.append(SimpleTerm(value=category, title=category))
        category_vocab = SimpleVocabulary(category_vocab_terms)
        self.email_subscribers_form.widgets['send_to_categories'].terms = category_vocab
        self.export_subscribers_form.widgets['export_categories'].terms = category_vocab
        self.merge_categories_form.widgets['rename_merge_categories'].terms = category_vocab
        self.delete_categories_form.widgets['delete_categories'].terms = category_vocab

    def __call__(self):
        registry = getUtility(IRegistry)
        if (registry.get('castle.plivo_auth_id') and
                registry.get('castle.plivo_auth_token') and
                registry.get('castle.plivo_phone_number')):
            self.hasTexting = True
        self.email_form.update()
        self.email_subscribers_form.update()
        self.text_subscribers_form.update()
        self.export_subscribers_form.update()
        self.import_subscribers_form.update()
        self.merge_categories_form.update()
        self.delete_categories_form.update()
        self.add_category_form.update()
        self.get_sub_count()
        self.update_terms()
        return super(AnnouncementsControlPanel, self).__call__()
