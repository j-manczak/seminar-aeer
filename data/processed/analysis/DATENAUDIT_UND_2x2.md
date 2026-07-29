# Datenaudit und 2×2-Design pro Kraftwerksstandort

*Antwort auf die Frage, warum in den 2×2-Zellen so viele Nullen standen, und was
statt dessen geht. Stand: 29.07.2026.*

---

## 1. Kurzfassung

1. **Die Nullen kamen nicht nur aus einem Logikfehler, sondern vor allem aus den
   Daten.** Deutschland hat an die EEA Waterbase **vor 2020 keine einzige
   Flusswassertemperatur gemeldet**. Alle 17.262 deutschen Temperaturmessungen
   vor 2020 in der Waterbase sind **Grundwasser** (`GW`). Ein 2×2 um die
   Abschaltung 2011 ist aus der Waterbase grundsätzlich unmöglich.
2. **Zusätzlich gab es drei echte Fehler in der Zuordnungslogik** (Schwesterblöcke,
   Fließrichtung, Nebenflüsse) — unten im Detail. Alle drei sind behoben.
3. **Es gibt eine brauchbare Alternativquelle.** Der Gewässerkundliche Dienst
   Bayern (GKD) veröffentlicht **Tagesmittel der Wassertemperatur ab 1995**.
   Wir haben daraus **305.070 Stationstage** an 35 Pegeln an Isar, Donau und Main
   heruntergeladen.
4. **Damit ergibt sich ein sauberes 2×2 für Isar 1 (2011)** — und das Ergebnis ist
   deutlich: der Temperaturunterschied unterhalb/oberhalb des Standorts fällt von
   **+1,90 °C auf −0,03 °C**, DiD = **−1,93 °C** (p < 0,0001), mit Donut-Spezifikation
   **−2,08 °C**. Das passt exakt zur genehmigten Aufwärmspanne von Isar 1 (max. 2,5 K).
5. **Die Kühlturm-Standorte zeigen erwartungsgemäß nichts** — und das ist ein
   Befund, kein Scheitern: Grafenrheinfeld gab nur ~3 % seiner Abwärme an den
   Main ab, 97 % gingen über die Kühltürme in die Luft.

---

## 2. Warum die 2×2-Zellen leer waren

### 2.1 Hauptursache: Waterbase enthält vor 2020 keine deutschen Flusstemperaturen

Wir haben die vollständige disaggregierte Waterbase (v2025_1, ~30 GB SQLite)
einmal komplett gescannt und **alle** deutschen Temperatur- und
Sauerstoffmessungen extrahiert (`scripts/extract_waterbase_de.py`):

| Wasserkörperart | vor 2020 | ab 2020 |
|---|---:|---:|
| `GW` Grundwasser | 17.262 | 9.200 |
| `RW` **Fließgewässer** | **0** | 25.482 |
| `LW` See | 0 | 808 |
| `TW` Trinkwasser | 0 | 352 |

Die bisherige Pipeline hat nicht nach `parameterWaterBodyCategory` gefiltert.
Hunderte deutsche **Grundwassermessstellen** liegen innerhalb von ein bis zwei
Kilometern einer Flussachse und wurden deshalb als Flusspegel behandelt. Das
erklärt, warum in `plant_level_did_results.csv` scheinbar Beobachtungen ab 2008
existierten: die Stationsnamen der „Pre-Periode" bei Biblis und Philippsburg
lauten `GWM FLACH KIRSCHGARTSHAUSEN…` (GWM = Grundwassermessstelle),
`TB SCHLIENGEN` (TB = Tiefbrunnen) und `QF WEST UND OST…` (QF = Quellfassung) —
das sind Brunnen und Quellen, keine Flusspegel.

Sobald man korrekt auf `RW` filtert, beginnt die Zeitreihe für **jeden** unserer
Studienflüsse erst 2020. Damit ist jede Zelle „downstream × vor 2011" zwangsläufig leer.

### 2.2 Logikfehler 1 — Schwesterblöcke haben sich gegenseitig ausgelöscht

