/**
 * AudioRecorder Utility
 * Captures user microphone input, resamples to 16kHz, converts Float32 to Int16 PCM,
 * and streams it in real-time.
 */

export class AudioRecorder {
  private audioContext: AudioContext | null = null;
  private mediaStream: MediaStream | null = null;
  private processorNode: ScriptProcessorNode | null = null;
  private sourceNode: MediaStreamAudioSourceNode | null = null;
  private onChunk: (base64Chunk: string) => void;
  private onSilence: (() => void) | null = null;
  private hasSpoken = false;
  private silentChunks = 0;

  constructor(onChunk: (base64Chunk: string) => void, onSilence?: () => void) {
    this.onChunk = onChunk;
    this.onSilence = onSilence || null;
  }

  public async start(): Promise<void> {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      throw new Error(
        "Microphone is blocked. You must use HTTPS (e.g. ngrok tunnel) or configure Chrome flags for secure context access."
      );
    }

    // 1. Get browser microphone media stream
    this.mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true,
      },
    });

    // 2. Initialize AudioContext at 16kHz
    const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
    this.audioContext = new AudioContextClass({ sampleRate: 16000 });

    // 3. Setup source and ScriptProcessor node (buffer size 4096)
    this.sourceNode = this.audioContext.createMediaStreamSource(this.mediaStream);
    this.processorNode = this.audioContext.createScriptProcessor(4096, 1, 1);

    this.hasSpoken = false;
    this.silentChunks = 0;

    this.processorNode.onaudioprocess = (e) => {
      const inputBuffer = e.inputBuffer.getChannelData(0); // Float32Array
      
      // Calculate RMS energy to detect speech vs silence
      let sum = 0;
      for (let i = 0; i < inputBuffer.length; i++) {
        sum += inputBuffer[i] * inputBuffer[i];
      }
      const rms = Math.sqrt(sum / inputBuffer.length);

      if (rms > 0.015) {
        this.hasSpoken = true;
        this.silentChunks = 0;
      } else if (this.hasSpoken) {
        this.silentChunks++;
        // 5 chunks at 256ms = ~1.28 seconds of silence
        if (this.silentChunks >= 5) {
          console.log("Local silence detected. Triggering auto-stop.");
          if (this.onSilence) {
            this.onSilence();
          }
          return;
        }
      }

      // Convert Float32 to Int16 PCM
      const pcmBuffer = this.floatTo16BitPCM(inputBuffer);
      
      // Convert PCM ArrayBuffer to Base64
      const base64Chunk = this.arrayBufferToBase64(pcmBuffer);
      
      this.onChunk(base64Chunk);
    };

    // 4. Connect nodes
    this.sourceNode.connect(this.processorNode);
    this.processorNode.connect(this.audioContext.destination);
  }

  public stop(): void {
    // 1. Disconnect and stop processing nodes
    if (this.processorNode) {
      this.processorNode.disconnect();
      this.processorNode.onaudioprocess = null;
      this.processorNode = null;
    }

    if (this.sourceNode) {
      this.sourceNode.disconnect();
      this.sourceNode = null;
    }

    // 2. Stop microphone tracks
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((track) => track.stop());
      this.mediaStream = null;
    }

    // 3. Close AudioContext
    if (this.audioContext && this.audioContext.state !== 'closed') {
      this.audioContext.close();
      this.audioContext = null;
    }
  }

  private floatTo16BitPCM(input: Float32Array): ArrayBuffer {
    const buffer = new ArrayBuffer(input.length * 2);
    const view = new DataView(buffer);
    for (let i = 0; i < input.length; i++) {
      let s = Math.max(-1, Math.min(1, input[i]));
      // Scale to 16-bit signed integer [-32768, 32767]
      let val = s < 0 ? s * 0x8000 : s * 0x7FFF;
      view.setInt16(i * 2, val, true); // Little-endian
    }
    return buffer;
  }

  private arrayBufferToBase64(buffer: ArrayBuffer): string {
    let binary = '';
    const bytes = new Uint8Array(buffer);
    const len = bytes.byteLength;
    for (let i = 0; i < len; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return window.btoa(binary);
  }
}
