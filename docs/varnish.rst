CastleCMS Varnish Integration
=============================

Thus far CastleCMS can only clear out the theming files (.css, .js, etc.) out of varnish.  Hopefully in the future we can add more support to the varnish servers.

Varnish Configuration Blocks
----------------------------

Below are some of the configuration blocks that you will need to put into your varnish server to be able to use the castle-cms functionality.

You can put the call anywhere in the vcl_recv.::

  sub vcl_recv {
    call purge_themes;
  
  }

The acl theme_purge acts as the list to determine who can and cannot clear out the theming.::
  
 acl theme_purge {
   "localhost";         // myself
   "10.0.2.2";	        // qemu host-machine
 }

The purge_themes subroutine actually purges the theming files from the vagrant cache.  Note that if you modify it, you must include a "200" somewhere in the response for when you succeed or else the varnish integration will not work properly.::

 sub purge_themes {
     if (req.request == "CASTLE_CMS_PURGE_THEMES"){
        if (client.ip ~ theme_purge) {
        	  ban("obj.http.x-url ~ (" + req.url + ").*(gif|jpeg|jpg|png|css|js)");
 	  error 200 "Ban added";
 	  return(error);
        	  }
 	  error 401 "IP not registered in the list.";
 	  return(error);
        }
 }
