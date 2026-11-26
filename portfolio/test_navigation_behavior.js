const assert = require('node:assert/strict');
const navigationPath = require.resolve('../static/js/navigation.js');

function runPage(sectionPositions) {
    const listeners = {};
    const progress = { style: {} };
    const headerClasses = new Set();
    const header = {
        classList: {
            toggle(name, enabled) {
                if (enabled) headerClasses.add(name);
                else headerClasses.delete(name);
            },
        },
        querySelector: () => progress,
    };
    const links = Object.keys(sectionPositions).map(id => ({
        attributes: { href: '#' + id },
        classes: new Set(),
        getAttribute(name) { return this.attributes[name]; },
        setAttribute(name, value) { this.attributes[name] = value; },
        removeAttribute(name) { delete this.attributes[name]; },
        classList: null,
    }));
    links.forEach(link => {
        link.classList = {
            add: name => link.classes.add(name),
            remove: name => link.classes.delete(name),
        };
    });
    const win = {
        scrollY: 0,
        innerHeight: 800,
        addEventListener(name, callback) {
            (listeners[name] ||= []).push(callback);
        },
        requestAnimationFrame(callback) { callback(); },
    };
    const doc = {
        readyState: 'complete',
        documentElement: { scrollHeight: 3500 },
        querySelector(selector) { return selector === '.site-header' ? header : null; },
        querySelectorAll(selector) { return selector === '.nav-link[href^="#"]' ? links : []; },
        getElementById(id) {
            return { id, getBoundingClientRect: () => ({ top: sectionPositions[id] - win.scrollY }) };
        },
    };
    const previousDocument = global.document;
    const previousWindow = global.window;
    global.document = doc;
    global.window = win;
    delete require.cache[navigationPath];
    require(navigationPath);
    delete require.cache[navigationPath];
    global.document = previousDocument;
    global.window = previousWindow;

    function withPageGlobals(callback) {
        const currentDocument = global.document;
        const currentWindow = global.window;
        global.document = doc;
        global.window = win;
        try {
            callback();
        } finally {
            global.document = currentDocument;
            global.window = currentWindow;
        }
    }

    return {
        links, headerClasses, progress,
        scroll(y) {
            withPageGlobals(() => {
                win.scrollY = y;
                (listeners.scroll || []).forEach(callback => callback());
            });
        },
    };
}

const page = runPage({ home: 0, about: 800, projects: 2000, contact: 3100 });
function active() {
    return page.links.filter(link => link.classes.has('active')).map(link => link.attributes.href);
}
assert.deepEqual(active(), ['#home']);
page.scroll(900);
assert.deepEqual(active(), ['#about']);
assert.equal(page.links[1].attributes['aria-current'], 'location');
assert.equal(page.links[0].attributes['aria-current'], undefined);
assert.equal(page.headerClasses.has('is-stuck'), true);
assert.equal(page.headerClasses.has('is-hidden'), false);
assert.equal(page.progress.style.transform, 'scaleX(0.3333333333333333)');
page.scroll(2700);
assert.deepEqual(active(), ['#contact']);
assert.equal(page.progress.style.transform, 'scaleX(1)');

const detail = runPage({});
detail.scroll(2700);
assert.equal(detail.progress.style.transform, 'scaleX(1)');
