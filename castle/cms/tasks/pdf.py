import time

from castle.cms.pdf.generator import create, create_raw_from_view, screenshot
from castle.cms.settings import PDFSetting
from castle.cms.utils import retriable
from collective.celery import task
from collective.celery.utils import getCelery


@retriable()
def _create_pdf(obj, html, css):
    blob = create(html, css)
    sblob = screenshot(blob)
    if not getCelery().conf.task_always_eager:
        obj._p_jar.sync()
    settings = PDFSetting(obj)
    settings.put(blob)
    settings.put_screenshot(sblob)


@task.as_admin()
def create_pdf(obj, html, css):
    # this completes so fast we get conflict errors on save sometimes.
    # just cool it a bit
    time.sleep(2)
    if not getCelery().conf.task_always_eager:
        obj._p_jar.sync()
    return _create_pdf(obj, html, css)


@task.as_admin()
def create_pdf_from_view(obj, css_files=[]):
    # this completes so fast we get conflict errors on save sometimes.
    # just cool it a bit
    time.sleep(2)
    if not getCelery().conf.task_always_eager:
        obj._p_jar.sync()
    html, css = create_raw_from_view(obj, css_files=css_files)
    return _create_pdf(obj, html, css)