`river_position.classify()` ordnete jede Messstelle dem *nächstgelegenen
oberhalb liegenden Reaktor* zu. Blöcke am selben Standort haben identische
Koordinaten, deshalb entschied bei Gleichstand die Listenreihenfolge: Biblis A
bekam alle Downstream-Stationen, **Biblis B keine einzige**. Dasselbe traf
Philippsburg 2, Neckarwestheim 2, Isar 2 und Gundremmingen C — das sind fünf der
Zeilen mit „0 downstream stations" in `plant_level_did_summary.csv`.

**Behoben:** Die Analyseeinheit ist jetzt der **Standort**, nicht der Block
(`pipeline/station_pairs.py`). Das ist auch physikalisch richtig — der Fluss
reagiert auf die *gesamte* Kühllast eines Standorts, und die Gruppenlogik in
`reactors.py` argumentiert ohnehin schon auf Standortebene.

### 2.3 Logikfehler 2 — Fließrichtung war ein geschätzter Richtungsvektor

`river_position.FLOW` enthielt **einen festen Richtungsvektor pro Fluss**, z. B.
Rhein = „nach Norden", Main = „nach Westen". Die Entfernung war die Projektion
der Luftlinie auf diesen Vektor. Bei mäandrierenden Abschnitten (Main, Neckar,
Isar) ist das nicht nur ungenau, es kann das Vorzeichen umdrehen — also
upstream/downstream vertauschen.

**Behoben:** `pipeline/river_network.py` baut den echten Hauptlauf jedes
Studienflusses aus **HydroRIVERS v1.0** (mit Fließtopologie über `NEXT_DOWN`)
und ergänzt tidale Elbe und Unterweser aus **OpenStreetMap**. Jeder Punkt wird
auf diese Achse projiziert; daraus ergibt sich ein echter Flusskilometer.

Validierung gegen amtliche Kilometrierung:

| Prüfung | Unser Wert | Amtlich | Abweichung |
|---|---:|---:|---:|
| Neckarwestheim | Neckar-km 124,5 | 125,0 | 0,4 % |
| Isar 1 (Ohu) | Isar-km 63,8 | 63,5 | 0,5 % |
| Maxau → Speyer | 39,9 km | 38,3 km | +4 % |
| Speyer → Worms | 43,2 km | 42,8 km | +1 % |
| Worms → Mainz | 56,0 km | 55,0 km | +2 % |
| Kaub → Köln | 146,8 km | 141,8 km | +4 % |
| Flusslänge Neckar | 342 km | 362 km | −6 % |
| Flusslänge Isar | 287 km | 295 km | −3 % |

### 2.4 Logikfehler 3 — Nebenflüsse zählten als Hauptfluss

Auch nach dem `RW`-Filter liegen Messstellen auf **Nebenflüssen** dicht an der
Hauptachse. Bei Biblis sind das `UNTERE WESCHNITZ` (1 km vom Standort) und
`SCHWARZBACH ASTHEIM` — beides Zuflüsse, die kurz vor bzw. nach Biblis in den
Rhein münden. Als „Rhein-Messstellen" wären sie wertlose Kontrollen.

**Behoben:** `monitoring_stations.names_the_river()` prüft das **erste
inhaltliche Token** des Wasserkörpernamens. Das trennt
`DONAU VON EINMUENDUNG LECH BIS …` (Donau) von
`LECH VON … BIS MUENDUNG IN DIE DONAU` (Lech) — ein einfacher Substring-Test
würde beide akzeptieren. Damit fallen 29 Waterbase-Messstellen weg.

---

## 3. Haben wir pro Standort eine Messstelle upstream und downstream?

Vollständige Tabelle: `data/processed/analysis/station_coverage.csv`.
Kriterium „nutzbar": Pegel liegt ≤ 120 km entlang des Flusses vom Standort,
liegt auf dem Hauptlauf, ist nicht durch ein anderes gleichzeitig abgeschaltetes
Kraftwerk kontaminiert, **und hat Messwerte, die vor der Abschaltung beginnen**.

