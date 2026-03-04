// Voice recognition functionality
class SesothoVoiceAI {
    constructor(backendUrl) {
        this.backendUrl = backendUrl;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
    }

    async initializeMicrophone() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.mediaRecorder = new MediaRecorder(stream);
            
            this.mediaRecorder.ondataavailable = event => {
                this.audioChunks.push(event.data);
            };
            
            this.mediaRecorder.onstop = this.processRecording.bind(this);
            
            return true;
        } catch (error) {
            console.error('Microphone error:', error);
            alert('Cannot access microphone. Please check permissions.');
            return false;
        }
    }

    startRecording() {
        if (!this.mediaRecorder) {
            alert('Please initialize microphone first');
            return;
        }
        
        this.audioChunks = [];
        this.mediaRecorder.start();
        this.isRecording = true;
        document.getElementById('recordButton').textContent = '⏹️ Stop Recording';
        document.getElementById('recordButton').classList.add('recording');
    }

    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
            document.getElementById('recordButton').textContent = '🎤 Start Recording';
            document.getElementById('recordButton').classList.remove('recording');
        }
    }

    async processRecording() {
        try {
            document.getElementById('voiceStatus').textContent = 'Processing...';
            
            const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.webm');
            
            const response = await fetch(`${this.backendUrl}/transcribe`, {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            this.displayResults(data);
            
        } catch (error) {
            console.error('Processing error:', error);
            document.getElementById('voiceStatus').textContent = 'Error: ' + error.message;
        }
    }

    displayResults(data) {
        const resultsDiv = document.getElementById('voiceResults');
        resultsDiv.innerHTML = `
            <div class="voice-result">
                <strong>You said:</strong> "${data.transcribed_text}"
            </div>
            <div class="voice-result">
                <strong>AI responds:</strong> "${data.ai_response}"
            </div>
        `;
        
        document.getElementById('voiceStatus').textContent = 'Ready';
    }
}
