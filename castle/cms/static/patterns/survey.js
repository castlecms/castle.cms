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
      var shown = false;
      $('.pat-survey').each(function() {
        var survey_tile = $(this);
        var survey_data = JSON.parse(survey_tile.attr('data-pat-survey'))
        var survey_rule = survey_data.rule.toLowerCase();
        if (survey_rule == "always") {
          self.showInvite(survey_tile, survey_data);
        } else if (survey_rule == "timer") {
          var remaining_duration = parseInt(survey_data.duration);
          if (!isNaN(remaining_duration)) {
            setInterval(function() {
              remaining_duration-=1;
              if (!shown && remaining_duration==0)
                self.showInvite(survey_tile, survey_data);
            }, 1000);
          }
        } else if (survey_rule == "count") {n
          count_goal = parseInt(survey_data.count);
          if (!isNaN(count_goal)) {
            var current = $.cookie('castle-page-count'); //check cookie for pages viewed
            current+=1;
            if (!shown && count >= count_goal) {
              self.showInvite(survey_tile, survey_data);
              count = 0;
            }
            $.cookie('castle-page-count', count)
          }
        } else if (survey_rule == "leave") {
          $(document).bind("mouseleave", function(e) {
            if (!shown && (e.pageY - $(window).scrollTop()) <=1) {
              self.showInvite(survey_tile, survey_data);
            }
          })
        }
      });
    },
    getToken: function(survey_data) {
      //var xhttp  = new XMLHttpRequest();
      //var url = survey_data.url+"/get_survey_token?survey_id="+survey_data.id
      //xhttp.open("POST", url, true);
      //xhttp.send();
      //var response = JSON.parse(xhttp.responseText);
      //return response.survey_token;
      return '1a2b3c';
    },
    showInvite: function(survey_tile, survey_data) {
      var survey_url = survey_data.url+"/survey/"+survey_data.id+"?token="+this.getToken(survey_data);
      var survey_invite = '<div class="survey-invite">You\'ve been invited to take a <a href="'+survey_url+'">survey</a>!</div>'
      if (survey_data.display.toLowerCase() == 'modal') {
        var modal = new Modal(survey_tile);
        modal.show();
        $('.plone-modal-body').append(survey_invite);
      } else {
        survey_tile.hide()
        survey_tile.css("background-color", "	#E6E6FA")
        survey_tile.append(survey_invite); //Show the survey invite in the .pat-survey div
        survey_tile.slideDown()
      }
      $.cookie('castle-survey-shown', 1);
    }
  });

  return SurveyPattern;

});
