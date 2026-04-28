#!/usr/bin/env python3
"""
Convert Insta360 dual-fisheye .insv files to equirectangular MP4.

Each .insv contains two 2880×2880 HEVC streams (front + back lens).
We hstack them into a 5760×2880 dual-fisheye frame, then use ffmpeg's
v360 filter to reproject to 3840×1920 equirectangular.

Uses VideoToolbox hardware H.264 encoding on macOS for speed.

Usage:
    python3 convert.py                # convert all data/*.insv
    python3 convert.py path/to/f.insv # convert one file
"""

import subprocess, sys, os, glob, time

INPUT_DIR  = os.path.join(os.path.dirname(__file__), "data")
OUTPUT_DIR = os.path.join(INPUT_DIR, "equirect")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Insta360 dual-fisheye lens FOV (ONE X / ONE X2 / ONE RS)
FOV = 193

# Output resolution (standard 4K equirect 2:1)
OUT_W, OUT_H = 3840, 1920


def convert(src: str) -> bool:
    name   = os.path.splitext(os.path.basename(src))[0]
    dst    = os.path.join(OUTPUT_DIR, name + ".mp4")

    if os.path.exists(dst):
        print(f"  skip  {name}.mp4 (already exists)")
        return True

    filter_graph = (
        f"[0:v:0][0:v:1]hstack=inputs=2[df];"
        f"[df]v360=dfisheye:equirect:ih_fov={FOV}:iv_fov={FOV}:"
        f"pitch=0:yaw=0:roll=0,"
        f"scale={OUT_W}:{OUT_H}[out]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", src,
        "-filter_complex", filter_graph,
        "-map", "[out]",
        "-map", "0:a:0?",          # audio if present
        "-c:v", "h264_videotoolbox",
        "-b:v", "25M",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        dst,
    ]

    print(f"  converting  {os.path.basename(src)} → {name}.mp4")
    t0 = time.time()
    result = subprocess.run(
        cmd,
        stderr=subprocess.PIPE,
        text=True,
    )
    elapsed = time.time() - t0

    if result.returncode != 0:
        # Fall back to software encoder if VideoToolbox unavailable
        print(f"  VideoToolbox failed, retrying with libx264…")
        cmd[cmd.index("h264_videotoolbox")] = "libx264"
        cmd[cmd.index("25M")]               = "23"          # CRF instead of bitrate
        cmd.insert(cmd.index("25M") + 1, "-crf")            # swap -b:v → -crf
        # rebuild clean fallback command
        cmd2 = [
            "ffmpeg", "-y",
            "-i", src,
            "-filter_complex", filter_graph,
            "-map", "[out]",
            "-map", "0:a:0?",
            "-c:v", "libx264", "-crf", "20", "-preset", "fast",
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            dst,
        ]
        result = subprocess.run(cmd2, stderr=subprocess.PIPE, text=True)
        elapsed = time.time() - t0

    if result.returncode != 0:
        print(f"  ERROR  {result.stderr[-400:]}")
        return False

    size_mb = os.path.getsize(dst) / 1024**2
    print(f"  done    {name}.mp4  ({size_mb:.0f} MB, {elapsed:.0f}s)")
    return True


if __name__ == "__main__":
    files = sys.argv[1:] if len(sys.argv) > 1 else sorted(glob.glob(os.path.join(INPUT_DIR, "*.insv")))

    if not files:
        print("No .insv files found in data/")
        sys.exit(1)

    print(f"Converting {len(files)} file(s) → {OUTPUT_DIR}\n")
    ok = all(convert(f) for f in files)
    print("\nAll done." if ok else "\nFinished with errors.")
