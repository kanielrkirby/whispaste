#!/usr/bin/env python3
import os
import sys
import wave
import platform
import subprocess
import signal
import tempfile
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

def get_config_dir():
    system = platform.system()
    if system == 'Windows':
        base = os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local')
        return Path(base) / 'whispaste'
    if system == 'Darwin':
        return Path.home() / 'Library' / 'Application Support' / 'whispaste'
    base = os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config')
    return Path(base) / 'whispaste'


CONFIG_DIR = get_config_dir()
PID_FILE = CONFIG_DIR / 'recorder.pid'
LOG_FILE = CONFIG_DIR / 'debug.log'
OPTS_FILE = CONFIG_DIR / 'opts.json'

TEMPLATES = {
    'translate': 'Translate the following text to English. Output only the translation, nothing else.',
    'cleanup': 'Clean up this transcribed speech. Fix grammar, punctuation, and remove filler words (um, uh, like, you know). Keep the original meaning and tone. Output only the cleaned text.',
    'organize': 'Organize this transcribed speech into a well-structured document. Use paragraphs, headings if appropriate, and proper formatting. Fix grammar and punctuation. Output only the organized text.',
}


def log(msg):
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(f"{msg}\n")
    except:
        pass


def run_cmd(cmd, input_text=None):
    try:
        subprocess.run(
            cmd,
            input=input_text.encode() if input_text else None,
            check=True,
            timeout=10,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except (FileNotFoundError, subprocess.SubprocessError):
        return False


def copy_to_primary(text):
    if run_cmd(['wl-copy', '--primary'], text):
        log("copy: wl-copy --primary")
        return True
    if run_cmd(['xclip', '-selection', 'primary'], text):
        log("copy: xclip -selection primary")
        return True
    if run_cmd(['xsel', '--primary', '--input'], text):
        log("copy: xsel --primary")
        return True
    log("copy: all methods failed")
    return False


def copy_to_clipboard(text):
    if run_cmd(['wl-copy'], text):
        log("clipboard: wl-copy")
        return True
    if run_cmd(['xclip', '-selection', 'clipboard'], text):
        log("clipboard: xclip")
        return True
    if run_cmd(['xsel', '--clipboard', '--input'], text):
        log("clipboard: xsel")
        return True
    if run_cmd(['pbcopy'], text):
        log("clipboard: pbcopy")
        return True
    if run_cmd(['clip'], text):
        log("clipboard: clip")
        return True
    try:
        import pyperclip
        pyperclip.copy(text)
        log("clipboard: pyperclip")
        return True
    except:
        pass
    log("clipboard: all methods failed")
    return False


def paste_primary():
    if run_cmd(['wtype', '-M', 'shift', '-k', 'Insert', '-m', 'shift']):
        log("paste: wtype shift+Insert")
        return True
    if run_cmd(['xdotool', 'key', 'shift+Insert']):
        log("paste: xdotool shift+Insert")
        return True
    if run_cmd(['xdotool', 'click', '2']):
        log("paste: xdotool middle-click")
        return True
    log("paste: all methods failed")
    return False


def type_text(text):
    if run_cmd(['wtype', '--', text]):
        log("type: wtype")
        return True
    if run_cmd(['ydotool', 'type', '--', text]):
        log("type: ydotool")
        return True
    if run_cmd(['xdotool', 'type', '--clearmodifiers', '--', text]):
        log("type: xdotool")
        return True
    if run_cmd(['osascript', '-e', f'tell app "System Events" to keystroke "{text}"']):
        log("type: osascript")
        return True
    log("type: all methods failed")
    return False


def insert_text(text):
    log(f"insert_text: {len(text)} chars")
    if copy_to_primary(text) and paste_primary():
        return True
    if type_text(text):
        return True
    log("insert_text: all methods failed")
    return False


def notify(msg):
    system = platform.system()
    try:
        if system == 'Linux':
            subprocess.run(['notify-send', 'whispaste', msg], timeout=2)
        elif system == 'Darwin':
            subprocess.run([
                'osascript', '-e',
                f'display notification "{msg}" with title "whispaste"'
            ], timeout=2)
        elif system == 'Windows':
            ps_cmd = f'''
            [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
            $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText01)
            $template.SelectSingleNode("//text[@id='1']").InnerText = "{msg}"
            '''
            subprocess.run(['powershell', '-Command', ps_cmd], timeout=2)
    except:
        pass


def is_process_alive(pid):
    try:
        if platform.system() == 'Windows':
            result = subprocess.run(
                ['tasklist', '/FI', f'PID eq {pid}'],
                capture_output=True, text=True
            )
            return str(pid) in result.stdout
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def kill_process(pid):
    try:
        if platform.system() == 'Windows':
            subprocess.run(['taskkill', '/PID', str(pid)], timeout=2)
        else:
            os.kill(pid, signal.SIGUSR1)
        return True
    except (OSError, ProcessLookupError, subprocess.SubprocessError):
        return False


def transcribe(audio_data, sample_rate, post_prompt=None, post_model=None):
    import numpy as np
    import io
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        notify('OPENAI_API_KEY not set')
        return None
    
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes((audio_data * 32767).astype(np.int16).tobytes())
    wav_buffer.seek(0)
    wav_buffer.name = 'recording.wav'
    
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    
    response = client.audio.transcriptions.create(
        model='gpt-4o-mini-transcribe',
        file=wav_buffer,
        response_format='text'
    )
    
    text = response.strip() if isinstance(response, str) else str(response).strip()
    
    if post_prompt and text:
        log(f"post-processing with {post_model or 'gpt-4o-mini'}")
        response = client.chat.completions.create(
            model=post_model or 'gpt-4o-mini',
            messages=[
                {'role': 'system', 'content': post_prompt},
                {'role': 'user', 'content': text}
            ]
        )
        text = response.choices[0].message.content.strip()
    
    return text


def run_daemon(clipboard_only=False, post_prompt=None, post_model=None):
    import numpy as np
    import sounddevice as sd
    
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(os.getpid()))
    log(f"daemon: pid={os.getpid()} clipboard_only={clipboard_only}")
    log(f"daemon: DISPLAY={os.environ.get('DISPLAY')}")
    
    audio_buffer = []
    sample_rate = 16000
    should_stop = False
    
    def audio_callback(indata, frames, time, status):
        audio_buffer.append(indata.copy())
    
    def handle_stop(signum, frame):
        nonlocal should_stop
        should_stop = True
    
    if platform.system() != 'Windows':
        signal.signal(signal.SIGUSR1, handle_stop)
        signal.signal(signal.SIGTERM, handle_stop)
        signal.signal(signal.SIGINT, handle_stop)
    
    notify('Recording...')
    
    try:
        with sd.InputStream(samplerate=sample_rate, channels=1, callback=audio_callback):
            while not should_stop:
                sd.sleep(50)
                if platform.system() == 'Windows' and not PID_FILE.exists():
                    should_stop = True
    except Exception as e:
        notify(f'Recording error: {e}')
        cleanup()
        sys.exit(1)
    
    if not audio_buffer:
        notify('No audio recorded')
        cleanup()
        sys.exit(1)
    
    opts = read_opts()
    if 'clipboard_only' in opts:
        clipboard_only = opts['clipboard_only']
    if 'post_prompt' in opts:
        post_prompt = opts['post_prompt']
    if 'post_model' in opts:
        post_model = opts['post_model']
    
    log(f"final opts: clipboard_only={clipboard_only} post_prompt={post_prompt} post_model={post_model}")
    notify('Transcribing...')
    
    try:
        audio_data = np.concatenate(audio_buffer)
        text = transcribe(audio_data, sample_rate, post_prompt, post_model)
        
        if text:
            log(f"Transcribed: {text[:50]}...")
            if clipboard_only:
                if copy_to_clipboard(text):
                    log("Copied to clipboard")
                    notify('Copied!')
                else:
                    log("Clipboard copy failed")
                    notify('Clipboard failed')
            else:
                if insert_text(text):
                    log("Insert done")
                    notify('Done!')
                else:
                    log("Insert failed, text in log only")
                    notify('Insert failed')
        else:
            notify('Transcription failed')
    except Exception as e:
        notify(f'Error: {e}')
    finally:
        cleanup()


