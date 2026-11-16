import json

des = "Details:\nSehr geehrte Damen und Herren,\nanbei erhalten Sie die Bestellanforderung 49607 zum Versand aus dem Pufferlager: Network Infrastructure.\nLieferadresse:\nDACHSER SE\nNiederlassung Hamburg\nHerr Jan Meier\nLagerstraße 8\n20095 Hamburg\nBitte folgende Artikel für die Auslieferung vorbereiten:\nMaterial\tText\tMenge\tGeplantes Lieferdatum\tEmpfänger\n11896\tC9300L-48P-4X-A DA-Bundle\t6\t06.12.2026\t\nMenge\tDID\tName\tKostenstelle\n6\t\tN/A\t7840020\n11897\tC9300L-24P-4X-A DA-Bundle\t2\t06.12.2026\t\nMenge\tDID\tName\tKostenstelle\n2\t\tN/A\t7840020\n\tCisco Linecard C9400-LC-48U\t1\t06.12.2026\t\nMenge\tDID\tName\tKostenstelle\n1\t\tN/A\t7840020\n\tC9500-16X-A\t2\t06.12.2026\t\nMenge\tDID\tName\tKostenstelle\n2\t\tN/A\t7840020\n--------------------------------------------------------------------------------------------------------"
SWITCHES = [
    "C9200CX-12P-2X2G-A",
    "C9300L-24P-4X-A",
    "C9300L-48P-4X-A",
    "C9500-16X-A",
    "C9410R-96U-BNDL-A",
    "Cisco Linecard C9400-LC-48U",
]


def parse_infos(description: str) -> dict:
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
        "switches": counts,
    },
}


if __name__ == "__main__":
    print(json.dumps(parse_infos(des), ensure_ascii=False, indent=2))
