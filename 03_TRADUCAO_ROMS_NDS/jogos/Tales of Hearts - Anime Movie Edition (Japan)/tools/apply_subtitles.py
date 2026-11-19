"""Aplica legendas .srt sobre _mc.avi com tarja preta full-width nos tempos das falas."""
import re
import subprocess
import sys
from pathlib import Path

FFMPEG = Path("03_TRADUCAO_ROMS_NDS/_ferramentas_nds/ffmpeg.exe")
MOVIES_DIR = Path(
    "03_TRADUCAO_ROMS_NDS/jogos/Tales of Hearts - Anime Movie Edition (Japan)/extracted/movies"
)

TIME_RE = re.compile(
    r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})"
)


def _to_sec(h: str, m: str, s: str, ms: str) -> float:
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0


def _build_enable_expr(srt_path: Path) -> str:
    spans = []
    for line in srt_path.read_text(encoding="utf-8").splitlines():
        m = TIME_RE.search(line)
        if m:
            t0 = _to_sec(*m.groups()[:4])
            t1 = _to_sec(*m.groups()[4:])
            spans.append(f"between(t,{t0:.3f},{t1:.3f})")
    return "+".join(spans) if spans else "0"


def apply_srt(name: str) -> int:
    jp_avi = MOVIES_DIR / f"{name}_JP_mc.avi"
    avi_in = jp_avi if jp_avi.exists() else MOVIES_DIR / f"{name}_mc.avi"
    srt_in = MOVIES_DIR / f"{name}.srt"
    avi_out = MOVIES_DIR / f"{name}_subbed.avi"

    if not avi_in.exists() or not srt_in.exists():
        print(f"Arquivo ausente: {avi_in} ou {srt_in}")
        return 1

    srt_escaped = str(srt_in).replace("\\", "/").replace(":", "\\:")
    style = (
        "FontName=Arial,FontSize=18,Bold=1,PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=1,MarginV=8"
    )
    vf = f"subtitles='{srt_escaped}':force_style='{style}'"
    cmd = [
        str(FFMPEG),
        "-y",
        "-v",
        "error",
        "-i",
        str(avi_in),
        "-vf",
        vf,
        "-c:v",
        "rawvideo",
        "-pix_fmt",
        "bgr24",
        "-c:a",
        "copy",
        str(avi_out),
    ]
    res = subprocess.run(cmd)
    if res.returncode == 0:
        print(f"Gerado: {avi_out} ({avi_out.stat().st_size} bytes)")
    return res.returncode


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "MOV001"
    sys.exit(apply_srt(target))
