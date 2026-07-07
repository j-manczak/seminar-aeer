# Analyse-Eingabedateien (Fenster 2006–2018, Studienstandorte)

Alle Dateien in diesem Ordner werden reproduzierbar durch

```
python scripts/build_group_assignment_and_filters.py
```

erzeugt und sind auf die Studienstandorte (≤ 50 km zu einem Studienreaktor) und
das Fenster 2006–2018 gefiltert. Jede Datei trägt in ihren `#`-Kopfzeilen die
angewandten Filter. Die vollständige Methodik steht in `../METHODS.md`.

| Datei | Inhalt | Status im Repo |
|---|---|---|
| `power_plants_2006_2018_study_sites.csv` | konventionelle Wärmekraftwerke (Confounder) | versioniert |
| `dissolved_oxygen_2006_2018_study_sites.PLACEHOLDER.csv` | gelöster Sauerstoff – Schema/Platzhalter, keine Quelldaten im Repo | versioniert |
| `discharge_2006_2018_study_sites.PLACEHOLDER.csv` | Abfluss – Schema/Platzhalter, keine Quelldaten im Repo | versioniert |
| `water_temperature_2006_2018_study_sites.csv` | Wassertemperatur-Jahreswerte (642 Zeilen) | **wird beim Skriptlauf erzeugt** |
| `weather_2006_2018_study_sites.csv` | Wetter, Station-Monat-Aggregate (3 379 Zeilen) | **wird beim Skriptlauf erzeugt** |

Die beiden zuletzt genannten Tabellen sind in dieser Web-Session nicht direkt
committet, weil der Git-Push-Pfad des Sandkastens schreibgesperrt ist und die
Dateien für die GitHub-API-Übertragung zu groß sind. Ein einmaliger Lauf des
Skripts stellt sie identisch wieder her.
