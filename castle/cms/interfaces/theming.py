from zope.interface import Interface


class ICastleCmsThemeTemplateLoader(Interface):
    """
    CastleCMS implementation of a theme template loader.
    """

    def load(filename, backup):
        """
        Loads and return a template file.

        The format parameter determines will parse the file. Valid
        options are `xml` and `text`.
        """

    def previous_template_file_cache(filename, data):
        """
        If we have read and create the template before and it is not too old,
        load the cache instead of the expensive load.
        """

    def read_file(filename):
        """
        We read the file using the filename, if we have encountered the file before.  Send the cache.
        """

    def load_raw(raw):
        """
        Load the template using the raw format.
        """
