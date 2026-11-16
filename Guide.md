# Setup Guide

What each command does and why it's needed.

---

## 1. Virtual environment (venv)

A venv is an isolated Python environment just for one project. Packages installed while it's active go into the `.venv/` folder, not into your system Python. Every project gets its own venv so packages don't conflict.

```powershell
Remove-Item -Recurse -Force .venv
```
Deletes the existing `.venv` folder. You need this when the venv is broken, for example after moving the project folder: a venv stores its absolute path and stops working once that path changes. You can also just delete the folder in Explorer.

```powershell
python -m venv .venv
```
Creates a new, empty venv in a folder called `.venv`. `-m venv` runs Python's built-in `venv` module.

```powershell
.venv\Scripts\activate
```
Activates the venv. After this, `python` and `pip` point to the venv instead of system Python. You'll see `(.venv)` at the start of the prompt.
- Linux/Mac: `source .venv/bin/activate`
- Leave the venv: `deactivate`
- Check it's active: `where python` should point to `...\.venv\Scripts\python.exe`

```powershell
pip install -r requirements.txt
```
Installs all packages listed in `requirements.txt` into the active venv. `-r` means "read from file".
- Create or update the file: `pip freeze > requirements.txt` (with the venv active)

---

## 2. Git: first-time setup

Run these once, when a project is not yet a git repository.

```bash
git init
```
Turns the current folder into a git repository by creating a hidden `.git/` folder. That folder holds the whole history.

**Run this only in the top-level folder.** If a subfolder has its own `.git`, git treats it as a separate repo (submodule), and GitHub shows it as an empty folder with an arrow icon.

```bash
git add .
```
Stages all new and changed files for the next commit. `.` means "everything in this folder". Files listed in `.gitignore` are skipped.

```bash
git status
```
Shows which files are staged, changed or untracked. Always check this before committing. `.env` and `.venv/` must **not** appear here.

```bash
git commit -m "initial commit"
```
Saves a snapshot of all staged files **locally** in `.git/`. `-m` is the commit message, a short description of what changed. Use normal quotes `"`, not typographic ones like `„ ”`.

```bash
git branch -M main
```
Renames the current branch to `main`. Older git versions call the default branch `master`, but GitHub expects `main`.

```bash
git remote add origin https://github.com/<user>/<repo>.git
```
Links your local repo to the GitHub repo. `origin` is the conventional name for that remote. You only need to do this once.
- Show the remote: `git remote -v`
- Change the URL: `git remote set-url origin <new-url>`

```bash
git push -u origin main
```
Uploads your local commits to GitHub. `-u` saves `origin main` as the default, so from then on a plain `git push` is enough.

---

## 3. .gitignore

Put this file in the top-level folder of the repo. It applies to all subfolders too.

```
.env
.venv/
__pycache__/
```

| Entry | Why it's ignored |
|---|---|
| `.env` | contains credentials, must never be on GitHub |
| `.venv/` | large, platform-specific, can be rebuilt from `requirements.txt` |
| `__pycache__/` | compiled bytecode, created automatically by Python |

Check that a file is ignored:
```bash
git check-ignore -v .env     # output = ignored
```

---

## 4. Daily workflow

```bash
git status
git add .
git status
git commit -m "what you changed"
git push
```

- **commit** saves the changes locally
- **push** uploads them to GitHub

---

## 5. Getting the project on a new PC

```powershell
git clone https://github.com/<user>/<repo>.git
cd <repo>\<project>
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```
Then create a `.env` with your own credentials. It isn't in the repo.
