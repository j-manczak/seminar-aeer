# Überholt — nicht mehr verwenden

Die Ergebnisse in diesem Verzeichnis (`plant_level_did_*.csv`,
`plant_level_did_report.md`) beruhen auf dem EEA-Waterbase-Panel **ohne** Filter
auf die Wasserkörperart.

Deutschland hat vor 2020 **keine Flusswassertemperatur** an die Waterbase
gemeldet. Alle scheinbaren „Vorperioden"-Beobachtungen dieser Auswertung stammen
aus **Grundwassermessstellen**, Tiefbrunnen und Quellfassungen, die zufällig
innerhalb von ein bis zwei Kilometern einer Flussachse liegen (Stationsnamen wie
`GWM FLACH KIRSCHGARTSHAUSEN…`, `TB SCHLIENGEN`, `QF WEST UND OST…`).

Zusätzlich ordnete die damalige Logik alle Downstream-Messstellen dem
erstgenannten von zwei koordinatengleichen Schwesterblöcken zu, weshalb Biblis B,
Philippsburg 2, Neckarwestheim 2, Isar 2 und Gundremmingen C jeweils null
Downstream-Stationen bekamen.

Ersetzt durch:

* `data/processed/analysis/DATENAUDIT_UND_2x2.md` — Audit und Empfehlung
* `data/processed/analysis/plant_2x2/` — korrigierte Schätzung
* `data/processed/analysis/station_coverage.csv` — Messstellenabdeckung je Standort
