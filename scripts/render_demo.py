"""Render only captured product pixels; FFmpeg is an optional maintainer tool."""
from pathlib import Path
import argparse
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[1]
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--font',required=True,help='Path to a locally licensed font')
    args=parser.parse_args()
    ffmpeg=shutil.which('ffmpeg')
    if not ffmpeg:parser.error('FFmpeg is required for asset rendering')
    frames=ROOT/'output/playwright/demo/frame-%04d.png'
    subprocess.run([ffmpeg,'-y','-framerate','6','-i',str(frames),'-filter_complex',
        'fps=6,scale=960:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=96:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=3',
        '-loop','0',str(ROOT/'docs/assets/butterflylab-demo.gif')],check=True)
    font=str(Path(args.font).resolve()).replace('\\','/').replace(':','\\:')
    image=ROOT/'docs/assets/parallel-worlds.png'
    filters=("scale=1160:440:force_original_aspect_ratio=decrease,pad=1280:640:(ow-iw)/2:190:color=0x0d1416,"
        f"drawtext=fontfile='{font}':text='ButterflyLab':x=60:y=36:fontsize=48:fontcolor=0xe3eee8,"
        f"drawtext=fontfile='{font}':text='Small interventions. Parallel worlds. Reproducible experiments.':x=60:y=105:fontsize=23:fontcolor=0xa9ddc6")
    subprocess.run([ffmpeg,'-y','-i',str(image),'-vf',filters,'-frames:v','1',
        str(ROOT/'docs/assets/social-preview.png')],check=True)
    print('GIF bytes:',(ROOT/'docs/assets/butterflylab-demo.gif').stat().st_size)

if __name__=='__main__':main()
