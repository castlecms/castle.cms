define([
  'jquery',
  'pat-base',
  'castle-url/libs/react/react.min',
  'castle-url/components/utils',
  'castle-url/components/modal',
  'pat-registry',
], function($, Base, R, cutils, CastleModal, Registry) {
  "use strict";

  var D = R.DOM;

  var ModalLinkContentComponent = cutils.Class([CastleModal], {
    getInitialState: function(){
      return {
      };
    },
    componentDidMount: function(){
      CastleModal.componentDidMount.apply(this);
    },

    renderContentContainer: function(){
      return D.div({ className: 'modal-content pt-' + this.props.content.portal_type }, [
        D.button({ type: 'button', className: 'close', onClick: this.hide }, [
          D.div({ className: 'close-button' }),
          D.span({ 'aria-hidden': 'true' }, '\u00d7')
        ]),
        D.div({ className: 'modal-body'}, this.renderContent()),
      ]);
    },

    renderVideo: function(){
      var data = this.props.content.data;
      var video;

      if(data.youtube_url){
        video = D.iframe({
          width: "100%", height: "100%",
          style: {width: '100%', height: '100%;', border: '0'},
          src: data.youtube_url, frameborder: "0", allowfullscreen: ""
        });
      }else{
        var image = null;
        if(this.props.content.has_image){
          image = this.props.content.url + '/@@images/image/high';
        }
        video = D.video({
          controls: "controls", className: "pat-video",
          poster: image, width: "100%", height: "100%",
          style: {width: '100%', height: '100%;'},
          preload: "auto"
        }, [
          D.source({
            src: this.props.content.url + '/@@download/file',
            type: data.content_type
          })
        ]);
      }
      return D.div({
        className: "video-container landscape"
      }, [
        D.div({
          className: "video-inner-container"
        }, video)
      ]);
    },
    renderImage: function(){
      return D.img({
        src: this.props.content.url + '/@@images/image/high',
        alt: this.props.content.data.title
      })
    },

    renderContent: function(){
      if(this.props.content.rendered){
        return D.div({
          dangerouslySetInnerHTML: {
            __html: this.props.content.rendered
          }
        });
      }else{
        var pt = this.props.content.portal_type;
        var func = this['render' + pt.charAt(0).toUpperCase() + pt.slice(1)];
        return func();
      }
    }
  });

  var ModalLinkPattern = Base.extend({
    name: 'modallink',
    trigger: 'a[data-linktype="modallink"],.pat-modallink',
    parser: 'mockup',
    defaults: {
      modal: {
        backdrop: 'static',
        show: true,
      }
    },
    init: function() {
      var self = this;
      self.$el.on('click', function(e){
        e.preventDefault();
        var url = self.$el.attr('href');
        if(url.substring(url.length - 5, url.length) === '/view'){
          url = url.substring(0, url.length - 5);
        }

        var el = document.createElement('div');
        $(el).addClass('castle-link-modal-wrapper');
        // inserting after screws up z-index? disable for now...
        // $(el).insertAfter(self.$el);
        $('body').append(el);

        $.get(url + '/@@content-body').done(function(data){
          R.render(R.createElement(ModalLinkContentComponent, {
            content: data
          }), el);
          Registry.scan($(el).find('.modal-body'));
        }).fail(function(){
          R.render(R.createElement(ModalLinkContentComponent, {
            content: {
              portal_type: 'Error',
              title: 'Error gettting info',
              url: $('body').attr('data-view-url'),
              id: 'error',
              rendered: '<p>Error rendering content</p>'
            }
          }), el);
        });
      });
    }
  });

  return ModalLinkPattern;

});
