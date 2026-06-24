from __future__ import annotations

import gc
import os
from pathlib import Path
from typing import Any

import librosa
import numpy as np


SAMPLE_RATE = int(os.getenv("DJ_AGENT_SAMPLE_RATE", "22050"))
HOP_LENGTH = 1024
MAX_ANALYSIS_SECONDS = int(os.getenv("DJ_AGENT_MAX_ANALYSIS_SECONDS", "720"))
CURVE_BUCKETS = 64


def safe_float(value: float, digits: int = 3) -> float:
    if np.isnan(value) or np.isinf(value):
        return 0.0
    return round(float(value), digits)


def clip01(value: float) -> float:
    return safe_float(float(np.clip(value, 0.0, 1.0)))


def nearest(values: np.ndarray, target: float) -> float:
    if not values.size:
        return safe_float(max(0.0, target))
    return safe_float(values[np.argmin(np.abs(values - target))])


def buckets(values: np.ndarray, count: int = CURVE_BUCKETS) -> list[float]:
    if not values.size:
        return []
    normalized = values / max(float(np.max(np.abs(values))), 1e-9)
    return [safe_float(float(np.mean(part))) for part in np.array_split(normalized, min(count, len(normalized)))]


def first_rise(times: np.ndarray, signal: np.ndarray, beats: np.ndarray, duration: float, start: float, end: float) -> tuple[float, float]:
    if len(signal) < 8:
        return nearest(beats, duration * start), 0.35
    smooth = np.convolve(signal, np.ones(8, dtype=np.float32) / 8, mode="same")
    delta = np.diff(smooth, prepend=smooth[0])
    left, right = int(len(delta) * start), max(int(len(delta) * end), int(len(delta) * start) + 1)
    index = left + int(np.argmax(delta[left:right]))
    confidence = clip01(float(delta[index]) * 4 + float(smooth[index]) * 0.35)
    return nearest(beats, float(times[min(index, len(times) - 1)])), confidence


def quiet_region(times: np.ndarray, energy: np.ndarray, novelty: np.ndarray, duration: float, start: float, end: float) -> tuple[float, float]:
    if len(energy) < 8:
        return duration * start, 0.3
    left, right = int(len(energy) * start), max(int(len(energy) * end), int(len(energy) * start) + 1)
    window = max(4, int(len(energy) * 0.03))
    candidates: list[tuple[float, int]] = []
    for index in range(left, max(left + 1, right - window)):
        novelty_slice = novelty[index:min(len(novelty), index + window)] if len(novelty) else np.array([0])
        score = float(np.var(energy[index:index + window])) + float(np.mean(novelty_slice)) * 0.2
        candidates.append((score, index))
    score, index = min(candidates, default=(0.5, left))
    return float(times[min(index, len(times) - 1)]), clip01(0.85 - score * 3)


def loop_region(beats: np.ndarray, energy: np.ndarray, duration: float) -> dict[str, Any]:
    if len(beats) < 33:
        start = max(0.0, duration * 0.1)
        return {"start": safe_float(start), "end": safe_float(min(duration, start + 16)), "bars": 8, "reason": "Fallback loop; limited beat data.", "confidence": 0.25}
    best = (float("inf"), float(beats[0]), 8)
    for bars in (8, 16, 32):
        beat_count = bars * 4
        for index in range(0, max(0, len(beats) - beat_count), 4):
            start_t, end_t = float(beats[index]), float(beats[index + beat_count - 1])
            if start_t < 8 or end_t > duration * 0.8:
                continue
            start_frame = int(index / len(beats) * max(1, len(energy) - 1))
            end_frame = int((index + beat_count) / len(beats) * max(1, len(energy) - 1))
            score = float(np.var(energy[start_frame:max(start_frame + 1, end_frame)])) + float(np.var(np.diff(beats[index:index + beat_count])))
            if score < best[0]:
                best = (score, start_t, bars)
    interval = float(np.median(np.diff(beats)))
    return {
        "start": safe_float(best[1]),
        "end": safe_float(best[1] + interval * best[2] * 4),
        "bars": best[2],
        "reason": "Stable energy and consistent beat spacing region.",
        "confidence": clip01(0.9 - best[0] * 4),
    }


