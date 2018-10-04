CastleCMS Control Panels
========================

The following describes CastleCMS' control panels, which an administrator uses to configure, control, and view the
current state of CastleCMS and its subprocesses.

Status Control Panel
--------------------
The CastleCMS status control panel checks and displays the status of components and subprocesses needed by CastleCMS.

- `docsplit`: checks if the docsplit tool is installed and available to used by the document viewer.

- `Celery`: checks if CastleCMS is able to connect to a Celery worker, which is used to process queued tasks.

- `Redis`: checks if CastleCMS is able to connect to Redis, which acts as a task queue.

- `Elasticsearch`: checks if CastleCMS is able to connect to the Elasticsearch search engine.

Here is what the status control panel looks like if CastleCMS' subcomponents and subprocesses are not available or running:

.. figure:: castlecms_status_errors.jpg
   :align: center

   CastleCMS Status control panel showing errors

Here is what the status control panel looks like if all components and subprocesses are present and functioning:

.. figure:: castlecms_status_ok.jpg
   :align: center

   CastleCMS Status control panel showing all OK

Keyword Manager Control Panel
-----------------------------

The Keyword Manager (Products.PloneKeywordManager) is useful for renaming and
merging keywords (aka tags or subjects). Upon loading the page, it will list all
keywords used across the current site.

The checkboxes next to each keyword are used to determine which keywords to
rename and/or merge. All selected keywords will be renamed to the value of the
"Keyword to apply" field.

Toggling the "Show similar keywords" checkbox, Keyword Manager can group similar
keywords with each keyword. Be warned that this will produce duplicate entries
on the page if duplicates are found.
