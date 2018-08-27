from zope.schema import TextLine


class TextInputSelect(TextLine):

    def __init__(self, vocabulary=None, *args, **kw):
        super(TextInputSelect, self).__init__(*args, **kw)
        self.vocabulary = vocabulary
