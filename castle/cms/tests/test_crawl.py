# -*- coding: utf-8 -*-
from castle.cms.cron._crawler import Crawler
from castle.cms.interfaces import ICrawlerConfiguration
from castle.cms.testing import CASTLE_PLONE_INTEGRATION_TESTING
from collective.elasticsearch.es import ElasticSearchCatalog
from plone import api
from plone.registry.interfaces import IRegistry
from zope.component import getUtility
import responses

import unittest


class TestCrawl(unittest.TestCase):

    layer = CASTLE_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']

    @responses.activate
    def test_crawl_page(self):
        responses.add(responses.GET, "https://www.foobar.com",
                      body=TEST_ARCHIVE_PAGE,
                      content_type="text/html")

        catalog = api.portal.get_tool('portal_catalog')
        es = ElasticSearchCatalog(catalog)
        registry = getUtility(IRegistry)
        settings = registry.forInterface(
            ICrawlerConfiguration, prefix='castle')
        crawler = Crawler(self.portal, settings, es)
        data = crawler.crawl_page(
            'https://www.foobar.com')

        self.assertEquals(data['domain'], 'www.foobar.com')
        self.assertEquals(
            data['url'],
            'https://www.foobar.com')
        self.assertEquals(data['portal_type'], 'Form Folder')
        self.assertTrue(bool(data['Title']))
        self.assertTrue(bool(data['SearchableText']))


