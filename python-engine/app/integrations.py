from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


class DjSoftwareAdapter(ABC):
    key: str
    name: str
    extension: str
    description: str

    def metadata(self) -> dict[str, str]:
        return {
            "key": self.key,
            "name": self.name,
            "extension": self.extension,
            "description": self.description,
        }

    @abstractmethod
    def export(self, payload: dict[str, Any], destination: Path) -> list[Path]:
        """Write one or more integration files and return their paths."""


def _track_location(path: str) -> str:
    return Path(path).resolve().as_uri()


class RekordboxXmlAdapter(DjSoftwareAdapter):
    key = "rekordbox"
    name = "rekordbox XML"
    extension = "xml"
    description = "Pioneer DJ collection and playlist XML with BPM and hot-cue markers."

    def export(self, payload: dict[str, Any], destination: Path) -> list[Path]:
        root = ET.Element("DJ_PLAYLISTS", Version="1.0.0")
        product = ET.SubElement(root, "PRODUCT", Name="DJ Agent Desktop", Version="0.1.0", Company="DJ Agent")
        product.tail = "\n"
        collection = ET.SubElement(root, "COLLECTION", Entries=str(len(payload["items"])))
        for item in payload["items"]:
            track = item["track"]
            node = ET.SubElement(
                collection,
                "TRACK",
                TrackID=str(track["track_id"]),
                Name=str(track["title"]),
                Artist=str(track.get("artist") or ""),
                Location=_track_location(track["path"]),
                AverageBpm=str(track["estimated_bpm"]),
                TotalTime=str(round(track["duration"])),
            )
            for cue in track["hot_cues"]:
                ET.SubElement(
                    node,
                    "POSITION_MARK",
                    Name=str(cue["name"]),
                    Type="0",
                    Start=str(cue["timestamp"]),
                    Num=str(max(0, ord(cue["label"][-1]) - ord("A"))),
                )
        playlists = ET.SubElement(root, "PLAYLISTS")
        playlist_root = ET.SubElement(playlists, "NODE", Type="0", Name="ROOT", Count="1")
        playlist = ET.SubElement(
            playlist_root,
            "NODE",
            Type="1",
            Name=str(payload["name"]),
            KeyType="0",
            Entries=str(len(payload["items"])),
        )
        for item in payload["items"]:
            ET.SubElement(playlist, "TRACK", Key=str(item["track"]["track_id"]))
        ET.indent(root, space="  ")
        ET.ElementTree(root).write(destination, encoding="utf-8", xml_declaration=True)
        return [destination]


class VirtualDjXmlAdapter(DjSoftwareAdapter):
    key = "virtualdj"
    name = "VirtualDJ database.xml"
    extension = "xml"
    description = "VirtualDJ-style song database containing scan metadata, POIs, and DJ Agent notes."

    def export(self, payload: dict[str, Any], destination: Path) -> list[Path]:
        root = ET.Element("VirtualDJ_Database", Version="8.6")
        for item in payload["items"]:
            track = item["track"]
            song = ET.SubElement(root, "Song", FilePath=str(track["path"]), FileSize="0", Flag="0")
            ET.SubElement(song, "Tags", Author=str(track.get("artist") or ""), Title=str(track["title"]))
            ET.SubElement(
                song,
                "Infos",
                SongLength=str(track["duration"]),
                FirstSeen="0",
                LastPlay="0",
                PlayCount="0",
            )
            ET.SubElement(song, "Scan", Version="801", Bpm=str(track["estimated_bpm"]))
            for index, cue in enumerate(track["hot_cues"]):
                ET.SubElement(
                    song,
                    "Poi",
                    Pos=str(cue["timestamp"]),
                    Type="cue",
                    Num=str(index),
                    Name=str(cue["name"]),
                )
            loop = track["loop_cue"]
            ET.SubElement(
                song,
                "Poi",
                Pos=str(loop["start"]),
                Type="loop",
                Num="4",
                Name=f"DJ Agent {loop['bars']}-bar loop",
            )
        ET.indent(root, space="  ")
        ET.ElementTree(root).write(destination, encoding="utf-8", xml_declaration=True)
        return [destination]


class SeratoM3uAdapter(DjSoftwareAdapter):
    key = "serato"
    name = "Serato crate bridge"
    extension = "m3u8"
    description = "Portable M3U8 crate plus JSON cue manifest for future native Serato crate writing."

    def export(self, payload: dict[str, Any], destination: Path) -> list[Path]:
        lines = ["#EXTM3U"]
        cue_manifest: dict[str, Any] = {
            "schema": "dj-agent-serato-cue-manifest-v1",
            "setlist": payload["name"],
            "tracks": [],
        }
        for item in payload["items"]:
            track = item["track"]
            lines.append(f"#EXTINF:{round(track['duration'])},{track.get('artist') or ''} - {track['title']}")
            lines.append(str(track["path"]))
            cue_manifest["tracks"].append(
                {
                    "path": track["path"],
                    "bpm": track["estimated_bpm"],
                    "cues": track["hot_cues"],
                    "loop": track["loop_cue"],
                }
            )
        destination.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")
        manifest = destination.with_suffix(".cues.json")
        manifest.write_text(json.dumps(cue_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        return [destination, manifest]


ADAPTERS: dict[str, DjSoftwareAdapter] = {
    adapter.key: adapter
    for adapter in (RekordboxXmlAdapter(), VirtualDjXmlAdapter(), SeratoM3uAdapter())
}


def integration_metadata() -> list[dict[str, str]]:
    return [adapter.metadata() for adapter in ADAPTERS.values()]


def export_for_dj_software(payload: dict[str, Any], target: str, destination: str) -> list[str]:
    adapter = ADAPTERS.get(target.lower())
    if not adapter:
        raise ValueError(f"Unsupported DJ software target: {target}.")
    path = Path(destination).expanduser()
    if path.suffix.lower() != f".{adapter.extension}":
        path = path.with_suffix(f".{adapter.extension}")
    path.parent.mkdir(parents=True, exist_ok=True)
    return [str(result) for result in adapter.export(payload, path)]
