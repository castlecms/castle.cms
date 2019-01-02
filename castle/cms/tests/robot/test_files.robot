*** Settings ***

 Force Tags  wip-not_in_docs

 Resource   plone/app/robotframework/selenium.robot
 Resource   keywords.robot
 Resource   common.robot

 Test Setup  Open test browser
 Test Teardown  Close all browsers

*** Test Cases ***

Test add files
   Given a logged-in site administrator
   Go to  ${PLONE_URL}

   Set Selenium Speed  .1

   Wait Until Page Contains Element  css=.introjs-skipall
   Click Element  css=.introjs-skipall
   Sleep  1

   Element Should Be Visible  css=div.castle-toolbar-container-side
   Click Element   css=.castle-toolbar-add a

   Execute Javascript  $('#add-modal-react-container .autotoc-level-upload')[0].click()
   Wait Until Page Contains Element  css=.castle-btn-select-files  1

   Click Element  css=.castle-btn-select-files
   Choose File  css=.castle-upload-container input[type="file"]  ${CURDIR}/files/video.mp4
   Wait Until Page Contains Element  css=.file-container:last-child .upload-field-title
   Input Text  css=.file-container:last-child .upload-field-title input  foobar
   Click Element  css=.file-container:last-child .castle-btn-upload
   Wait Until Page Contains Element  css=.file-container:last-child .finished-container

   Click Element  css=.castle-btn-select-files
   Choose File  css=.castle-upload-container input[type="file"]  ${CURDIR}/files/video.mp4
   Wait Until Page Contains Element  css=.file-container:last-child .upload-field-title
   Input Text  css=.file-container:last-child .upload-field-title input  foobar2
   Input Text  css=.file-container:last-child .upload-field-youtube_url input  https://www.youtube.com/watch?v=_uk_6vfqwTA
   Click Element  css=.file-container:last-child .castle-btn-upload
   Wait Until Page Contains Element  css=.file-container:last-child .finished-container

   Click Element  css=.castle-btn-select-files
   Choose File  css=.castle-upload-container input[type="file"]  ${CURDIR}/files/audio.mp3
   Wait Until Page Contains Element  css=.file-container:last-child .upload-field-title
   Input Text  css=.file-container:last-child .upload-field-title input  foobar3
   Click Element  css=.file-container:last-child .castle-btn-upload
   Wait Until Page Contains Element  css=.file-container:last-child .finished-container

   Click Element  css=.castle-btn-select-files
   Choose File  css=.castle-upload-container input[type="file"]  ${CURDIR}/files/test.zip
   Wait Until Page Contains Element  css=.file-container:last-child .upload-field-title
   Input Text  css=.file-container:last-child .upload-field-title input  foobar4
   Click Element  css=.file-container:last-child .castle-btn-upload
   Wait Until Page Contains Element  css=.file-container:last-child .finished-container


   Go to  ${PLONE_URL}/video-repository/video.mp4/view
   Page Should Contain  ${PLONE_URL}/video-repository/video.mp4/@@videoplayer
   Page Should Contain Element  css=video

   Go to  ${PLONE_URL}/video-repository/video.mp4/@@videoplayer
   Page Should Contain Element  css=video

   Go to  ${PLONE_URL}/video-repository/video-1.mp4/view
   Page Should Contain  ${PLONE_URL}/video-repository/video-1.mp4/@@videoplayer
   Page Should Contain Element  css=iframe

   Go to  ${PLONE_URL}/video-repository/video-1.mp4/@@videoplayer
   Page Should Contain Element  css=video

   Go to  ${PLONE_URL}/audio-repository/audio.mp3/view
   Page Should Contain  ${PLONE_URL}/video-repository/audio.mp3/@@audioplayer
   Page Should Contain Element  css=audio

   Go to  ${PLONE_URL}/audio-repository/audio.mp3/@@audioplayer
   Page Should Contain Element  css=audio
