*** Settings ***

 Force Tags  wip-not_in_docs

 Resource  plone/app/robotframework/selenium.robot
 Resource   keywords.robot
 Resource   common.robot

 Test Setup  Open test browser
 Test Teardown  Close all browsers

*** Test Cases ***

Basic Castle Functions
   Given a logged-in site administrator
   Go to  ${PLONE_URL}/manage
   Page should contain  Zope

   Go to  ${PLONE_URL}
   Sleep  1

   Wait Until Page Contains Element  css=.introjs-skipall
   Click Element  css=.introjs-skipall
   Element Should Be Visible  css=div.castle-toolbar-container-side
   Element Should Be Visible  css=div.castle-toolbar-container-top
