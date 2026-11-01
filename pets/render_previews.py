#!/usr/bin/env python3
"""Verify archived pet assets or render the four-pet previews from their atlases."""

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "pets" / "manifest.json"
PREFIX = "beatles-quartet"
FPS = 100  # Every original frame duration is an exact multiple of 10 ms.


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def probe(path, ffprobe):
    result = subprocess.run(
        [ffprobe, "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height,nb_frames:format=duration", "-of", "json", str(path)],
        check=True, capture_output=True, text=True,
    )
    return json.loads(result.stdout)


def verify_archive(manifest, check_previews=True):
    geometry = manifest["atlas"]
    for pet in manifest["pets"]:
        path = ROOT / pet["spritesheet"]
        if path.stat().st_size != pet["bytes"] or digest(path) != pet["sha256"]:
            raise ValueError(f"Atlas checksum mismatch: {pet['spritesheet']}")
        with Image.open(path) as image:
            if image.format != "PNG" or image.mode != "RGBA" or image.size != (
                geometry["width"], geometry["height"]
            ):
                raise ValueError(f"Unexpected atlas format: {pet['spritesheet']}")
        report = json.loads((ROOT / pet["validation"]).read_text(encoding="utf-8"))
        if not all((report["atlas_validation"]["ok"], report["quality"]["ok"],
                    report["mcp_preflight"]["valid"], report["blind_review"]["ok"])):
            raise ValueError(f"Non-passing archived report: {pet['validation']}")
        if report["atlas_validation"]["sha256"] != pet["sha256"]:
            raise ValueError(f"Report checksum mismatch: {pet['validation']}")
        generation = json.loads((ROOT / pet["generation"]).read_text(encoding="utf-8"))
        for relative in generation["identity_references"]:
            if not (ROOT / relative).is_file():
                raise FileNotFoundError(relative)
        for prompt in generation["prompts"].values():
            if not (ROOT / prompt["file"]).is_file():
                raise FileNotFoundError(prompt["file"])
    for preview in manifest["previews"] if check_previews else []:
        path = ROOT / preview["file"]
        if path.stat().st_size != preview["bytes"] or digest(path) != preview["sha256"]:
            raise ValueError(f"Preview checksum mismatch: {preview['file']}")


