import datetime
import platform
import subprocess
import sys
from pathlib import Path
from subprocess import DEVNULL

import yaml

# Rawdog dir
rawdog_dir = Path.home() / ".rawdog"
rawdog_log_path = rawdog_dir / "logs.jsonl"
rawdog_dir.mkdir(exist_ok=True)

# Command history file
history_file = rawdog_dir / "cmdline_history"


class EnvInfo:
    def __init__(self, data=None):
        if data:
            self._set_from_dict(data)
        else:
            self._set_from_env()

    def _set_from_dict(self, data):
        """Used when preparing fine-tuning examples"""
        self.data = data["date"]
        self.cwd = data["cwd"]
        self.os = data["os"]
        self.is_git = data["is_git"]
        self.cwd_info = data["cwd_info"]
        self.last_commit = data["last_commit"]

    def _set_from_env(self):
        self.date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cwd = Path.cwd()
        self.os = platform.system()
        self.is_git = "IS" if Path(".git").exists() else "is NOT"
        self.cwd_info = self._get_cwd_info()
        self.last_commit = "" if not self.is_git else "\nThe last commit message is: " + (
            subprocess.run(
                ["git", "log", "-1", "--pretty=%B"], stdout=subprocess.PIPE
            )
            .stdout.decode()
            .strip()
        )

    def _get_cwd_info(self, max_items=100):
        output = []
        for i, item in enumerate(self.cwd.iterdir()):
            if i >= max_items:
                break
            name = ("" if not item.is_dir() else "/") + item.name
            last_modified = datetime.datetime.fromtimestamp(
                item.stat().st_mtime
            ).strftime("%Y-%m-%d %H:%M:%S") 
            size = len(list(item.iterdir())) if item.is_dir() else  item.stat().st_size
            unit = " bytes" if item.is_file() else " items"
            output.append(f"{last_modified} {size:10}{unit} {name}")
        if not output:
            return "The directory is empty."
        return "\n".join(output)

    def render_prompt(self):
        return """\
Today's date is {date}.
The current working directory is {cwd}, which {is_git} a git repository.
The user's operating system is {os}.
The contents of the current working directory are:
{cwd_info}{last_commit}""".format(
            date=self.date, 
            cwd=self.cwd, 
            is_git=self.is_git, 
            os=self.os, 
            cwd_info=self.cwd_info,
            last_commit=self.last_commit, 
        )


# Script execution environment
def get_rawdog_python_executable():
    venv_dir = rawdog_dir / "venv"
    if platform.system() == "Windows":
        python_executable = venv_dir / "Scripts" / "python"
    else:
        python_executable = venv_dir / "bin" / "python"
    if not venv_dir.exists():
        print(f"Creating virtual environment in {venv_dir}...")
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_dir)],
            stdout=DEVNULL,
            stderr=DEVNULL,
            check=True,
        )
        install_pip_packages("matplotlib", "pandas", "numpy")
    return str(python_executable)


def install_pip_packages(*packages: str):
    python_executable = get_rawdog_python_executable()
    print(f"Installing {', '.join(packages)} with pip...")
    subprocess.run(
        [python_executable, "-m", "pip", "install", *packages],
        stdout=DEVNULL,
        stderr=DEVNULL,
        check=True,
    )
