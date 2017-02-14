from Acquisition import aq_inner
from Acquisition import aq_parent
from plone.app.dexterity.behaviors.discussion import IAllowDiscussion
from plone.app.discussion.browser.conversation import ConversationView
from plone.app.discussion.interfaces import IDiscussionSettings
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from zope.component import queryUtility


IAllowDiscussion['allow_discussion'].description = (u'Allow discussion for this content '
                                                    u'object. If set on folder, it will '
                                                    u'enable for all items inside folder.')


class CastleConversationView(ConversationView):

    def enabled(self):
        """
        We only support dexterity anyways so do complete check here...

        Returns True if discussion is enabled for this conversation.

        This method checks five different settings in order to figure out if
        discussion is enable on a specific content object:

        1) Check if discussion is enabled globally in the plone.app.discussion
           registry/control panel.

        2) Check if the allow_discussion boolean flag on the content object is
           set. If it is set to True or False, return the value. If it set to
           None, try further.

        3) Check if discussion is allowed for the content type.
        """
        context = aq_inner(self.context)

        # Fetch discussion registry
        registry = queryUtility(IRegistry)
        settings = registry.forInterface(IDiscussionSettings, check=False)

        # Check if discussion is allowed globally
        if not settings.globally_enabled:
            return False

        # Check if discussion is allowed on the content object
        if hasattr(context, "allow_discussion"):
            if context.allow_discussion is not None:
                return context.allow_discussion

        # now, check parent for setting...
        parent = aq_parent(context)
        if hasattr(parent, "allow_discussion"):
            if parent.allow_discussion:
                return True

        # Check if discussion is allowed on the content type
        portal_types = getToolByName(self, 'portal_types')
        document_fti = getattr(portal_types, context.portal_type)
        return document_fti.getProperty('allow_discussion')
