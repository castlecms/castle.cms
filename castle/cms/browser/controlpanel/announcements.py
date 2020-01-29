from Acquisition import aq_inner
from castle.cms import subscribe, texting
from castle.cms.browser.utils import Utils
from castle.cms.constants import ALL_SUBSCRIBERS
from castle.cms.interfaces import IAnnouncementData, IEmailTemplateSchema
from castle.cms.tasks import send_email, send_email_to_subscribers
from castle.cms.widgets import (AjaxSelectFieldWidget, SelectFieldWidget,
                                TinyMCETextFieldWidget)
from plone import api
from plone.app.registry.browser import controlpanel
from plone.app.textfield import RichText, RichTextValue
from plone.app.textfield.value import RichTextValue
from plone.autoform import directives
from plone.autoform.form import AutoExtensibleForm
from plone.dexterity.utils import createContentInContainer
from plone.outputfilters import apply_filters
from plone.outputfilters.interfaces import IFilter
from plone.registry.interfaces import IRegistry
from plone.supermodel import model
from Products.CMFPlone.utils import safe_unicode
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage
from z3c.form import button, form
from z3c.form.browser.file import FileWidget
from z3c.form.interfaces import (HIDDEN_MODE, INPUT_MODE,
                                 WidgetActionExecutionError)
from zope import component, interface, schema
from zope.component import getAdapters, getUtility
from zope.interface import Invalid
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary
from Products.CMFPlone.interfaces.constrains import ISelectableConstrainTypes
from zope.interface import implements
from plone.dexterity.interfaces import IDexterityContent
from zope.component import adapter

reg_key = 'castle.subscriber_categories'

def verify_email_templates_folder(context):
    site = api.portal.get()

    if 'email-templates' not in site:
        folder = api.content.create(
            container=site,
            type='Folder',
            id='email-templates',
            title='Email Templates',
        )
        allowable_type = 'EmailTemplate'
        aspect = ISelectableConstrainTypes(folder, None)

        if aspect and aspect.getConstrainTypesMode() != 1:
            aspect.setConstrainTypesMode(1)
            aspect.setLocallyAllowedTypes([allowable_type])
            aspect.setImmediatelyAddableTypes([allowable_type])
        if not getattr(folder, 'exclude_from_nav', False):
            folder.exclude_from_nav = True
            folder.reindexObject()


class AnnouncementsControlPanelForm(controlpanel.RegistryEditForm):
    schema = IAnnouncementData
    schema_prefix = 'castle'
    id = "AnnouncementsControlPanel"
    label = u"Announcements"
    description = ""

    def updateFields(self):
        super(AnnouncementsControlPanelForm, self).updateFields()
        self.fields['site_announcement'].widgetFactory = TinyMCETextFieldWidget
        self.fields['site_disclaimer'].widgetFactory = TinyMCETextFieldWidget







class ISendEmailUsersForm(IEmailTemplateSchema):

    directives.widget(send_to_groups=SelectFieldWidget)
    send_to_groups = schema.List(
        title=u'Send to groups',
        value_type=schema.Choice(
            vocabulary='plone.app.vocabularies.Groups'
        ),
        required=False
    )


    directives.widget(send_to_users=SelectFieldWidget)
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


    directives.widget(select_email_template=SelectFieldWidget)
    select_email_template = schema.Choice(
        title=u'Load Email Template',     
        vocabulary='castle.cms.vocabularies.EmailTemplates', 
        required=False,
        default='None'
    )

@implementer(IEmailTemplateSchema)
@adapter(IDexterityContent)
class Tags(object):
    """Store tags in the Dublin Core metadata Subject field. This makes
    tags easy to search for.
    """

    def __init__(self, context):
        self.context = context

    # the properties below are not necessary the first time when you just want to see your added field(s)
    @property
    def tags(self):
        return set(self.context.Subject())
    @tags.setter
    def tags(self, value):
        if value is None:
            value = ()
        self.context.setSubject(tuple(value))
