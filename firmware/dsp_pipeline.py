import numpy as np
from scipy import signal


class BioNeuralDSP:
    def __init__(self, sample_rate=2000, window_size_ms=150, stride_ms=30):
        self.fs = sample_rate
        self.win_len = int((window_size_ms / 1000.0) * self.fs)
        self.stride = int((stride_ms / 1000.0) * self.fs)

        # Design 4th-Order Butterworth Bandpass (20 - 450 Hz)
        self.b_bp, self.a_bp = signal.butter(
            N=4,
            Wn=[20.0, 450.0],
            btype='bandpass',
            fs=self.fs
        )

        # Design 50 Hz IIR Notch Filter
        self.b_notch, self.a_notch = signal.iirnotch(
            w0=50.0,
            Q=35.0,
            fs=self.fs
        )

    def filter_signal(self, raw_emg: np.ndarray) -> np.ndarray:
        """Applies cascaded bandpass and powerline notch rejection."""
        bp_filtered = signal.lfilter(self.b_bp, self.a_bp, raw_emg, axis=-1)
        conditioned = signal.lfilter(
            self.b_notch, self.a_notch, bp_filtered, axis=-1)
        return conditioned

    def extract_features(self, window: np.ndarray, deadband: float = 1e-5) -> np.ndarray:
        """
        Computes MAV, RMS, WL, and ZC across a window of shape (channels, samples).
        """
        mav = np.mean(np.abs(window), axis=-1)
        rms = np.sqrt(np.mean(np.square(window), axis=-1))
        wl = np.sum(np.abs(np.diff(window, axis=-1)), axis=-1)

        # Zero Crossings with noise deadband threshold
        sign_changes = (window[:, :-1] * window[:, 1:]) < 0
        diff_threshold = np.abs(np.diff(window, axis=-1)) >= deadband
        zc = np.sum(sign_changes & diff_threshold, axis=-1)

        return np.stack([mav, rms, wl, zc], axis=-1)


# Quick verification testbench
if __name__ == "__main__":
    dsp = BioNeuralDSP()
    duration_s = 1.0
    t = np.linspace(0, duration_s, int(dsp.fs * duration_s), endpoint=False)

    # Simulate 8-channel raw EMG with mixed frequencies + 50 Hz mains noise
    synthetic_emg = (
        np.sin(2 * np.pi * 75 * t) * 0.5 +
        np.sin(2 * np.pi * 50 * t) * 1.2 +  # Powerline interference
        np.random.normal(0, 0.2, (8, len(t)))
    )

    filtered = dsp.filter_signal(synthetic_emg)
    test_window = filtered[:, :dsp.win_len]
    features = dsp.extract_features(test_window)

    print(f"Engine Initialized: Filtered shape {filtered.shape}")
    print(f"Extracted Feature Tensor: {features.shape} (Channels x Features)")
