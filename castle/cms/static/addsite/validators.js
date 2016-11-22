define([
  'castle-url/libs/react/react.min',
  'castle-url/addsite/store',
  'castle-url/addsite/actions'
], function(React, Store, Actions){

  var required = function(value){
    if( value === '' ) {
      return 'Input is required.';
    }
    return '';
  };

  var image = function(value) {
    var extension = value.substr(value.lastIndexOf('.')+1);

    if( (['png', 'jpg', 'gif', 'jpeg'].lastIndexOf(extension) + 1 ) > 0 ) {
      return '';
    }else{
      return 'Invalid file type';
    }
  };

  var email = function(value) {

    if( value === '' ) {
      return '';
    }

    var r = new RegExp("[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?");

    if( r.test(value) ) {
      return '';
    }

    return "Invalid email.";
  };

  var url = function(value) {
    var r = /(^|\s)((https?:\/\/)?[\w-]+(\.[\w-]+)+\.?(:\d+)?(\/\S*)?)/gi;

    if( r.test(value) ) {
      return '';
    }

    return "Invalid url.";

  };
  return {
    'required': required,
    'email': email,
    'url': url,
    'image': image
  };
});
