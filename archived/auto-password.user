// ==UserScript==
// @name         Project Skyscraper: Auto-fill password
// @namespace    https://project-skyscraper.com
// @version      1.0
// @description  Auto-fills known passwords on project-skyscraper.com password-protected pages
// @author       vector_cmdr
// @match        https://project-skyscraper.com/*
// @grant        none
// ==/UserScript==

(function() {
    'use strict';

    var page = window.location.pathname;

    // Add new page and password pairs here:
    var passwords = {
        '/request-memory-timestamp-094317/': 'EMILY',
        '/report-bru-ent-reunion-peak/': 'EVENT HORIZON',
    };

    var pw = null;
    for (var path in passwords) {
        if (page.startsWith(path)) {
            pw = passwords[path];
            break;
        }
    }
    if (!pw) return;

    // Check if already unlocked (no password form)
    var form = document.querySelector('form.post-password-form');
    if (!form) return;

    var input = form.querySelector('input[name="post_password"]');
    if (!input) return;
    var submit = form.querySelector('input[type="submit"]');

    input.type = 'text';
    input.value = pw;
    if (submit) submit.disabled = false;

    // Auto-submit after a brief delay so the reveal is visible
    setTimeout(function() {
        form.submit();
    }, 300);
})();