class SendEmailUsersForm(AutoExtensibleForm, form.Form):
    schema = ISendEmailUsersForm
    implements(IEmailTemplateSchema)

    def template_loaded(self):
        try:
            self.request.form['email-template']
        except Exception:
            return False
        return True
    
    def no_template_loaded(self):
        return not self.template_loaded()

    def set_redirect_url(self, email_template_id):
        redirect_url = '%s/@@announcements-controlpanel' % (self.context.absolute_url())
        if not email_template_id == 'None':
            redirect_url += '?email-template=' + email_template_id
        self.request.response.redirect(redirect_url)

    def getContent(self):
        try:
            email_template_id = str(self.request.form['email-template'])
        except Exception:
            self.ignoreContext = True
            return
        self.status = 'Viewing Email Template "{}"'.format(email_template_id)
        self.context = api.portal.get()['email-templates'][email_template_id]
        return self.context

    # def updateFields(self):
    #     super(SendEmailUsersForm, self).updateFields()
    #     self.fields.omit('unsubscribe_links', 'send_to_categories')
    
    # def updateWidgets(self):
    #     super(SendEmailUsersForm, self).updateWidgets()
    #     self.widgets['select_email_template'].mode = INPUT_MODE
    #     self.widgets['unsubscribe_links'].mode = HIDDEN_MODE
    #     self.widgets['send_to_categories'].mode = HIDDEN_MODE


    @button.buttonAndHandler(u'Load selected template', name='import_template')
    def import_template(self, action):
        messages = IStatusMessage(self.request)
        email_template_id = str(self.request.get('form.widgets.select_email_template'))
        if str(email_template_id) in ('None', ''):
            messages.add(u'No Email Template Selected', type=u'error')
        else:
            messages.add(u'Loaded Email Template "{}"'.format(email_template_id), type=u'info')
            self.set_redirect_url(email_template_id)
    

    @button.buttonAndHandler(u'Save As Template', name='save_template', condition=no_template_loaded)
    def handle_save(self, action):
        import pdb; pdb.set_trace()
        # messages = IStatusMessage(self.request)
        data, errors = self.extractData()
        # error_messages = []
        # required_keys = ('subject', 'body')
        # for key in required_keys: 
        #     if key not in data:
        #         error_messages.append(u'Email Template must have a {}'.format(key))
        # if error_messages:
        #     for message in error_messages:
        #         messages.add(message)
        #     return
        if not errors:
            verify_email_templates_folder(self.context)
            subject = data['subject']
            send_from = data['send_from'] or None
            # send_to_groups =  data['send_to_groups'] or []
            # send_to_users = data['send_to_users'] or []
            # send_to_custom = data['send_to_custom'] or []
            body = data['body']
            unsubscribe_links = RichTextValue( 
                u'<p></p><p></p>'
                u'<p><a href="{{change_url}}">Change your subscription settings</a></p>'
                u'<p><a href="{{unsubscribe_url}}">Unsubscribe from these messages</a></p>',
                'text/html', 'text/html'
            )
            portal = api.portal.get()
            item = createContentInContainer(
                portal['email-templates'],
                'EmailTemplate',
                id=subject,
                # send_to_custom=send_to_custom,
                # send_to_groups=send_to_groups,
                # send_to_users=send_to_users,
                body=body,
                subject=subject,
                send_from=send_from,
                title=subject,
                unsubscribe_links=unsubscribe_links
            )
            if item:
                messages = IStatusMessage(self.request)
                messages.add(u'Email Template saved as "{}"'.format(item.getId()), type=u"info")
                self.set_redirect_url(item.id)

    @button.buttonAndHandler(u'Cancel')
    def handle_cancel(self, action):
        """User cancelled. Redirect back to the front page.
        """
        contextURL = self.context.absolute_url()
        self.request.response.redirect(contextURL)

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


class ISendEmailSubscribersForm(IEmailTemplateSchema):
    

    directives.widget(send_to_categories=SelectFieldWidget)
    send_to_categories = schema.List(
        title=u'Send to categories',
        required=False,
        value_type=schema.Choice(
            vocabulary='castle.cms.vocabularies.EmailCategories'
        )
    )



    body = RichText(
        title=u'Body',
        description=u'Message body',
        default_mime_type='text/html',
        output_mime_type='text/html',
        allowed_mime_types=('text/html',),
        required=True
    )


    directives.widget(select_email_template=SelectFieldWidget)
    select_email_template = schema.Choice(
        title=u'Load Email Template',     
        vocabulary='castle.cms.vocabularies.EmailTemplates', 
        required=False,
        default='None'
    )

