require([
  'jquery',
  'mockup-utils',
  'pat-registry'
], function($, utils, Registry){
  var page = 2;

  var timeout = null;
  $('.filter-form input,.filter-form select').on('change', function(){
    if(timeout){
      clearTimeout(timeout);
    }
    timeout = setTimeout(function(){
      page = 2;
      var $form = $('.filter-form');
      var qs = $form.serialize();
      utils.loading.show();
      $.ajax({
        url: window.location.origin + window.location.pathname + '?' + qs
      }).done(function(data){
        var body = utils.parseBodyTag(data);
        var $body = $(body);
        $('.audit-results').replaceWith($('.audit-results', $body));
        $('.result-total').replaceWith($('.result-total', $body));
        Registry.scan($('.audit-results'));
      }).always(function(){
        utils.loading.hide();
      }).fail(function(){
        alert('error loading results');
      });
    }, 800);
  });

  $('.load-more-results').on('submit', function(e){
    e.preventDefault();
    var $form = $(this);
    var qs = $form.serialize();
    qs += '&page=' + page;
    utils.loading.show();
    $.ajax({
      url: window.location.origin + window.location.pathname + '?' + qs
    }).done(function(data){
      var body = utils.parseBodyTag(data);
      var $body = $(body);
      $('.audit-results tbody').append($('.audit-results tbody tr', $body));
      Registry.scan($('.audit-results tbody'));
      page += 1;
    }).always(function(){
      utils.loading.hide();
    }).fail(function(){
      alert('error loading more results')
    });
  });
});
