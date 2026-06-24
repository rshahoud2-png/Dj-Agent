from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .analysis import analyze_audio_file, average_energy, cue_points
from .database import connection, json_value, row, rows


def list_tracks() -> list[dict[str, Any]]:
    return rows(
        """SELECT t.*, a.bpm, a.duration, a.analysis_confidence
           FROM tracks t LEFT JOIN analyses a ON a.track_id=t.id
           ORDER BY t.artist COLLATE NOCASE, t.title COLLATE NOCASE"""
    )


def _decode_analysis(record: dict[str, Any]) -> dict[str, Any]:
    for key in ("beat_timestamps", "energy_curve", "loop_cue", "confidence_scores", "warnings"):
        record[key] = json.loads(record[key])
    record["estimated_bpm"] = record.pop("bpm")
    return record


def get_analysis(track_id: int) -> dict[str, Any]:
    track = row("SELECT id, title, artist FROM tracks WHERE id=?", (track_id,))
    analysis = row("SELECT * FROM analyses WHERE track_id=?", (track_id,))
    if not track or not analysis:
        raise ValueError("Track analysis was not found.")
    result = {**track, **_decode_analysis(analysis)}
    result["hot_cues"] = rows(
        "SELECT id, label, name, timestamp, reason, confidence FROM cue_points WHERE track_id=? ORDER BY id",
        (track_id,),
    )
    return result


