"""
Whispaste: Dead-Simple Voice-to-Paste.
CLI Entry Point & Daemon Logic.
"""
import sys
import os
import signal
import json
import argparse
import subprocess
from .config import CONFIG
from .system import System
from .audio import AudioEngine
from .clipboard import Clipboard
from .injector import Injector

TEMPLATES = {
    'cleanup': 'Clean up this transcribed speech. Fix grammar, punctuation, and remove filler words. Keep original meaning. Output only cleaned text.',
    'email': 'Format this as a professional email. Output only the email body.',
    'code': 'Format this as code. Detect the language. Output only the code block.'
}

def worker_loop():
    """
    Optimized worker with instant recording start.
    Pre-warms audio system then records immediately.
    """
    # 1. Setup PID
    CONFIG.pid_file.write_text(str(os.getpid()))
    
    should_stop = False
    def stop_signal_handler(signum, frame):
        nonlocal should_stop
        should_stop = True
        
    signal.signal(signal.SIGTERM, stop_signal_handler)
    signal.signal(signal.SIGINT, stop_signal_handler)
    
    try:
        # 2. Start recording IMMEDIATELY - no pre-warming delay
        System.notify("Listening...")
        engine = AudioEngine()  # Lightweight, no pre-warming
        audio = engine.record_until_stop(lambda: should_stop)
        
        # 4. Transcribe & Action
        if audio is not None:
            # Reload opts (passed from the CLI trigger)
            opts = CONFIG.get_opts()
            
            text = engine.transcribe(
                audio, 
                post_prompt=opts.get('prompt'),
                post_model=opts.get('model')
            )
            
            if text:
                if opts.get('clipboard', False):
                    if Clipboard.write(text):
                        System.notify("Copied to clipboard!")
                    else:
                        System.notify("Failed to copy.")
                else:
                    Injector.insert(text)
        else:
            System.notify("No audio recorded.")
            
    except Exception as e:
        System.notify(f"Critical Error: {e}")
        System.log(str(e))
    finally:
        CONFIG.cleanup()

def start_daemon(args):
    """Spawn the worker process in the background."""
    # Save options for the worker to read
    opts = {
        'clipboard': args.clipboard,
        'prompt': args.prompt,
        'model': args.model
    }
    CONFIG.save_opts(opts)
    
    # Launch the worker package as a detached subprocess
    subprocess.Popen(
        [sys.executable, '-m', 'whispaste', '--daemon'],
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL
    )

def stop_daemon(pid):
    """Signal the existing worker process to stop recording and process."""
    System.kill(pid)  # Sends SIGTERM

def manage_daemon_state(args):
    """
    CLI Controller Logic:
    - If running -> Stop it (Process audio).
    - If stopped -> Start it (Begin recording).
    """
    pid_file = CONFIG.pid_file
    
    # Check for existing process
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            if System.is_running(pid):
                stop_daemon(pid)
                return
        except Exception:
            pass
        # PID file exists but process is dead (stale)
        pid_file.unlink(missing_ok=True)

    # If we get here, no valid daemon is running
    start_daemon(args)

def main():
    parser = argparse.ArgumentParser(description="Whispaste: Voice-to-Paste")
    # --daemon is an internal flag used by the worker process
    parser.add_argument('--daemon', action='store_true', help=argparse.SUPPRESS)
    
    parser.add_argument('-c', '--clipboard', action='store_true', help='Copy to clipboard only, do not type')
    parser.add_argument('-p', '--prompt', help='Post-processing prompt')
    parser.add_argument('-m', '--model', help='Post-processing model (default: gpt-4o-mini)')
    parser.add_argument('-t', '--template', choices=TEMPLATES.keys(), help='Use a preset prompt template')


    args = parser.parse_args()
    
    # Resolve Template
    if args.template:
        args.prompt = TEMPLATES[args.template]

    if args.daemon:
        # We are the background worker
        worker_loop()
    else:
        # We are the user CLI
        manage_daemon_state(args)

if __name__ == "__main__":
    main()
