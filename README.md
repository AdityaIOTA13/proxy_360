# proxy_360

Minimal browser-based 360° video viewer for Insta360 `.insv` footage.

## How it works

Each `.insv` file contains two 2880×2880 HEVC streams (front + back fisheye lens).  
`convert.py` stitches them into a 3840×1920 equirectangular MP4 using ffmpeg's `v360=dfisheye:equirect` filter.  
`index.html` renders the video onto a WebGL sphere via A-Frame with a custom GLSL shader that softens the stitching seam in real time.

## Setup

```
proxy_360/
├── data/           ← place your .insv files here
│   └── equirect/   ← auto-created by convert.py
├── equi_video/     ← optional: drop Insta360 Studio exports here (highest quality)
├── index.html
├── server.py
└── convert.py
```

### 1 · Convert footage (requires ffmpeg)

```bash
python3 convert.py
```

Converts all `data/*.insv` → `data/equirect/*.mp4` (3840×1920, H.264, VideoToolbox).  
If you have Insta360 Studio exports, drop them into `equi_video/` — the viewer prefers those automatically.

### 2 · Serve locally

```bash
python3 server.py        # http://localhost:8360
python3 server.py 9000   # custom port
```

### 3 · View

Open **http://localhost:8360** in your browser.

- **Drag** to look around (pure yaw/pitch, no roll drift)
- **← →** arrows or clip buttons to switch clips
- **Space** to play/pause
- Clips are colour-coded: **blue = Studio export**, **green = ffmpeg equirect**, **grey = raw**

## Notes

- Video files are gitignored (too large for GitHub).  
- The GitHub Pages link shows the viewer UI only; you need to run `server.py` locally with your footage.
- Proper stitching at the seam requires Insta360 Studio; the ffmpeg path is a fast approximation.
