// ==UserScript==
// @name         Project Skyscraper - Node Controller
// @namespace    http://tampermonkey.net/
// @version      1.1
// @description  Control node count on project-skyscraper.com via date override
// @author       vector_cmdr
// @match        https://project-skyscraper.com/*
// @grant        none
// @run-at       document-start
// ==/UserScript==

(function() {
    'use strict';

    // Change this value or use the UI slider
    let TARGET_DAY = 28;

    // Override Date
    const OrigDate = Date;
    function applyDateOverride(day) {
        const d = Math.max(1, Math.min(31, Math.round(day)));
        const fakeDate = new OrigDate(`2026-01-${String(d).padStart(2, '0')}T12:00:00Z`);
        Date = class extends OrigDate {
            constructor(...args) {
                if (args.length) return new OrigDate(...args);
                return new OrigDate(fakeDate.getTime());
            }
            static now() { return fakeDate.getTime(); }
            static parse(s) { return OrigDate.parse(s); }
            static UTC(...a) { return OrigDate.UTC(...a); }
        };
        TARGET_DAY = d;
        return d;
    }
    applyDateOverride(TARGET_DAY);

    // Panel
    window.addEventListener('DOMContentLoaded', () => {
        const panel = document.createElement('div');
        panel.id = 'ps-node-panel';
        panel.innerHTML = `
            <div style="background:rgba(0,0,0,0.85);border:1px solid #0df;border-radius:6px;padding:10px 14px;font:13px monospace;color:#0df;">
                <div style="margin-bottom:6px;font-weight:bold;letter-spacing:1px;">NODE CONTROLLER</div>
                <label style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
                    Day: <input type="range" id="ps-day-slider" min="1" max="31" value="${TARGET_DAY}" style="width:120px;">
                    <span id="ps-day-val">${TARGET_DAY}</span>
                </label>
                <label style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
                    Nodes: <span id="ps-node-est">${Math.max(3, Math.round(TARGET_DAY * 48 / 28))}</span>
                </label>
                <button id="ps-rebuild" style="background:#0df;color:#111;border:none;border-radius:3px;padding:3px 10px;cursor:pointer;font:bold 12px monospace;margin-top:4px;">REBUILD</button>
                <span style="color:#666;margin-left:8px;font-size:11px;">(canvas)</span>
            </div>
        `;
        Object.assign(panel.style, {
            position: 'fixed', bottom: '20px', left: '20px', zIndex: '99999', userSelect: 'none'
        });
        document.body.appendChild(panel);

        const slider = document.getElementById('ps-day-slider');
        const dayVal = document.getElementById('ps-day-val');
        const nodeEst = document.getElementById('ps-node-est');
        const rebuildBtn = document.getElementById('ps-rebuild');

        function updateEst(d) {
            dayVal.textContent = d;
            nodeEst.textContent = Math.max(3, Math.round(d * 48 / 28));
        }

        slider.addEventListener('input', () => {
            updateEst(parseInt(slider.value, 10));
        });

        rebuildBtn.addEventListener('click', () => {
            const d = parseInt(slider.value, 10);
            applyDateOverride(d);
            updateEst(d);
            // Trigger canvas rebuild by forcing resize event
            window.dispatchEvent(new Event('resize'));
        });
    });
})();
