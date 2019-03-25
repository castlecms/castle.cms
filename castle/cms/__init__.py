from zope.i18nmessageid import MessageFactory

_ = MessageFactory('castle.cms')


zodbupdate_decode_dict = {
    'five.intid.keyreference KeyReferenceToPersistent root_dbname': 'utf-8',
    'five.intid.keyreference KeyReferenceToPersistent root_oid': 'utf-8',
    'five.intid.keyreference KeyReferenceToPersistent oid': 'bytes',
    'five.intid.keyreference KeyReferenceToPersistent dbname': 'utf-8',
}


def initialize(context):
    """Initializer called when used as a Zope 2 product."""
