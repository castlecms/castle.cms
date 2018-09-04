#!/bin/sh
#
# Shell script to manage .po files.
#
# Run this file in the folder main __init__.py of product
#
# E.g. if your product is yourproduct.name
# you run this file in yourproduct.name/yourproduct/name
#
#
# Copyright 2010 mFabrik http://mfabrik.com
#
# http://plone.org/documentation/manual/plone-community-developer-documentation/i18n/localization
#

# Assume the product name is the current folder name
CURRENT_PATH=`pwd`
CATALOGNAME="collective.pwexpiry"

# List of languages
LANGUAGES="en it de"

# Create locales folder structure for languages
ROOT_DIR=..
#install -d locales
for lang in $LANGUAGES; do
    install -d $ROOT_DIR/locales/$lang/LC_MESSAGES
done

# Assume i18ndude is installed with buildout
# and this script is run under src/ folder with two nested namespaces in the package name (like mfabrik.plonezohointegration)
I18NDUDE=i18ndude

#
# Do we need to merge manual PO entries from a file called manual.pot.
# this option is later passed to i18ndude
#
if test -e $ROOT_DIR/locales/manual.pot; then
        echo "Manual PO entries detected"
        MERGE="--merge $ROOT_DIR/locales/manual.pot"
else
        echo "No manual PO entries detected"
        MERGE=""
fi

# Rebuild .pot
$I18NDUDE rebuild-pot --wrap --pot $ROOT_DIR/locales/$CATALOGNAME.pot $MERGE --create $CATALOGNAME $ROOT_DIR


# Compile po files
for lang in $(find $ROOT_DIR/locales -mindepth 1 -maxdepth 1 -type d); do

    if test -d $lang/LC_MESSAGES; then

        PO=$lang/LC_MESSAGES/${CATALOGNAME}.po

        # Create po file if not exists
        touch $PO

        # Sync po file
        echo "Syncing $PO"
        $I18NDUDE sync --wrap --pot $ROOT_DIR/locales/$CATALOGNAME.pot $PO
#
#
#        # Plone 3.3 and onwards do not need manual .po -> .mo compilation,
#        # but it will happen on start up if you have
#        # registered the $ROOT_DIR/locales directory in ZCML
#        # For more info see http://vincentfretin.ecreall.com/articles/my-translation-doesnt-show-up-in-plone-4
#
#        # Compile .po to .mo
#        # MO=$lang/LC_MESSAGES/${CATALOGNAME}.mo
#        # echo "Compiling $MO"
#        # msgfmt -o $MO $lang/LC_MESSAGES/${CATALOGNAME}.po
    fi
done
