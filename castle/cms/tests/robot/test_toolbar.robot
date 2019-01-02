*** Settings ***

 Force Tags  wip-not_in_docs

 Resource  plone/app/robotframework/selenium.robot
 Resource   keywords.robot
 Resource   common.robot

 Test Setup  Open test browser
 Test Teardown  Close all browsers

*** Test Cases ***

Verify Toolbar buttons
   Given a logged-in site administrator
   Go to  ${PLONE_URL}

   Close The Tour Popup

   Element Should Be Visible  css=li.castle-toolbar-view-page
   Element Should Be Visible  css=li.castle-toolbar-folder_contents
   Element Should Be Visible  css=li.castle-toolbar-add
   Element Should Be Visible  css=li.castle-toolbar-edit
   Element Should Be Visible  css=li.castle-toolbar-state
   Element Should Be Visible  css=li.castle-toolbar-design
   Element Should Be Visible  css=li.castle-toolbar-sharing
   Element Should Be Visible  css=li.castle-toolbar-history
   Element Should Be Visible  css=li.castle-toolbar-aliases
   Element Should Be Visible  css=li.castle-toolbar-syndication
   Element Should Be Visible  css=li.castle-toolbar-analytics
   Element Should Be Visible  css=li.castle-toolbar-preview
   Element Should Be Visible  css=li.castle-toolbar-slots

   # Some things should *not* be here

   Element Should Not Be Visible  css=li.castle-toolbar-cut
   Element Should Not Be Visible  css=li.castle-toolbar-copy
   Element Should Not Be Visible  css=li.castle-toolbar-delete
   Element Should Not Be Visible  css=li.castle-toolbar-rename

   # Now the top menus
   Element Should Be Visible  css=div.castle-toolbar-container-top
   Element Should Be Visible  css=div.castle-btn-dropdown-messages
   Element Should Be Visible  css=div.castle-btn-dropdown-cog
   Element Should Be Visible  css=div.castle-btn-dropdown-user

   # None of the menus should be open
   Element Should Not Be Visible  css=li.castle-toolbar-site_setup
   Element Should Not Be Visible  css=li.castle-toolbar-dashboard

   # First..
   Close The Tour Popup

   # Now lets see if any of these buttons actually work
   # Top Menu
   Click Element   css=div.castle-btn-dropdown-cog
   Sleep  .25
   Element Should Be Visible  css=li.castle-toolbar-site_setup
   Element Should Be Visible  css=li.castle-toolbar-impersonate
   Element Should Be Visible  css=li.castle-toolbar-tour
   Element Should Be Visible  css=li.castle-toolbar-recycle
   Click Element   css=div.castle-btn-dropdown-cogopened
   Element Should Not Be Visible  css=li.castle-toolbar-site_setup

   Click Element    css=div.castle-btn-dropdown-user
   Element Should Be Visible  css=li.castle-toolbar-dashboard
   Element Should Be Visible  css=li.castle-toolbar-preferences
   Element Should Be Visible  css=li.castle-toolbar-activity_log
   Element Should Be Visible  css=li.castle-toolbar-logout
   Click Element    css=div.castle-btn-dropdown-useropened
   Element Should Not Be Visible  css=li.castle-toolbar-dashboard
