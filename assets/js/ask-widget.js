/**
 * Ask Widget - AI-powered Q&A interface for Food Premi
 * Provides a clean, modern chat interface for customer questions
 */

class AskWidget {
    constructor(options = {}) {
        this.options = {
            apiEndpoint: '/api/ask',
            placeholder: 'Ask about our menu, hours, or dietary options...',
            maxMessages: 10,
            theme: 'light',
            position: 'bottom-right',
            ...options
        };

        this.isOpen = false;
        this.messages = [];
        this.isLoading = false;

        this.init();
    }

    init() {
        this.createWidgetHTML();
        this.attachEventListeners();
        this.loadChatHistory();
    }

    createWidgetHTML() {
        // Create widget container
        const widgetContainer = document.createElement('div');
        widgetContainer.className = `ask-widget ${this.options.theme} ${this.options.position}`;
        widgetContainer.innerHTML = `
            <!-- Chat Button -->
            <div class="ask-widget-button" id="askWidgetButton">
                <svg class="chat-icon" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M20 2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h4l4 4 4-4h4c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-2 12H6v-2h12v2zm0-3H6V9h12v2zm0-3H6V6h12v2z"/>
                </svg>
                <svg class="close-icon" viewBox="0 0 24 24" fill="currentColor" style="display: none;">
                    <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                </svg>
            </div>

            <!-- Chat Window -->
            <div class="ask-widget-window" id="askWidgetWindow" style="display: none;">
                <div class="ask-widget-header">
                    <h3>Ask Food Premi</h3>
                    <p>Get instant answers about our menu, hours, and services</p>
                </div>

                <div class="ask-widget-messages" id="askWidgetMessages">
                    <div class="message bot-message">
                        <div class="message-content">
                            👋 Hi! I'm here to help answer questions about Food Premi. Ask me about our healthy menu options, hours, dietary accommodations, or anything else!
                        </div>
                    </div>
                </div>

                <div class="ask-widget-input-container">
                    <div class="ask-widget-input-wrapper">
                        <input
                            type="text"
                            id="askWidgetInput"
                            placeholder="${this.options.placeholder}"
                            maxlength="500"
                        >
                        <button id="askWidgetSend" class="send-button">
                            <svg viewBox="0 0 24 24" fill="currentColor">
                                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                            </svg>
                        </button>
                    </div>
                    <div class="quick-questions">
                        <button class="quick-question" data-question="What healthy options do you have?">
                            🥗 Healthy Options
                        </button>
                        <button class="quick-question" data-question="What are your hours?">
                            🕒 Hours
                        </button>
                        <button class="quick-question" data-question="Do you have vegan menu items?">
                            🌱 Vegan Menu
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(widgetContainer);
        this.widget = widgetContainer;
    }

    attachEventListeners() {
        const button = document.getElementById('askWidgetButton');
        const input = document.getElementById('askWidgetInput');
        const sendButton = document.getElementById('askWidgetSend');
        const quickQuestions = document.querySelectorAll('.quick-question');

        // Toggle widget
        button.addEventListener('click', () => this.toggleWidget());

        // Send message on enter or button click
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        sendButton.addEventListener('click', () => this.sendMessage());

        // Quick questions
        quickQuestions.forEach(btn => {
            btn.addEventListener('click', () => {
                const question = btn.dataset.question;
                input.value = question;
                this.sendMessage();
            });
        });

        // Close widget when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.widget.contains(e.target) && this.isOpen) {
                // Don't close immediately, add a small delay
                setTimeout(() => {
                    if (!this.widget.matches(':hover')) {
                        this.closeWidget();
                    }
                }, 100);
            }
        });
    }

    toggleWidget() {
        if (this.isOpen) {
            this.closeWidget();
        } else {
            this.openWidget();
        }
    }

    openWidget() {
        this.isOpen = true;
        const window = document.getElementById('askWidgetWindow');
        const button = document.getElementById('askWidgetButton');

        window.style.display = 'block';
        button.querySelector('.chat-icon').style.display = 'none';
        button.querySelector('.close-icon').style.display = 'block';

        // Focus input
        setTimeout(() => {
            document.getElementById('askWidgetInput').focus();
        }, 100);

        // Scroll to bottom
        this.scrollToBottom();
    }

    closeWidget() {
        this.isOpen = false;
        const window = document.getElementById('askWidgetWindow');
        const button = document.getElementById('askWidgetButton');

        window.style.display = 'none';
        button.querySelector('.chat-icon').style.display = 'block';
        button.querySelector('.close-icon').style.display = 'none';
    }

    async sendMessage() {
        const input = document.getElementById('askWidgetInput');
        const message = input.value.trim();

        if (!message || this.isLoading) return;

        input.value = '';
        this.addMessage(message, 'user');
        this.setLoading(true);

        try {
            const response = await fetch(this.options.apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question: message })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                this.addMessage(data.answer, 'bot', {
                    sources: data.sources,
                    confidence: data.confidence_score
                });
            } else {
                throw new Error(data.error || 'Unknown error occurred');
            }

        } catch (error) {
            console.error('Error sending message:', error);
            this.addMessage(
                'Sorry, I\'m having trouble connecting right now. Please try again in a moment or contact us directly.',
                'bot',
                { isError: true }
            );
        } finally {
            this.setLoading(false);
        }
    }

    addMessage(content, type, metadata = {}) {
        const messagesContainer = document.getElementById('askWidgetMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;

        let messageHTML = `<div class="message-content">${this.formatMessage(content)}</div>`;

        // Add confidence indicator for bot messages
        if (type === 'bot' && metadata.confidence !== undefined) {
            const confidence = Math.round(metadata.confidence * 100);
            let confidenceClass = 'low';
            if (confidence >= 70) confidenceClass = 'high';
            else if (confidence >= 50) confidenceClass = 'medium';

            messageHTML += `<div class="confidence-indicator ${confidenceClass}">
                Confidence: ${confidence}%
            </div>`;
        }

        // Add sources if available
        if (metadata.sources && metadata.sources.length > 0) {
            messageHTML += `<div class="message-sources">
                <small>Sources: ${metadata.sources.length} reference(s)</small>
            </div>`;
        }

        messageDiv.innerHTML = messageHTML;
        messagesContainer.appendChild(messageDiv);

        // Store message
        this.messages.push({
            content,
            type,
            timestamp: new Date().toISOString(),
            metadata
        });

        // Limit message history
        if (this.messages.length > this.options.maxMessages) {
            this.messages = this.messages.slice(-this.options.maxMessages);
            // Remove old message elements
            const messageElements = messagesContainer.querySelectorAll('.message');
            if (messageElements.length > this.options.maxMessages) {
                messageElements[0].remove();
            }
        }

        this.scrollToBottom();
        this.saveChatHistory();
    }

    setLoading(loading) {
        this.isLoading = loading;
        const sendButton = document.getElementById('askWidgetSend');
        const input = document.getElementById('askWidgetInput');

        if (loading) {
            sendButton.disabled = true;
            input.disabled = true;
            this.addTypingIndicator();
        } else {
            sendButton.disabled = false;
            input.disabled = false;
            this.removeTypingIndicator();
        }
    }

    addTypingIndicator() {
        const messagesContainer = document.getElementById('askWidgetMessages');
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message bot-message typing-indicator';
        typingDiv.innerHTML = `
            <div class="message-content">
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        typingDiv.id = 'typingIndicator';
        messagesContainer.appendChild(typingDiv);
        this.scrollToBottom();
    }

    removeTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    formatMessage(content) {
        // Basic formatting for URLs, line breaks, etc.
        return content
            .replace(/\n/g, '<br>')
            .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" rel="noopener">$1</a>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>');
    }

    scrollToBottom() {
        const messagesContainer = document.getElementById('askWidgetMessages');
        setTimeout(() => {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }, 10);
    }

    saveChatHistory() {
        try {
            localStorage.setItem('askWidget_history', JSON.stringify(this.messages));
        } catch (e) {
            console.warn('Could not save chat history:', e);
        }
    }

    loadChatHistory() {
        try {
            const saved = localStorage.getItem('askWidget_history');
            if (saved) {
                this.messages = JSON.parse(saved);

                // Restore recent messages (limit to last few)
                const recentMessages = this.messages.slice(-5);
                const messagesContainer = document.getElementById('askWidgetMessages');

                recentMessages.forEach(msg => {
                    if (msg.type === 'user' || msg.type === 'bot') {
                        const messageDiv = document.createElement('div');
                        messageDiv.className = `message ${msg.type}-message`;
                        messageDiv.innerHTML = `<div class="message-content">${this.formatMessage(msg.content)}</div>`;
                        messagesContainer.appendChild(messageDiv);
                    }
                });
            }
        } catch (e) {
            console.warn('Could not load chat history:', e);
        }
    }

    // Public methods
    clearHistory() {
        this.messages = [];
        localStorage.removeItem('askWidget_history');
        const messagesContainer = document.getElementById('askWidgetMessages');
        // Keep only the welcome message
        const messages = messagesContainer.querySelectorAll('.message');
        for (let i = 1; i < messages.length; i++) {
            messages[i].remove();
        }
    }

    destroy() {
        if (this.widget) {
            this.widget.remove();
        }
    }
}

// Auto-initialize if page is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize if not already present
    if (!document.querySelector('.ask-widget')) {
        window.askWidget = new AskWidget();
    }
});

// Export for manual initialization
window.AskWidget = AskWidget;