import pyaudio
import wave
import numpy as np
import matplotlib.pyplot as plt
import threading
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QComboBox
import sys
import os

class VoiceRecorder:
    def __init__(self, frames_per_buffer=3200, format=pyaudio.paInt16, channels=1, rate=16000):
        self.frames_per_buffer = frames_per_buffer
        self.format = format
        self.channels = channels
        self.rate = rate
        self.pa = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self.currently_recording = False
        self.filename = ""
        self.save_directory = os.path.join(os.path.expanduser("~"), "OneDrive", "Documents", "School stuff", "solo_code")
        os.makedirs(self.save_directory, exist_ok=True)

    def toggle_recording(self, filename, button, disable_buttons, enable_buttons, enable_plot):
        if self.currently_recording:
            self.stop_recording(button, enable_buttons, enable_plot)
        else:
            self.start_recording(filename, button, disable_buttons)
    
    def start_recording(self, filename, button, disable_buttons):
        self.filename = filename
        self.frames = []
        self.currently_recording = True
        button.setText("Stop Recording")
        
        for btn in disable_buttons:
            btn.setEnabled(False)
        
        def record():
            self.stream = self.pa.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.frames_per_buffer
            )
            print(f"Start recording: {self.filename}")
            
            while self.currently_recording:
                data = self.stream.read(self.frames_per_buffer, exception_on_overflow=False)
                self.frames.append(data)
            
            self.save_recording()
        
        threading.Thread(target=record, daemon=True).start()
    
    def stop_recording(self, button, enable_buttons, enable_plot):
        self.currently_recording = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        button.setText("Start Recording")
        print("Recording stopped")
        self.save_recording()
        
        for btn in enable_buttons:
            btn.setEnabled(True)
        
        if os.path.exists("recording_1.wav") and os.path.exists("recording_2.wav"):
            enable_plot.setEnabled(True)
        
    def save_recording(self):
        if not self.filename:
            return
        obj = wave.open(self.filename, "wb")
        obj.setnchannels(self.channels)
        obj.setsampwidth(self.pa.get_sample_size(self.format))
        obj.setframerate(self.rate)
        obj.writeframes(b"".join(self.frames))
        obj.close()
        print(f"Recording saved as {self.filename}")
        
    def plot_recordings(self, files, mode, save_as_image=False):
        fig, ax = plt.subplots(2 if mode == "Both" else 1, 1, figsize=(12, 6))
        if mode != "Both":
            ax = [ax]

        colors = ['b', 'g', 'r', 'c', 'm', 'y']
        alpha_values = [0.7, 0.5, 0.3]
        signals = []
        sample_freq = None

        for i, file in enumerate(files):
            try:
                if not os.path.exists(file):
                    print(f"Error: File {file} not found. Skipping.")
                    continue

                with wave.open(file, "rb") as f:
                    sample_freq = f.getframerate()
                    frames = f.getnframes()
                    signal_wave = f.readframes(-1)
                    audio_array = np.frombuffer(signal_wave, dtype=np.int16)
                    times = np.linspace(0, frames / sample_freq, num=frames)

                    color = colors[i % len(colors)]
                    alpha = alpha_values[min(i, len(alpha_values) - 1)]

                    if mode in ["Oscilloscope", "Both"]:
                        ax[0].plot(times, audio_array, color=color, linewidth=1, alpha=alpha, label=file)
                    if mode in ["Spectrum Analyzer", "Both"]:
                        freqs = np.fft.fftfreq(len(audio_array), 1/sample_freq)
                        fft_values = np.abs(np.fft.fft(audio_array))
                        ax[-1].semilogx(freqs[:len(freqs)//2], fft_values[:len(freqs)//2], color=color, linewidth=1, alpha=alpha, label=file)

                    signals.append(audio_array)

            except Exception as e:
                print(f"Error processing {file}: {e}")

        if len(signals) > 1:
            min_length = min(len(sig) for sig in signals)
            composite_signal = np.sum([sig[:min_length] for sig in signals], axis=0) / len(signals)
            times = np.linspace(0, min_length / sample_freq, num=min_length)

            if mode in ["Oscilloscope", "Both"]:
                ax[0].plot(times, composite_signal, color='r', linestyle="dashed", linewidth=1, alpha=0.8, label="Composite Signal")
            
            if mode in ["Spectrum Analyzer", "Both"]:
                composite_freqs = np.fft.fftfreq(len(composite_signal), 1/sample_freq)
                composite_fft_values = np.abs(np.fft.fft(composite_signal))
                ax[-1].semilogx(
                    composite_freqs[:len(composite_freqs)//2], 
                    composite_fft_values[:len(composite_fft_values)//2], 
                    color="red", linestyle="dashed", linewidth=1, alpha=0.8, label="Composite Signal"
                )

        for axis in ax:
            axis.set_xlabel("Frequency (Hz)" if mode in ["Spectrum Analyzer", "Both"] else "Time (s)")
            axis.set_ylabel("Magnitude" if mode in ["Spectrum Analyzer", "Both"] else "Amplitude")
            axis.grid(True, which='both', linestyle='--', linewidth=0.5)
            axis.legend()

        if save_as_image:
            save_path = os.path.join(self.save_directory, "recorded_plot.jpeg")
            plt.savefig(save_path)
            print(f"Plot saved as {save_path}")

        plt.show()

class RecorderApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        self.recorder = VoiceRecorder()
        layout = QVBoxLayout()
        
        self.label = QLabel("Voice Recorder")
        layout.addWidget(self.label)
        
        self.record1_btn = QPushButton("Start Recording")
        self.record2_btn = QPushButton("Start Recording")
        self.plot_btn = QPushButton("Plot Audio")
        self.download_btn = QPushButton("Download Plot")
        
        self.plot_btn.setEnabled(False)
        
        self.record1_btn.clicked.connect(lambda: self.recorder.toggle_recording("recording_1.wav", self.record1_btn, [self.record2_btn, self.plot_btn], [self.record2_btn], self.plot_btn))
        self.record2_btn.clicked.connect(lambda: self.recorder.toggle_recording("recording_2.wav", self.record2_btn, [self.record1_btn, self.plot_btn], [self.record1_btn], self.plot_btn))
        self.plot_btn.clicked.connect(self.plot_audio)
        self.download_btn.clicked.connect(self.download_plot)
        
        layout.addWidget(self.record1_btn)
        layout.addWidget(self.record2_btn)
        layout.addWidget(self.plot_btn)
        layout.addWidget(self.download_btn)
        
        self.plot_mode = QComboBox()
        self.plot_mode.addItems(["Oscilloscope", "Spectrum Analyzer", "Both"])
        layout.addWidget(self.plot_mode)
        
        self.setLayout(layout)
        self.setWindowTitle("Voice Recorder with PyQt")
    
    def plot_audio(self):
        mode = self.plot_mode.currentText()
        files = ["recording_1.wav", "recording_2.wav"]
        self.recorder.plot_recordings(files, mode)
    
    def download_plot(self):
        mode = self.plot_mode.currentText()
        files = ["recording_1.wav", "recording_2.wav"]
        self.recorder.plot_recordings(files, mode, save_as_image=True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RecorderApp()
    window.show()
    sys.exit(app.exec_())
