/* global history */
/* designed to be loaded in manage archive file,
   not included arbitrarily right now */

// `initial_data` is expected to exist in a global context, defined in the
// head of the page that uses this component

require([
    'jquery',
    'underscore',
    'mockup-utils'
  ], function($, _, utils){

    var template = _.template(
'<% _.each(items, function(item){ %>' +
  '<tr>' +
    '<td><a href="<%- item.url %>/view"><%- item.title %></a></td>' +
    '<td><%- item.modified %></td>' +
    '<td><a href="#" class="remove-item" data-uid="<%- item.uid %>">Extend</a></td>' +
  '</tr>' +
'<% }); %>');

    var load = function(json_dump){
      var html = template({items: json_dump});
      $('#review-items').html(html);
      $('.remove-item').click(function(e){
        utils.loading.show();
        e.preventDefault();
        var uid = $(this).attr('data-uid');
        $.ajax({
          url: window.location.origin + window.location.pathname,
          data: {
            extend: uid,
            _authenticator: utils.getAuthenticator()
          },
          dataType: 'json',
          method: 'POST'
        }).done(function(data){
          load(data);
          utils.loading.hide();
        });
      });
    }
    load(initial_data);
  });