import re

from lxml.html import fromstring
from lxml.html import tostring
from lxml.html.clean import Cleaner


_truncate_cleaner = Cleaner(
    scripts=True, javascript=True, comments=True, style=True, links=True,
    meta=True, page_structure=True, embedded=True, frames=True, forms=True,
    annoying_tags=True, remove_tags=('div',), kill_tags=('img', 'hr'),
    remove_unknown_tags=True)


def truncate_text(text, max_words=30, more_link=None, clean=False):
    """
    adapted from Django
    """

    if not isinstance(text, basestring):
        return ''

    if clean:
        try:
            if not isinstance(text, unicode):
                text = text.decode('utf8')
            xml = fromstring(text)
            _truncate_cleaner(xml)
            # also remove empty tags...
            for p in xml.xpath("//p"):
                if len(p):
                    continue
                t = p.text
                if not (t and t.replace('&nbsp;', '').strip()):
                    p.getparent().remove(p)
            text = tostring(xml)
        except Exception:
            pass
    length = int(max_words)
    if length <= 0:
        return u''
    html4_singlets = ('br', 'col', 'link', 'base',
                      'img', 'param', 'area', 'hr', 'input')
    # Set up regular expressions
    re_words = re.compile(r'&.*?;|<.*?>|(\w[\w-]*)', re.U)
    re_tag = re.compile(r'<(/)?([^ ]+?)(?: (/)| .*?)?>')
    # Count non-HTML words and keep note of open tags
    pos = 0
    end_text_pos = 0
    words = 0
    open_tags = []
    while words <= length:
        m = re_words.search(text, pos)
        if not m:
            # Checked through whole string
            break
        pos = m.end(0)
        if m.group(1):
            # It's an actual non-HTML word
            words += 1
            if words == length:
                end_text_pos = pos
            continue
        # Check for tag
        tag = re_tag.match(m.group(0))
        if not tag or end_text_pos:
            # Don't worry about non tags or tags after our truncate point
            continue
        closing_tag, tagname, self_closing = tag.groups()
        tagname = tagname.lower()  # Element names are always case-insensitive
        if self_closing or tagname in html4_singlets:
            pass
        elif closing_tag:
            # Check for match in open tags list
            try:
                i = open_tags.index(tagname)
            except ValueError:
                pass
            else:
                # SGML: An end tag closes, back to the matching start tag,
                # all unclosed intervening start tags with omitted end tags
                open_tags = open_tags[i + 1:]
        else:
            # Add it to the start of the open tags list
            open_tags.insert(0, tagname)

    if words <= length:
        # Don't try to close tags if we don't need to truncate
        return text
    out = text[:end_text_pos]
    out += '&hellip;'
    if more_link:
        out += ' <a href="%s">more &#x2192;</a>' % more_link
    # Close any tags still open
    for tag in open_tags:
        out += '</%s>' % tag
    # Return string
    return out
