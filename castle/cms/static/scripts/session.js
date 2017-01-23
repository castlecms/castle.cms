/* global localStorage */
//
// Script used to refresh user session to make sure if there is user activity,
// they aren't logged out...
//

require([
  'jquery'
], function($){
  'use strict';

  var timeout = 5 * 60 * 1000; // ping every 5 minutes
  var storageKey = 'sessionRefreshLastCheck';

  var store = function(){
    localStorage.setItem(storageKey, (new Date()).getTime());
  };

  var check = function(){
    var lastChecked = localStorage.getItem(storageKey);
    var now = (new Date()).getTime();
    if(lastChecked){
      try{
        lastChecked = parseInt(lastChecked);
        if((now - lastChecked) > timeout){
          return ping();
        }
      }catch(e){
        store();
      }
    }else{
      store();
    }
  };

  var ping = function(){
    setTimeout(function(){
      $.ajax({
        url: $('body').attr('data-portal-url') + '/acl_users/session/refresh'
      }).done(function(){
        store();
        check();
      });
    }, 5000);
  };

  var _checkTimeout = -1;
  $('body').bind('mouseover click keydown', function(){
    clearTimeout(_checkTimeout);
    _checkTimeout = setTimeout(check, 400);
  });

});
