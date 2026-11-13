"""Lay the ElevenLabs voiceovers onto the v2 videos, line by line.

Each mp3 is split into its script lines at natural pauses (silencedetect),
choosing the split points whose cumulative lengths best match each line's
share of the text. Each line is then placed at its cue time from
../demos_motion_v2/voiceover_scripts.md (pushed later if the previous line
is still speaking). Video is stream-copied; v2 files are not modified.

usage: python sync_voice.py [mp3_dir]      (default D:/Downloads, files 1..8.mp3)
"""
import math, os, re, subprocess, sys
import wave
import numpy as np
import imageio_ffmpeg

HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.join(HERE, "..", "demos_motion_v2")
MP3 = sys.argv[1] if len(sys.argv) > 1 else r"D:\Downloads"
FF = imageio_ffmpeg.get_ffmpeg_exe()
VIDEOS = ["01_creating_account", "02_forgot_password", "03_customer_booking",
          "04_additional_customer", "05_Vendor", "06_Staff", "07_Dispatcher", "08_Admin"]
SR = 48000
GAP = 0.25
EARLY = 1.5  # how far a line may lead its cue when the voice runs long  # min breath between lines when a line runs late


def parse_md():
    md = open(os.path.join(V2, "voiceover_scripts.md"), encoding="utf-8").read()
    out = []
    for sec in re.split(r"\n## 0\d", md)[1:]:
        cues = [int(m) * 60 + int(s) for m, s in re.findall(r"^\| (\d+):(\d\d) \|", sec, re.M)]
        block = re.search(r"```text\n(.*?)```", sec, re.S).group(1)
        lines = [re.sub(r"\[[^\]]*\]|…", "", l).strip() for l in block.strip().splitlines()]
        assert len(cues) == len(lines), (cues, lines)
        out.append((cues, lines))
    return out


def probe(path, af):
    r = subprocess.run([FF, "-nostdin", "-hide_banner", "-i", path, "-af", af, "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stderr


def duration(path):
    h, m, s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", probe(path, "anull")).groups()
    return int(h) * 3600 + int(m) * 60 + float(s)


def pauses(path):
    err = probe(path, "silencedetect=noise=-40dB:d=0.2")
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", err)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    return list(zip(st, en))


def split(lines, gaps, total):
    """Cut the take at len(lines)-1 of its pauses so every line's duration is
    as close as possible (in log ratio) to what its text length predicts."""
    w = [len(l) + 8 for l in lines]  # +8: fixed per-line overhead (breath, onset)
    exp = [x / sum(w) * total for x in w]
    pts = [0.0] + [(s + e) / 2 for s, e in gaps] + [total]
    n, k = len(lines), len(pts) - 1
    INF = float("inf")
    # dp[i][j]: best cost with line i ending at point j
    dp = [[INF] * (k + 1) for _ in range(n + 1)]
    bk = [[0] * (k + 1) for _ in range(n + 1)]
    dp[0][0] = 0.0
    for i in range(1, n + 1):
        for j in range(i, k + 1 if i == n else k):
            if i == n and j != k:
                continue
            for q in range(i - 1, j):
                if dp[i - 1][q] == INF:
                    continue
                c = dp[i - 1][q] + math.log((pts[j] - pts[q]) / exp[i - 1]) ** 2
                if c < dp[i][j]:
                    dp[i][j], bk[i][j] = c, q
    cuts, j = [k], k
    for i in range(n, 0, -1):
        j = bk[i][j]
        cuts.append(j)
    cuts.reverse()
    return [(pts[cuts[i]], pts[cuts[i + 1]]) for i in range(n)]


def main():
    scripts = parse_md()
    for idx, (name, (cues, lines)) in enumerate(zip(VIDEOS, scripts), 1):
        mp3 = os.path.join(MP3, f"{idx}.mp3")
        vid = os.path.join(V2, name + ".mp4")
        vdur, adur = duration(vid), duration(mp3)
        chunks = split(lines, pauses(mp3), adur)
        print(f"\n{name}  (voice {adur:.1f}s, video {vdur:.1f}s)")
        raw = subprocess.run([FF, "-nostdin", "-v", "error", "-i", mp3, "-f", "f32le",
                              "-ac", "2", "-ar", str(SR), "-"], capture_output=True, check=True).stdout
        voice = np.frombuffer(raw, np.float32).reshape(-1, 2)
        track = np.zeros((int(vdur * SR), 2), np.float32)
        # forward: each line at its cue, or right after the previous line
        starts, end = [], 0.0
        for i, ((a, b), cue) in enumerate(zip(chunks, cues)):
            at = max(cue + 0.15, end + GAP if i else 0.6)
            starts.append(at)
            end = at + (b - a)
        # backward: if the voice overruns the video, pull lines earlier
        # (at most EARLY seconds ahead of their cue)
        limit = vdur - 0.35
        for i in range(len(starts) - 1, -1, -1):
            ln = chunks[i][1] - chunks[i][0]
            starts[i] = max(min(starts[i], limit - ln), cues[i] - EARLY, 0.3)
            limit = starts[i] - GAP
        end = 0.0
        fade = np.linspace(0, 1, int(0.03 * SR), dtype=np.float32)[:, None]
        for i, ((a, b), cue, text) in enumerate(zip(chunks, cues, lines)):
            at = starts[i]
            end = at + (b - a)
            print(f"  {at:5.1f}-{end:5.1f}s  (cue {cue:3d}s)  {text[:60]}")
            seg = voice[int(a * SR):int(b * SR)].copy()
            seg[:len(fade)] *= fade
            seg[-len(fade):] *= fade[::-1]
            o = int(at * SR)
            seg = seg[:max(0, len(track) - o)]
            track[o:o + len(seg)] += seg
        if end > vdur - 0.3:
            print(f"  !! voice ends at {end:.1f}s, past the video ({vdur:.1f}s)")
        wav = os.path.join(HERE, f"_{name}.wav")
        with wave.open(wav, "wb") as w:
            w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes((np.clip(track, -1, 1) * 32767).astype(np.int16).tobytes())
        out = os.path.join(HERE, name + ".mp4")
        subprocess.run([FF, "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
                        "-i", vid, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k",
                        "-ar", str(SR), "-movflags", "+faststart", out], check=True)
        os.remove(wav)


if __name__ == "__main__":
    main()
