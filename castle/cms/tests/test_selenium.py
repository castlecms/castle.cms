from Acquisition import aq_parent
from castle.cms import authentication
from castle.cms.testing import SELENIUM_PLONE_FUNCTIONAL_TESTING
from castle.cms.tests import utils as test_utils
from plone.app.testing import selenium_layers
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC  # noqa
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select

import os
import transaction
import unittest2 as unittest


_dir = os.path.dirname(os.path.realpath(__file__))
TEST_FILE = os.path.join(_dir, 'testimage.png')


class CreateSite(unittest.TestCase):
    """
    Read: https://pypi.python.org/pypi/plone.app.testing
          https://github.com/plone/plone.app.testing/blob/master/plone/app/testing/selenium_layers.pypi
    for more info

    Xvfb :99 &
    export DISPLAY=:99

    To save screenshot while debugging tests:
        self.selenium.save_screenshot('/opt/plone/src/foobar.png')
    """

    layer = SELENIUM_PLONE_FUNCTIONAL_TESTING
    username_selector = '.castle-secure-login-form-code-authorized .username'
    password_selector = '.castle-secure-login-form-code-authorized .password'
    login_selector = ('.castle-secure-login-form-code-authorized '
                      '.castle-secure-login-login-button')

    def setUp(self):
        self.selenium = self.layer['selenium']
        self.portal = self.layer['portal']
        self.app = aq_parent(self.portal)
        authentication.install_acl_users(self.app)
        transaction.commit()

    def login(self):
        self.open(self.app.absolute_url() + '/@@secure-login')
        self.get(self.username_selector).send_keys(SITE_OWNER_NAME)
        self.get(self.password_selector).send_keys(SITE_OWNER_PASSWORD)
        self.get(self.login_selector).click()
        self.selenium.get(self.portal.absolute_url())
        test_utils.dismiss_tour(self.selenium, 8)

    def open(self, url):
        selenium_layers.open(self.selenium, url)

    def click(self, selector):
        test_utils.click_it(self.selenium, By.CSS_SELECTOR, selector)

    def get(self, selector, detection=EC.visibility_of_element_located):
        return test_utils.get_element(
            self.selenium, By.CSS_SELECTOR, selector, detection=detection)

    def screenshot(self):
        filepath = os.path.join(test_utils.src_dir, 'current.png')
        self.selenium.get_screenshot_as_file(filepath)

    def wait_then_click(self, selector, wait=10):
        el = WebDriverWait(self.selenium, wait).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, selector)))
        el.click()
        return el

    def get_element(self, method, locator, wait=10):
        return test_utils.get_element(self.selenium, method, locator, wait)

    def is_element_present(self, method, locator, wait=10):
        try:
            WebDriverWait(self.selenium, wait).until(
                EC.presence_of_element_located((method, locator)))
            return True
        except:
            return False

    def test_query_listing(self):
        selenium = self.selenium
        self.login()
        # create a folder
        test_utils.create_folder(selenium, 'folder-query', 'testfolder')
        # add tag for folder
        test_utils.add_tag(selenium, 'test_tag')
        # create some content in this new folder
        # create a page
        test_utils.create_page(selenium, 'basic')
        # add tag for this page
        # click edit
        test_utils.add_tag(selenium, 'test_tag')
        # create a page
        test_utils.create_page(selenium, 'document')
        # add tag for this page
        test_utils.add_tag(selenium, 'test_tag')
        test_utils.create_page(selenium, 'twocolumn')
        test_utils.add_tag(selenium, 'test_tag')
        test_utils.create_page(selenium, 'threecolumn')
        test_utils.add_tag(selenium, 'test_tag')
        # fill rest with news items until pagenation occurs
        pagen_trigger = 12
        while pagen_trigger > 0:
            test_utils.create_news_item(selenium, 'test_news%s' % pagen_trigger)
            test_utils.add_tag(selenium, 'test_tag')
            pagen_trigger -= 1

        selenium.get(self.portal.absolute_url() + '/testfolder')

    def test_add_from_dashboard(self):
        selenium = self.selenium
        self.login()
        # navigate to dashboard
        selenium.get(self.portal.absolute_url() + '/@@dashboard')
        # add a page
        self.get('.add-content-btn.contenttype-document').click()
        # provid page title
        self.get('#contentTitle').send_keys('foobar-dash')
        # click save on modal dialog
        self.click('#add-modal-react-container .modal-footer .plone-btn-primary')
        self.click('.mosaic-button-save')
        self.assertEqual(
            self.selenium.current_url, self.portal.absolute_url() + '/foobar-dash')

    def test_image_edit(self):
        selenium = self.selenium
        self.login()
        selenium.get(self.portal.absolute_url())
        # get image for upload
        try:
            test_utils.prep_file_upload(self.selenium, TEST_FILE, 'image')
        except:
            test_utils.prep_file_upload(self.selenium, TEST_FILE, 'image')
        # click image edit button
        self.get('.file-list .castle-btn-edit').click()
        # click rotate
        self.get('.castle-cropper-container .castle-btn-rotate-left').click()
        # click save
        self.get('.castle-cropper-container .castle-btn-save').click()
        # click upload
        self.get('.file-list .castle-btn-upload').click()
        # will error if can't find it
        self.get('.finished-container')

    def test_tile_edit(self):
        selenium = self.selenium
        self.login()
        selenium.get(self.portal.absolute_url())
        # create basic page
        test_utils.create_page(selenium, 'basic')
        # click edit
        test_utils.click_it(selenium, By.CSS_SELECTOR, '.castle-toolbar-edit a')
        # get title element
        edit_element = self.get('.mosaic-IDublinCore-title-tile .mosaic-rich-text')
        edit_element.click()
        # clear the text from this field
        test_utils.clear_it(edit_element)
        test_utils.dismiss_tour(self.selenium)
        edit_element.send_keys('new title is right here!')
        # click the save button
        self.click('.mosaic-button-save')
        self.assertTrue('new title' in self.selenium.page_source)

    def test_add_tile(self):
        selenium = self.selenium
        self.login()
        selenium.get(self.portal.absolute_url())
        # create a basic page
        test_utils.create_page(selenium, 'basic')
        # click edit
        self.click('.castle-toolbar-edit a')
        # click customize
        self.click('.mosaic-button-layout')
        self.click('.mosaic-button-customizelayout')
        # click insert select2
        test_utils.mousedown(selenium, By.CSS_SELECTOR, '.mosaic-menu-insert .select2-chosen')
        # select text tile to insert
        test_utils.mousedown(
            selenium, By.CSS_SELECTOR,
            '.select2-results .mosaic-option-plone-app-standardtiles-rawhtml .select2-result-label')
        # click on the page to place this new text tile
        click_placement = self.get('#content .mosaic-IDublinCore-description-tile')
        actionchain = ActionChains(selenium)
        actionchain.move_to_element_with_offset(click_placement, 0, 0)
        actionchain.click(click_placement)
        actionchain.perform()

        container = self.get('.mosaic-selected-tile')
        container.find_element_by_class_name('mosaic-rich-text')

        # click the save button
        try:
            self.click('.mosaic-button-save')
        except:
            self.selenium.find_element_by_id('form-buttons-save').click()

    def test_image_insert(self):
        selenium = self.selenium
        self.login()
        selenium.get(self.portal.absolute_url())
        test_utils.create_page(selenium, 'document')
        # click edit
        self.click('.castle-toolbar-edit a')
        # click description area so it receives focus and mce toolbar is visible
        self.click('#content .mosaic-IRichText-text-tile .mosaic-rich-text')
        self.click('#content .mosaic-IDublinCore-description-tile')
        self.click('#content .mosaic-IRichText-text-tile .mosaic-rich-text')
        # click the mce insert image button
        self.get('[aria-label="Insert/edit image"] button').click()
        # click the external tab
        self.click("#tinymce-autotoc-autotoc-1")
        # specify the external image url
        self.get(".form-group input[name='externalImage']").send_keys(
            'https://plone.org/logo@2x.png')
        # give the image a title
        self.get(".form-group input[name='alt']").send_keys('testimage')
        # click the insert button
        self.get('div.pattern-modal-buttons > input[name="insert"]').click()
        # click the save button
        test_utils.click_it(selenium, By.CSS_SELECTOR, '.mosaic-button-save')

    def test_add_video(self):
        selenium = self.selenium
        self.login()
        selenium.get(self.portal.absolute_url())
        test_utils.create_page(selenium, 'basic')
        self.get('.castle-toolbar-edit a').click()
        test_utils.mousedown(selenium, By.CSS_SELECTOR, '.mosaic-button-layout')
        test_utils.mousedown(selenium, By.CSS_SELECTOR, '.mosaic-button-customizelayout')
        test_utils.mousedown(selenium, By.CSS_SELECTOR, '.mosaic-menu-insert .select2-choice')
        test_utils.mousedown(selenium, By.CSS_SELECTOR, '.mosaic-option-castle-cms-videotile')
        tmpelement = self.get('#castle-cms-videotile-youtube_url')
        tmpelement.send_keys('https://www.youtube.com/watch?v=dQw4w9WgXcQ')
        test_utils.click_it(selenium, By.CSS_SELECTOR, '.plone-modal-footer #buttons-save')
        test_utils.click_it(selenium, By.CSS_SELECTOR, '#content > div:nth-child(2)')
        test_utils.mousedown(selenium, By.CSS_SELECTOR, '.mosaic-button-save')
        self.assertTrue(self.is_element_present(By.CSS_SELECTOR, '.video-container'))

    def test_change_page_title(self):
        selenium = self.selenium
        self.login()
        selenium.get(self.portal.absolute_url())
        # create the page
        test_utils.create_page(selenium, 'basic')
        # page is created, now edit the title
        self.get('.castle-toolbar-edit a').click()
        self.get('h1').send_keys('new title')
        self.click('.mosaic-button-save')

    def test_image_upload(self):
        self.login()
        self.selenium.get(self.portal.absolute_url())
        try:
            test_utils.prep_file_upload(self.selenium, TEST_FILE, 'image')
        except:
            test_utils.prep_file_upload(self.selenium, TEST_FILE, 'image')
        # click submit
        self.click('.castle-upload-container .castle-btn-upload')
        # will error if can't find it
        self.get('.finished-container')

    def test_file_upload(self):
        self.login()
        self.selenium.get(self.portal.absolute_url())
        test_utils.prep_file_upload(self.selenium, TEST_FILE, 'file')
        # click submit
        self.click('.castle-upload-container .castle-btn-upload')
        # will error if can't find it
        self.get('.finished-container')

    def test_createpages(self):
        selenium = self.selenium
        self.login()
        selenium.get(self.portal.absolute_url())
        test_utils.create_page(selenium, 'basic')
        self.assertEqual(self.selenium.current_url,
                         self.portal.absolute_url() + '/test_basic')
        selenium.get(self.portal.absolute_url())
        test_utils.create_page(selenium, 'document')
        self.assertEqual(self.selenium.current_url,
                         self.portal.absolute_url() + '/test_document')
        selenium.get(self.portal.absolute_url())
        test_utils.create_page(selenium, 'twocolumn')
        self.assertEqual(self.selenium.current_url,
                         self.portal.absolute_url() + '/test_twocolumn')
        selenium.get(self.portal.absolute_url())
        test_utils.create_page(selenium, 'threecolumn')
        self.assertEqual(self.selenium.current_url,
                         self.portal.absolute_url() + '/test_threecolumn')

    def test_create_page_under_folder(self):
        selenium = self.selenium
        self.login()
        selenium.get(self.portal.absolute_url())
        test_utils.create_folder(selenium, 'folder')
        test_utils.create_page(selenium, 'basic')
        self.assertEqual(self.selenium.current_url,
                         self.portal.absolute_url() + '/test_folder/test_basic')

    def test_createfolders(self):
        selenium = self.selenium
        self.login()
        selenium.get(self.portal.absolute_url())
        test_utils.create_folder(selenium, 'folder')
        self.assertEqual(self.selenium.current_url, self.portal.absolute_url() + '/test_folder')
        selenium.get(self.portal.absolute_url())
        test_utils.create_folder(selenium, 'folder-query')
        self.assertEqual(
            self.selenium.current_url, self.portal.absolute_url() + '/test_folder-query')

    def test_link(self):
        selenium = self.selenium
        self.login()
        selenium.get(self.portal.absolute_url())
        self.get('.castle-toolbar-add a').click()
        self.get('.contenttype-link-container a').click()
        self.get('#contentTitle').send_keys('foobarlink')
        test_utils.click_it(
            selenium, By.CSS_SELECTOR,
            '#add-modal-react-container .modal-footer .plone-btn-primary')
        test_utils.click_it(selenium, By.ID, 'form-buttons-save')
        self.assertEqual(self.selenium.current_url,
                         self.portal.absolute_url() + '/foobarlink')

    def test_event(self):
        self.login()
        self.generic_add('event')
        self.assertEqual(self.selenium.current_url,
                         self.portal.absolute_url() + '/test_event')

    def test_newsitem(self):
        selenium = self.selenium
        self.login()
        self.get('.castle-toolbar-add a').click()
        self.get('.contenttype-news-item-container a').click()
        self.get('#contentTitle').send_keys('foobar-newsitem')
        test_utils.click_it(
            selenium, By.CSS_SELECTOR,
            '#add-modal-react-container .modal-footer .plone-btn-primary')
        test_utils.click_it(self.selenium, By.CSS_SELECTOR, '.mosaic-button-save')
        self.assertEqual(self.selenium.current_url,
                         self.portal.absolute_url() + '/foobar-newsitem')

    def generic_add(self, testtype):
        self.get('.castle-toolbar-add a').click()
        self.get('.contenttype-%s-container a' % testtype).click()
        self.get('#contentTitle').send_keys('test_%s' % testtype)
        test_utils.click_it(
            self.selenium, By.CSS_SELECTOR,
            '#add-modal-react-container .modal-footer .plone-btn-primary')
        try:
            self.click('.mosaic-button-save')
        except:
            self.selenium.find_element_by_id('form-buttons-save').click()

    def test_impersonate(self):
        self.login()
        self.click('.icon-cog.plone-btn')
        self.click('.castle-toolbar-impersonate')
        self.click('.castle-btn-asanonymous')
        self.get('.userrole-anonymous')
        self.get('#impersonator')
        self.assertTrue('role="toolbar"' not in self.selenium.page_source)
        self.click('#impersonator a.stop')
        self.get('.castle-toolbar-container')

    def test_add_slot_tile(self):
        self.login()
        self.get('.castle-toolbar-slots a').click()
        self.get('.slot-chooser iframe')  # make sure it's loaded...
        self.selenium.switch_to_frame('choose_slot')
        self.get('[data-tile-id="meta-left"]').click()
        self.selenium.switch_to_default_content()
        self.get('[name="slotMode"][value="add"]').click()

        select = Select(self.get('.slot-manager-render-here select'))
        select.select_by_visible_text('Rich text')

        self.selenium.switch_to_frame(
            self.get('#plone-app-standardtiles-rawhtml-content_ifr'))
        self.get('.mce-content-body').send_keys('foobar slot')
        self.selenium.switch_to_default_content()

        # might be outside visibility of selenium screen...
        save_btn = self.get(
            '.pattern-modal-buttons input[value="Save"][type="submit"]',
            detection=EC.presence_of_element_located)
        save_btn.click()

        self.get('.modal .plone-btn').click()
        el = self.get('.tile-container-plone-app-standardtiles-rawhtml')
        self.assertTrue('foobar slot' in el.text)

    def test_preview(self):
        self.login()
        self.get('.castle-toolbar-preview a').click()

        select = Select(self.get('.castle-preview select'))
        select.select_by_visible_text('Tablet')

        self.assertEqual(self.get('.castle-preview iframe').size['width'], 800)

    def test_search(self):
        self.login()
        self.generic_add('document')
        self.open(self.portal.absolute_url() + '/@@search')

        self.get('.search-input').send_keys('test_document')
        self.assertTrue('test_document' in self.get('.searchResults li .result-title').text)
