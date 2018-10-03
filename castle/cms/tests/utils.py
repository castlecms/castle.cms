from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC  # noqa
from selenium.webdriver.support.ui import WebDriverWait
from zope.component import getMultiAdapter

import castle
import os
import time


src_dir = os.path.sep.join(castle.__file__.split(os.path.sep)[:-3])


def dismiss_tour(driver, wait=1):
    try:
        el = WebDriverWait(driver, wait).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '.introjs-skipall')))
        el.click()
    except Exception:
        return
    if el:
        try:
            el.click()
        except Exception:
            pass


def screenshot(selenium, name):
    filepath = os.path.join(src_dir, 'error_clicking_%s.png' % name)
    selenium.get_screenshot_as_file(filepath)
    return filepath


def click_it(driver, method, locator, wait=10):
    try:
        element = WebDriverWait(driver, wait).until(
            EC.element_to_be_clickable((method, locator)))
        element.click()
    except Exception:
        # log error but still raise exception because we don't want to have
        # to wait for the tests to finish in order to inspect the problem
        filepath = screenshot(driver, locator)
        raise Exception('Unable to find or click element {}\n{}'.format(
            locator, filepath))


def clear_it(web_element):
    try:
        web_element.clear()
    except Exception:
        text_length = len(web_element.text)
        while text_length > 0:
            web_element.send_keys(Keys.DELETE)
            text_length -= 1


def get_element(driver, method, locator, wait=10,
                detection=EC.visibility_of_element_located):
    try:
        element = WebDriverWait(driver, wait).until(
            detection((method, locator)))
        return element
    except Exception:
        filepath = screenshot(driver, locator)
        raise Exception('unable to find element %s\n%s' % (
            locator, filepath
        ))


def mousedown(driver, method, locator):
    # this will simulate a mousedown and up event.  This is a lower
    # level interface with mouse events and in the background is
    # calling a mousedown
    # some of the mosaic toolbar items need this instead of a normal "click"
    action_element = get_element(driver, method, locator)
    actionchain = ActionChains(driver)
    actionchain.click(action_element)
    actionchain.perform()


def create_page(selenium, pagetype='document'):
    click_it(selenium, By.CSS_SELECTOR, '.castle-toolbar-add a')
    click_it(selenium, By.CSS_SELECTOR, '.contenttype-document-container a')
    title_field = get_element(selenium, By.CSS_SELECTOR, '#contentTitle')
    title_field.send_keys('test_' + pagetype)
    click_it(selenium, By.CSS_SELECTOR,
             '#add-modal-react-container .modal-footer .plone-btn-primary')

    tmpcss = pagetype
    if pagetype == 'basic' or pagetype == 'document':
        tmpcss = 'default/' + tmpcss
    else:
        tmpcss = 'castle/' + tmpcss

    # open the select layout dialog
    click_it(selenium, By.CSS_SELECTOR, '.mosaic-button-layout')
    click_it(selenium, By.CSS_SELECTOR, '.mosaic-button-changelayout')
    click_it(selenium, By.CSS_SELECTOR,
             '.mosaic-select-layout [data-value="%s.html"]' % tmpcss)
    click_it(selenium, By.CSS_SELECTOR, '.mosaic-button-save')


def create_news_item(selenium, newsitem_title):
    get_element(selenium, By.CSS_SELECTOR, '.castle-toolbar-add a').click()
    click_it(selenium, By.CSS_SELECTOR, '.contenttype-news-item-container a')
    title_field = get_element(selenium, By.CSS_SELECTOR, '#contentTitle')
    title_field.send_keys('test_' + newsitem_title)
    click_it(selenium, By.CSS_SELECTOR,
             '#add-modal-react-container .modal-footer .plone-btn-primary')
    click_it(selenium, By.CSS_SELECTOR, '.mosaic-button-save')


def create_folder(selenium, foldertype, name=None):
    click_it(selenium, By.CSS_SELECTOR, '.castle-toolbar-add a')
    click_it(selenium, By.CSS_SELECTOR, '.contenttype-folder-container a')
    entry_field = get_element(selenium, By.CSS_SELECTOR, '#contentTitle')
    title = name
    if title is None:
        title = 'test_' + foldertype
    entry_field.send_keys(title)
    click_it(selenium, By.CSS_SELECTOR,
             '#add-modal-react-container .modal-footer .plone-btn-primary')
    click_it(selenium, By.CSS_SELECTOR, '.mosaic-button-layout')
    click_it(selenium, By.CSS_SELECTOR, '.mosaic-button-changelayout')
    click_it(
        selenium, By.CSS_SELECTOR,
        '.mosaic-select-layout [data-value="castle/%s.html"]' % foldertype)
    click_it(selenium, By.CSS_SELECTOR, '.mosaic-button-save')


def prep_file_upload(selenium, filetoupload, what):
    get_element(selenium, By.CSS_SELECTOR, '.castle-toolbar-add a').click()
    get_element(selenium, By.CSS_SELECTOR, ".autotoc-level-upload").click()
    click_it(selenium, By.CSS_SELECTOR,
             '.castle-upload-container .droparea button')
    # send file name to hidden input field
    get_element(
        selenium, By.CSS_SELECTOR,
        '.castle-upload-container input[type="file"]',
        detection=EC.presence_of_element_located).send_keys(filetoupload)
    # enter title
    get_element(
        selenium, By.CSS_SELECTOR,
        '#castle-upload-field-title').click()
    get_element(
        selenium, By.CSS_SELECTOR,
        '#castle-upload-field-title').send_keys(what)
    # enter description
    # for some reason the element needs to be clicked prior to
    # entering text into it.
    get_element(
        selenium, By.CSS_SELECTOR,
        '#castle-upload-field-description').click()
    get_element(
        selenium, By.CSS_SELECTOR,
        '#castle-upload-field-description').send_keys(what)


def add_tag(selenium, tagtoadd):
    # click edit
    click_it(selenium, By.CSS_SELECTOR, '.castle-toolbar-edit a')
    # click properties
    click_it(selenium, By.CSS_SELECTOR, '.mosaic-button-properties')
    # click category tab
    click_it(selenium, By.LINK_TEXT, "Categorization")
    # type tag into tag select2
    entry_field = get_element(
        selenium, By.CSS_SELECTOR,
        '#formfield-form-widgets-IDublinCore-subjects .select2-input')
    entry_field.send_keys(tagtoadd)
    time.sleep(1)
    # press enter to add tag
    entry_field.send_keys(Keys.ENTER)
    click_it(selenium, By.CSS_SELECTOR, '.mosaic-overlay-ok-button')
    # save
    click_it(selenium, By.CSS_SELECTOR, '.mosaic-button-save')


def get_tile(request, context, name, data):
    tile = getMultiAdapter((context, request), name=name)

    for key in data.iterkeys():
        tile.data[key] = data[key]

    return tile


def render_tile(request, context, name, data):
    tile = get_tile(request, context, name, data)
    page = tile.render()
    return page
