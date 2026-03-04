class MolebohengAI {
    constructor() {
        this.conversation = document.getElementById('conversation');
        this.micBtn = document.getElementById('micBtn');
        this.status = document.getElementById('status');
        this.suggestions = document.getElementById('suggestions');
        
        this.isListening = false;
        this.recognition = null;
        this.speechSupported = false;
        
        this.init();
    }
    
    init() {
        this.checkSpeechSupport();
        this.createTextInput(); // Add text input here
        this.bindEvents();
        this.updateStatus('Ready to speak Sesotho');
        this.showWelcome();
        this.loadSuggestions();
    }
    
    createTextInput() {
        // Create text input container
        const inputContainer = document.createElement('div');
        inputContainer.className = 'text-input-container';
        inputContainer.innerHTML = `
            <p><strong>Or type Sesotho:</strong></p>
            <input type="text" class="text-input" id="textInput" placeholder="Type Sesotho phrase here and press Enter...">
        `;
        
        // Insert after the controls div
        const controls = document.querySelector('.controls');
        if (controls) {
            controls.parentNode.insertBefore(inputContainer, controls.nextSibling);
        }
    }
    
    checkSpeechSupport() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (!SpeechRecognition) {
            this.showError('Your browser does not support speech recognition. Try Chrome or Firefox.');
            this.micBtn.disabled = true;
            this.speechSupported = false;
            return;
        }
        
        this.recognition = new SpeechRecognition();
        this.recognition.lang = 'st-ZA';
        this.recognition.continuous = false;
        this.recognition.interimResults = false;
        this.recognition.maxAlternatives = 1;
        
        // Set up event handlers
        this.setupRecognitionEvents();
        this.speechSupported = true;
    }
    
    setupRecognitionEvents() {
        this.recognition.onstart = () => {
            this.isListening = true;
            this.updateButtonState();
            this.updateStatus('🎤 Listening... Speak now in Sesotho');
        };
        
        this.recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            console.log('Speech recognized:', transcript);
            this.handleUserInput(transcript);
        };
        
        this.recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
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
        // Microphone button
        this.micBtn.addEventListener('click', () => {
            if (this.isListening) {
                this.stopListening();
            } else {
                this.startListening();
            }
        });
        
        // Text input Enter key
        const textInput = document.getElementById('textInput');
        if (textInput) {
            textInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && textInput.value.trim()) {
                    this.handleUserInput(textInput.value.trim());
                    textInput.value = ''; // Clear input
                }
            });
        }
        
        // Keyboard shortcut: Ctrl+Space for microphone
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
        if (!this.speechSupported) {
            this.showError('Speech recognition not supported in this browser');
            return;
        }
        
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            // Request microphone permission first
            navigator.mediaDevices.getUserMedia({ audio: true })
                .then(() => {
                    console.log('Microphone access granted');
                    this.recognition.start();
                })
                .catch((err) => {
                    console.error('Microphone access denied:', err);
                    this.handleRecognitionError('not-allowed');
                });
        } else {
            // Fallback for browsers without getUserMedia
            this.recognition.start();
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
        this.updateStatus('Processing your Sesotho...');
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
            console.error('API Error:', error);
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
        if (!window.speechSynthesis) {
            console.log('Text-to-speech not supported');
            return;
        }
        
        // Cancel any ongoing speech
        speechSynthesis.cancel();
        
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = 'st-ZA';
        utterance.rate = 0.9;
        utterance.pitch = 1;
        utterance.volume = 1;
        
        // Wait for voices to load
        const speak = () => {
            const voices = speechSynthesis.getVoices();
            
            // Try to find Sesotho/SA voice
            const sesothoVoice = voices.find(voice => 
                voice.lang === 'st-ZA' || 
                voice.lang === 'af-ZA' || 
                voice.lang.includes('Africa') ||
                voice.name.includes('South Africa')
            );
            
            if (sesothoVoice) {
                utterance.voice = sesothoVoice;
            }
            
            speechSynthesis.speak(utterance);
        };
        
        if (speechSynthesis.getVoices().length === 0) {
            speechSynthesis.onvoiceschanged = speak;
        } else {
            speak();
        }
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
            // Don't auto-speak on mobile
            if (!this.isMobileDevice()) {
                this.speakResponse('Lumela! Ke Moleboheng. U ka bua le nna ka Sesotho.');
            }
        }, 1000);
    }
    
    isMobileDevice() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    }
    
    loadSuggestions() {
        const suggestions = ['Lumela', 'Kea leboha', 'Lebitso la hau ke mang?', 'Sala hantle', 'O phela joang?'];
        
        if (this.suggestions) {
            this.suggestions.innerHTML = `
                <p><strong>Try saying or clicking:</strong></p>
                ${suggestions.map(text => 
                    `<span class="suggestion-item">${text}</span>`
                ).join(' ')}
            `;
        }
    }
    
    handleRecognitionError(error) {
        let message = 'Ha ke a utloa hantle. Ka kopo, leka hape.';
        let statusMsg = 'Microphone error';
        
        switch(error) {
            case 'no-speech':
                message = 'Ha ho lentsoe le utloahalang. Ka kopo, buisa hape.';
                statusMsg = 'No speech detected';
                break;
            case 'audio-capture':
                message = 'Ha ho microphone e fumanehang.';
                statusMsg = 'No microphone found';
                break;
            case 'not-allowed':
            case 'permission-denied':
                message = 'Tumello ea microphone ha e\'a fuoa. Ka kopo, fana ka tumello.';
                statusMsg = 'Microphone permission denied';
                break;
            case 'network':
                message = 'Bothata ka marang-rang. Ka kopo, netefatsa hore u ikopanye le inthanete.';
                statusMsg = 'Network error';
                break;
            case 'language-not-supported':
                message = 'Sesotho ha se tšehetsoe ke sebatli. Ka kopo, sebedisa Chrome.';
                statusMsg = 'Language not supported';
                break;
        }
        
        this.updateStatus(statusMsg);
        this.addMessage('bot', message);
        
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
    // Add browser compatibility warning
    const isChrome = !!window.chrome && (!!window.chrome.webstore || !!window.chrome.runtime);
    const isFirefox = typeof InstallTrigger !== 'undefined';
    
    if (!isChrome && !isFirefox) {
        const warning = document.createElement('div');
        warning.style.cssText = `
            background: #FFF3CD;
            border: 1px solid #FFEAA7;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
            text-align: center;
            color: #856404;
        `;
        warning.innerHTML = '💡 <strong>Tip:</strong> For best speech recognition, use Chrome or Firefox browser.';
        document.querySelector('.container').insertBefore(warning, document.querySelector('.browser-note').nextSibling);
    }
    
    window.moleboheng = new MolebohengAI();
});
