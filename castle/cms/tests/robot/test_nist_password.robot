*** Settings ***

 Force Tags  wip-not_in_docs

 Resource   plone/app/robotframework/selenium.robot
 Resource   keywords.robot
 Resource   common.robot

 Test Setup  Open test browser
 Test Teardown  Close all browsers

*** Test Cases ***

Test verify create user
   Given a logged-in site administrator
   Go to  ${PLONE_URL}/@@usergroup-userprefs
   Close the Tour Popup

   Wait Until Page Contains Element  css=.plone-btn-primary
   Click Element   css=.plone-btn-primary

   Wait Until Page Contains Element  css=#form-widgets-email
   Input Text  css=#form-widgets-email  foo.bar@gmail.com
   Input Text  css=#form-widgets-username  Dingus
   Input Text  css=#form-widgets-password  Asdfasdf1234!
   Input Text  css=#form-widgets-password_ctl  Asdfasdf1234!
   Sleep  1
   Click Element  css=#form-buttons-register

   Wait Until Page Contains Element  css=.standalone
   Click Element  css=.standalone

   Import library  Dialogs
   Pause execution