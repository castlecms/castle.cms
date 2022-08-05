#!/usr/bin/env python3
"""
Grab all data from an ES2.x store of the CastleCMS 2.x audit log, and use the python standard
logger to dump it to the appropriate handlers using the schema loosly described
in castle/cms/audit.py

requires `requests` to be installed to python environment

tested on python 3.9

Environment Variables to configure:

AUDIT_LOG_CONFIG_FILE
ES2_HOST
ES2_INDEX
ES2_SCROLLTIME
AUDIT_INSTANCE
AUDIT_SITE
SKIP_DUPLICATES_ON_IMPORT
GELF_URL

# only used if SKIP_DUPLICATES_ON_IMPORT is true
OS_HOST
OS_INDEX
OS_VERIFY_SSL
"""
import hashlib
import json
import logging
import logging.config
import os
import sys
import sqlite3

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning


# no need for warnings with verify=False on requests
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

logger = logging.getLogger(__name__)

DEFAULT_AUDIT_LOGGER_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'basic': {
            'format': '%(asctime)s %(levelname)s %(message)s',  # noqa
        },
        'auditlog': {
            'format': '%(asctime)s %(levelname)s %(name)s %(es2id)s %(schema_version)s %(schema_type)s "%(instance)s" "%(site)s" "%(type)s" "%(actionname)s" "%(summary)s" "%(user)s" "%(request_uri)s" "%(date)s" "%(object)s" "%(path)s"',  # noqa
        }
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'basic',
        },
        'auditconsole': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'auditlog',
        },
    },
    'loggers': {
        'root': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'auditlogger': {
            'handlers': ['auditconsole'],
            'propagate': False,
            'level': 'INFO',
        },
    },
}

# if this path exists, and loads fine as json, then apply the json as logging
# config (or try to) -- otherwise just pump to stdout
logging_config_file = os.getenv("AUDIT_LOG_CONFIG_FILE", None)
if logging_config_file is not None and os.path.exists(logging_config_file):
    try:
        with open(logging_config_file, "r") as fin:
            configdict = json.load(fin)
    except Exception:
        configdict = DEFAULT_AUDIT_LOGGER_CONFIG
        logger.error(
            "Couldn't load configuration for auditlogger python logger, "
            "defaulting to stdout", exc_info=True)
else:
    configdict = DEFAULT_AUDIT_LOGGER_CONFIG

try:
    # note: with 'disable_existing_loggers' set to False, this shouldn't wipeout
    # the config from Plone, etc
    logging.config.dictConfig(configdict)
except Exception:
    logger.error("failed to configure audit logger", exc_info=True)
auditlogger = logging.getLogger("auditlogger")


ES2_HOST = os.getenv("ES2_HOST", "http://127.0.0.1:9200/")
ES2_INDEX = os.getenv("ES2_INDEX", "audit")
ES2_SCROLLTIME = os.getenv("ES2_SCROLLTIME", "1m")