class SendEmailSubscribersForm(AutoExtensibleForm, form.Form):
    schema = ISendEmailSubscribersForm
    def no_template_loaded(self):
        try:
            self.request.form['email-template']
        except Exception:
            return True
        return False

    def set_redirect_url(self, email_template_id):
        redirect_url = '%s/@@announcements-controlpanel' % (self.context.absolute_url())
        if not email_template_id == 'None':
            redirect_url += '?email-template=' + email_template_id
        redirect_url += '#autotoc-item-autotoc-1'
        self.request.response.redirect(redirect_url)

    def getContent(self):
        print('i got here2')

        try:
            email_template_id = self.request.form['email-template']
            email_template_id = str(email_template_id)
            self.status = 'Viewing Email Template "{}"'.format(email_template_id)
        except Exception:
            self.ignoreContext = True
            return
        self.context = api.portal.get()['email-templates'][email_template_id]
        return self.context

    # def updateFields(self):
    #     super(SendEmailSubscribersForm, self).updateFields()
    #     self.fields.omit('send_to_groups', 'send_to_users', 'send_to_custom')
        

    # def updateWidgets(self):
    #     super(SendEmailSubscribersForm, self).updateWidgets()
    #     self.widgets['send_to_groups'].mode = HIDDEN_MODE
    #     self.widgets['send_to_users'].mode = HIDDEN_MODE
    #     self.widgets['send_to_custom'].mode = HIDDEN_MODE
    #     self.widgets['select_email_template'].mode = INPUT_MODE
    #     self.widgets['send_to_categories'].mode = INPUT_MODE

    def action(self):
        print('action')
        return self.context.absolute_url() + '/@@announcements-controlpanel' + '#autotoc-item-autotoc-1'

    @button.buttonAndHandler(u'Save as template', name='handle_save2', condition=no_template_loaded)
    def handle_save2(self, action):
        # import pdb; pdb.set_trace()
        data, errors = self.extractData()

            # return
        if not errors:
            subject = data['subject']
            body = data['body']
            send_to_custom = data['send_to_custom'] or []
            send_to_groups =  data['send_to_groups'] or []
            send_to_users = data['send_to_users'] or []
            unsubscribe_links = data['unsubscribe_links'] or RichTextValue(u'')
            try:
                send_from = data['send_from']
            except Exception:
                send_from = None

            portal = api.portal.get()
            item = createContentInContainer(
                portal['email-templates'],
                'EmailTemplate',
                id=subject,
                title=subject,
                send_to_custom=send_to_custom,
                send_to_groups=send_to_groups,
                send_to_users=send_to_users,
                body=body,
                subject=subject,
                send_from=send_from,
                unsubscribe_links=unsubscribe_links
            )
            if item:
                messages = IStatusMessage(self.request)
                messages.add(u'Email Template saved as "{}"'.format(item.getId()), type=u"info")
            self.set_redirect_url(item.id)

            

    @button.buttonAndHandler(u'Load selected template', name='import_template2', condition=no_template_loaded)
    def import_template2(self, action):

        messages = IStatusMessage(self.request)
        email_template_id = str(self.request.get('form.widgets.select_email_template'))
        if str(email_template_id) in ('None', ''):
            messages.add(u'No Email Template Selected', type=u'error')
        else:
            messages.add(u'Loaded Email Template "{}"'.format(email_template_id), type=u'info')
        self.set_redirect_url(email_template_id)

    @button.buttonAndHandler(u'Send', name='send2')
    def handle_send2(self, action):
        data, errors = self.extractData()
        if not errors:
            utils = Utils(self.context, self.request)
            public_url = utils.get_public_url()
            html = data['body'].output + data['unsubscribe_links'].output
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

    @button.buttonAndHandler(u'Cancel', name='cancel2')
    def handle_cancel2(self, action):
        """User cancelled. Redirect back to the front page.
        """
        contextURL = self.context.absolute_url()
        self.request.response.redirect(contextURL)

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


class ManageSubscribers(BrowserView):
    def get_page(self, page):
        subscribers = []
        for email, subscriber in subscribe.get_page(page):
            subscribers.append({
                subscriber['email'],
                subscriber['confirmed'],
                subscriber['created']
            })
        return subscribers
