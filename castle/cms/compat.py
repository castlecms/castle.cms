import six


# python 3 compatible stuff


try:
    six.text_type = six.text_type
except NameError:
    six.text_type = str

try:
    six.string_types = six.string_types
except NameError:
    six.string_types = str