TEST_ARCHIVE_PAGE = '''

<!DOCTYPE html PUBLIC
                "-//W3C//DTD XHTML 1.0 Transitional//EN"
                "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
<meta http-equiv="Content-Type" content="text/html;charset=utf-8"/>
<meta name="generator" content="CastleCMS - http://www.wildcardcorp.com"/>


<!--[if IE]>
      <meta http-equiv="X-UA-Compatible" content="IE=8; IE=7; IE=5" />
      <![endif]-->
<base href="https://www.foobar.com/"/><!--[if lt IE 7]></base><![endif]-->
<meta name="DC.format" content="text/plain"/>
<meta name="DC.type" content="Form Folder"/>
<meta name="DC.date.valid_range" content="2012/02/09 - "/>
<meta name="DC.date.created" content="2016-06-20T14:12:16+00:00"/>
<meta name="DC.language" content="en"/>
<meta name="DC.date.modified" content="2016-06-20T14:53:04+00:00"/>
<style type="text/css" media="screen">@import url(https://www.foobar.com/portal_css/foobarTheme/base-cachekey-dbdb8fad070a40dcb5f536fa03ca1f1b.css);</style>
<style type="text/css" media="screen">@import url(https://www.foobar.com/portal_css/foobarTheme/columns-cachekey-e8b80fdb0d7fda3d97c9b4c121264879.css);</style>
<link rel="stylesheet" type="text/css" href="https://www.foobar.com/portal_css/foobarTheme/resourcetinymce.stylesheetstinymce-cachekey-0f418c220786988a7bf86e000fb1655b.css" media="screen"/>
<style type="text/css">@import url(https://www.foobar.com/portal_css/foobarTheme/print-cachekey-32662b10c7e3296c50f5776b4cd91e5f.css);</style>
<link rel="stylesheet" type="text/css" href="https://www.foobar.com/portal_css/foobarTheme/resourceplone.app.discussion.stylesheetsdiscussion-cachekey-bd4ed6e7272a04edb5a6bc1c1f5067b5.css" media="screen"/>
<!--[if IE 8]>

    <style type="text/css" media="screen">@import url(https://www.foobar.com/portal_css/foobarTheme/ie8fixes-cachekey-9213db1b6a69c06fa22b79ee009598b4.css);</style>
        <![endif]-->
<style type="text/css" media="screen">@import url(https://www.foobar.com/portal_css/foobarTheme/resourceeasyslider-portlet-cachekey-030b6fd1f2ea40e4a71ce418d774b5e0.css);</style>
<!--[if IE]>

    <style type="text/css">@import url(https://www.foobar.com/portal_css/foobarTheme/IEAllVersions-cachekey-c5721d6b43b43de3af1c0ec99daa1add.css);</style>
        <![endif]-->
<style type="text/css">@import url(https://www.foobar.com/portal_css/foobarTheme/jscalendarcalendar-system-cachekey-1e12e89e18a4d6b3d925ce836442f63a.css);</style>
<script type="text/javascript" src="https://www.foobar.com/portal_javascripts/foobarTheme/resourceplone.app.jquery-cachekey-f5487f1b1c781ef75c72f204a746c834.js"></script>
<script type="text/javascript" src="https://www.foobar.com/portal_javascripts/foobarTheme/resourceeasyslider-portlet-cachekey-c6142033b322f3b1acfae3b9269a431f.js"></script>
<script type="text/javascript" src="https://www.foobar.com/portal_javascripts/foobarTheme/foreseeforesee-alive-cachekey-b631c890f4c17b38353a07e694aa8d18.js"></script>
<script type="text/javascript" src="https://www.foobar.com/portal_javascripts/foobarTheme/custom-cachekey-07d8ddee05772bddba96179480d9b837.js"></script>
<title>Foobar</title>

<meta name="modificationDate" content="2016/06/20"/>
<meta name="creationDate" content="2016/06/20"/>
<meta name="publicationDate" content="2012/02/09"/>
<meta name="expirationDate"/>
<meta name="portalType" content="FormFolder"/>
<meta name="mobileEnabled"/>
<meta name="location" content=""/>
<meta name="contentType" content="text/plain"/>

<meta property="og:type" content="article"/>
<meta property="og:url" content="https://www.foobar.com"/>
<meta property="og:description" content=""/>
<meta name="DC.format" content="text/plain"/>
<meta name="DC.type" content="Form Folder"/>
<meta name="DC.date.valid_range" content="2012/02/09 - "/>
<meta name="DC.date.created" content="2016-06-20T14:12:16+00:00"/>
<meta name="DC.language" content="en"/>
<meta name="DC.date.modified" content="2016-06-20T14:53:04+00:00"/>
<link rel="canonical" href="https://www.foobar.com"/>
<link rel="shortcut icon" type="image/x-icon" href="https://www.foobar.com/favicon.ico"/>
<link rel="apple-touch-icon" href="https://www.foobar.com/touch_icon.png"/>

<meta http-equiv="imagetoolbar" content="no"/>
<script type="text/javascript" charset="iso-8859-1" src="https://www.foobar.com/widgets/js/textcount.js">
      </script>
<style type="text/css" media="screen">@import url(norfolk-speaker-request-form.css);</style>
</head>
<body class="obj-d48ed00212f8438eb4beb4b16bb0547b portaltype-formfolder template-fg_base_view_p3 portaltype-formfolder site-forms icons-on userrole-anonymous" dir="ltr">
<div id="shadow">
<div id="visual-portal-wrapper">
<div id="portal-top">
<div id="portal-header">
<div id="portal-searchbox">
<div id="portal-advanced-search" class="hiddenStructure">
<a href="https://www.foobar.com/search_form" accesskey="5">Advanced Search&hellip;</a>
</div>
</div>
<div id="portal-logo">
<a accesskey="1" href="https://www.foobar.com">
<img id="logo1" alt="Federal Bureau of Investigation" src="https://www.foobar.com/logo1.png"/><img id="logo2" alt="Federal Bureau of Investigation" src="https://www.foobar.com/logo2.png"/><img id="logo3" alt="Federal Bureau of Investigation" src="https://www.foobar.com/logo3.png"/>
</a>
</div>
<h5 class="hiddenStructure">Sections</h5>
<div class="visualClear"></div>
<div id="topnav-container">
</div>
<ul id="portal-globalnav"></ul>
</div>
<div id="portal-header-cell">
<div class="header-cell image-cell main-layout" colspan="2">
<img alt="Header Cell Image" src="https://www.foobar.com/header.jpg"/>
</div>
<div id="portal-breadcrumbs">
<a href="https://www.foobar.com"><font color="#b71318">Home</font></a>
<span class="breadcrumbSeparator">
&bull;
</span>
<span dir="ltr">
</span>
</div>
<div class="visualClear" id="clear-space-before-wrapper-table"> </div>
<table id="portal-columns">
<tbody>
<tr>
<td id="portal-column-content">
<div class="content_border_wrapper">
<div class="">
<div id="region-content" class="documentContent">
<span id="contentTopLeft"></span>
<span id="contentTopRight"></span>
<a name="documentContent"></a>
<dl class="portalMessage info" id="kssPortalMessage" style="display:none">
<dt>Info</dt>
<dd></dd>
</dl>
<div id="viewlet-above-content"></div>
<div id="content">
<div class="" id="parent-fieldname-formPrologue-d48ed00212f8438eb4beb4b16bb0547b">
<p align="center">Please note: Requests for speakers must be received by the Kansas City Field Office a minimum of 45 days <br/>prior to your presentation date. All requests are subject to availability.<strong> <br/></strong></p>
</div>
<div class="pfg-form">
<form name="edit_form" method="post" enctype="multipart/form-data" class="fgBaseEditForm enableUnloadProtection enableAutoFocus" action="https://www.foobar.com" id="fg-base-edit">
<div></div>
<div id="pfg-fieldwrapper">
<fieldset class="PFGFieldsetWidget" id="pfg-fieldsetname-column1">
<div class="formHelp" id="column1_help"></div>
<div class="field PFG-RichLabel" id="archetypes-fieldname-contact-information">
<p><strong><font size="3">Contact Information</font></strong></p>
</div>
<div class="field ArchetypesStringWidget " id="archetypes-fieldname-contact-person" data-uid="d48ed00212f8438eb4beb4b16bb0547b" data-fieldname="contact-person">
<span></span>
<label class="formQuestion" for="contact-person">
Contact Person:
<span class="required" title="Required">&nbsp;</span>
<span class="formHelp" id="contact-person_help"></span>
</label>
<div class="fieldErrorBox"></div>
<input type="text" name="contact-person" class="blurrable firstToFocus" id="contact-person" size="30" maxlength="255"/>
</div>
<div class="field ArchetypesStringWidget " id="archetypes-fieldname-position-title" data-uid="d48ed00212f8438eb4beb4b16bb0547b" data-fieldname="position-title">
<span></span>
<label class="formQuestion" for="position-title">
Position/Title:
<span class="required" title="Required">&nbsp;</span>
<span class="formHelp" id="position-title_help"></span>
</label>
<div class="fieldErrorBox"></div>
<input type="text" name="position-title" class="blurrable firstToFocus" id="position-title" size="30" maxlength="255"/>
</div>
<div class="field ArchetypesStringWidget " id="archetypes-fieldname-contacts-email-address" data-uid="d48ed00212f8438eb4beb4b16bb0547b" data-fieldname="contacts-email-address">
<span></span>
<label class="formQuestion" for="contacts-email-address">
Contact's E-Mail Address:
<span class="required" title="Required">&nbsp;</span>
<span class="formHelp" id="contacts-email-address_help"></span>
</label>
<div class="fieldErrorBox"></div>
<input type="text" name="contacts-email-address" class="blurrable firstToFocus" id="contacts-email-address" size="30" maxlength="255"/>
</div>
<div class="field ArchetypesStringWidget " id="archetypes-fieldname-contacts-phone" data-uid="d48ed00212f8438eb4beb4b16bb0547b" data-fieldname="contacts-phone">
<span></span>
<label class="formQuestion" for="contacts-phone">
Contact's Phone:
<span class="required" title="Required">&nbsp;</span>
<span class="formHelp" id="contacts-phone_help"></span>
</label>
<div class="fieldErrorBox"></div>
<input type="text" name="contacts-phone" class="blurrable firstToFocus" id="contacts-phone" size="30" maxlength="255"/>
</div>
<div class="field ArchetypesStringWidget " id="archetypes-fieldname-contacts-secondary-phone" data-uid="d48ed00212f8438eb4beb4b16bb0547b" data-fieldname="contacts-secondary-phone">
<span></span>
<label class="formQuestion" for="contacts-secondary-phone">
Contact's Secondary Phone:
<span class="formHelp" id="contacts-secondary-phone_help"></span>
</label>
<div class="fieldErrorBox"></div>
<input type="text" name="contacts-secondary-phone" class="blurrable firstToFocus" id="contacts-secondary-phone" size="30" maxlength="255"/>
</div>
<div class="field PFG-RichLabel" id="archetypes-fieldname-about-the-organization">
<p><strong><font size="3">About the Organization<br/></font></strong></p>
</div>
<div class="field ArchetypesStringWidget " id="archetypes-fieldname-organization-group-name" data-uid="d48ed00212f8438eb4beb4b16bb0547b" data-fieldname="organization-group-name">
<span></span>
<label class="formQuestion" for="organization-group-name">
Organization/Group Name
<span class="required" title="Required">&nbsp;</span>
<span class="formHelp" id="organization-group-name_help"></span>
</label>
<div class="fieldErrorBox"></div>
<input type="text" name="organization-group-name" class="blurrable firstToFocus" id="organization-group-name" size="30" maxlength="255"/>
</div>
<div class="field ArchetypesSelectionWidget " id="archetypes-fieldname-audience-type" data-uid="d48ed00212f8438eb4beb4b16bb0547b" data-fieldname="audience-type">
<span></span>
<div class="fieldErrorBox"></div>
<span id="audience-type">

<div class="formQuestion label">
Audience Type
<span class="required" title="Required">&nbsp;</span>
<span class="formHelp" id="audience-type_help"></span>
</div>
<input class="noborder blurrable" type="radio" name="audience-type" id="audience-type_1" value="Business Professionals"/>
<label for="audience-type_1">Business Professionals</label>
<br/>
<input class="noborder blurrable" type="radio" name="audience-type" id="audience-type_2" value="Civic Group"/>
<label for="audience-type_2">Civic Group</label>
<br/>
<input class="noborder blurrable" type="radio" name="audience-type" id="audience-type_3" value="Faith-Based Organization"/>
<label for="audience-type_3">Faith-Based Organization</label>
<br/>
<input class="noborder blurrable" type="radio" name="audience-type" id="audience-type_4" value="Law Enforcement"/>
<label for="audience-type_4">Law Enforcement</label>
<br/>
<input class="noborder blurrable" type="radio" name="audience-type" id="audience-type_5" value="Seniors"/>
<label for="audience-type_5">Seniors</label>
<br/>
<input class="noborder blurrable" type="radio" name="audience-type" id="audience-type_6" value="Teens"/>
<label for="audience-type_6">Teens</label>
<br/>
<input class="noborder blurrable" type="radio" name="audience-type" id="audience-type_7" value="Other (describe below in comments section)"/>
<label for="audience-type_7">Other (describe below in comments section)</label>
<br/>
</span>
</div>
<div class="field PFG-RichLabel" id="archetypes-fieldname-presentation-date-location">
<p><strong><font size="3">Presentation Date/Location</font></strong></p>
</div>
<div class="field ArchetypesStringWidget " id="archetypes-fieldname-event-date-time" data-uid="d48ed00212f8438eb4beb4b16bb0547b" data-fieldname="event-date-time">
<span></span>
<label class="formQuestion" for="event-date-time">
Event Date/Time:
<span class="required" title="Required">&nbsp;</span>
<span class="formHelp" id="event-date-time_help"></span>
</label>
<div class="fieldErrorBox"></div>
<input type="text" name="event-date-time" class="blurrable firstToFocus" id="event-date-time" size="30" maxlength="255"/>
</div>
<div class="field ArchetypesTextAreaWidget " id="archetypes-fieldname-event-location" data-uid="d48ed00212f8438eb4beb4b16bb0547b" data-fieldname="event-location">
<span></span>
<label class="formQuestion" for="event-location">
Event Location:
<span class="required" title="Required">&nbsp;</span>
<span class="formHelp" id="event-location_help"></span>
</label>
<div class="fieldErrorBox"></div>
<textarea class="blurrable firstToFocus" name="event-location" id="event-location" cols="40" rows="5"></textarea>
</div>
</fieldset>
<fieldset class="PFGFieldsetWidget" id="pfg-fieldsetname-column2">
<div class="formHelp" id="column2_help"></div>
<div class="field PFG-RichLabel" id="archetypes-fieldname-about-the-event"><strong><font size="3">About the Event<br/></font></strong></div>
<div class="field ArchetypesTextAreaWidget " id="archetypes-fieldname-purpose-of-the-event" data-uid="d48ed00212f8438eb4beb4b16bb0547b" data-fieldname="purpose-of-the-event">
<span></span>
<label class="formQuestion" for="purpose-of-the-event">
Purpose of the Event:
<span class="required" title="Required">&nbsp;</span>
<span class="formHelp" id="purpose-of-the-event_help"></span>
</label>
<div class="fieldErrorBox"></div>
<textarea class="blurrable firstToFocus" name="purpose-of-the-event" id="purpose-of-the-event" cols="40" rows="5"></textarea>
</div>
<div class="field ArchetypesStringWidget " id="archetypes-fieldname-number-of-attendees-expected" data-uid="d48ed00212f8438eb4beb4b16bb0547b" data-fieldname="number-of-attendees-expected">
<span></span>
<label class="formQuestion" for="number-of-attendees-expected">
Number of Attendees Expected
<span class="required" title="Required">&nbsp;</span>
<span class="formHelp" id="number-of-attendees-expected_help">(minimum 25 attendees)</span>
</label>
<div class="fieldErrorBox"></div>
<input type="text" name="number-of-attendees-expected" class="blurrable firstToFocus" id="number-of-attendees-expected" size="30" maxlength="255"/>
</div>
<div class="field ArchetypesStringWidget " id="archetypes-fieldname-length-of-presentation-e.g.-30-45-minutes" data-uid="d48ed00212f8438eb4beb4b16bb0547b" data-fieldname="length-of-presentation-e.g.-30-45-minutes">
<span></span>
<label class="formQuestion" for="length-of-presentation-e.g.-30-45-minutes">
Length of Presentation (e.g. 30-45 minutes)
<span class="required" title="Required">&nbsp;</span>
<span class="formHelp" id="length-of-presentation-e.g.-30-45-minutes_help"></span>
</label>
<div class="fieldErrorBox"></div>
<input type="text" name="length-of-presentation-e.g.-30-45-minutes" class="blurrable firstToFocus" id="length-of-presentation-e.g.-30-45-minutes" size="30" maxlength="255"/>
</div>
<div class="field PFG-RichLabel" id="archetypes-fieldname-presentation-topic">
<p><strong><font size="3">Presentation Topic<br/></font></strong></p>
</div>
<div class="field ArchetypesMultiSelectionWidget " id="archetypes-fieldname-choose-a-topic-that-suits-your-event-select-all-that-apply" data-uid="d48ed00212f8438eb4beb4b16bb0547b" data-fieldname="choose-a-topic-that-suits-your-event-select-all-that-apply">
<span></span>
<div class="fieldErrorBox"></div>
<label class="formQuestion" for="choose-a-topic-that-suits-your-event-select-all-that-apply">
Choose a topic that suits your event (select all that apply)
<span class="required" title="Required">&nbsp;</span>
</label>
<select multiple="multiple" class="blurrable" name="choose-a-topic-that-suits-your-event-select-all-that-apply:list" id="choose-a-topic-that-suits-your-event-select-all-that-apply" size="5">
<option value="Terrorism">Terrorism</option>
<option value="CREST Program*">CREST Program*</option>
<option value="Cyber Crime">Cyber Crime</option>
<option value="Public Corruption">Public Corruption</option>
<option value="Gangs">Gangs</option>
<option value="Civil Rights">Civil Rights</option>
<option value="Recruitment and Hiring">Recruitment and Hiring</option>
<option value="Youth-Based Presentation">Youth-Based Presentation</option>
<option value="Other (describe below in comments section)">Other (describe below in comments section)</option>
</select>
</div>
<div class="field PFG-RichLabel" id="archetypes-fieldname-other-event-information">
<p><strong><font size="3">Other Event Information<br/></font></strong></p>
</div>
<div class="field ArchetypesSelectionWidget " id="archetypes-fieldname-will-there-be-q-a-afterwards" data-uid="d48ed00212f8438eb4beb4b16bb0547b" data-fieldname="will-there-be-q-a-afterwards">
<span></span>
<div class="fieldErrorBox"></div>
<span id="will-there-be-q-a-afterwards">

<div class="formQuestion label">
Will there be Q&amp;A afterwards?
<span class="required" title="Required">&nbsp;</span>
<span class="formHelp" id="will-there-be-q-a-afterwards_help"></span>
</div>
<input class="noborder blurrable" type="radio" name="will-there-be-q-a-afterwards" id="will-there-be-q-a-afterwards_1" value="Yes"/>
<label for="will-there-be-q-a-afterwards_1">Yes</label>
<br/>
<input class="noborder blurrable" type="radio" name="will-there-be-q-a-afterwards" id="will-there-be-q-a-afterwards_2" value="No"/>
<label for="will-there-be-q-a-afterwards_2">No</label>
<br/>
</span>
</div>
<div class="field ArchetypesSelectionWidget " id="archetypes-fieldname-will-there-be-audio-visual-equipment-available-for-powerpoint-slides" data-uid="d48ed00212f8438eb4beb4b16bb0547b" data-fieldname="will-there-be-audio-visual-equipment-available-for-powerpoint-slides">
<span></span>
<div class="fieldErrorBox"></div>
<span id="will-there-be-audio-visual-equipment-available-for-powerpoint-slides">

<div class="formQuestion label">
Will there be audio/visual equipment available for PowerPoint slides?
<span class="required" title="Required">&nbsp;</span>
<span class="formHelp" id="will-there-be-audio-visual-equipment-available-for-powerpoint-slides_help"></span>
</div>
<input class="noborder blurrable" type="radio" name="will-there-be-audio-visual-equipment-available-for-powerpoint-slides" id="will-there-be-audio-visual-equipment-available-for-powerpoint-slides_1" value="Yes"/>
<label for="will-there-be-audio-visual-equipment-available-for-powerpoint-slides_1">Yes</label>
<br/>
<input class="noborder blurrable" type="radio" name="will-there-be-audio-visual-equipment-available-for-powerpoint-slides" id="will-there-be-audio-visual-equipment-available-for-powerpoint-slides_2" value="No"/>
<label for="will-there-be-audio-visual-equipment-available-for-powerpoint-slides_2">No</label>
<br/>
</span>
</div>
<div class="field ArchetypesSelectionWidget " id="archetypes-fieldname-is-a-bio-needed-for-the-speaker" data-uid="d48ed00212f8438eb4beb4b16bb0547b" data-fieldname="is-a-bio-needed-for-the-speaker">
<span></span>
<div class="fieldErrorBox"></div>
<span id="is-a-bio-needed-for-the-speaker">

<div class="formQuestion label">
Is a bio needed for the speaker?
<span class="required" title="Required">&nbsp;</span>
<span class="formHelp" id="is-a-bio-needed-for-the-speaker_help"></span>
</div>
<input class="noborder blurrable" type="radio" name="is-a-bio-needed-for-the-speaker" id="is-a-bio-needed-for-the-speaker_1" value="Yes"/>
<label for="is-a-bio-needed-for-the-speaker_1">Yes</label>
<br/>
<input class="noborder blurrable" type="radio" name="is-a-bio-needed-for-the-speaker" id="is-a-bio-needed-for-the-speaker_2" value="No"/>
<label for="is-a-bio-needed-for-the-speaker_2">No</label>
<br/>
</span>
</div>
<div class="field ArchetypesSelectionWidget " id="archetypes-fieldname-will-media-be-present" data-uid="d48ed00212f8438eb4beb4b16bb0547b" data-fieldname="will-media-be-present">
<span></span>
<div class="fieldErrorBox"></div>
<span id="will-media-be-present">

<div class="formQuestion label">
Will media be present?
<span class="required" title="Required">&nbsp;</span>
<span class="formHelp" id="will-media-be-present_help"></span>
</div>
<input class="noborder blurrable" type="radio" name="will-media-be-present" id="will-media-be-present_1" value="Yes"/>
<label for="will-media-be-present_1">Yes</label>
<br/>
<input class="noborder blurrable" type="radio" name="will-media-be-present" id="will-media-be-present_2" value="No"/>
<label for="will-media-be-present_2">No</label>
<br/>
</span>
</div>
<div class="field ArchetypesSelectionWidget " id="archetypes-fieldname-do-you-plan-to-do-any-publicity-related-to-this-event-either-before-or-after-including-through-press-releases-websites-blog-posts-photos-or-other-means" data-uid="d48ed00212f8438eb4beb4b16bb0547b" data-fieldname="do-you-plan-to-do-any-publicity-related-to-this-event-either-before-or-after-including-through-press-releases-websites-blog-posts-photos-or-other-means">
<span></span>
<div class="fieldErrorBox"></div>
<span id="do-you-plan-to-do-any-publicity-related-to-this-event-either-before-or-after-including-through-press-releases-websites-blog-posts-photos-or-other-means">

<div class="formQuestion label">
Do you plan to do any publicity related to this event (either before or after), including through press releases, websites, blog posts, photos, or other means?
<span class="required" title="Required">&nbsp;</span>
<span class="formHelp" id="do-you-plan-to-do-any-publicity-related-to-this-event-either-before-or-after-including-through-press-releases-websites-blog-posts-photos-or-other-means_help"></span>
</div>
<input class="noborder blurrable" type="radio" name="do-you-plan-to-do-any-publicity-related-to-this-event-either-before-or-after-including-through-press-releases-websites-blog-posts-photos-or-other-means" id="do-you-plan-to-do-any-publicity-related-to-this-event-either-before-or-after-including-through-press-releases-websites-blog-posts-photos-or-other-means_1" value="Yes"/>
<label for="do-you-plan-to-do-any-publicity-related-to-this-event-either-before-or-after-including-through-press-releases-websites-blog-posts-photos-or-other-means_1">Yes</label>
<br/>
<input class="noborder blurrable" type="radio" name="do-you-plan-to-do-any-publicity-related-to-this-event-either-before-or-after-including-through-press-releases-websites-blog-posts-photos-or-other-means" id="do-you-plan-to-do-any-publicity-related-to-this-event-either-before-or-after-including-through-press-releases-websites-blog-posts-photos-or-other-means_2" value="No"/>
<label for="do-you-plan-to-do-any-publicity-related-to-this-event-either-before-or-after-including-through-press-releases-websites-blog-posts-photos-or-other-means_2">No</label>
<br/>
</span>
</div>
<div class="field ArchetypesTextAreaWidget " id="archetypes-fieldname-if-yes-please-explain" data-uid="d48ed00212f8438eb4beb4b16bb0547b" data-fieldname="if-yes-please-explain">
<span></span>
<label class="formQuestion" for="if-yes-please-explain">
If yes, please explain.
<span class="formHelp" id="if-yes-please-explain_help"></span>
</label>
<div class="fieldErrorBox"></div>
<textarea class="blurrable firstToFocus" name="if-yes-please-explain" id="if-yes-please-explain" cols="40" rows="5"></textarea>
</div>
</fieldset>
<div class="field ArchetypesTextAreaWidget " id="archetypes-fieldname-comments" data-uid="d48ed00212f8438eb4beb4b16bb0547b" data-fieldname="comments">
<span></span>
<label class="formQuestion" for="comments">
Comments
<span class="formHelp" id="comments_help"></span>
</label>
<div class="fieldErrorBox"></div>
<textarea class="blurrable firstToFocus" name="comments" id="comments" cols="40" rows="5"></textarea>
</div>
<div class="field ArchetypesCaptchaWidget " id="archetypes-fieldname-captcha" data-uid="d48ed00212f8438eb4beb4b16bb0547b" data-fieldname="captcha">
<span></span>
<label class="formQuestion" for="captcha">
Captcha
<span class="required" title="Required">&nbsp;</span>
<span class="formHelp" id="captcha_help"></span>
</label>
<div class="fieldErrorBox"></div>
<script type="text/javascript">
        function playAudio(url) {
        document.getElementById("captcha-audio-embed").innerHTML=
        "<embed src='"+url+"' hidden=true autostart=true loop=false>";
        }
        </script>
<div class="captchaImage">
<script type="text/javascript">
    var RecaptchaOptions = {
        lang: 'en'
    };
    </script>
<script type="text/javascript" src="https://www.google.com/recaptcha/api/challenge?k=6LfDkLwSAAAAAD4IfxM2UpXo_jrotbWHVPWLwZVN&hl=en"></script>
<noscript>
<iframe src="https://www.google.com/recaptcha/api/noscript?k=6LfDkLwSAAAAAD4IfxM2UpXo_jrotbWHVPWLwZVN&hl=en" height="300" width="500" frameborder="0"></iframe><br/>
<textarea name="recaptcha_challenge_field" rows="3" cols="40"></textarea>
<input type='hidden' name='recaptcha_response_field' value='manual_challenge'/>
</noscript>
&nbsp;
</div>
<input type="hidden" name="captcha" value="x"/>
</div>
</div>
<div class="formControls">
<input type="hidden" name="fieldset" value="default"/>
<input type="hidden" name="form.submitted" value="1"/>
<input type="hidden" name="add_reference.field:record" value=""/>
<input type="hidden" name="add_reference.type:record" value=""/>
<input type="hidden" name="add_reference.destination:record" value=""/>
<input type="hidden" name="last_referer" value="https://www.foobar.com"/>
<input type="hidden" name="_authenticator" value="69f4453815e7831cf99ec3eb0c08bec1a6a2c36a"/>
<input class="context" type="submit" name="form_submit" value="Submit"/>
</div>
</form>
</div>
<script>
    // block inline validation
    jQuery(function ($) {
        $("#pfg-fieldwrapper .field").removeAttr('data-uid');
    });
</script>
</div>
<span id="contentBottomLeft"></span>
<span id="contentBottomRight"></span>
</div>
</div>
</td>
</tr>
</tbody>
</table>
</div>
</div>
<div class="visualClear" id="clear-space-before-footer"> </div>
<div id="portal-footer">
<div class="footerWrapper">
<div align="center">
</div>
</div>
</div>
<div id="portal-footer2">
<div class="footer2Wrapper">

</div>
<div id="kss-spinner"><img alt="" src="https://www.foobar.com/spinner.gif"/></div>
</div>
</body>
</html>
'''  # noqa
