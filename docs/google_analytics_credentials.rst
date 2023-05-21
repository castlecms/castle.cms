Generate JSON credentials for Google Analytics Data API (GA4)
=============================================================


Login to Google Cloud Console:
------------------------------

    https://console.cloud.google.com/


Creating a project:
-------------------

    Click on the “Select a project” drop down at the top left.
    Select "New Project" if creating a project for the first time.


Enable APIs:
------------

    Click on APIs & Services, then select the Library submenu.
    Search for Google Analytics Data API then select enable


Creating API credentials:
-------------------------

    Return to APIs & Services dashboard, then select the Credentials submenu
    Select Configure Consent Screen from the warning at the top of the page
    Fill out the resulting forms for OAuth Consent, Scopes (Google Analytics Data API), and Test Users


Creating OAuth credentials:
---------------------------

    Return to the Credentials submenu
    Select Create Credentials at the top of the page then click OAuth client ID
    Select Desktop App as the Application type and enter a name then select Create
    The resulting modal will have an option to download the JSON file, otherwise this can be found under the OAuth 2.0 Client IDs section from the Credentials submenu
    Add the JSON file


Using the JSON file for authentication:
---------------------------------------

    Navigate to the CastleCMS menu in Site Setup and upload the file to APIs -> Google API Service Key File 
    Alternatively you may set the GOOGLE_PATH_TO_SERVICE_KEY environment variable as a path to the file i.e. '/path/to/credentials.json'
