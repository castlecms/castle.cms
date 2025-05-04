
function createElement(tag, options){
  var el = document.createElement(tag);
  if(options.className){
    if (el.classList)
      el.classList.add(options.className);
    else
      el.className += ' ' + options.className;
  }
  if(options.text){
    el.textContent = options.text;
  }
  if(options.children){
    for(var i=0; i<options.children.length; i++){
      el.appendChild(options.children[i]);
    }
  }
   return el;
}

require([
  'jquery',
  'mockup-patterns-modal',
], function($, Modal) {
  // global context script which allows html to be rendered in @fc-trash success messages
  (function($, setTimeout, kvs) {
      parseResponseHTML = function(restext) {
          return JSON.parse(restext)['msg']['html'];
      };

      if(!kvs['trash_html_event_bound']) { // check if we have bound this event already
          $(document).ajaxSuccess(function(event, xhr, settings) { // bind event to ajaxSuccess
              if( (settings.url.split('@@fc-trash').length > 1) && (!(settings.data.split('&render=yes').length > 1)) ) { // only run on @@fc-trash AJAX requests where "&render=yes" does not exist in the request data
                  setTimeout(function() {
                      $('.alert-success').find('span').html(parseResponseHTML(xhr.responseText)); // inject the HTML
                  }, 250); //wait a bit because underscore will render first and then this function will overide it
              }
          });

          kvs['trash_html_event_bound'] = true; // prevent this event from being bound to the Global Ajax Event Handler multiple times
      }
  })($, window.setTimeout, (function() {
      // basic object based key value storage -- accessed as "kvs" in the main function above
      if(typeof window.__ === 'undefined') {
          window.__ = {};
      }

      return window.__;
  })());

  if(Modal.prototype._init === undefined){
    Modal.prototype._init = Modal.prototype.init;
    Modal.prototype.init = function(){
      this.options.loadLinksWithinModal = false;
      this.options.backdropOptions.closeOnClick = false;
      this.options.backdropOptions.closeOnEsc = false;
      Modal.prototype._init.apply(this, []);
    };
  }

  if($('#formfield-form-widgets-ILayoutAware-content').size() > 0){
    // Show form errors in the interface so user knows if there
    // are required fields missing or errors in fields
    var $errors = $('.portalMessage.error');
    if($errors.size() > 0){
      var container = createElement('div', {
        className: 'castle-editor-errors'
      });
      $('body').append(container);
      $errors.each(function(){
        container.appendChild(this);
      });
      var $errorFields = $('.field.error');
      if($errorFields.size() > 0){
        var ul = document.createElement('ul');
        $errors.find('dd').append(ul);
        $errorFields.each(function(){
          var $this = $(this);
          if($this.find('label').size() > 0 && $this.find('.fieldErrorBox .error').size() > 0){
            var li = createElement('li', {
              children: [
                createElement('span', {
                  className: 'title',
                  text: $this.find('label')[0].textContent.trim()
                }),
                createElement('span', {
                  className: 'details',
                  text: $this.find('.fieldErrorBox .error')[0].textContent
                }),
              ]
            });
            ul.appendChild(li);
          }
        });
      }
    }
  }

  $(document).ready(function() {
    var cookieNegotiation = (
      $("#form-widgets-use_cookie_negotiation > input").value === 'selected');
    if (cookieNegotiation !== true) {
      $("#formfield-form-widgets-authenticated_users_only").hide();
    }else{
      $("#formfield-form-widgets-authenticated_users_only").show();
    }

    $('#form-widgets-upload_to_youtube-0').on('change', function(){
      var ytUrl = document.getElementById('form-widgets-youtube_url');
      if (this.checked) {
        ytUrl.setAttribute('readonly', true);
        ytUrl.value = '';
      } else {
        ytUrl.removeAttribute('readonly');
      }
    });
  });
});
