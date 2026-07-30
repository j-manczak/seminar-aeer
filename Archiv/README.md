# Archiv — überholte Analysen

Hier liegt alles, was durch das Datenaudit vom 29. Juli 2026 hinfällig geworden
ist. Nichts wurde gelöscht; die Git-Historie ist vollständig, und die Dateien
laufen weiterhin, wenn man sie zurückschiebt.

## Warum das hier liegt

Alle Auswertungen in diesem Ordner beruhen auf dem EEA-Waterbase-Panel **ohne
Filter auf die Wasserkörperart** (`parameterWaterBodyCategory`). Deutschland hat
vor 2020 **keine Flusswassertemperatur** an die EEA gemeldet — alle 17.262
deutschen Temperaturmessungen vor 2020 in der Waterbase sind **Grundwasser**.
Die scheinbare „Vorperiode" dieser Analysen stammt also aus
Grundwassermessstellen, Tiefbrunnen und Quellfassungen, die zufällig innerhalb
von ein bis zwei Kilometern einer Flussachse liegen (Stationsnamen wie
`GWM FLACH KIRSCHGARTSHAUSEN…`, `TB SCHLIENGEN`, `QF WEST UND OST…`).

Dazu kamen zwei Fehler in der Zuordnung:

* Downstream-Messstellen wurden dem *erstgenannten* von zwei koordinatengleichen
  Schwesterblöcken zugeordnet, weshalb Biblis B, Philippsburg 2,
  Neckarwestheim 2, Isar 2 und Gundremmingen C jeweils null Downstream-Stationen
  bekamen.
* Fließrichtung und Entfernung kamen aus einem festen Richtungsvektor pro Fluss
  statt aus der echten Flussgeometrie.

Details: [`../data/processed/analysis/DATENAUDIT_UND_2x2.md`](../data/processed/analysis/DATENAUDIT_UND_2x2.md)

## Inhalt

| Pfad | war | ersetzt durch |
|---|---|---|
| `analysis/plant_level_did/` | erste blockweise DiD-Ergebnisse | `data/processed/analysis/plant_2x2/` |
| `analysis/2x2_2011_shutdowns/` | erster 2011-Versuch samt Fallback-Trendanalyse | dito |
| `analysis/did_water_temperature_results.md` | erster DiD-Durchlauf, Coverage-Diagnose | `analysis/DATENAUDIT_UND_2x2.md` |
| `analysis/research_summary_and_design_implications.md` | Designnotizen auf Basis der alten Coverage | METHODS.md §4.7–4.9, §10 |
| `analysis/thermal_regulation_grouping_review.md` | Gruppierungsreview | METHODS.md §3.5 (mit korrigierter Kühlungsklassifikation) |
| `figures/plant_level_did/`, `figures/2x2_2011_shutdowns/` | zugehörige Abbildungen | `figures/plant_2x2/` |
| `figures/did_coverage.png`, `did_trends.png` | Coverage- und Trendbilder | `figures/plant_2x2/long_run_gap_*.png` |
| `scripts/plant_level_did.py` | blockweise DiD | `scripts/plant_2x2_did.py` |
| `scripts/analyze_2011_shutdowns.py`, `2011_fallback_analysis.py`, `2011_analysis/` | 2011-Sonderauswertung | dito |
| `scripts/did_analysis.py` | erster DiD-Durchlauf | dito |
| `scripts/did_staggered.py` | gestaffelter DiD-Entwurf | noch offen, siehe METHODS.md §6 |

## Was *nicht* archiviert wurde

`scripts/pipeline/river_position.py` bleibt in der Pipeline: die alten
Ausgabedateien tragen seine Spalten, und `build_all.py` sowie
`waterbase_disaggregated.py` importieren es noch. Für die aktuelle Analyse ist
es durch `pipeline/river_network.py` ersetzt — siehe METHODS.md §4.6.

Die Skripte hier laufen nicht mehr an ihrem alten Pfad, weil sie
`scripts/pipeline` relativ importieren. Zum Nachvollziehen einfach
zurückkopieren; für Ergebnisse gilt die Warnung oben.
