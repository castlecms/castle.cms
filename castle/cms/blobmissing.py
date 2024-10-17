# -*- coding: utf-8 -*-
from pkg_resources import resource_filename
from shutil import copyfile
from ZEO import ClientStorage
from ZODB.blob import BlobFile
from ZODB.POSException import POSKeyError
from ZODB.POSException import Unsupported

import logging
import os


logger = logging.getLogger(__name__)


def patched_blob_init(self, name, mode, blob):
    allow_experimental = os.getenv("CASTLE_ALLOW_EXPERIMENTAL_BLOB_REPLACEMENT", None)
    if not os.path.exists(name) and allow_experimental is not None:
        create_empty_blob(name)
    super(BlobFile, self).__init__(name, mode + 'b')
    self.blob = blob


def patched_loadBlob(self, oid, serial):
    # Load a blob.  If it isn't present and we have a shared blob
    # directory, then assume that it doesn't exist on the server
    # and return None.

    blob_filename = self.fshelper.getBlobFilename(oid, serial)
    allow_experimental = os.getenv("CASTLE_ALLOW_EXPERIMENTAL_BLOB_REPLACEMENT", None)

    if allow_experimental is None:
        # Exhibit original behavior if blob replacement is not enabled
        if not os.path.exists(blob_filename):
            logger.error("No blob file at path: %s", blob_filename)
            raise POSKeyError("No blob file", oid, serial)
        return blob_filename
    
    if self.shared_blob_dir:
        if os.path.exists(blob_filename):
            return blob_filename
        else:
            # create empty file
            create_empty_blob(blob_filename)
        if os.path.exists(blob_filename):
            return blob_filename
        else:
            # We're using a server shared cache.  If the file isn't
            # here, it's not anywhere.
            raise POSKeyError("No blob file", oid, serial)

    if os.path.exists(blob_filename):
        return ClientStorage._accessed(blob_filename)
    else:
        # create empty file
        create_empty_blob(blob_filename)

    if os.path.exists(blob_filename):
        return ClientStorage._accessed(blob_filename)

    # First, we'll create the directory for this oid, if it doesn't exist.
    self.fshelper.createPathForOID(oid)

    # OK, it's not here and we (or someone) needs to get it.  We
    # want to avoid getting it multiple times.  We want to avoid
    # getting it multiple times even accross separate client
    # processes on the same machine. We'll use file locking.

    lock = ClientStorage._lock_blob(blob_filename)
    try:
        # We got the lock, so it's our job to download it.  First,
        # we'll double check that someone didn't download it while we
        # were getting the lock:

        if os.path.exists(blob_filename):
            return ClientStorage._accessed(blob_filename)

        # Ask the server to send it to us.  When this function
        # returns, it will have been sent. (The recieving will
        # have been handled by the asyncore thread.)

        self._server.sendBlob(oid, serial)

        if os.path.exists(blob_filename):
            return ClientStorage._accessed(blob_filename)

        raise POSKeyError("No blob file", oid, serial)

    finally:
        lock.close()


def create_empty_blob(filename):
    dirname = os.path.split(filename)[0]
    if not os.path.isdir(dirname):
        os.makedirs(dirname, 0o700)
    
    logger.info("Broken blob reference detected for: %s", filename)

    source = resource_filename(
        'castle.cms',
        'static/images/placeholder.png',
    )

    copyfile(source, filename)
    logger.info("Placeholder blob created for: %s", filename)