def encode_video(path, frames, durations_ms, repetitions, ffmpeg):
    width, height = frames[0].size
    command = [
        ffmpeg, "-hide_banner", "-loglevel", "error", "-f", "rawvideo",
        "-pixel_format", "rgb24", "-video_size", f"{width}x{height}",
        "-framerate", str(FPS), "-i", "pipe:0", "-an", "-c:v", "libx264",
        "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", str(path),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        for _ in range(repetitions):
            for frame, duration in zip(frames, durations_ms):
                if duration % 10:
                    raise ValueError("Frame durations must be multiples of 10 ms")
                pixels = frame.tobytes()
                for _ in range(duration // 10):
                    process.stdin.write(pixels)
    except Exception:
        process.kill()
        process.wait()
        raise
    finally:
        process.stdin.close()
    errors = process.stderr.read().decode("utf-8", errors="replace")
    if process.wait():
        raise RuntimeError(errors)


def render(manifest, output_dir, repetitions, force):
    ffmpeg, ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise RuntimeError("Install FFmpeg with both ffmpeg and ffprobe on PATH")
    names = [f"{PREFIX}-animations.mp4", f"{PREFIX}-look-loop.gif",
             f"{PREFIX}-look-loop.mp4", f"{PREFIX}-render-manifest.json"]
    output_dir.mkdir(parents=True, exist_ok=True)
    if not force and any((output_dir / name).exists() for name in names):
        raise FileExistsError("Output exists; use --force or a different --output-dir")
    pets = {pet["slug"]: pet for pet in manifest["pets"]}
    ordered = [pets[slug] for slug in manifest["preview_order"]]
    atlases = []
    for pet in ordered:
        with Image.open(ROOT / pet["spritesheet"]) as image:
            atlases.append(image.convert("RGBA"))
    cell_w = manifest["atlas"]["cell_width"]
    cell_h = manifest["atlas"]["cell_height"]
    size = (cell_w * len(ordered), cell_h + 44)

    def scene(row, column, label):
        image = Image.new("RGB", size, "#f5f1e7")
        draw = ImageDraw.Draw(image)
        for index, (atlas, pet) in enumerate(zip(atlases, ordered)):
            frame = atlas.crop((column * cell_w, row * cell_h,
                                (column + 1) * cell_w, (row + 1) * cell_h))
            image.paste(frame, (index * cell_w, 44), frame)
            draw.text((index * cell_w + 6, 6), pet["name"], fill="#252525")
            draw.text((index * cell_w + 6, 23), label, fill="#252525")
        return image

    actions, durations = [], []
    for state in manifest["states"]:
        for column, duration in enumerate(state["durations_ms"]):
            actions.append(scene(state["row"], column,
                                 f"{state['name']} {column + 1}/{state['frames']}"))
            durations.append(duration)
    looks = [scene(9 + index // 8, index % 8, f"look {degree:05.1f}")
             for index, degree in enumerate(manifest["look_directions_clockwise"])]
    with tempfile.TemporaryDirectory(prefix=".render-", dir=output_dir) as temporary:
        staging = Path(temporary)
        looks[0].save(staging / names[1], save_all=True, append_images=looks[1:],
                      duration=180, loop=0, optimize=False)
        encode_video(staging / names[0], actions, durations, 1, ffmpeg)
        encode_video(staging / names[2], looks, [180] * len(looks), repetitions, ffmpeg)
        videos = {}
        for name, expected_ms in [(names[0], sum(durations)),
                                  (names[2], 180 * len(looks) * repetitions)]:
            info = probe(staging / name, ffprobe)
            stream = info["streams"][0]
            if (stream["width"], stream["height"]) != size:
                raise ValueError(f"Incorrect video dimensions: {name}")
            if abs(float(info["format"]["duration"]) - expected_ms / 1000) > 0.01:
                raise ValueError(f"Incorrect video duration: {name}")
            if int(stream["nb_frames"]) != expected_ms // 10:
                raise ValueError(f"Incorrect encoded frame count: {name}")
            videos[name] = info
        with Image.open(staging / names[1]) as gif:
            if gif.n_frames != 16 or gif.size != size:
                raise ValueError("Incorrect look GIF geometry")
        result = {"characters": [pet["name"] for pet in ordered],
                  "source_atlases": [{"file": pet["spritesheet"], "sha256": pet["sha256"]}
                                     for pet in ordered],
                  "action_duration_ms": sum(durations), "look_gif_duration_ms": 2880,
                  "look_mp4_repetitions": repetitions, "media": videos,
                  "outputs": [{"file": name, "sha256": digest(staging / name)}
                              for name in names[:3]]}
        (staging / names[3]).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        for name in names:
            (staging / name).replace(output_dir / name)
    print(json.dumps(result, indent=2))
    if output_dir == ROOT / "pets" / "previews":
        for preview in manifest["previews"]:
            path = ROOT / preview["file"]
            preview.update(bytes=path.stat().st_size, sha256=digest(path))
            if path.suffix == ".mp4":
                info = videos[path.name]
                preview.update(info["streams"][0])
                preview["duration_seconds"] = float(info["format"]["duration"])
                preview["sequence_repetitions"] = repetitions if "look-loop" in path.name else 1
        MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify archived checksums and reports only")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "pets" / "previews")
    parser.add_argument("--look-mp4-loops", type=int, default=2)
    parser.add_argument("--force", action="store_true", help="Replace existing rendered previews")
    args = parser.parse_args()
    if args.look_mp4_loops < 1:
        parser.error("--look-mp4-loops must be at least 1")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    verify_archive(manifest, check_previews=args.check)
    if args.check:
        print("Verified four final atlases, their QA evidence, source links and three archived previews.")
        return
    render(manifest, args.output_dir.resolve(), args.look_mp4_loops, args.force)


if __name__ == "__main__":
    main()
