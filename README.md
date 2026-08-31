# Runkosarjaveikkaus 2026–2027 – datapäivitys

Ensimmäinen tuotantovaihe: Liigan runkosarjan sarjataulukon automaattinen päivitys.

- `scripts/update_standings.py` hakee Liigan standings-datan.
- Skripti hyväksyy päivityksen vain, jos mukana ovat täsmälleen kaikki 17 Liiga-joukkuetta.
- `data/standings.json` on Weeblyn myöhemmin lukema tuotantodata.
- `.github/workflows/update-standings.yml` ajaa päivityksen kerran tunnissa sekä käsin pyydettäessä.
