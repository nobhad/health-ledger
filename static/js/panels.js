"use strict";
// Three-panel pages (Sources, References): drag a splitter to resize the
// outer panels, and remember the widths.
//
// A .panel-container with two .panel-splitter children gets this. The first
// and last .panel are the ones resized; the middle one takes what is left.
// data-panel-state on the container names the pair of localStorage keys, so
// each page remembers its own widths.
(() => {
    const LEFT_MIN_WIDTH = 200;
    const LEFT_MAX_WIDTH = 500;
    const RIGHT_MIN_WIDTH = 250;
    const RIGHT_MAX_WIDTH = 600;
    const RESIZE_CURSOR = 'col-resize';
    function setUp(container) {
        const splitters = Array.from(container.querySelectorAll(':scope > .panel-splitter'));
        const panels = Array.from(container.querySelectorAll(':scope > .panel'));
        if (splitters.length !== 2 || panels.length !== 3) {
            return;
        }
        const [leftSplitter, rightSplitter] = splitters;
        const leftPanel = panels[0];
        const rightPanel = panels[2];
        const stateName = container.dataset.panelState;
        const leftKey = stateName ? `${stateName}LeftWidth` : null;
        const rightKey = stateName ? `${stateName}RightWidth` : null;
        if (leftKey && rightKey) {
            const savedLeft = localStorage.getItem(leftKey);
            const savedRight = localStorage.getItem(rightKey);
            if (savedLeft) {
                leftPanel.style.width = savedLeft;
            }
            if (savedRight) {
                rightPanel.style.width = savedRight;
            }
        }
        let dragging = null;
        const start = (splitter) => (event) => {
            dragging = splitter;
            splitter.classList.add('active');
            document.body.style.cursor = RESIZE_CURSOR;
            event.preventDefault();
        };
        leftSplitter.addEventListener('mousedown', start(leftSplitter));
        rightSplitter.addEventListener('mousedown', start(rightSplitter));
        document.addEventListener('mousemove', (event) => {
            if (!dragging) {
                return;
            }
            const bounds = container.getBoundingClientRect();
            if (dragging === leftSplitter) {
                const width = event.clientX - bounds.left;
                if (width > LEFT_MIN_WIDTH && width < LEFT_MAX_WIDTH) {
                    leftPanel.style.width = `${width}px`;
                }
            }
            else {
                const width = bounds.right - event.clientX;
                if (width > RIGHT_MIN_WIDTH && width < RIGHT_MAX_WIDTH) {
                    rightPanel.style.width = `${width}px`;
                }
            }
        });
        document.addEventListener('mouseup', () => {
            if (!dragging) {
                return;
            }
            dragging.classList.remove('active');
            dragging = null;
            document.body.style.cursor = '';
            if (leftKey && rightKey) {
                localStorage.setItem(leftKey, leftPanel.style.width);
                localStorage.setItem(rightKey, rightPanel.style.width);
            }
        });
    }
    document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('.panel-container').forEach(setUp);
    });
})();
