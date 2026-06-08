// ==UserScript==
// @name         WordPress: Show PW String + Try Casing
// @namespace    http://project-skyscraper.com
// @version      1.1
// @description  Reveals password fields & auto-tries capitalization variants on submit
// @author       vector_cmdr
// @match        *://*/*
// @grant        none
// ==/UserScript==

(function() {
    'use strict';

    var working = sessionStorage.getItem('wpPwWorking');
    var orig    = sessionStorage.getItem('wpPwOriginal');
    var lastTried = sessionStorage.getItem('wpPwLastTried');
    var queueRaw  = sessionStorage.getItem('wpPwQueue');
    var pwForm = document.querySelector('form.post-password-form');
    var unlocked = !pwForm;

    // --- Step 0: show success popup (after detection reload) ---
    if (working) {
        sessionStorage.removeItem('wpPwWorking');
        sessionStorage.removeItem('wpPwOriginal');
        sessionStorage.removeItem('wpPwLastTried');
        sessionStorage.removeItem('wpPwQueue');
        sessionStorage.removeItem('wpPwIdx');
        alert('Password accepted!\n\nEntered: ' + orig + '\nWorking: ' + working);
        return;
    }

    // --- Step 1: page reloaded and password was accepted ---
    if (unlocked && lastTried) {
        sessionStorage.setItem('wpPwWorking', lastTried);
        sessionStorage.removeItem('wpPwLastTried');
        location.reload();
        return;
    }

    // --- Step 2: page locked, queue running -> try next variant ---
    if (pwForm && queueRaw) {
        var queue = JSON.parse(queueRaw);
        var idx   = parseInt(sessionStorage.getItem('wpPwIdx') || '0', 10);
        var pwInput = pwForm.querySelector('input[name="post_password"]');
        if (!pwInput) return;

        if (idx >= queue.length) {
            sessionStorage.removeItem('wpPwQueue');
            sessionStorage.removeItem('wpPwIdx');
            sessionStorage.removeItem('wpPwLastTried');
            pwInput.placeholder = 'All variants tried — check manually';
            var btn = pwForm.querySelector('input[type="submit"]');
            if (btn) btn.disabled = false;
            return;
        }

        // Set the next variant and submit
        sessionStorage.setItem('wpPwLastTried', queue[idx]);
        sessionStorage.setItem('wpPwIdx', idx + 1);
        pwInput.value = queue[idx];
        pwForm.submit();
        return;
    }

    // --- Step 3: idle state on locked page ---
    if (pwForm) {
        // Reveal password fields
        document.querySelectorAll('input[type="password"]').forEach(function(input) {
            input.type = 'text';
        });

        var pwInput = pwForm.querySelector('input[name="post_password"]');
        if (!pwInput) return;

        pwForm.addEventListener('submit', function(e) {
            e.preventDefault();

            var val = pwInput.value;
            if (!val) return;

            var variants = generateVariants(val);
            sessionStorage.setItem('wpPwOriginal', val);
            sessionStorage.setItem('wpPwQueue', JSON.stringify(variants));
            sessionStorage.setItem('wpPwIdx', 1);
            sessionStorage.setItem('wpPwLastTried', variants[0]);

            pwInput.value = variants[0];
            pwForm.submit();
        });
    }

    function generateVariants(s) {
        var seen = new Set();
        var out = [];

        function add(v) {
            if (!seen.has(v)) { seen.add(v); out.push(v); }
        }

        add(s);
        add(s.toUpperCase());
        add(s.toLowerCase());
        add(capitalizeWords(s));
        add(capitalizeFirst(s));
        add(toggleCase(s));
        add(alternatingCase(s, true));
        add(alternatingCase(s, false));

        return out;
    }

    function capitalizeWords(s) {
        return s.toLowerCase().replace(/\b\w/g, function(c) { return c.toUpperCase(); });
    }

    function capitalizeFirst(s) {
        return s.charAt(0).toUpperCase() + s.slice(1).toLowerCase();
    }

    function toggleCase(s) {
        return s.split('').map(function(c) {
            return c === c.toUpperCase() ? c.toLowerCase() : c.toUpperCase();
        }).join('');
    }

    function alternatingCase(s, startUpper) {
        var i = 0;
        return s.split('').map(function(c) {
            if (c === ' ') return c;
            var result = (startUpper ? (i % 2 === 0) : (i % 2 === 1)) ? c.toUpperCase() : c.toLowerCase();
            i++;
            return result;
        }).join('');
    }
})();