def analyze_track(track_id: int) -> dict[str, Any]:
    track = row("SELECT * FROM tracks WHERE id=?", (track_id,))
    if not track:
        raise ValueError("Track was not found.")
    path = Path(track["path"])
    if not path.exists():
        raise ValueError("Audio file no longer exists at its scanned path.")
    with connection() as db:
        db.execute("UPDATE tracks SET status='analyzing', error=NULL, updated_at=CURRENT_TIMESTAMP WHERE id=?", (track_id,))
    try:
        analysis = analyze_audio_file(path)
        cues = cue_points(analysis)
        with connection() as db:
            db.execute(
                """INSERT INTO analyses(
                    track_id, bpm, duration, beat_timestamps, energy_curve, intro_cue, mix_in_cue,
                    drop_cue, mix_out_cue, loop_cue, confidence_scores, analysis_confidence, warnings
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(track_id) DO UPDATE SET
                    bpm=excluded.bpm, duration=excluded.duration, beat_timestamps=excluded.beat_timestamps,
                    energy_curve=excluded.energy_curve, intro_cue=excluded.intro_cue, mix_in_cue=excluded.mix_in_cue,
                    drop_cue=excluded.drop_cue, mix_out_cue=excluded.mix_out_cue, loop_cue=excluded.loop_cue,
                    confidence_scores=excluded.confidence_scores, analysis_confidence=excluded.analysis_confidence,
                    warnings=excluded.warnings, analyzed_at=CURRENT_TIMESTAMP""",
                (
                    track_id, analysis["estimated_bpm"], analysis["duration"], json_value(analysis["beat_timestamps"]),
                    json_value(analysis["energy_curve"]), analysis["intro_cue"], analysis["mix_in_cue"],
                    analysis["drop_cue"], analysis["mix_out_cue"], json_value(analysis["loop_cue"]),
                    json_value(analysis["confidence_scores"]), analysis["analysis_confidence"], json_value(analysis["warnings"]),
                ),
            )
            db.execute("DELETE FROM cue_points WHERE track_id=?", (track_id,))
            db.executemany(
                "INSERT INTO cue_points(track_id, label, name, timestamp, reason, confidence) VALUES (?, ?, ?, ?, ?, ?)",
                [(track_id, cue["label"], cue["name"], cue["timestamp"], cue["reason"], cue["confidence"]) for cue in cues],
            )
            db.execute("UPDATE tracks SET status='complete', error=NULL, updated_at=CURRENT_TIMESTAMP WHERE id=?", (track_id,))
        return get_analysis(track_id)
    except Exception as exc:
        with connection() as db:
            db.execute("UPDATE tracks SET status='failed', error=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (str(exc), track_id))
        raise


def transition(current: dict[str, Any], nxt: dict[str, Any]) -> dict[str, Any]:
    bpm_diff = abs(current["estimated_bpm"] - nxt["estimated_bpm"])
    energy_delta = average_energy(nxt) - average_energy(current)
    if bpm_diff <= 4:
        transition_type = "Blend"
    elif bpm_diff <= 8:
        transition_type = "Loop Transition"
    elif energy_delta > 0.15:
        transition_type = "Drop Swap"
    elif bpm_diff >= 20:
        transition_type = "Cut"
    elif energy_delta < -0.2:
        transition_type = "Fade"
    else:
        transition_type = "Echo Out"
    bars = 32 if transition_type in {"Blend", "Loop Transition"} else 8 if transition_type in {"Cut", "Drop Swap"} else 16
    compatibility = int(max(0, min(100, (100 - bpm_diff * 4) * 0.5 + (100 - abs(energy_delta) * 80) * 0.3 + min(current["analysis_confidence"], nxt["analysis_confidence"]) * 20)))
    warnings: list[str] = []
    if bpm_diff > 18:
        warnings.append("Large BPM difference; use a cut, echo, or tempo reset.")
    if min(current["analysis_confidence"], nxt["analysis_confidence"]) < 0.45:
        warnings.append("Verify cue placement because one track has low analysis confidence.")
    instruction = (
        f"Start {nxt['title']} from Hot Cue A or B on a {bars}-bar phrase. "
        f"Bring in highs and mids first, keep bass out, then swap bass on the final downbeat. "
        f"Recommended transition: {transition_type}."
    )
    result = {
        "from_track_id": current["track_id"],
        "to_track_id": nxt["track_id"],
        "compatibility_score": compatibility,
        "recommended_transition_type": transition_type,
        "suggested_transition_length_bars": bars,
        "dj_performance_instruction": instruction,
        "warnings": warnings,
    }
    with connection() as db:
        db.execute(
            """INSERT INTO transitions(from_track_id, to_track_id, compatibility_score, transition_type, transition_bars, instruction, warnings)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(from_track_id, to_track_id) DO UPDATE SET compatibility_score=excluded.compatibility_score,
               transition_type=excluded.transition_type, transition_bars=excluded.transition_bars,
               instruction=excluded.instruction, warnings=excluded.warnings""",
            (current["track_id"], nxt["track_id"], compatibility, transition_type, bars, instruction, json_value(warnings)),
        )
    return result


EVENT_SECTIONS = {
    "arabic wedding": ["Dinner", "Entrance", "First Dance", "Arabic Warmup", "Dabke", "Arabic Peak", "English / Latin Peak", "Slow Dance", "Closing"],
    "wedding": ["Dinner", "Entrance", "First Dance", "Open Dance", "Throwbacks", "Peak Party", "Slow Dance", "Closing"],
    "club": ["Warmup", "Build Up", "Peak", "Reset", "Peak 2", "Closing"],
    "lounge": ["Background", "Warm Groove", "Social Energy", "Cooldown"],
    "bar": ["Background", "Warm Groove", "Social Energy", "Late Energy", "Cooldown"],
    "corporate": ["Arrival", "Networking", "Dinner", "Feature", "Social", "Closing"],
    "cafe": ["Background", "Warm Groove", "Social Energy", "Cooldown"],
}


def section_energy(section: str) -> float:
    value = section.lower()
    if any(word in value for word in ("dinner", "background", "first dance", "slow", "cooldown")):
        return 0.28
    if any(word in value for word in ("dabke", "peak", "party", "late energy")):
        return 0.82
    if any(word in value for word in ("warm", "entrance", "social", "feature")):
        return 0.5
    return 0.6


def generate_setlist(event_type: str, event_duration: int, name: str) -> dict[str, Any]:
    analyses = [get_analysis(item["id"]) for item in rows("SELECT id FROM tracks WHERE status='complete' ORDER BY id")]
    if not analyses:
        raise ValueError("Analyze at least one track before generating a set.")
    sections = EVENT_SECTIONS.get(event_type.lower(), EVENT_SECTIONS["club"])
    target_count = max(1, min(len(analyses), round(event_duration / 4)))
    remaining, selected = analyses[:], []
    for index in range(target_count):
        section = sections[min(len(sections) - 1, int(index / target_count * len(sections)))]
        target = section_energy(section)
        def score(candidate: dict[str, Any]) -> float:
            energy_fit = 1 - abs(average_energy(candidate) - target)
            transition_fit = transition(selected[-1], candidate)["compatibility_score"] / 100 if selected else 0.7
            artist_penalty = 0.18 if candidate["artist"] and any(previous["artist"] == candidate["artist"] for previous in selected[-3:]) else 0
            return energy_fit * 0.5 + candidate["analysis_confidence"] * 0.25 + transition_fit * 0.25 - artist_penalty
        best = max(remaining, key=score)
        remaining.remove(best)
        selected.append(best)
    items = []
    warnings: list[str] = []
    for index, track in enumerate(selected):
        section = sections[min(len(sections) - 1, int(index / len(selected) * len(sections)))]
        trans = transition(selected[index - 1], track) if index else None
        if trans and trans["compatibility_score"] < 55:
            warnings.append(f"Weak transition into track {index + 1}: {track['title']}.")
        items.append({
            "position": index + 1,
            "section": section,
            "track": track,
            "transition": trans,
            "cue_notes": [f"{cue['label']} {cue['name']} at {cue['timestamp']}s" for cue in track["hot_cues"]],
            "warnings": track["warnings"] + (trans["warnings"] if trans else []),
        })
    payload = {
        "id": 0, "name": name, "event_type": event_type, "event_duration": event_duration,
        "confidence_score": round(sum(track["analysis_confidence"] for track in selected) / len(selected), 3),
        "items": items, "warnings": sorted(set(warnings)),
    }
    with connection() as db:
        cursor = db.execute(
            "INSERT INTO setlists(name, event_type, event_duration, confidence_score, payload) VALUES (?, ?, ?, ?, ?)",
            (name, event_type, event_duration, payload["confidence_score"], json_value(payload)),
        )
        payload["id"] = cursor.lastrowid
        db.execute("UPDATE setlists SET payload=? WHERE id=?", (json_value(payload), cursor.lastrowid))
    return payload


def export_setlist(setlist_id: int, export_format: str, destination: str) -> str:
    record = row("SELECT payload FROM setlists WHERE id=?", (setlist_id,))
    if not record:
        raise ValueError("Setlist was not found.")
    payload = json.loads(record["payload"])
    path = Path(destination).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    if export_format.lower() == "json":
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    elif export_format.lower() == "csv":
        with path.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.writer(handle)
            writer.writerow(["Position", "Section", "Title", "Artist", "BPM", "Intro Cue", "Mix In Cue", "Drop Cue", "Mix Out Cue", "Transition", "DJ Instructions"])
            for item in payload["items"]:
                track, trans = item["track"], item.get("transition")
                writer.writerow([
                    item["position"], item["section"], track["title"], track["artist"], track["estimated_bpm"],
                    track["intro_cue"], track["mix_in_cue"], track["drop_cue"], track["mix_out_cue"],
                    trans["recommended_transition_type"] if trans else "Opening track",
                    trans["dj_performance_instruction"] if trans else "Open clean from Hot Cue A.",
                ])
    else:
        raise ValueError("Export format must be csv or json.")
    return str(path)
