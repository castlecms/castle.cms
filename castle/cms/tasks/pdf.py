import logging
import time

from castle.cms.pdf.generator import PDFGenerationError
from castle.cms.pdf.generator import create
from castle.cms.pdf.generator import create_raw_from_view
from castle.cms.pdf.generator import screenshot
from castle.cms.settings import PDFSetting
from castle.cms.utils import retriable
from collective.celery import task
from collective.celery.utils import getCelery


logger = logging.getLogger('castle.cms')


@retriable()
def _create_pdf(obj, html, css, additional_args={}):
    try:
        blob = create(html, css, additional_args)
    except PDFGenerationError:
        logger.error('princexml error converting pdf', exc_info=True)
        return
    sblob = screenshot(blob)
    if not getCelery().conf.task_always_eager:
        obj._p_jar.sync()
    settings = PDFSetting(obj)
    settings.put(blob)
    settings.put_screenshot(sblob)


@task.as_admin()
def create_pdf(obj, html, css, additional_args={}):
    # this completes so fast we get conflict errors on save sometimes.
    # just cool it a bit
    time.sleep(2)
    if not getCelery().conf.task_always_eager:
        obj._p_jar.sync()
    return _create_pdf(obj, html, css, additional_args)


@task.as_admin()
def create_pdf_from_view(obj, css_files=[], unrestricted_traverse=False, additional_args={}):
    # this completes so fast we get conflict errors on save sometimes.
    # just cool it a bit
    time.sleep(2)
    if not getCelery().conf.task_always_eager:
        obj._p_jar.sync()
    html, css = create_raw_from_view(
        obj,
        css_files=css_files,
        unrestricted_traverse=unrestricted_traverse,
    )
    return _create_pdf(obj, html, css, additional_args)
