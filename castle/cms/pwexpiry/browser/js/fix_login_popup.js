jQuery(function($){

    if (jQuery.browser.msie && parseInt(jQuery.browser.version, 10) < 7) {
        // it's not realistic to think we can deal with all the bugs
        // of IE 6 and lower. Fortunately, all this is just progressive
        // enhancement.
        return;
    }

    // First remove the original registration.
    pb.remove_overlay($('#portal-personaltools a[href$="/login"], #portal-personaltools a[href$="/login_form"], .discussion a[href$="/login"], .discussion a[href$="/login_form"]'));

    // And reregister with 'form[name="mail_password"]' in it.
    // login form (based on plone's default registration - also handles mail_password form to show warning for expired passwords.
    $('#portal-personaltools a[href$="/login"], #portal-personaltools a[href$="/login_form"], .discussion a[href$="/login"], .discussion a[href$="/login_form"]').prepOverlay(
        {
            subtype: 'ajax',
            filter: common_content_filter,
            formselector: 'form#login_form, form[name="mail_password"]',
            cssclass: 'overlay-login',
            noform: function () {
                if (location.href.search(/pwreset_finish$/) >= 0) {
                    return 'redirect';
                } else {
                    return 'reload';
                }
            },
            redirect: function () {
                var href = location.href;
                if (href.search(/pwreset_finish$/) >= 0) {
                    return href.slice(0, href.length-14) + 'logged_in';
                } else {
                    return href;
                }
            }
        }
    );
});