| Standort | Fluss | Abschaltung | Kühlung | Wärme in den Fluss | upstream | downstream | 2×2 möglich |
|---|---|---:|---|---|---|---|---|
| **Biblis** | Rhein | 2011 | Durchlauf | **hoch** | — | — | ✗ |
| **Isar** | Isar | 2011 | Durchlauf | **hoch** | Landshut-Birket (16 km) | Landau (34 km) | ✔ |
| Neckarwestheim | Neckar | 2011 | Kühlturm | niedrig | — | — | ✗ |
| Philippsburg | Rhein | 2011 | hybrid | mittel | — | — | ✗ |
| **Unterweser** | Weser | 2011 | Durchlauf | **hoch** | — | — | ✗ |
| Grafenrheinfeld | Main | 2015 | Kühlturm | niedrig | Schweinfurt (6 km) | Astheim (19 km) | ✔ |
| Gundremmingen | Donau | 2017 | Kühlturm | niedrig | Neu-Ulm (39 km) | Donauwörth (46 km) | ✔ |
| Philippsburg | Rhein | 2019 | hybrid | mittel | — | — | ✗ |
| Brokdorf | Elbe | 2021 | Durchlauf | hoch | „FLUSS" (54 km) | — | ✗ |
| Grohnde | Weser | 2021 | Kühlturm | niedrig | Hemeln (105 km) | Hess. Oldendorf (21 km) | ✔ |
| Gundremmingen | Donau | 2021 | Kühlturm | niedrig | Böfinger Halde (33 km) | Dillingen (14 km) | ✔ |
| Emsland | Ems | 2023 | Kühlturm | niedrig | Rheinenord (25 km) | Herbrum (79 km) | ✔ |
| Isar | Isar | 2023 | Kühlturm | niedrig | Landshut-Birket (16 km) | Landau (34 km) | ✔ |
| Neckarwestheim | Neckar | 2023 | Kühlturm | niedrig | Besigheim (6 km) | Kochendorf (24 km) | ✔ |

**8 von 14 Standort-Ereignissen sind schätzbar — aber nur eines davon ist ein
2011-Ereignis (Isar).** Für alle anderen 2011-Standorte fehlt die Vorperiode
komplett, weil die Waterbase erst 2020 beginnt und wir für Rhein, Neckar, Weser
und Elbe noch keine Alternativquelle erschlossen haben (siehe §6).

---

## 4. Welche Kraftwerke geben ihre Abwärme überhaupt an den Fluss ab?

Das war die Rückmeldung „do research on the plants that don't have the assumed
output". Ergebnis — und **zwei Einträge in unserer Reaktortabelle waren falsch**:

| Standort | bisher | korrekt | Beleg |
|---|---|---|---|
| **Biblis A/B** | `cooling_tower` | **`once_through`** | Lief normal mit Frischwasserkühlung: ~60 m³/s aus dem Rhein, rund 10 K wärmer zurück. Die zwei 80-m-Zellenkühltürme an Block B waren nur Rückfallebene bei warmem/niedrigem Rhein. |
| **Philippsburg 1/2** | `cooling_tower` | **`hybrid`** | Naturzugkühltürme **und** die Möglichkeit, erwärmtes Kühlwasser direkt in den Rhein abzugeben. |
| Isar 1 | `once_through` | bestätigt | Durchlaufkühlung, genehmigte Aufwärmung der Isar **bis 2,5 K**. Schwesterblock Isar 2 hat einen 165-m-Naturzugkühlturm. |
| Grafenrheinfeld | `cooling_tower` | bestätigt | **97 % der Abwärme gingen als Wasserdampf in die Luft**, nur ~3 % in den Main — das entspricht ~0,5–1 K. |
| Gundremmingen B/C | `cooling_tower` | bestätigt | Naturzug-Nasskühltürme, Zusatzwasser über einen 1,4 km langen Kanal aus der Donau. |
| Unterweser | `once_through` | bestätigt | Durchlaufkühlung aus der tidalen Unterweser. |
| Brokdorf | `once_through` | bestätigt | Frischwasserkühlung aus der Elbe; musste in heißen Sommern drosseln. |
| Grohnde, Emsland, Neckarwestheim | `cooling_tower` | bestätigt | Nasskühltürme. |

