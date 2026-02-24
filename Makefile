.PHONY: less-plone less-plone-logged-in compile-plone compile-plone-logged-in verify-gruntfile-exists
ERROR_MESSAGE = You must run ./bin/plone-compile-resources --site-id <YOUR_SITE_ID> before these targets will work

verify-gruntfile-exists:
	test -f Gruntfile.js || ( echo "\n\n$(ERROR_MESSAGE)\n\n"; exit 1 )

less-plone:
	make verify-gruntfile-exists && grunt less:plone

less-plone-logged-in:
	make verify-gruntfile-exists && grunt less:plone-logged-in

compile-plone:
	make verify-gruntfile-exists && grunt compile-plone

compile-plone-logged-in:
	make verify-gruntfile-exists && grunt compile-plone-logged-in
