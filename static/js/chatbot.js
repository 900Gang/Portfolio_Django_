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
        var suggestions = root.querySelector('.chatbot-suggestions');
        var form = root.querySelector('.chatbot-form');
        var input = root.querySelector('.chatbot-input');
        var send = root.querySelector('.chatbot-send');
        var csrf = root.querySelector('input[name="csrfmiddlewaretoken"]');
        var url = root.getAttribute('data-chat-url');

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
            panel.hidden = true;
            root.classList.remove('is-open');
            launcher.setAttribute('aria-expanded', 'false');
            launcher.focus();
        }

        launcher.addEventListener('click', open);
        closeButton.addEventListener('click', close);

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
            messages.scrollTop = messages.scrollHeight;
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
        }

        function ask(rawQuestion) {
            var question = rawQuestion.trim();
            if (!question || busy) {
                return;
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
                        addMessage('assistant', result.data.reply);
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
                    input.focus();
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
