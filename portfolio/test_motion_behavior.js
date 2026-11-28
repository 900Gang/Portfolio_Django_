const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const source = fs.readFileSync(require.resolve('../static/js/motion.js'), 'utf8');

function page(readyState = 'complete', cinematic = false) {
    const classes = new Set(['motion-ready']);
    const listeners = {};
    const frames = new Map();
    const timers = new Map();
    const observers = [];
    let nextId = 0;
    const preference = {
        matches: false,
        addEventListener(name, callback) { (listeners['motion:' + name] ||= []).push(callback); },
        removeEventListener() {},
    };
    const score = { textContent: '0.99', getAttribute: () => '0.99' };
    const stat = { textContent: '04', getAttribute: () => '4' };
    const word = { style: {} };
    const photo = { style: {} };
    const hero = {};
    const sceneClasses = new Set();
    const scene = {
        clientWidth: 1000, clientHeight: 600,
        classList: {
            add: name => sceneClasses.add(name),
            remove: name => sceneClasses.delete(name),
            contains: name => sceneClasses.has(name),
        },
    };
    const document = {
        readyState,
        documentElement: { classList: {
            contains: name => classes.has(name),
            add: name => classes.add(name),
            remove: name => classes.delete(name),
        } },
        querySelector(selector) {
            return {
                '.hero-detect-score': score, '.hero': hero,
                '.hero-word-wrap': word, '.hero-parallax': photo,
                '.hero-cinematic': cinematic ? scene : null,
            }[selector] || null;
        },
        querySelectorAll(selector) { return selector === '[data-count]' ? [stat] : []; },
        addEventListener(name, callback) { (listeners['document:' + name] ||= []).push(callback); },
        removeEventListener() {},
    };
    class IntersectionObserver {
        constructor(callback) { this.callback = callback; this.disconnected = false; observers.push(this); }
        observe() {}
        unobserve() {}
        disconnect() { this.disconnected = true; }
    }
    const window = {
        matchMedia: () => preference, innerWidth: 1200, scrollY: 100,
        IntersectionObserver,
        requestAnimationFrame(callback) { const id = ++nextId; frames.set(id, callback); return id; },
        cancelAnimationFrame(id) { frames.delete(id); },
        setTimeout(callback, delay) { const id = ++nextId; timers.set(id, { callback, delay }); return id; },
        clearTimeout(id) { timers.delete(id); },
        addEventListener(name, callback) { (listeners[name] ||= []).push(callback); },
        removeEventListener(name, callback) {
            listeners[name] = (listeners[name] || []).filter(item => item !== callback);
        },
    };
    vm.runInNewContext(source, {
        window, document, IntersectionObserver,
        getComputedStyle: () => ({ getPropertyValue: () => '' }),
    });
    return {
        classes, sceneClasses, preference, score, stat, word, photo, frames, timers, observers, listeners,
        dispatch(name) { (listeners[name] || []).slice().forEach(callback => callback()); },
        reduce() { preference.matches = true; this.dispatch('motion:change'); },
    };
}

const running = page();
assert.equal(running.score.textContent, '0.00');
assert.equal(running.stat.textContent, '00');
running.observers[0].callback([{ isIntersecting: true, target: running.stat }]);
running.dispatch('scroll');
const queued = [...running.frames.values()];
running.frames.clear();
queued.forEach(callback => callback(0));
assert.notEqual(running.word.style.transform, '');
running.reduce();
assert.equal(running.classes.has('motion-ready'), false);
assert.equal(running.score.textContent, '0.99');
assert.equal(running.stat.textContent, '04');
assert.equal(running.word.style.transform, '');
assert.equal(running.photo.style.transform, '');
assert.equal(running.frames.size, 0);
assert.equal(running.timers.size, 0);
assert.ok(running.observers.every(observer => observer.disconnected));
queued.forEach(callback => callback(1000));
running.observers[0].callback([{ isIntersecting: true, target: running.stat }]);
running.dispatch('scroll');
assert.equal(running.stat.textContent, '04');
assert.equal(running.frames.size, 0);

const beforeReady = page('loading');
beforeReady.reduce();
beforeReady.dispatch('document:DOMContentLoaded');
assert.equal(beforeReady.classes.has('motion-ready'), false);
assert.equal(beforeReady.score.textContent, '0.99');
assert.equal(beforeReady.stat.textContent, '04');
assert.equal(beforeReady.observers.length, 0);

const intro = page('complete', true);
assert.equal(intro.sceneClasses.has('is-playing'), true);
assert.equal(intro.classes.has('cinematic-active'), true);
assert.ok([...intro.timers.values()].some(timer => timer.delay === 7450));
intro.reduce();
assert.equal(intro.sceneClasses.has('is-playing'), false);
assert.equal(intro.classes.has('cinematic-active'), false);
assert.equal(intro.frames.size, 0);
assert.equal(intro.timers.size, 0);

const dismissedIntro = page('complete', true);
dismissedIntro.dispatch('keydown');
assert.equal(dismissedIntro.sceneClasses.has('is-playing'), false);
assert.equal(dismissedIntro.classes.has('cinematic-active'), false);
assert.equal(dismissedIntro.timers.size, 1); // Detection counter remains active.
