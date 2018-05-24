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
      var shown = $.cookie('castle-survey-shown')
      if (typeof(shown) === "undefined") {
        shown = false;
        $.cookie('castle-survey-shown', shown);
      }
      $('.pat-survey').each(function() {
        self.survey_tile = $(this);
        self.survey_data = JSON.parse(self.survey_tile.attr('data-pat-survey'))
        var survey_rule = self.survey_data.rule.toLowerCase();
        var shown = ($.cookie('castle-survey-shown') == 'true')
        if (survey_rule == "always" && !shown) {
          self.showInvite(self.survey_tile, self.survey_data);
        } else if (survey_rule == "timer") {
          var remaining_duration = parseInt(self.survey_data.duration);
          if (!isNaN(remaining_duration)) {
            setInterval(function() {
              remaining_duration-=1;
              if (!shown && remaining_duration==0)
                self.showInvite(self.survey_tile, self.survey_data);
            }, 1000);
          }
        } else if (survey_rule == "count") {
          var count_goal = parseInt(self.survey_data.count);
          if (!isNaN(count_goal)) {
            var current = parseInt($.cookie('castle-page-count'));
            if (isNaN(current)) {
              current = 0; //the cookie didn't exist yet
            }
            current+=1;
            if (!shown && current >= count_goal) {
              self.showInvite(self.survey_tile, self.survey_data);
              current = 0;
            }
            console.log(current);
            $.cookie('castle-page-count', current);
          }
        } else if (survey_rule == "leave") {
          $(document).bind("mouseleave", function(e) {
            if ((e.pageY - $(window).scrollTop()) <=1) {
              shown = ($.cookie('castle-survey-shown') == 'true')
              if (!shown)
                self.showInvite(self.survey_tile, self.survey_data);
            }
          })
        }
      });
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
      xhr.responseType = 'json'
      return xhr;
    },
    getToken: function(survey_tile, survey_data) {
      var self = this;
      var url = survey_data.url+"/get-survey-token"
      var data = new FormData()
      data.append('survey_id', survey_data.id)
      var xhr = self.createRequest('POST', url);
      if (!xhr) {
        throw new Error('CORS not supported');
      }
      try {
        xhr.send(data);
        xhr.onload = function() {
          self.renderInvite(self.survey_tile, self.survey_data, xhr.response.survey_token);
        }
      } catch (error) {
        console.log('Something went wrong with survey API: ' + error);
      }
    },
    showInvite: function(survey_tile, survey_data) {
      this.getToken(survey_tile, survey_data);
    },
    renderInvite: function(survey_tile, survey_data, token) {
      var survey_url = survey_data.url+"/survey/"+survey_data.id+"?token="+token;
      var survey_invite = '<div class="survey-invite"><br><br>You\'ve been invited to take a <a href="'+survey_url+'">survey</a>!<br><br></div>'
      if (survey_data.display.toLowerCase() == 'modal') {
        var modal = new Modal(survey_tile);
        modal.show();
        $('.plone-modal-body').append(survey_invite);
      } else {
        survey_tile.hide();
        survey_tile.css("background-color", "	#E6E6FA");
        survey_tile.append(survey_invite); //Show the survey invite in the .pat-survey div
        survey_tile.slideDown()
      }
      $.cookie('castle-survey-shown', true);
    }
  });

  return SurveyPattern;

});