def cleanup():
    for f in [PID_FILE, OPTS_FILE]:
        try:
            f.unlink()
        except:
            pass


def write_opts(clipboard_only, post_prompt, post_model):
    import json
    opts = {}
    if clipboard_only:
        opts['clipboard_only'] = True
    if post_prompt:
        opts['post_prompt'] = post_prompt
    if post_model:
        opts['post_model'] = post_model
    if opts:
        OPTS_FILE.write_text(json.dumps(opts))


def read_opts():
    import json
    if not OPTS_FILE.exists():
        return {}
    try:
        return json.loads(OPTS_FILE.read_text())
    except:
        return {}


def spawn_daemon(clipboard_only=False, no_daemon=False, post_prompt=None, post_model=None):
    system = platform.system()
    script = sys.argv[0]
    python = sys.executable
    
    args = [python, script, '--daemon']
    if clipboard_only:
        args.append('--clipboard')
    if post_prompt:
        args.extend(['--post-prompt', post_prompt])
    if post_model:
        args.extend(['--post-model', post_model])
    
    if no_daemon:
        run_daemon(clipboard_only=clipboard_only, post_prompt=post_prompt, post_model=post_model)
        return
    
    if system == 'Windows':
        DETACHED_PROCESS = 0x00000008
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        subprocess.Popen(
            args,
            creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=os.environ.copy(),
        )
        return
    
    pid = os.fork()
    if pid > 0:
        os.waitpid(pid, 0)
        return
    
    os.setsid()
    pid2 = os.fork()
    if pid2 > 0:
        sys.exit(0)
    
    os.umask(0)
    sys.stdin = open(os.devnull, 'r')
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')
    run_daemon(clipboard_only=clipboard_only, post_prompt=post_prompt, post_model=post_model)


