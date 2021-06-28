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
   Go to  ${PLONE_URL}/@@security-controlpanel
   Close the Tour Popup

   Wait Until Page Contains Element  css=#form-widgets-nist_password_mode-0
   Click Element  css=#form-widgets-nist_password_mode-0
   Click Element  css=#form-buttons-save

   Go to  ${PLONE_URL}/@@usergroup-userprefs
   Close the Tour Popup

   Wait Until Page Contains Element  css=.castle-btn-reset-password
   Click Element   css=.castle-btn-reset-password
   Element Should Contain  css=.portalMessage.warning  Password must be longer than 12 characters

   Input Text  css=.password-reset-one  PassWithNoSpecial
   Input Text  css=.password-reset-two  PassWithNoSpecial
   Element Should Contain  css=.portalMessage.warning  Password must contain at least 1 special character(s)

   Input Text  css=.password-reset-one  BeTt3Rp@s5w*rD
   Input Text  css=.password-reset-two  BeTt3Rp@s5w*rD
   Page Should Not Contain Element  css=.portalMessage.warning
   Click Element  css=.reset-password

   Page Should Contain Element  css=#confirmation-modal
