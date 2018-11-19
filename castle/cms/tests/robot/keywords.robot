*** Keywords *****************************************************************

# --- SETUP ------------------------------------------------------------------

Refresh JS/CSS resources
  # If we do not regenerate the resources meta-bundles, the baseUrl value in
  # config.js is http://foo/plone. We need to trigger the meta-bundles
  # generation from the browser so baseUrl gets the proper value.
  Enable autologin as  Manager
  Execute Javascript    $.post($('body').attr('data-portal-url')+'/@@resourceregistry-controlpanel', {action: 'save-registry', _authenticator: $('input[name="_authenticator"]').val()});
  Disable Autologin

# --- GIVEN ------------------------------------------------------------------

a logged-in site administrator
  Enable autologin as  Site Administrator  Contributor  Reviewer
  Set autologin username  admin

a document '${title}'
  Create content  type=Document  id=doc  title=${title}

a file '${title}'
  Create content  type=File  id=file  title=${title}

a news item '${title}'
  Create content  type=News Item  id=doc  title=${title}

an image '${title}'
  Create content  type=Image  id=doc  title=${title}

a folder '${title}'
  Create content  type=Folder  title=${title}

patterns are loaded
  Wait For Condition  return $('body.patterns-loaded').size() > 0

a folder with a document '${title}'
  ${folder_uid}=  Create content  type=Folder  title=folder
  Create content  type=Document  container=${folder_uid}  title=${title}

# Some Castle specific stuff
Close The Tour Popup
  ${Tour} =   Run Keyword And Return Status   Element Should Be Visible   css=a.introjs-skipall
  Run Keyword If  ${Tour} == 'PASS'  Clear Tour Popup
  Sleep   .25

Clear Tour Popup
  Click Element   css=a.introjs-skipall