SKIP_DUPLICATES_ON_IMPORT = os.getenv("SKIP_DUPLICATES_ON_IMPORT", "true").strip().lower() in ("yes", "1", "true", "on")
DUPCONN = None
DUPCUR = None
if SKIP_DUPLICATES_ON_IMPORT:
    DUPLICATE_SQLITE3_PATH = os.getenv("DUPLICATE_SQLITE3_PATH", None)
    if DUPLICATE_SQLITE3_PATH is None:
        logger.warn("no DUPLICATE_SQLITE3_PATH set, will use OS lookup")
    if DUPLICATE_SQLITE3_PATH is not None and os.path.isdir(DUPLICATE_SQLITE3_PATH):
        logger.warn("DUPLICATE_SQLITE3_PATH seems to be a folder, will use OS lookup")
    if DUPLICATE_SQLITE3_PATH is not None and not os.path.isdir(DUPLICATE_SQLITE3_PATH):
        logger.info(f"will be using db at {DUPLICATE_SQLITE3_PATH} for checking duplicates")
        DUPCONN = sqlite3.connect(DUPLICATE_SQLITE3_PATH)
        DUPCUR = DUPCONN.cursor()
        DUPCUR.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='duplicates' ''')
        if DUPCUR.fetchone()[0] < 1:
            DUPCUR.execute(''' CREATE TABLE duplicates (es2id text) ''')
            DUPCONN.commit()
OS_HOST = os.getenv("OS_HOST", "https://127.0.0.1:9200")
OS_INDEX = os.getenv("OS_INDEX", "gelfs")
OS_VERIFY_SSL = os.getenv("OS_VERIFY_SSL", "true").strip().lower() in ("yes", "1", "true", "on")


# max 10000 results, hard coded into ES for all intents and purposes
query = {
    "size": 10000,
    "query": {
        "match_all": {},
    },
    "sort":  [{
        "date": {
            "order": "asc",
        },
    }],
}
url = "{}/{}/_search".format(ES2_HOST, ES2_INDEX)
params = dict(scroll=ES2_SCROLLTIME)
logger.info("performing initial search...")
resp = requests.get(url, params=params, json=query)
if resp.status_code < 200 or resp.status_code >= 300:
    logger.error("non-200 code from es2 instance: HTTP {}: {}".format(resp.status_code, resp.text))
    sys.exit(1)
respdata = resp.json()
totalhits = respdata.get("hits", {}).get("total", -1)
entries = respdata.get("hits", {}).get("hits", [])
scrollid = respdata.get("_scroll_id", None)
scrollurl = "{}/_search/scroll".format(ES2_HOST)
if scrollid is not None and totalhits >= 10000:
    logger.info("{} entries in search, scrolling... {}".format(totalhits, len(entries)))
    query = dict(
        scroll=ES2_SCROLLTIME,
        scroll_id=scrollid
    )
    while True:
        resp = requests.get(scrollurl, json=query)
        if resp.status_code < 200 or resp.status_code >= 300:
            logger.error("non-200 code from es2 instance when fetching scroll: HTTP {}: {}".format(resp.status_code, resp.text))
            break
        respdata = resp.json()
        scrollentries = respdata.get("hits", {}).get("hits", [])
        if len(scrollentries) <= 0:
            logger.info("no more scrolled entries")
            break
        entries += scrollentries
        logger.info("scrolling... {}".format(len(entries)))

logger.info("logging {} entries to the auditlogger".format(len(entries)))
num = 0
for entry in entries:
    logger.info("starting on {}".format(num))
    num += 1
    es2id = entry.get("_id", hashlib.sha256(json.dumps(entry["_source"]).encode()).hexdigest())

    if SKIP_DUPLICATES_ON_IMPORT:
        if DUPCONN is not None:
            DUPCUR.execute(''' SELECT count(es2id) FROM duplicates WHERE es2id=? ''', (es2id,))
            if DUPCUR.fetchone()[0] >= 1:
                logger.info(f"found es2id ({es2id}) in sqlite3 duplicates db, skipping")
                continue
        else:
            existsurl = "{}/{}/_search".format(OS_HOST, OS_INDEX)
            searchquery = {
                "query": {
                    "match": {
                        "full_message.es2id": es2id,
                    },
                },
            }
            resp = requests.get(existsurl, json=searchquery, verify=OS_VERIFY_SSL)
            if resp.status_code < 200 or resp.status_code >= 300:
                logger.error("error when querying opensearch for match, skipping. HTTP {} : {}".format(resp.status_code, resp.text))
                continue

            respjson = resp.json()
            totalhits = respjson.get("hits", {}).get("total", {}).get("value", -1)
            if totalhits > 0:
                _id = respjson["hits"]["hits"][0]["_id"]
                logger.info("found es2id ({}) in opensearch (_id {}), skipping".format(es2id, _id))
                continue

    # the first part of the object path should be equivalent to the site_path
    site_path = "/".join(entry["_source"].get("path", "/").split("/")[0:1])
    auditlogger.info(
        "",  # IE the "message" -- this is not data currently placed into ES, so will likely be empty
        extra=dict(
            schema_version="1",
            schema_type="castle.cms.audit",
            # we need to distinguish not only between sites within an instance, but between
            # difference instances too, incase there are overlapping site names between instances
            # so, "instance" and "site" were not in the original data, but have to be derived
            # from the index name
            instance=os.getenv("AUDIT_INSTANCE", "(not configured)"),
            site=os.getenv("AUDIT_SITE", "(not configured)"),
            type=entry["_source"].get("type", None),
            actionname=entry["_source"].get("name", None),
            user=entry["_source"].get("user", None),
            summary=entry["_source"].get("summary", None),
            request_uri=entry["_source"].get("request_uri", None),
            date=entry["_source"].get("date", None),
            object=entry["_source"].get("object", None),
            path=entry["_source"].get("path", None),
            es2id=es2id,
        )
    )

    # if we've logged it, and we have a DUPCONN, we should record the es2id for the dup checker
    DUPCUR.execute(''' INSERT INTO duplicates VALUES (?) ''', (es2id,))
    DUPCONN.commit()

if DUPCONN is not None:
    DUPCONN.close()
