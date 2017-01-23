
require([
  'jquery',
  'mockup-patterns-modal',
], function($, Modal) {
  if(Modal.prototype._init === undefined){
    Modal.prototype._init = Modal.prototype.init;
    Modal.prototype.init = function(){
      this.options.loadLinksWithinModal = false;
      this.options.backdropOptions.closeOnClick = false;
      this.options.backdropOptions.closeOnEsc = false;
      Modal.prototype._init.apply(this, []);
    };
  }

  $(document).ready(function() {
    var cookieNegotiation = (
      $("#form-widgets-use_cookie_negotiation > input").value === 'selected');
    if (cookieNegotiation !== true) {
      $("#formfield-form-widgets-authenticated_users_only").hide();
    }else{
      $("#formfield-form-widgets-authenticated_users_only").show();
    }
  });
});
