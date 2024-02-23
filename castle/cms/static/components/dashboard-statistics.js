require([
  'jquery',
  'pat-registry',
  'mockup-utils'
], function($, Registry, utils){
  var csel = '.castle-statistics-container';
  var bind = function(){
    $(csel + ' button.load-more').off('click').on('click', function(e){
      e.preventDefault();
      var $btn = $(this);
      utils.loading.show();
      var data = {};
      data[$btn.attr('data-name') + '_start'] = $btn.attr('data-end');
      $.ajax({
        url: $('body').attr('data-portal-url') + '/@@castle.cms.fragment?fragment=dashboard-statistics',
        data: data
      }).done(function(data){
        var body = utils.parseBodyTag(data);
        var $body = $(body);
        var loadContainerSelector = '.load-container-' + $btn.attr('data-name');
        var $container = $(loadContainerSelector, $body);
        $(loadContainerSelector + ' tbody').append($container.find('tbody tr'));
        $(loadContainerSelector + ' .load-more').replaceWith($container.find('.load-more'));
        Registry.scan($(loadContainerSelector));
        bind();
      }).fail(function(){
        alert('error loading more');
      }).always(function(){
        utils.loading.hide();
      })
    });
  };
  bind();

  var bindShowHide = function(){
    $(csel + ' button.show-hide').off('click').on('click', function(e){
      e.preventDefault();
      var $btn = $(this);
      var x = document.getElementById($btn.attr('data-name'));
      if (x.style.display === "none") {
        x.style.display = "block";
      } else {
        x.style.display = "none";
      }
    });
  };
  bindShowHide();
});