def analyze_audio_file(path: Path) -> dict[str, Any]:
    y: np.ndarray | None = None
    warnings: list[str] = []
    try:
        y, sr = librosa.load(path, sr=SAMPLE_RATE, mono=True, duration=MAX_ANALYSIS_SECONDS)
        y = y.astype(np.float32, copy=False)
        if not y.size:
            raise ValueError("Audio file contains no decodable audio.")
        duration = float(librosa.get_duration(y=y, sr=sr))
        if duration < 5:
            raise ValueError("Track is too short for DJ structure analysis.")
        if duration >= MAX_ANALYSIS_SECONDS - 0.5:
            warnings.append(f"Only the first {MAX_ANALYSIS_SECONDS // 60} minutes were analyzed.")

        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, hop_length=HOP_LENGTH)
        bpm = float(np.ravel(tempo)[0]) if np.size(tempo) else 0.0
        beats = librosa.frames_to_time(beat_frames, sr=sr, hop_length=HOP_LENGTH).astype(np.float32, copy=False)
        rms = librosa.feature.rms(y=y, hop_length=HOP_LENGTH)[0].astype(np.float32, copy=False)
        energy = rms / max(float(np.max(rms)), 1e-9)
        onset = librosa.onset.onset_strength(y=y, sr=sr, hop_length=HOP_LENGTH).astype(np.float32, copy=False)
        onset = onset / max(float(np.max(onset)), 1e-9)
        times = librosa.frames_to_time(np.arange(len(energy)), sr=sr, hop_length=HOP_LENGTH).astype(np.float32, copy=False)
        novelty = np.pad(onset, (0, max(0, len(energy) - len(onset))))[:len(energy)]
        combined = energy + novelty * 0.55

        intro = nearest(beats, 0.0)
        intro_end, intro_conf = first_rise(times, combined, beats, duration, 0.04, 0.28)
        mix_in = nearest(beats, max(intro_end, duration * 0.1))
        drop, drop_conf = first_rise(times, combined, beats, duration, 0.15, 0.62)
        mix_out, outro_conf = quiet_region(times, energy, novelty, duration, 0.65, 0.93)
        loop = loop_region(beats, energy, duration)
        tempo_conf = clip01(min(1.0, len(beats) / max(1.0, duration / 60 * max(bpm, 60))))
        confidence_scores = {"tempo": tempo_conf, "intro": intro_conf, "drop": drop_conf, "outro": outro_conf, "loop": loop["confidence"]}
        confidence = clip01(float(np.mean(list(confidence_scores.values()))))
        if tempo_conf < 0.45:
            warnings.append("Tempo confidence is low; verify BPM manually.")
        if drop_conf < 0.4:
            warnings.append("Drop estimate is uncertain.")
        if outro_conf < 0.35:
            warnings.append("Mix-out estimate is uncertain.")
        return {
            "estimated_bpm": safe_float(bpm, 2),
            "duration": safe_float(duration, 2),
            "beat_timestamps": [safe_float(value, 2) for value in beats[:512]],
            "energy_curve": buckets(energy),
            "intro_cue": safe_float(intro, 2),
            "mix_in_cue": safe_float(mix_in, 2),
            "drop_cue": safe_float(drop, 2),
            "mix_out_cue": safe_float(mix_out, 2),
            "loop_cue": loop,
            "confidence_scores": confidence_scores,
            "analysis_confidence": confidence,
            "warnings": warnings,
        }
    finally:
        del y
        gc.collect()


def cue_points(analysis: dict[str, Any]) -> list[dict[str, Any]]:
    scores = analysis["confidence_scores"]
    return [
        {"label": "Hot Cue A", "name": "Intro Start", "timestamp": analysis["intro_cue"], "reason": "First stable beat / intro phrase.", "confidence": max(0.6, scores["intro"])},
        {"label": "Hot Cue B", "name": "Mix In", "timestamp": analysis["mix_in_cue"], "reason": "Estimated first main phrase after the intro.", "confidence": scores["intro"]},
        {"label": "Hot Cue C", "name": "Drop / Hook", "timestamp": analysis["drop_cue"], "reason": "Largest early energy and onset increase.", "confidence": scores["drop"]},
        {"label": "Hot Cue D", "name": "Mix Out", "timestamp": analysis["mix_out_cue"], "reason": "Lower-complexity phrase in the final third.", "confidence": scores["outro"]},
    ]


def average_energy(analysis: dict[str, Any]) -> float:
    curve = analysis.get("energy_curve", [])
    return float(np.mean(curve)) if curve else 0.5
