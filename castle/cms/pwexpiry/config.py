from zope.i18nmessageid import MessageFactory

_ = MessageFactory("collective.pwexpiry")

# Ideally, this should be language dependent, but we'll do US default for now
DATETIME_FORMATSTRING = "%m/%d/%Y %H:%M"
