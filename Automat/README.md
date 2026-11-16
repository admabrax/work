# Order SUP Finder

Finds the SUP-ID of an order based on the number of switches. You enter the switch counts and the tool searches your Outlook shipping notifications (Versandbenachrichtigungen) for matching tickets.

## Requirements

- Windows with the Outlook desktop app (signed in)
- Python 3.x
- An Outlook folder containing all Versandbenachrichtigung emails

## Outlook setup

1. In Outlook, search for all Versandbenachrichtigung emails assigned to our group.
2. Create a new folder and move all results into it.
3. Create a rule that moves all future Versandbenachrichtigung emails into this folder automatically.

## Installation

```powershell
git clone https://github.com/<user>/<repo>.git
cd <repo>
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

In the folder create a file ".env" and insert API_LOGIN=<username> and API_PASSWORD=<password>

## Usage

```powershell
.venv\Scripts\activate
python gui.py
```

1. Enter the number of switches in the fields. Empty fields default to `0`.
2. Select your Outlook folder.
3. Choose a search mode:
   - **Exact**: only tickets where the switch count matches exactly
   - **Include**: all tickets that contain the given switch count
