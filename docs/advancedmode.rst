Advanced Mode
=============

CastleCMS by default hides several buttons/elements that most users may not need. These
elements can be re-enabled by toggling "Advanced Mode."


Toggling Advanced Mode
----------------------

Currently, to toggle Advanced Mode, there's a button on the Dexterity type list page. It
is located there for now since everything that it shows/hides is related to Dexterity,
but that could change.

The setting is stored locally as a cookie (castlecms-advanced). It will persist even after
a user logs out. But it needs to be re-enabled when switching to a new computer/browser.

Elements Revealed by Enabling Advanced Mode
-------------------------------------------

These are the elements that are hidden by default and why they are hidden.

- Clone button on /@@dexterity-types

  - The functionality of the New Content Type button changed and now prompts the user to
    select a content type to clone. Having the clone button is redundant.

- Edit XML button on /dexterity-types/{TYPE}/@@fields

  - Most users should be able to get by with only making changes through the content type
    field editor. If not, it is still accessible with Advanced Mode.
