/* global define */

define([
  'jquery',
  'pat-base',
  'mockup-patterns-modal',
  'jquery.cookie'
], function($, Base, Modal) {
  'use strict';

  var SurveyPattern = Base.extend({
    name: 'survey',
    trigger: '.pat-survey',
    parser: 'mockup',
    defaults: {
    },

    init: function() {
      var self = this;
      $('.pat-survey').each(function() {
        self.survey_tile = $(this);
        self.survey_data = JSON.parse(window.atob(self.survey_tile.attr('data-pat-survey')));
        var survey_rule = self.survey_data.rule.toLowerCase();
        var cookie_rule = self.survey_data.cookie.toLowerCase();
        self.cookie_data = self.getCookie();
        var shown = self.cookie_data.shown;
        var clicked = self.cookie_data.clicked;
        if (survey_rule == "always") {
          if ((cookie_rule == "always") ||
              (cookie_rule == "show_once" && !shown) ||
              (cookie_rule == "until_clicked" && !clicked)) {
                self.showInvite(self.survey_tile, self.survey_data);
          }
        } else if (survey_rule == "timer") {
          var remaining_duration = parseInt(self.survey_data.duration);
          if (!isNaN(remaining_duration)) {
            setInterval(function() {
              remaining_duration-=1;
              if (remaining_duration==0) {
                if ((cookie_rule == "always") ||
                    (cookie_rule == "show_once" && !shown) ||
                    (cookie_rule == "until_clicked" && !clicked)) {
                      self.showInvite(self.survey_tile, self.survey_data);
                }
              }
            }, 1000);
          }
        } else if (survey_rule == "count") {
          var count_goal = parseInt(self.survey_data.count);
          if (!isNaN(count_goal)) {
            var current = parseInt(self.cookie_data['count']);
            if (isNaN(current)) {
              current = 0; //the cookie didn't exist yet
            }
            current+=1;
            if (current >= count_goal) {
              if ((cookie_rule == "always") ||
                  (cookie_rule == "show_once" && !shown) ||
                  (cookie_rule == "until_clicked" && !clicked)) {
                    self.showInvite(self.survey_tile, self.survey_data);
                    current = 0;
              }
            }
            self.updateCookie('count', current);
          }
        } else if (survey_rule == "leave") {
          $(document).bind("mouseleave", function(e) {
            if ((e.pageY - $(window).scrollTop()) <=1) {
              var cookie_data = self.getCookie();
              if (!cookie_data.shown) {
                self.showInvite(self.survey_tile, self.survey_data);
              }
            }
          });
        }
      });
    },

    getCookie: function() {
      var survey_cookie = $.cookie('__c_s__');
      if (typeof(survey_cookie) === "undefined") {
        //init cookie
        survey_cookie = window.btoa('{"shown": false, "clicked": false, "count": 0}');
        $.cookie('__c_s__', survey_cookie);
      }
      try {
        var cookie_data = JSON.parse(window.atob(survey_cookie));
      } catch(e) {
        console.log("Problem parsing JSON.");
        return false;
      }
      return cookie_data;
    },

    updateCookie: function(key,value) {
      try {
        this.cookie_data[key] = value;
        $.cookie('__c_s__', window.btoa(JSON.stringify(this.cookie_data)));
      } catch(e) {
        console.log("Problem setting cookie.");
      }
    },

    createRequest: function(method, url) {
      //function to handle IE credit Nicholas Zakas
      var xhr = new XMLHttpRequest();
      if ("withCredentials" in xhr) {
        xhr.open(method, url, true);
      } else if (typeof XDomainRequest != "undefined") {
        xhr = new XDomainRequest();
        xhr.open(method, url);
      } else {
        xhr = null;
      }
      xhr.responseType = 'json';
      return xhr;
    },

    getInvite: function(survey_tile, survey_data) {
      var self = this;
      var url = survey_data.url+"/get-invite";
      var data = new FormData()
      data.append('survey_id', survey_data.id);
      var xhr = self.createRequest('POST', url);
      if (!xhr) {
        throw new Error('CORS not supported');
      }
      try {
        xhr.send(data);
        xhr.onload = function() {
          try {
            self.invite_data = JSON.parse(xhr.response);
          } catch (error) {
            self.invite_data = xhr.response;
          }
          self.renderInvite(self.survey_tile, self.survey_data, self.invite_data);
        }
      } catch (error) {
        console.log('Something went wrong with survey API: ' + error);
      }
    },

    showInvite: function(survey_tile, survey_data) {
      if (survey_data.custom_url != null) { //custom overrides API if both were selected.
        this.renderInvite(survey_tile, survey_data, null);
      } else {
        this.getInvite(survey_tile, survey_data);
      }
    },

    renderInvite: function(survey_tile, survey_data, invite_data) {
      if (invite_data === null) {
        var survey_url = survey_data.custom_url;
        var title = "";
        var desc = "";
        var disclaimer = "";
        var active = true;
      } else {
        var survey_url = invite_data.survey_endpoint;
        var title = (invite_data.api_ext_title || "");
        var desc = (invite_data.api_ext_desc || "");
        var disclaimer = (invite_data.api_ext_disclaimer || "");
        if ('token' in invite_data) {
          survey_url+="?token="+invite_data.token;
        }
      }
      var invite_html = '<div class="survey-invite"> \
                          <img src="'+survey_data.logo+'">\
                          <br>\
                          <div class="survey-api-title">'+title+'</div>\
                          <div class="survey-api-desc">'+desc+'</div>\
                          <br>\
                          <form action="'+survey_url+'"><input id="survey-button" type="submit" value="Take Survey"/></form>\
                          <br>\
                        </div>';
      var disclaimer_html = '<div class="survey-disclaimer">'+disclaimer+'</div>';
      if (survey_data.display.toLowerCase() == 'modal') {
        var modal = new Modal(survey_tile, {loadLinksWithinModal: true});
        modal.show();
        $('.plone-modal-content').css({
          "max-width": "50%",
          "min-height": "50%"
        });
        $('.plone-modal-close').css({
          "position": "relative",
          "top": "-15px"
        })
        $('.plone-modal-body').append(invite_html);
        $('.plone-modal-footer').append(disclaimer_html);
      } else {
        survey_tile.hide();
        survey_tile.append(invite_html); //Show the survey invite in the .pat-survey div
      }
      if (survey_data.display.toLowerCase() != 'modal') {
        survey_tile.append(disclaimer_html);
        survey_tile.slideDown();
      }
      var button = $('#survey-button');
      var that = this;
      button.click(function(){
        that.updateCookie('clicked', true);
      });
      that.updateCookie('shown', true);
    }
  });

  return SurveyPattern;

});
