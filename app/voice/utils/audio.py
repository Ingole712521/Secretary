"""Voice platform utility functions."""

from __future__ import annotations

import struct


def pcm_duration_seconds(
    audio: bytes,
    *,
    sample_rate: int,
    sample_width: int = 2,
) -> float:
    """Return duration of PCM audio in seconds.

    Args:
        audio: PCM audio bytes.
        sample_rate: Sample rate in Hz.
        sample_width: Bytes per sample.

    Returns:
        Duration in seconds.
    """
    if sample_rate <= 0 or sample_width <= 0:
        return 0.0
    return len(audio) / (sample_rate * sample_width)


def normalize_pcm_volume(audio: bytes, *, factor: float) -> bytes:
    """Adjust PCM audio volume by a multiplier.

    Args:
        audio: 16-bit PCM audio bytes.
        factor: Volume multiplier.

    Returns:
        Scaled PCM audio bytes.
    """
    if factor == 1.0 or not audio:
        return audio
    clamped = min(max(factor, 0.0), 4.0)
    sample_count = len(audio) // 2
    samples = struct.unpack(f"<{sample_count}h", audio)
    scaled = [int(max(-32768, min(32767, sample * clamped))) for sample in samples]
    return struct.pack(f"<{sample_count}h", *scaled)


def generate_silence_pcm(
    duration_ms: int,
    *,
    sample_rate: int,
    sample_width: int = 2,
) -> bytes:
    """Generate silent PCM audio bytes.

    Args:
        duration_ms: Silence duration in milliseconds.
        sample_rate: Sample rate in Hz.
        sample_width: Bytes per sample.

    Returns:
        Silent PCM bytes.
    """
    frame_count = int(sample_rate * duration_ms / 1000)
    return b"\x00" * frame_count * sample_width


def wav_header(
    data_size: int,
    *,
    sample_rate: int,
    channels: int = 1,
    sample_width: int = 2,
) -> bytes:
    """Build a WAV file header for PCM data.

    Args:
        data_size: Size of PCM data in bytes.
        sample_rate: Sample rate in Hz.
        channels: Number of channels.
        sample_width: Bytes per sample.

    Returns:
        44-byte WAV header.
    """
    byte_rate = sample_rate * channels * sample_width
    block_align = channels * sample_width
    return struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        36 + data_size,
        b"WAVE",
        b"fmt ",
        16,
        1,
        channels,
        sample_rate,
        byte_rate,
        block_align,
        sample_width * 8,
        b"data",
        data_size,
    )


def pcm_to_wav(pcm: bytes, *, sample_rate: int, channels: int = 1) -> bytes:
    """Wrap raw PCM bytes in a WAV container.

    Args:
        pcm: PCM audio bytes.
        sample_rate: Sample rate in Hz.
        channels: Number of channels.

    Returns:
        Complete WAV file bytes.
    """
    return wav_header(len(pcm), sample_rate=sample_rate, channels=channels) + pcm