**Konsequenz für das Design:** „Treatment" ist nicht gleich Treatment. Die
Reaktortabelle trägt jetzt ein Feld `river_heat_load` (`high`/`moderate`/`low`).
Ein Nullergebnis bei Grafenrheinfeld oder Neckarwestheim ist **kein Gegenbeweis
für den Mechanismus** — dort wurde nie nennenswert Wärme in den Fluss geleitet.
Die Standorte mit echtem Signalpotenzial sind: **Unterweser, Biblis, Isar 1**
(und Brokdorf als Kontrolle mit Durchlaufkühlung).

---

## 5. Ergebnisse des korrigierten 2×2

**Spezifikation.** Beide Pegel messen am selben Tag denselben Fluss, deshalb ist
die schärfste Schreibweise des 2×2 die **gepaarte Tagesdifferenz**

```
ΔT_t = T_downstream,t − T_upstream,t
ΔT_t = a + b · post_t + Monatsdummies + e_t
```

`b` ist numerisch der DiD-Schätzer, entfernt aber Wetter, Saison und
flussweiten Trend. Standardfehler HAC/Newey-West mit 30 Tagen Bandbreite
(Tagestemperaturen sind stark autokorreliert). Fenster ±3 Jahre, Ereignisjahr
ausgeschlossen.

### Hauptergebnisse

| Standort | Ereignis | Wärme in Fluss | Lücke vorher | Lücke nachher | **DiD** | p | Donut | Placebo |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| **Isar** | **2011** | **hoch** | **+1,90 °C** | **−0,03 °C** | **−1,93 °C** | <0,0001 | **−2,08** | −0,20 (n.s.) |
| Isar | 2023 | niedrig | +0,19 °C | +0,05 °C | −0,14 °C | 0,15 | — | +0,19 |
| Grafenrheinfeld | 2015 | niedrig | +0,09 °C | +0,50 °C | +0,41 °C | <0,0001 | +0,55 | −0,05 (n.s.) |
| Gundremmingen | 2017 | niedrig | +0,65 °C | +0,86 °C | +0,21 °C | 0,002 | +0,12 | **−0,52** |
| Gundremmingen | 2021 | niedrig | +0,86 °C | +1,08 °C | +0,22 °C | 0,0003 | +0,31 | **+0,32** |

### Interpretation

**Isar 2011 ist das Ergebnis.** Die Lücke zwischen Landau (34 km unterhalb) und
Landshut-Birket (16 km oberhalb) liegt 2007–2009 stabil bei +1,9 bis +2,2 °C,
fällt dann und liegt ab 2012 bei ungefähr null — und bleibt dort bis 2024
(siehe `figures/plant_2x2/long_run_gap.png`). Die Größenordnung passt zur
genehmigten Aufwärmspanne von Isar 1 (bis 2,5 K). Der Placebo drei Jahre früher
ist null.

**Der beste Robustheitstest steckt im selben Standort.** Am Standort Isar gibt
es zwei Abschaltungen mit demselben Pegelpaar:

* **Isar 1, 2011, Durchlaufkühlung → −1,93 °C** (hoch signifikant)
* **Isar 2, 2023, Kühlturm → −0,14 °C** (nicht signifikant)

Gleicher Fluss, gleiche Pegel, gleiche Methode — der Unterschied ist genau die
Kühltechnik. Das ist eine stärkere Bestätigung des Mechanismus, als ein Vergleich
über verschiedene Kraftwerke sie liefern könnte.

**Die Kühlturm-Standorte sind nicht identifiziert, nicht „null".** Bei
Gundremmingen 2021 ist der Placebo (+0,32) genauso groß wie der „Effekt" (+0,31),
und die Jahresreihe schwankt über die ganze Periode zwischen 0,35 und 1,4 °C ohne
sichtbaren Bruch. Bei Grafenrheinfeld hat der Effekt sogar das **falsche
Vorzeichen** (nach der Abschaltung ist es unterhalb *wärmer*). Beides ist mit dem
Mechanismus vereinbar — dort ging kaum Wärme in den Fluss — aber keines der
beiden Ergebnisse sollte als Effektschätzung berichtet werden.

### Wichtige Einschränkung: keine saubere Sprungstelle bei Isar 2011

