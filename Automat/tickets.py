import requests
import win32com.client
import re
from concurrent.futures import ThreadPoolExecutor
import json
from dotenv import load_dotenv
import os

SWITCHES = [
    "C9200CX-12P-2X2G-A",
    "C9300L-24P-4X-A",
    "C9300L-48P-4X-A",
    "C9500-16X-A",
    "C9410R-96U-BNDL-A",
    "Cisco Linecard C9400-LC-48U",
]

load_dotenv()
# --- Zugangsdaten: hier deine Werte eintragen ---
PROXY_URL = "http://USER:ENCODED_PASS@proxy.dachser.com:8080"
API_LOGIN = os.getenv("API_LOGIN")
API_PASSWORD = os.getenv("API_PASSWORD")
# ------------------------------------------------

base_url = "https://dachser.efectecloud-test.com/rest-api/itsm/v1"
proxies = {"http": PROXY_URL, "https": PROXY_URL}

DEFAULT_FOLDER = "test"


def get_wichtig():
    outlook = win32com.client.Dispatch("Outlook.Application")
    ns = outlook.GetNamespace("MAPI")
    root = ns.GetDefaultFolder(6).Parent                     # das Postfach
    return root.Folders["Wichtig"]


def list_folders():
    """Namen aller Unterordner von 'Wichtig' (für die Auswahl in der GUI)."""
    return [f.Name for f in get_wichtig().Folders]


def auth():
    auth_url = f"{base_url}/users/login"
    r_auth = requests.post(auth_url, data={"login": API_LOGIN, "password": API_PASSWORD}, proxies=proxies, timeout=10)
    return r_auth.json()["token"].removeprefix("Bearer ")


def get_email(foldername):
    folder = get_wichtig().Folders[foldername]
    print(f"Foldername: {folder.Name}, Count: {folder.Items.Count}")
    return get_numbers(folder)


def get_numbers(folder):
    ids = []
    for mail in folder.Items:
        if mail.Class != 43:      # 43 = MailItem; skip meeting invites, read receipts etc.
            continue
        m = re.search(r"(?:/incident/data/|datacard/view/)(\d+)", mail.Body)
        if m:
            ids.append(m.group(1))
    return ids


def fetch(s, incident_id):
    r = s.get(f"{base_url}/dc/incident/data/{incident_id}", timeout=10)
    data = r.json()["data"]
    description = data["description"]["values"][0]["value"]
    sup_id = data["efecte_id"]["values"][0]["value"]
    link = data["datacard_link"]["values"][0]["value"]
    return incident_id, description, sup_id, link


def parse_infos(description: str, sup_id, link) -> dict:
    lines = description.split("\n")
    counts = dict.fromkeys(SWITCHES, 0)
    niederlassungsnummer = ""

    for i, line in enumerate(lines[:-1]):
        # Artikelzeile = die Zeile direkt vor "Menge\tDID..."
        if lines[i + 1].startswith("Menge\tDID"):
            art = line.split("\t")
            text, menge = art[1], int(art[2])
            for model in SWITCHES:
                if model in text:
                    counts[model] += menge
                    break

            if not niederlassungsnummer and i + 2 < len(lines):
                kostenstelle = lines[i + 2].split("\t")[-1].strip()
                niederlassungsnummer = kostenstelle[:-4].zfill(3)

    return {
        "infos": {
            "niederlassungsnummer": niederlassungsnummer,
            "sup-id": sup_id,
            "link": link,
            "switches": counts,
        }
    }


def main(foldername=DEFAULT_FOLDER, on_total=None, on_progress=None):
    headers = {"Authorization": "Bearer " + auth()}

    s = requests.Session()
    s.headers.update(headers)
    s.proxies.update(proxies)

    email_numbers = get_email(foldername)
    if on_total:
        on_total(len(email_numbers))          # Anzahl an die GUI melden

    tickets = {}

    with ThreadPoolExecutor(max_workers=5) as ex:
        results = ex.map(lambda i: fetch(s, i), email_numbers)
        for done, (id, description, sup_id, link) in enumerate(results, start=1):
            tickets[id] = parse_infos(description, sup_id, link)
            if on_progress:
                on_progress(done)             # "done Tickets fertig" an die GUI melden

    return tickets


if __name__ == "__main__":
    print("main_call_wuzzi")