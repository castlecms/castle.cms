*** Settings ***

Force Tags  wip-not_in_docs

Resource  plone/app/robotframework/variables.robot
Resource  plone/app/robotframework/selenium.robot
Resource  castle/cms/tests/robot/keywords.robot

# Library  Remote  ${PLONE_URL}/RobotRemote

Test Setup  Open test browser
Test Teardown  Close all browsers
*** Variables ***

${SLIDESHOW_NAME} =  cool-slideshow
@{SLIDE_TYPES} =  Background Image  Left Image Right Text  Background Video  Left Video Right Text  Resource Slide


*** Test Cases ***

Admin Can Create Slideshow
    I create a new slideshow
    I verify my slideshow

#  Seems to fail on chrome robot test   
# Admin Can Add Background Image Slide
#     Verify Admin Can Add Background Image Slide

#  Loop not yet functional
# Verify Admin Can Add Any Valid Slide Type
#     FOR  ${SLIDE_TYPE}  IN  @{SLIDE_TYPES}
#         Log  hello, there
#         Log  ${SLIDE_TYPE}
#         Verify Admin Can Add ${SLIDE_TYPE} Slide
#     END


*** Keywords ***
Verify Admin Can Add ${SLIDE_TYPE} Slide
    I create a new slideshow
    
    I add a new ${SLIDE_TYPE} slide

    Then page should contain  ${SLIDE_TYPE} slide


I create a new slideshow
    Given a logged-in site administrator
      and a slideshow '${SLIDESHOW_NAME}'

I verify my slideshow
    When I go to view ${SLIDESHOW_NAME}
     and Close the Tour Popup
     and Wait until page contains  ${SLIDESHOW_NAME}

    Then Page should contain  ${SLIDESHOW_NAME}

I go to view ${ID}
    Go to  ${PLONE_URL}/${ID}/view

I add a new ${SLIDE_TYPE} slide
    Go to  ${PLONE_URL}/${SLIDESHOW_NAME}/edit
    Close the Tour Popup
    
    Click Button  Layout
    Click Button  Customize
    # Wait until page contains  Insert
    Click Element  xpath=//*[contains(text(), "Insert")]
    # Wait until page contains  Slide (for Slideshow only)
    Click Element  css=.mosaic-option-castle-cms-slide>div

    Click Element  xpath=//*[contains(text(), "${SLIDE_TYPE}")]
    # Sleep  30
    Click Button  css=.pattern-modal-buttons>#buttons-save
    Click Button  css=.mosaic-toolbar-primary-functions>.mosaic-button-save
    # Click Button  Save