Die Jahresreihe fällt nicht abrupt im März 2011, sondern **ab 2009/2010**.
Grund: Isar 1 lief vor der endgültigen Abschaltung nicht mehr voll — im Februar
2010 musste der Block wegen eines defekten Brennelements vom Netz. Die
Behandlungsintensität sank also schon vor dem Moratorium.

Konsequenz: Die strenge Parallel-Trends-Annahme für einen harten Schnitt bei 2011
hält **nicht**. Deshalb ist die **Donut-Spezifikation die ehrlichere**: 2010–2012
werden herausgenommen, das Ergebnis ist mit **−2,08 °C** sogar etwas größer. Für
das Paper sollte das offen so geschrieben werden — der Effekt ist robust, aber
das Timing ist ein Auslaufen über 2009–2011, kein Sprung.

### Distanzsensitivität

| Standort | Ereignis | Pegel | Entfernung | DiD |
|---|---:|---|---:|---:|
| Grafenrheinfeld | 2015 | Astheim | 19 km | +0,41 |
| Grafenrheinfeld | 2015 | Würzburg | 78 km | +0,32 |
| Grafenrheinfeld | 2015 | Erlabrunn | 88 km | +0,24 |
| Gundremmingen | 2017 | Donauwörth | 46 km | +0,21 |
| Gundremmingen | 2017 | Ingolstadt | 100 km | +0,20 |
| Gundremmingen | 2021 | Donauwörth | 46 km | +0,22 |
| Gundremmingen | 2021 | Ingolstadt | 100 km | +0,01 |
| Isar | 2011 | Landau | 34 km | −1,93 |

Für die Isar gibt es leider **keinen zweiten Downstream-Pegel** innerhalb von
120 km (Plattling liegt 54 km unterhalb, hat aber erst ab 2020 Daten), deshalb
lässt sich der Abstandsabfall dort nicht messen. Das ist die größte offene
Lücke der Sensitivitätsanalyse.

---

## 6. Empfehlung — was wir konkret machen sollten

**A. Isar 2011 zum Hauptergebnis machen.** Das ist das einzige 2011-Ereignis mit
sauberen Daten, es hat den stärksten theoretischen Treatment (Durchlaufkühlung,
2,5 K genehmigt), einen großen Effekt, einen Null-Placebo und mit Isar 2 (2023)
eine Falsifikation innerhalb desselben Standorts. Das trägt ein Kapitel.

**B. Die Kühlturm-Standorte als Heterogenitätsbefund berichten, nicht als Null.**
Die Botschaft ist: der Effekt tritt genau dort auf, wo die Technik ihn
vorhersagt. Dafür brauchen wir die `river_heat_load`-Spalte im Paper.

**C. Wenn Zeit bleibt: Daten für die übrigen 2011-Standorte holen.** Uns fehlen
Rhein (Biblis, Philippsburg), Neckar (Neckarwestheim), Weser (Unterweser). Die
Pegel existieren physisch — PEGELONLINE listet Wassertemperatur u. a. bei
Rechtenfleth (Weser-km 46,5) und Nordenham (55,8), die Unterweser (~52) direkt
einrahmen. PEGELONLINE liefert aber nur 30 Tage Historie. Die Archive liegen bei
den Ländern:
* Baden-Württemberg (Neckar, Rhein): LUBW / HVZ — `udo.lubw.baden-wuerttemberg.de`
  war aus diesem Netz nicht erreichbar, `hvz.baden-wuerttemberg.de` schon.
* Hessen / Rheinland-Pfalz (Rhein bei Biblis): HLNUG, LfU RLP.
* Niedersachsen / Bremen (Weser): NLWKN, FGG Weser.
* Schleswig-Holstein (Elbe, Brokdorf): FGG Elbe (`elbe-datenportal.de`, JS-Portal).

Der GKD-Downloader (`pipeline/gkd_bayern.py`) ist so gebaut, dass sich dieselbe
Struktur für ein weiteres Landesportal nachziehen lässt.

**D. Was ich *nicht* empfehle:** die Waterbase-basierten Ergebnisse in
`plant_level_did/` und `2x2_2011_shutdowns/` weiter zu verwenden. Sie beruhen auf
Grundwassermessstellen. Die Verzeichnisse sollten als überholt markiert oder
gelöscht werden.