def signal_stop(clipboard_only=False, post_prompt=None, post_model=None):
    if not PID_FILE.exists():
        return False
    
    try:
        pid = int(PID_FILE.read_text().strip())
    except (ValueError, IOError):
        cleanup()
        return False
    
    if not is_process_alive(pid):
        cleanup()
        return False
    
    write_opts(clipboard_only, post_prompt, post_model)
    
    if platform.system() == 'Windows':
        PID_FILE.unlink()
    else:
        kill_process(pid)
    
    return True


def whispaste(clipboard_only=False, no_daemon=False, post_prompt=None, post_model=None):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            if is_process_alive(pid):
                signal_stop(clipboard_only=clipboard_only, post_prompt=post_prompt, post_model=post_model)
                return
        except (ValueError, IOError):
            pass
        cleanup()
    
    spawn_daemon(clipboard_only=clipboard_only, no_daemon=no_daemon, post_prompt=post_prompt, post_model=post_model)


def get_arg(name):
    for i, arg in enumerate(sys.argv):
        if arg == name and i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return None


def resolve_prompt(post_prompt, template):
    if template:
        if template in TEMPLATES:
            return TEMPLATES[template]
        print(f"Unknown template: {template}")
        print(f"Available: {', '.join(TEMPLATES.keys())}")
        sys.exit(1)
    return post_prompt


if __name__ == '__main__':
    clipboard_only = '--clipboard' in sys.argv
    no_daemon = '--no-daemon' in sys.argv
    post_prompt = get_arg('--post-prompt')
    post_model = get_arg('--post-model')
    template = get_arg('--template')
    
    post_prompt = resolve_prompt(post_prompt, template)
    
    if '--daemon' in sys.argv:
        run_daemon(clipboard_only=clipboard_only, post_prompt=post_prompt, post_model=post_model)
    else:
        whispaste(clipboard_only=clipboard_only, no_daemon=no_daemon, post_prompt=post_prompt, post_model=post_model)
