#!/usr/bin/env python3
"""Tworzy pliki testowe dla testów w tests/ (domyślnie w /tmp/looper-fixtures, zmienna LOOPER_FIX).

  test.wav                20 s, 48 kHz stereo: prosta melodia (zwykłe „nagranie z Dyktafonu”)
  loud.wav, quiet.wav     12 s, 48 kHz mono: sinus 440 Hz ok. −22 dBFS i 330 Hz ok. −40 dBFS (test wyrównania poziomów)
  clip.mov                4 s, H.264 + AAC 48 kHz mono (film z iPhone'a)
  fast.mp4                3 s, AAC 48 kHz stereo, moov na początku (+faststart)
  screen.mp4              5 s, AAC 44,1 kHz stereo (nagranie ekranu)
  silent.mp4              2 s, sam obraz bez dźwięku (aplikacja ma to grzecznie zgłosić)
  legacy-backup.looper    kopia zapasowa w starym formacie: jedno wspólne tempo −12% dla całej sesji
                          (sprzed wersji z osobnym tempem dla każdej części)

Filmy wymagają ffmpeg; bez niego powstaną tylko pliki WAV i kopia zapasowa.
"""
import json, math, os, shutil, struct, subprocess, sys, wave

FIX = os.environ.get('LOOPER_FIX', '/tmp/looper-fixtures')
SR = 48000


def sine(freq, amp, sec):
    n = int(SR * sec)
    return [int(round(amp * math.sin(2 * math.pi * freq * i / SR))) for i in range(n)]


def write_wav(path, samples):
    with wave.open(path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(struct.pack('<%dh' % len(samples), *samples))


def write_melody(path, sec=20):
    notes = [261.63, 293.66, 329.63, 349.23, 392.0, 440.0, 493.88, 523.25]
    n = int(SR * sec)
    frames = bytearray()
    for i in range(n):
        k = i // (SR // 2)
        f = notes[k % len(notes)]
        t = (i % (SR // 2)) / SR
        env = min(1.0, t * 40) * max(0.0, 1 - t * 1.6)
        v = int(8000 * env * math.sin(2 * math.pi * f * i / SR))
        frames += struct.pack('<hh', v, v)
    with wave.open(path, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(bytes(frames))


def ffmpeg(args, out):
    cmd = ['ffmpeg', '-y', '-v', 'error'] + args + [out]
    subprocess.run(cmd, check=True)


def legacy_backup(path):
    pcm = sine(440, 2584, 3)
    data = struct.pack('<%dh' % len(pcm), *pcm)

    def slot(i):
        return {'id': i, 'name': 'nagranie', 'vol': 1, 'trim': 1, 'offset': 0, 'has': True, 'mute': False, 'solo': False}

    state = {
        'v': 4, 'nextId': 4, 'tempoPct': -12, 'semi': 0, 'curPart': 'A', 'playMode': 'part',
        'sequence': [{'p': 'A', 'n': 1}],
        'parts': {
            'A': {'A': None, 'B': None, 'loopOn': True, 'locked': False, 'slots': [slot(1)]},
            'B': {'A': None, 'B': None, 'loopOn': True, 'locked': False, 'slots': [slot(2)]},
            'C': {'A': None, 'B': None, 'loopOn': True, 'locked': False,
                  'slots': [{'id': 3, 'name': '', 'vol': 1, 'offset': 0, 'has': False}]},
        },
    }
    items = [{'id': i, 'kind': 'pcm', 'sr': SR, 'name': 'nagranie', 'bytes': len(data)} for i in (1, 2)]
    meta = {'format': 'looper-backup', 'version': 1, 'created': 0,
            'sessions': [{'name': 'Stara sesja', 'created': 0, 'updated': 0, 'tracks': 2, 'state': state, 'items': items}]}
    js = json.dumps(meta).encode('utf-8')
    with open(path, 'wb') as f:
        f.write(b'LOOPERB1' + struct.pack('<I', len(js)) + js + data + data)


def main():
    os.makedirs(FIX, exist_ok=True)
    write_melody(os.path.join(FIX, 'test.wav'))
    write_wav(os.path.join(FIX, 'loud.wav'), sine(440, 2584, 12))
    write_wav(os.path.join(FIX, 'quiet.wav'), sine(329.63, 325, 12))
    legacy_backup(os.path.join(FIX, 'legacy-backup.looper'))
    if shutil.which('ffmpeg'):
        tone = lambda f, d, sr, ch: ['-f', 'lavfi', '-i', f'sine=frequency={f}:duration={d}:sample_rate={sr}', '-ac', str(ch)]
        video = lambda d, size: ['-f', 'lavfi', '-i', f'testsrc=duration={d}:size={size}:rate=30']
        ffmpeg(video(4, '640x360') + tone(440, 4, 48000, 1) + ['-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-shortest'], os.path.join(FIX, 'clip.mov'))
        ffmpeg(video(3, '320x240') + tone(550, 3, 48000, 2) + ['-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-shortest', '-movflags', '+faststart'], os.path.join(FIX, 'fast.mp4'))
        ffmpeg(video(5, '640x360') + tone(660, 5, 44100, 2) + ['-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-shortest'], os.path.join(FIX, 'screen.mp4'))
        ffmpeg(video(2, '320x240') + ['-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-an'], os.path.join(FIX, 'silent.mp4'))
    else:
        print('uwaga: brak ffmpeg, pomijam filmy testowe', file=sys.stderr)
    print('pliki testowe w', FIX)


if __name__ == '__main__':
    main()