---

## 7. Was neu im Repo ist

| Datei | Zweck |
|---|---|
| `scripts/extract_waterbase_de.py` | Einmaliger Scan der 30-GB-SQLite → alle deutschen Temperatur-/Sauerstoffproben |
| `scripts/pipeline/river_network.py` | Echte Flussachsen (HydroRIVERS + OSM), echter Flusskilometer, Fließrichtung aus der Topologie |
| `scripts/pipeline/gkd_bayern.py` | Downloader für GKD Bayern (Tagesmittel ab 1995) |
| `scripts/pipeline/monitoring_stations.py` | Einheitliche Stationstabelle beider Quellen, `RW`-Filter, Nebenfluss-Filter |
| `scripts/pipeline/station_pairs.py` | Standort- statt Blockebene, saubere Up-/Downstream-Paare, Kontaminationsprüfung |
| `scripts/plant_2x2_did.py` | 2×2 auf der gepaarten Tagesdifferenz + Donut, Placebo, Saison, Distanz |
| `scripts/station_coverage_report.py` | Die Tabelle aus §3 |
| `scripts/make_study_map.py` | Übersichtskarte mit echter Geometrie und benannten Messstellen |
| `scripts/make_sites_by_reactor.py` | Ein Kartenausschnitt je Standort, Messstellen mit Namen und Flusskilometer-Abstand |

Ergebnisse: `data/processed/analysis/plant_2x2/`, `data/processed/analysis/station_coverage.csv`
Abbildungen: `figures/plant_2x2/`, `figures/study_map.png`, `figures/study_sites_by_reactor.png`

**Reproduktion:**
```bash
python scripts/extract_waterbase_de.py        # braucht die Waterbase-SQLite lokal
python scripts/pipeline/river_network.py      # lädt HydroRIVERS beim ersten Lauf
python scripts/pipeline/gkd_bayern.py         # ~10 min, cached pro Station
python scripts/station_coverage_report.py
python scripts/plant_2x2_did.py
python scripts/make_study_map.py
python scripts/make_sites_by_reactor.py
```

---

## 8. Quellen für die Kühlungsrecherche

* Kernkraftwerk Biblis — <https://de.wikipedia.org/wiki/Kernkraftwerk_Biblis>
* Kernkraftwerk Isar — <https://de.wikipedia.org/wiki/Kernkraftwerk_Isar>
* Kernkraftwerk Grafenrheinfeld — <https://de.wikipedia.org/wiki/Kernkraftwerk_Grafenrheinfeld>
* Kernkraftwerk Philippsburg — <https://de.wikipedia.org/wiki/Kernkraftwerk_Philippsburg>
* Kernkraftwerk Gundremmingen — <https://de.wikipedia.org/wiki/Kernkraftwerk_Gundremmingen>
* Kernkraftwerk Brokdorf — <https://de.wikipedia.org/wiki/Kernkraftwerk_Brokdorf>
* Kernkraftwerk Grohnde — <https://de.wikipedia.org/wiki/Kernkraftwerk_Grohnde>
* KKU Unterweser, Kurzbeschreibung — <https://www.atommuellreport.de/fileadmin/Dateien/pdf/Datenblaetter/Esenshamm/Kurzbeschreibung_062015.pdf>
* Kühlwassernutzung, LfU Bayern — <https://www.lfu.bayern.de/wasser/thermische_nutzung_gewaesser/kuehlwassernutzung/index.htm>
* Kühltürme Philippsburg, EnBW — <https://www.enbw.com/kuehltuerme/funktion-der-kuehltuerme/>

**Daten:**
* HydroRIVERS v1.0 (Europa) — <https://www.hydrosheds.org/products/hydrorivers>
* OpenStreetMap via Overpass (tidale Elbe, Unterweser) — © OpenStreetMap-Mitwirkende, ODbL
* Gewässerkundlicher Dienst Bayern — <https://www.gkd.bayern.de/de/fluesse/wassertemperatur>
* EEA Waterbase WISE6, v2025_1 disaggregiert
