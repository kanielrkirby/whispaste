"""
Configuration management for Whispaste.
"""
import os
import json
import platform
from pathlib import Path
from typing import Dict, Any

class Config:
    APP_NAME = "whispaste"
    
    @staticmethod
    def get_dir() -> Path:
        system = platform.system()
        if system == 'Windows':
            base = os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local')
        elif system == 'Darwin':
            base = Path.home() / 'Library' / 'Application Support'
        else:
            base = os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config')
        path = Path(base) / Config.APP_NAME
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def pid_file(self) -> Path: return self.get_dir() / 'recorder.pid'
    
    @property
    def log_file(self) -> Path: return self.get_dir() / 'debug.log'
    
    @property
    def env_file(self) -> Path: return self.get_dir() / '.env'
    
    @property
    def opts_file(self) -> Path: return self.get_dir() / 'opts.json'

    def load_env(self):
        """Lazy load environment variables."""
        # We don't import dotenv at module level to keep startup fast
        from dotenv import load_dotenv
        load_dotenv(self.env_file)
        load_dotenv() # Check CWD as well

    def save_opts(self, opts: Dict[str, Any]):
        self.opts_file.write_text(json.dumps(opts))

    def get_opts(self) -> Dict[str, Any]:
        if not self.opts_file.exists():
            return {}
        try:
            return json.loads(self.opts_file.read_text())
        except:
            return {}

    def cleanup(self):
        """Clean up temporary files."""
        try:
            if self.pid_file.exists(): self.pid_file.unlink()
            if self.opts_file.exists(): self.opts_file.unlink()
        except: pass

# Singleton instance
CONFIG = Config()
