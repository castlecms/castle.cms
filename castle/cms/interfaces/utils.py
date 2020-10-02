from zope.interface import Interface


class IUtils(Interface):

    def get_registry_value(name, default):
        pass

    def get_object_url(object):
        pass

    def get_object(val):
        pass

    def has_image(obj):
        pass

    def format_date(date, format):
        pass

    def iso_date(date):
        pass

    def valid_date(date):
        pass

    def get_location(obj):
        pass

    def get_locations(obj):
        pass

    def get_youtube_url(obj):
        pass

    def clean_youtube_url(url):
        pass

    def get_external_youtube_url(obj):
        pass

    def get_uid(obj):
        pass

    def get_scale_url(content, scale):
        pass

    def get_main_links():
        pass

    def get_actions(name):
        pass

    def get_folder_section():
        pass

    def get_public_url():
        pass

    def render_breadcrumbs():
        pass

    def search():
        pass

    def is_anonymous():
        pass

    def site():
        pass

    def truncate_text():
        pass

    def get_popular_tags():
        pass

    def focal_image_tag():
        pass

    def normalize():
        pass

    def get_logo():
        pass

    def get_next_prev():
        pass

    def get_summary_text():
        pass

    def add_resource_on_request():
        pass

    def get_path():
        pass

    def get_backend_url_no_trailing_slash():
        pass


class IDashboardUtils(Interface):
    def get_totals():
        pass

    def find_areas_of_interest():
        pass

    def sessions():
        pass

    def is_root():
        pass

    def get_path():
        pass

    def parse_ua():
        pass

    def get_in_review():
        pass

    def get_recently_modified():
        pass

    def get_recently_created():
        pass

    def get_creator():
        pass

    def get_modifier():
        pass

    def has_add_permission():
        pass

    def whois():
        pass
