/**
 * Portfolio assistant widget.
 *
 * Sends the visitor's question, plus the last few turns, to the chat
 * endpoint and shows the reply. Replies are model output, so they are shown
 * by building DOM nodes and setting textContent; no reply text is ever
 * parsed as markup. Only http(s), mailto and site-relative targets become
 * links.
 */
(function () {
    'use strict';

    var MAX_HISTORY = 6;
    var SAFE_LINK = /^(https?:\/\/|mailto:|\/(?!\/))/i;

    function ready(fn) {
        if (document.readyState !== 'loading') {
            fn();
        } else {
            document.addEventListener('DOMContentLoaded', fn);
        }
    }

    function newConversationId() {
        // The server generates one when this is empty.
        return window.crypto && window.crypto.randomUUID ? window.crypto.randomUUID() : '';
    }

    /* --- Rendering: a small, safe subset of Markdown ----------------------- */
    function makeLink(label, href) {
        if (!SAFE_LINK.test(href)) {
            return document.createTextNode(label);
        }
        var link = document.createElement('a');
        link.className = 'chatbot-link';
        link.href = href;
        link.textContent = label;
        if (/^https?:/i.test(href)) {
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
        }
        return link;
    }

    // **bold**, [text](url) and bare URLs.
    function appendInline(parent, text) {
        var pattern = /\*\*([^*]+)\*\*|\[([^\]]+)\]\(([^)\s]+)\)|(https?:\/\/[^\s)]+)/g;
        var last = 0;
        var match;
        while ((match = pattern.exec(text)) !== null) {
            if (match.index > last) {
                parent.appendChild(document.createTextNode(text.slice(last, match.index)));
            }
            if (match[1] !== undefined) {
                var strong = document.createElement('strong');
                strong.textContent = match[1];
                parent.appendChild(strong);
            } else if (match[2] !== undefined) {
                parent.appendChild(makeLink(match[2], match[3]));
            } else {
                parent.appendChild(makeLink(match[4], match[4]));
            }
            last = pattern.lastIndex;
        }
        if (last < text.length) {
            parent.appendChild(document.createTextNode(text.slice(last)));
        }
    }

    // Paragraphs, with runs of "- " lines turned into bullet lists.
    function renderReply(container, text) {
        var list = null;
        var paragraph = null;
        text.replace(/\r/g, '').split('\n').forEach(function (raw) {
            var line = raw.trim();
            if (!line) {
                list = null;
                paragraph = null;
                return;
            }
            if (/^[-*]\s+/.test(line)) {
                paragraph = null;
                if (!list) {
                    list = document.createElement('ul');
                    container.appendChild(list);
                }
                var item = document.createElement('li');
                appendInline(item, line.replace(/^[-*]\s+/, ''));
                list.appendChild(item);
            } else {
                list = null;
                if (paragraph) {
                    paragraph.appendChild(document.createElement('br'));
                } else {
                    paragraph = document.createElement('p');
                    container.appendChild(paragraph);
                }
                appendInline(paragraph, line);
            }
        });
    }

    /* --- Widget ------------------------------------------------------------ */
    function init() {
        var root = document.querySelector('.chatbot');
        if (!root) {
            return;
        }

        var launcher = root.querySelector('.chatbot-launcher');
        var panel = root.querySelector('.chatbot-panel');
        var closeButton = root.querySelector('.chatbot-close');
        var messages = root.querySelector('.chatbot-messages');
        var conversation = root.querySelector('.chatbot-conversation');
        var suggestions = root.querySelector('.chatbot-suggestions');
        var form = root.querySelector('.chatbot-form');
        var input = root.querySelector('.chatbot-input');
        var send = root.querySelector('.chatbot-send');
        var csrf = root.querySelector('input[name="csrfmiddlewaretoken"]');
        var url = root.getAttribute('data-chat-url');
        var avatar = root.querySelector('.chatbot-avatar');
        var avatarStatus = root.querySelector('.chatbot-avatar-status');
        var micButton = root.querySelector('.chatbot-mic');
        var speechButton = root.querySelector('.chatbot-speech');
        var voiceStatus = root.querySelector('.chatbot-voice-status');
        var Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        var recognition = null;
        var recognitionActive = false;
        var speechEnabled = false;
        var speechSupported = !!(window.speechSynthesis && window.SpeechSynthesisUtterance);
        var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
        var outfits = ['black', 'red', 'white', 'blue', 'violet', 'power'];
        var outfitIndex = 0;
        var clickTimer = null;
        var smashTimer = null;
        var pointerFrame = null;

        var history = [];
        var conversationId = newConversationId();
        var busy = false;

        function open() {
            panel.hidden = false;
            root.classList.add('is-open');
            launcher.setAttribute('aria-expanded', 'true');
            input.focus();
        }

        function close() {
            if (recognitionActive) {
                recognition.abort();
            }
            if (window.speechSynthesis) {
                window.speechSynthesis.cancel();
            }
            panel.hidden = true;
            root.classList.remove('is-open');
            launcher.setAttribute('aria-expanded', 'false');
            launcher.focus();
        }

        function roar() {
            var AudioContext = window.AudioContext || window.webkitAudioContext;
            if (!AudioContext) {
                avatarStatus.textContent = 'Green transformation. Sound is unavailable in this browser.';
                return;
            }
            try {
                var context = new AudioContext();
                var oscillator = context.createOscillator();
                var volume = context.createGain();
                var noise = context.createBufferSource();
                var noiseGain = context.createGain();
                var filter = context.createBiquadFilter();
                var now = context.currentTime;
                var buffer = context.createBuffer(1, Math.ceil(context.sampleRate * 0.56), context.sampleRate);
                var samples = buffer.getChannelData(0);
                for (var i = 0; i < samples.length; i += 1) {
                    samples[i] = Math.random() * 2 - 1;
                }
                noise.buffer = buffer;
                noiseGain.gain.setValueAtTime(0.35, now);
                filter.type = 'lowpass';
                filter.frequency.setValueAtTime(700, now);
                oscillator.type = 'sawtooth';
                oscillator.frequency.setValueAtTime(190, now);
                oscillator.frequency.exponentialRampToValueAtTime(65, now + 0.55);
                volume.gain.setValueAtTime(0.001, now);
                volume.gain.exponentialRampToValueAtTime(0.045, now + 0.06);
                volume.gain.exponentialRampToValueAtTime(0.001, now + 0.55);
                oscillator.connect(volume);
                noise.connect(filter);
                filter.connect(noiseGain);
                noiseGain.connect(volume);
                volume.connect(context.destination);
                oscillator.onended = function () { context.close(); };
                oscillator.start(now);
                noise.start(now);
                oscillator.stop(now + 0.56);
                if (context.state === 'suspended') {
                    context.resume().catch(function () {
                        avatarStatus.textContent = 'Green transformation. Sound could not be played.';
                        context.close();
                    });
                }
            } catch (error) {
                avatarStatus.textContent = 'Green transformation. Sound could not be played.';
            }
        }

        function changeOutfit() {
            window.clearTimeout(clickTimer);
            clickTimer = null;
            window.clearTimeout(smashTimer);
            avatar.classList.remove('is-smashing');
            outfitIndex = (outfitIndex + 1) % outfits.length;
            avatar.setAttribute('data-outfit', outfits[outfitIndex]);
            if (outfits[outfitIndex] === 'power') {
                avatarStatus.textContent = 'Green transformation and smash.';
                avatar.classList.add('is-smashing');
                smashTimer = window.setTimeout(function () {
                    avatar.classList.remove('is-smashing');
                }, 1800);
                roar();
            } else {
                avatarStatus.textContent = 'Avatar outfit: ' + outfits[outfitIndex] + '.';
            }
        }

        launcher.addEventListener('click', function (event) {
            // Keyboard activation opens chat immediately.
            if (event.detail === 0) {
                window.clearTimeout(clickTimer);
                clickTimer = null;
                open();
                return;
            }
            if (clickTimer !== null) {
                window.clearTimeout(clickTimer);
                clickTimer = null;
                changeOutfit();
                return;
            }
            clickTimer = window.setTimeout(function () {
                clickTimer = null;
                open();
            }, 400);
        });
        launcher.addEventListener('keydown', function (event) {
            if (event.shiftKey && event.key.toLowerCase() === 'c') {
                event.preventDefault();
                changeOutfit();
            }
        });
        window.addEventListener('pointermove', function (event) {
            if (event.pointerType !== 'mouse' || reducedMotion.matches || root.classList.contains('is-open')) {
                return;
            }
            if (pointerFrame !== null) {
                window.cancelAnimationFrame(pointerFrame);
            }
            pointerFrame = window.requestAnimationFrame(function () {
                var rect = avatar.getBoundingClientRect();
                var x = Math.max(-4, Math.min(4, (event.clientX - (rect.left + rect.width / 2)) / 100));
                var y = Math.max(-3, Math.min(3, (event.clientY - (rect.top + rect.height / 2)) / 100));
                avatar.style.setProperty('--avatar-x', x + 'px');
                avatar.style.setProperty('--avatar-y', y + 'px');
                pointerFrame = null;
            });
        }, { passive: true });
        reducedMotion.addEventListener('change', function () {
            if (reducedMotion.matches) {
                if (pointerFrame !== null) {
                    window.cancelAnimationFrame(pointerFrame);
                    pointerFrame = null;
                }
                avatar.style.removeProperty('--avatar-x');
                avatar.style.removeProperty('--avatar-y');
            }
        });
        closeButton.addEventListener('click', close);

        if (Recognition && window.isSecureContext) {
            recognition = new Recognition();
            recognition.lang = document.documentElement.lang || 'en';
            recognition.interimResults = false;
            recognition.maxAlternatives = 1;
            micButton.disabled = false;
            recognition.onstart = function () {
                if (panel.hidden || busy) {
                    recognition.abort();
                    return;
                }
                micButton.setAttribute('aria-pressed', 'true');
                micButton.textContent = 'Stop listening';
                voiceStatus.textContent = 'Listening. Speak your question.';
            };
            recognition.onresult = function (event) {
                if (panel.hidden || busy) {
                    return;
                }
                var spoken = event.results[0][0].transcript.trim();
                var combined = input.value.trim() ? input.value.trim() + ' ' + spoken : spoken;
                input.value = combined.slice(0, input.maxLength);
                voiceStatus.textContent = combined.length > input.maxLength
                    ? 'Transcript shortened to 500 characters. Review it before sending.'
                    : 'Transcript ready. Review it before sending.';
                input.focus();
            };
            recognition.onerror = function (event) {
                if (event.error === 'aborted') {
                    return;
                }
                if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
                    voiceStatus.textContent = 'Microphone access was denied. Check browser permissions or type your question.';
                } else {
                    voiceStatus.textContent = 'Voice input failed (' + event.error + '). Try again or type your question.';
                }
            };
            recognition.onend = function () {
                recognitionActive = false;
                micButton.setAttribute('aria-pressed', 'false');
                micButton.textContent = 'Speak';
                if (voiceStatus.textContent === 'Listening. Speak your question.' ||
                    voiceStatus.textContent === 'Starting voice input...') {
                    voiceStatus.textContent = 'Listening stopped. You can speak again or type your question.';
                }
            };
            micButton.addEventListener('click', function () {
                if (recognitionActive) {
                    recognition.abort();
                    return;
                }
                try {
                    recognitionActive = true;
                    micButton.setAttribute('aria-pressed', 'true');
                    micButton.textContent = 'Stop listening';
                    voiceStatus.textContent = 'Starting voice input...';
                    recognition.start();
                } catch (error) {
                    recognitionActive = false;
                    micButton.setAttribute('aria-pressed', 'false');
                    micButton.textContent = 'Speak';
                    voiceStatus.textContent = 'Could not start voice input. Try again or type your question.';
                }
            });
        }
        if (speechSupported) {
            speechButton.disabled = false;
            speechButton.addEventListener('click', function () {
                speechEnabled = !speechEnabled;
                speechButton.setAttribute('aria-pressed', String(speechEnabled));
                speechButton.textContent = 'Read replies aloud: ' + (speechEnabled ? 'On' : 'Off');
                if (!speechEnabled) {
                    window.speechSynthesis.cancel();
                }
                voiceStatus.textContent = speechEnabled ? 'New replies will be read aloud.' : 'Spoken replies are off.';
            });
        }
        voiceStatus.textContent = (recognition
            ? 'Use Speak for voice input, or type your question.'
            : 'Voice input is unavailable in this browser or connection. You can still type.')
            + (speechSupported ? '' : ' Spoken replies are unavailable in this browser.');

        // Escape closes; Tab stays inside the open dialog.
        panel.addEventListener('keydown', function (event) {
            if (event.key === 'Escape') {
                event.preventDefault();
                close();
                return;
            }
            if (event.key !== 'Tab') {
                return;
            }
            var focusable = Array.prototype.filter.call(
                panel.querySelectorAll('button, textarea, a[href]'),
                function (element) { return !element.disabled && element.offsetParent !== null; }
            );
            if (!focusable.length) {
                return;
            }
            var first = focusable[0];
            var last = focusable[focusable.length - 1];
            if (event.shiftKey && document.activeElement === first) {
                event.preventDefault();
                last.focus();
            } else if (!event.shiftKey && document.activeElement === last) {
                event.preventDefault();
                first.focus();
            }
        });

        function scrollToEnd() {
            conversation.scrollTop = conversation.scrollHeight;
        }

        function addMessage(kind, text) {
            var bubble = document.createElement('div');
            bubble.className = 'chatbot-message is-' + kind;
            if (kind === 'assistant') {
                renderReply(bubble, text);
            } else {
                var paragraph = document.createElement('p');
                paragraph.textContent = text;
                bubble.appendChild(paragraph);
            }
            messages.appendChild(bubble);
            scrollToEnd();
            return bubble;
        }

        function showTyping() {
            var typing = document.createElement('div');
            typing.className = 'chatbot-message is-assistant chatbot-typing';
            typing.setAttribute('role', 'status');
            typing.setAttribute('aria-label', 'The assistant is typing');
            for (var i = 0; i < 3; i += 1) {
                typing.appendChild(document.createElement('span'));
            }
            messages.appendChild(typing);
            scrollToEnd();
            return typing;
        }

        function setBusy(state) {
            busy = state;
            input.disabled = state;
            send.disabled = state;
            micButton.disabled = state || !recognition;
        }

        function ask(rawQuestion) {
            var question = rawQuestion.trim();
            if (!question || busy) {
                return;
            }
            if (recognitionActive) {
                recognition.abort();
            }
            if (suggestions) {
                suggestions.hidden = true;
            }
            addMessage('user', question);
            input.value = '';
            setBusy(true);
            var typing = showTyping();

            fetch(url, {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrf ? csrf.value : ''
                },
                body: JSON.stringify({
                    message: question,
                    history: history.slice(-MAX_HISTORY),
                    conversation_id: conversationId
                })
            })
                .then(function (response) {
                    return response.json()
                        .catch(function () { return {}; })
                        .then(function (data) { return { ok: response.ok, data: data }; });
                })
                .then(function (result) {
                    typing.remove();
                    if (result.ok && result.data.reply) {
                        if (result.data.conversation_id) {
                            conversationId = result.data.conversation_id;
                        }
                        history.push(
                            { role: 'user', content: question },
                            { role: 'assistant', content: result.data.reply }
                        );
                        var reply = addMessage('assistant', result.data.reply);
                        if (speechEnabled && !panel.hidden) {
                            window.speechSynthesis.cancel();
                            var utterance = new SpeechSynthesisUtterance(reply.textContent);
                            utterance.onerror = function (event) {
                                if (event.error !== 'canceled' && event.error !== 'interrupted') {
                                    voiceStatus.textContent = 'Could not play the spoken reply. The text is still available.';
                                }
                            };
                            window.speechSynthesis.speak(utterance);
                        }
                    } else {
                        addMessage('error', result.data.error || 'Something went wrong. Please try again.');
                    }
                })
                .catch(function () {
                    typing.remove();
                    addMessage('error', 'The assistant could not be reached. Check your connection and try again.');
                })
                .then(function () {
                    setBusy(false);
                    if (!panel.hidden) {
                        input.focus();
                    }
                });
        }

        form.addEventListener('submit', function (event) {
            event.preventDefault();
            ask(input.value);
        });

        // Enter sends; Shift+Enter starts a new line.
        input.addEventListener('keydown', function (event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                ask(input.value);
            }
        });

        if (suggestions) {
            suggestions.addEventListener('click', function (event) {
                var chip = event.target.closest('.chatbot-chip');
                if (chip) {
                    ask(chip.textContent);
                }
            });
        }
    }

    ready(init);
})();
