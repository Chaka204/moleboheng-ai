class MolebohengAI {
    constructor() {
        this.conversation = document.getElementById('conversation');
        this.micBtn = document.getElementById('micBtn');
        this.status = document.getElementById('status');
        this.suggestions = document.getElementById('suggestions');
        
        this.isListening = false;
        this.recognition = null;
        
        this.init();
    }
    
    init() {
        this.setupSpeechRecognition();
        this.bindEvents();
        this.updateStatus('Ready to speak Sesotho');
        this.showWelcome();
        this.loadSuggestions();
    }
    
    setupSpeechRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (!SpeechRecognition) {
            this.showError('Browser does not support speech recognition');
            this.micBtn.disabled = true;
            return;
        }
        
        this.recognition = new SpeechRecognition();
        this.recognition.lang = 'st-ZA';
        this.recognition.continuous = false;
        this.recognition.interimResults = false;
        
        this.recognition.onstart = () => {
            this.isListening = true;
            this.updateButtonState();
            this.updateStatus('Listening... Speak now');
        };
        
        this.recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            this.handleUserInput(transcript);
        };
        
        this.recognition.onerror = (event) => {
            this.handleRecognitionError(event.error);
        };
        
        this.recognition.onend = () => {
            this.isListening = false;
            this.updateButtonState();
            if (!this.isProcessing) {
                this.updateStatus('Ready to speak');
            }
        };
    }
    
    bindEvents() {
        this.micBtn.addEventListener('click', () => {
            if (this.isListening) {
                this.stopListening();
            } else {
                this.startListening();
            }
        });
        
        // Keyboard shortcut: Space key to toggle listening
        document.addEventListener('keydown', (e) => {
            if (e.code === 'Space' && e.ctrlKey) {
                e.preventDefault();
                if (this.isListening) {
                    this.stopListening();
                } else {
                    this.startListening();
                }
            }
        });
        
        // Click on suggestions
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('suggestion-item')) {
                this.handleUserInput(e.target.textContent);
            }
        });
    }
    
    startListening() {
        if (this.recognition && !this.isListening) {
            try {
                this.recognition.start();
            } catch (error) {
                this.showError('Could not start microphone');
            }
        }
    }
    
    stopListening() {
        if (this.recognition && this.isListening) {
            this.recognition.stop();
        }
    }
    
    async handleUserInput(text) {
        this.addMessage('user', text);
        this.isProcessing = true;
        this.updateStatus('Processing...');
        this.updateButtonState();
        
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: text })
            });
            
            const data = await response.json();
            
            this.addMessage('bot', data.response, data.metadata);
            
            // Speak the response
            this.speakResponse(data.response);
            
        } catch (error) {
            console.error('Error:', error);
            this.addMessage('bot', 'Ho na le bothata ka server. Ka kopo, leka hape.');
        } finally {
            this.isProcessing = false;
            this.updateStatus('Ready to speak');
            this.updateButtonState();
        }
    }
    
    addMessage(role, text, metadata = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}-message`;
        
        const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        let metadataHTML = '';
        if (metadata) {
            metadataHTML = `<div class="message-metadata">Match: ${metadata.match_type} | Intent: ${metadata.intent}</div>`;
        }
        
        messageDiv.innerHTML = `
            <div class="message-header">
                <strong>${role === 'user' ? 'You' : 'Moleboheng'}</strong>
                <span>${time}</span>
            </div>
            <div>${text}</div>
            ${metadataHTML}
        `;
        
        this.conversation.appendChild(messageDiv);
        this.conversation.scrollTop = this.conversation.scrollHeight;
    }
    
    speakResponse(text) {
        if (!window.speechSynthesis) return;
        
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = 'st-ZA';
        utterance.rate = 0.9;
        
        // Try to find Sesotho voice
        const voices = speechSynthesis.getVoices();
        const sesothoVoice = voices.find(voice => voice.lang === 'st-ZA' || voice.lang.includes('st'));
        
        if (sesothoVoice) {
            utterance.voice = sesothoVoice;
        }
        
        speechSynthesis.speak(utterance);
    }
    
    updateStatus(text) {
        if (this.status) {
            this.status.textContent = `Status: ${text}`;
        }
    }
    
    updateButtonState() {
        if (this.isListening) {
            this.micBtn.innerHTML = '⏹️ Stop Listening';
            this.micBtn.classList.add('listening');
        } else if (this.isProcessing) {
            this.micBtn.innerHTML = '⏳ Processing...';
            this.micBtn.classList.remove('listening');
            this.micBtn.disabled = true;
        } else {
            this.micBtn.innerHTML = '🎤 Speak Sesotho';
            this.micBtn.classList.remove('listening');
            this.micBtn.disabled = false;
        }
    }
    
    showWelcome() {
        setTimeout(() => {
            this.addMessage('bot', 'Lumela! Ke Moleboheng. U ka bua le \'na ka Sesotho.');
            this.speakResponse('Lumela! Ke Moleboheng. U ka bua le nna ka Sesotho.');
        }, 1000);
    }
    
    loadSuggestions() {
        const suggestions = ['Lumela', 'Kea leboha', 'Lebitso la hau ke mang?', 'Sala hantle'];
        
        if (this.suggestions) {
            this.suggestions.innerHTML = `
                <p><strong>Try saying:</strong></p>
                ${suggestions.map(text => 
                    `<span class="suggestion-item">${text}</span>`
                ).join(' ')}
            `;
        }
    }
    
    handleRecognitionError(error) {
        let message = 'Microphone error. Please try again.';
        
        switch(error) {
            case 'no-speech':
                message = 'No speech detected.';
                break;
            case 'audio-capture':
                message = 'No microphone found.';
                break;
            case 'not-allowed':
                message = 'Microphone permission denied.';
                break;
        }
        
        this.updateStatus(message);
        this.addMessage('bot', 'Ha ke a utloa hantle. Ka kopo, leka hape.');
        
        setTimeout(() => {
            this.updateStatus('Ready to speak');
        }, 3000);
    }
    
    showError(message) {
        this.addMessage('bot', `Error: ${message}`);
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.moleboheng = new MolebohengAI();
});
