# Methodendokumentation

Diese Datei dokumentiert fortlaufend und nachvollziehbar das Vorgehen bei der
Aufbereitung der Daten für unsere Differenz-von-Differenzen-Analyse (DiD) zum
deutschen Atom-Moratorium von 2011. Sie ist so geschrieben, dass einzelne
Absätze direkt als Textbausteine für den Methodenteil des Papers übernommen
werden können. Jeder Arbeitsschritt nennt die Datenquelle mit Abrufdatum, die
Filter- und Aggregationsentscheidungen mit Begründung, die Ausschlüsse von
Stationen oder Reaktoren sowie die offenen Annahmen.

*Bearbeitungsstand: 7. Juli 2026.*

---

## 1. Fragestellung und Untersuchungsfenster

Wir untersuchen, ob der Wegfall der thermischen Kühllast durch die im März 2011
abgeschalteten Kernkraftwerke die Wassertemperatur (und perspektivisch den
gelösten Sauerstoff) der betroffenen Flüsse messbar verändert hat. Als
Beobachtungsfenster legen wir die Jahre **2006 bis 2018 (einschließlich)** fest.
Das Fenster umfasst fünf Vorjahre und sieben Nachjahre um den Schock von 2011
und ist damit annähernd symmetrisch. Alle nachfolgenden Filter verwenden dieses
Fenster einheitlich.

---

## 2. Datenquellen und Abrufdaten

| Datensatz | Datei im Repository | Ursprungsquelle | Abruf-/Standdatum |
|---|---|---|---|
| Reaktoren (Standort, Fluss) | `data/Plants-River-Treatment.xlsx` | Projekt-Arbeitsblatt der Gruppe | im Repo vorliegend, gelesen 07.07.2026 |
| Kernkraftwerke (Stammdaten) | `data/processed/nuclear_plants_de_clean.csv` | Open Power System Data, `conventional_power_plants_DE` (Teilmenge `energy_source = Nuclear`) | im Repo vorliegend, gelesen 07.07.2026 |
| Konventionelle Wärmekraftwerke | `data/processed/conventional_plants_de_relevant_clean.csv` | Open Power System Data, `conventional_power_plants_DE` | im Repo vorliegend, gelesen 07.07.2026 |
| Wassertemperatur (Jahreswerte) | `data/processed/water_temperature_de_annual_clean.csv` | EEA Waterbase v2020_1, `T_WISE6_AggregatedData` (Determinand *Water temperature*) | im Repo vorliegend, gelesen 07.07.2026 |
| Gewässer-Messstellen (Stammdaten) | `data/processed/water_monitoring_sites_de_clean.csv` | EEA Waterbase v2020_1, `S_WISE6_SpatialObject_DerivedData` | im Repo vorliegend, gelesen 07.07.2026 |
| Wetter (Tageswerte) | `data/processed/dwd_kl_daily_near_nuclear.csv` | Deutscher Wetterdienst (DWD), Climate Data Center, Tageswerte KL | im Repo vorliegend, gelesen 07.07.2026 |
| DWD-Stationsstammdaten | `data/processed/dwd_stations_near_nuclear_30km.csv` | DWD Climate Data Center, Stationsliste | im Repo vorliegend, gelesen 07.07.2026 |

Ergänzend haben wir für die Gruppenzuordnung reaktorspezifische Angaben
(Stilllegungsjahr, Kühlungstyp) aus öffentlichen Quellen recherchiert, weil
diese Angaben in den obigen Rohdaten nicht oder nur unvollständig enthalten
sind. Diese Quellen wurden am **7. Juli 2026** abgerufen:

- Bundesamt für die Sicherheit der nuklearen Entsorgung (BASE): „Der Atomausstieg in Deutschland" — Stilllegungsdaten der Blöcke. <https://www.base.bund.de/en/nuclear-safety/nuclear-phase-out/nuclear-phase-out_content.html>
- World Nuclear News, „Three German reactors cease operation" (Abschaltungen 31.12.2021 und 15.04.2023). <https://www.world-nuclear-news.org/Articles/Three-German-reactors-cease-operation>
- Betreiber- und Fachdokumentation zum Kühlungstyp: PreussenElektra-Standortbroschüre Isar (Durchlaufkühlung KKI 1 vs. Naturzug-Nasskühlturm KKI 2); BASE-Standortseite Brokdorf (Frischwasserkühlung aus der Elbe); Wikipedia-Artikel „Kernkraftwerk Grohnde" (Naturzug-Nasskühlturm).

**Offene Annahme (Abrufdatum Rohdaten):** Die exakten Download-Daten der
EEA-Waterbase-, OPSD- und DWD-Rohdateien sind im Repository nicht protokolliert.
Wir dokumentieren die jeweilige Datenversion (Waterbase **v2020_1**, OPSD
`conventional_power_plants_DE`, DWD KL-Tageswerte) und tragen das exakte
Bezugsdatum nach, sobald es aus den ursprünglichen Download-Skripten rekonstruiert
ist.

---

## 3. Gruppenzuordnung der Reaktoren

### 3.1 Prüfung der durchgehenden Netzverfügbarkeit im Fenster 2006–2018

Für jede potenzielle Kontrollanlage haben wir explizit geprüft, ob der Reaktor
über das **gesamte** Fenster 2006–2018 durchgehend am Netz war. Kriterium: Der
Block muss vor 2006 in Betrieb gegangen und darf frühestens 2019 (also nach dem
Fenster) stillgelegt worden sein; zusätzlich darf er nicht bereits vor 2011
faktisch dauerhaft vom Netz gewesen sein. Grundlage ist das **Stilllegungsjahr
je Reaktor**.

Zwei nominelle „Weiterbetrieb"-Anlagen bestehen diese Prüfung **nicht** und sind
daher **keine gültigen Vollzeit-Kontrollen**:

- **Grafenrheinfeld (KKG)** wurde Ende **2015** stillgelegt, also mitten im
  Fenster.
- **Gundremmingen B (KRB B)** wurde Ende **2017** stillgelegt, also ebenfalls
  mitten im Fenster.

Beide werden aus der Kontrollgruppe ausgeschlossen und stattdessen als **spätere,
gestaffelte Treatments** markiert (Gruppe `Gestaffeltes Treatment`), weil ihre
Abschaltung selbst einen — nur zeitlich versetzten — Wegfall der Kühllast
darstellt. Für ein bereinigtes DiD sollten sie entweder ganz ausgeschlossen oder
in einem gestaffelten („staggered") Design mit reaktorspezifischem
Behandlungszeitpunkt geführt werden.

Alle übrigen Kontrollkandidaten (Grohnde 2021, Emsland 2023, Brokdorf 2021,
Isar 2 2023, Neckarwestheim 2 2023, Philippsburg 2 2019, Gundremmingen C 2021)
liefen 2006–2018 durchgehend und bestehen die Prüfung.

### 3.2 Zuordnungslogik der drei Hauptgruppen

Jeder Reaktor wird begründet genau einer Gruppe zugeordnet; die Begründung steht
zeilenweise in `data/processed/group_assignment.csv`.

- **Treatment** — Standorte, die 2011 **vollständig** abgeschaltet wurden, so
  dass die **gesamte** Kühllast wegfiel: **Biblis A**, **Biblis B**
  (beide Blöcke desselben Standorts) und **Unterweser**.
- **Partial** — 2011 abgeschaltete Blöcke, deren **Schwesterblock am selben
  Standort weiterlief**, so dass nur ein Teil der Kühllast entfiel:
  **Isar 1**, **Neckarwestheim 1**, **Philippsburg 1**.
- **Kontrolle** — Reaktoren, die 2006–2018 durchgehend liefen: **Grohnde**,
  **Emsland**, **Brokdorf**, **Isar 2**, **Neckarwestheim 2**,
  **Philippsburg 2**, **Gundremmingen C**.

Die weiterlaufenden Schwesterblöcke (Isar 2, Neckarwestheim 2, Philippsburg 2)
ordnen wir **auf Reaktorebene** der Kontrollgruppe zu, weil der Block selbst
durchgehend in Betrieb war. Wir vermerken jedoch in der Begründungsspalte
ausdrücklich, dass an ihrem **Standort** 2011 eine partielle Lastreduktion
stattfand (der jeweilige Block 1 wurde abgeschaltet). Analog liegt am Standort
Gundremmingen mit der Abschaltung von Block B (2017) eine gestaffelte
Standort-Behandlung vor, während Block C weiterlief. Wer auf Standortebene
statt auf Reaktorebene modelliert, muss diese Blöcke folglich als teil- bzw.
gestaffelt behandelt führen. Diese Designentscheidung ist bewusst getroffen und
transparent dokumentiert.

### 3.3 Ausgeschlossene Reaktoren

- **Brunsbüttel (KKB)** und **Krümmel (KKK)** wurden zwar mit dem Moratorium 2011
  formal vom Netz genommen, waren aber faktisch schon **vor 2011** dauerhaft
  außer Betrieb (Brunsbüttel seit einem Störfall 2007; Krümmel nach dem
  Transformatorbrand 2007 nur noch kurz und ab 2009 gar nicht mehr am Netz). Sie
  liefern damit **keinen echten Kühllast-Schock im Jahr 2011** und werden aus
  der Analyse ausgeschlossen (Gruppe `Ausgeschlossen`). Wir schlagen ihren
  vollständigen Ausschluss vor, weil sie weder als Treatment (kein 2011-Schock)
  noch als Kontrolle (nicht durchgehend am Netz) taugen.

### 3.4 Ergebnis

`data/processed/group_assignment.csv` enthält 17 Reaktoren mit den Spalten
`Reaktor, Gruppe, Fluss, Kühlungstyp, Stilllegungsjahr, Begründung`. Die
Gruppengrößen:

| Gruppe | n | Reaktoren |
|---|---|---|
| Treatment | 3 | Biblis A, Biblis B, Unterweser |
| Partial | 3 | Isar 1, Neckarwestheim 1, Philippsburg 1 |
| Kontrolle | 7 | Grohnde, Emsland, Brokdorf, Isar 2, Neckarwestheim 2, Philippsburg 2, Gundremmingen C |
| Gestaffeltes Treatment | 2 | Grafenrheinfeld (2015), Gundremmingen B (2017) |
| Ausgeschlossen | 2 | Krümmel, Brunsbüttel |

### 3.5 Kühlungstyp

Der Kühlungstyp ist in keinem der Rohdatensätze enthalten; er ist aber für die
Interpretation zentral, weil Anlagen mit **Durchlaufkühlung** (Frischwasser,
kein Kühlturm) ihre Abwärme direkt in den Fluss einleiten und daher ein
stärkeres, unmittelbar flussabwärts messbares Temperatursignal hinterlassen als
Anlagen mit **Kreislaufkühlung über Nasskühlturm**, die den Großteil der Abwärme
an die Luft abgeben. Wir haben den Kühlungstyp aus öffentlicher
Betreiber- und Behördendokumentation zusammengetragen (siehe Abschnitt 2):

- **Durchlaufkühlung (Frischwasser):** Unterweser, Brokdorf, Krümmel,
  Brunsbüttel, Isar 1 (mit ergänzenden Zellenkühlern).
- **Kreislaufkühlung (Nasskühlturm):** Biblis A/B, Neckarwestheim 1/2,
  Philippsburg 1/2, Grafenrheinfeld, Grohnde, Gundremmingen B/C, Emsland,
  Isar 2.

**Offene Annahme (Kühlungstyp):** Die Klassifikation stützt sich auf
Literaturangaben, nicht auf die Projektdaten. Sie ist für die eindeutig
belegten Fälle (Isar 1 vs. Isar 2, Brokdorf, Grohnde, Unterweser) gesichert; für
die übrigen Blöcke sollte sie vor der Veröffentlichung noch einmal gegen eine
Primärquelle (z. B. Sicherheitsberichte der Betreiber) geprüft werden.

---

## 4. Gefilterte Analyse-Ausgabedateien

Für jeden verfügbaren Datensatz erzeugen wir genau **eine** gefilterte Datei in
`data/processed/analysis/`. Alle Dateien sind auf **unsere Standorte** (die 15
Studienreaktoren ohne die ausgeschlossenen Anlagen Krümmel und Brunsbüttel) und
auf das **Fenster 2006–2018** beschränkt. Als räumliches Kriterium für „unsere
Standorte" verwenden wir einen Radius von **50 km** um einen Studienreaktor;
dieser Wert entspricht dem in `scripts/prepare_data.py` genutzten
Behandlungsradius. Jede Datei trägt in den führenden, mit `#` beginnenden
Kopfzeilen die vollständige Filterbeschreibung, so dass die Provenienz mit der
Datei mitwandert. Erzeugt werden die Dateien reproduzierbar durch
`scripts/build_group_assignment_and_filters.py`.

### 4.1 Wassertemperatur — `water_temperature_2006_2018_study_sites.csv`

- **Quelle:** `data/processed/water_temperature_de_annual_clean.csv`.
- **Filter 1 (Standort):** nur Messstellen innerhalb von 50 km zu einem
  Studienreaktor. Wir berechnen die Distanz jeder Messstelle zu allen 15
  Studienreaktoren (Haversine) und behalten die Stelle, wenn die kleinste
  Distanz ≤ 50 km ist. Der nächste Studienreaktor, seine Gruppe, sein Fluss und
  die Distanz werden als Zusatzspalten angehängt.
- **Filter 2 (Fenster):** nur Beobachtungsjahre 2006–2018.
- **Aggregationsentscheidung:** Es findet **keine weitere** Aggregation statt;
  die Waterbase-Quelle liegt bereits als **Jahreswert je Messstelle** vor
  (Mittel-, Minimal- und Maximalwert der Wassertemperatur). Wir übernehmen diese
  Jahresauflösung unverändert.
- **Datenlücken:** Die Waterbase liefert für unsere Stellen **keine** Werte für
  2006, 2007 und 2015; das Fenster materialisiert sich daher als 2008–2014 sowie
  2016–2018. Die Jahresabdeckung ist unausgewogen (wenige Stellen 2013/2014,
  viele 2018). Diese Lücke ist bei der Modellierung (z. B. durch Jahres-Fixed-
  Effects und stellenbezogene Gewichtung) zu berücksichtigen.

### 4.2 Gelöster Sauerstoff — `dissolved_oxygen_2006_2018_study_sites.PLACEHOLDER.csv`

- **Status:** **Platzhalter ohne Datenzeilen.** Für den gelösten Sauerstoff
  liegt im Repository **keine** Quelldatei vor. Der Determinand *Dissolved
  oxygen* stammt aus derselben EEA-Waterbase-Datei `T_WISE6_AggregatedData` wie
  die Wassertemperatur; diese Rohdatei ist wegen der GitHub-Größenbeschränkung
  nicht eingecheckt (siehe `.gitignore`, `Waterbase_v2020_1_*`).
- **Vorgesehener Filter (sobald die Rohdaten vorliegen):** identisch zur
  Wassertemperatur — Messstellen ≤ 50 km zu einem Studienreaktor, Jahre
  2006–2018, Jahreswerte je Stelle.
- **Zweck des Platzhalters:** Er fixiert das Zielschema und die Filterdefinition,
  so dass die Rohdaten später ohne Änderung der Pipeline eingespielt werden
  können. **Offener Punkt:** EEA-Waterbase v2020_1 herunterladen, den
  Determinand *Dissolved oxygen* extrahieren und durch dieselbe Filterfunktion
  laufen lassen.

### 4.3 Abfluss — `discharge_2006_2018_study_sites.PLACEHOLDER.csv`

- **Status:** **Platzhalter ohne Datenzeilen.** Für den Abfluss (Q in m³/s)
  liegt im Repository **überhaupt keine** Quelldatei vor.
- **Empfohlene Quelle:** deutsche Pegel-Abflussdaten, z. B. GRDC (Global Runoff
  Data Centre) oder BfG/PEGELONLINE, als Tages- oder Jahreswerte.
- **Vorgesehener Filter (sobald die Rohdaten vorliegen):** Pegel ≤ 50 km zu
  einem Studienreaktor, Jahre 2006–2018.
- **Begründung der Aufnahme:** Der Abfluss ist ein zentraler Kovariat, weil die
  flussbürtige Temperatur stark vom Wasserführungsvolumen abhängt und die
  Verdünnung der Wärmeeinleitung bestimmt. **Offener Punkt:** Pegel den
  Studienflüssen zuordnen und Abflussreihen beschaffen.

### 4.4 Wetter — `weather_2006_2018_study_sites.csv`

- **Quelle:** `data/processed/dwd_kl_daily_near_nuclear.csv` (DWD-Tageswerte:
  Mittel-/Min-/Max-Temperatur, Niederschlag, Windgeschwindigkeit).
- **Filter 1 (Standort):** nur Stationen ≤ 50 km zu einem Studienreaktor;
  nächster Reaktor, Gruppe und Distanz werden angehängt.
- **Filter 2 (Fenster):** nur Tage in 2006–2018.
- **Aggregationsentscheidung:** Wir aggregieren die über 100 000 Tageswerte je
  **Station und Kalendermonat** zu Monatskennwerten (Mittel-/Min-/Max-
  Lufttemperatur, Niederschlagssumme, mittlere Windgeschwindigkeit) und führen
  die Zahl der beobachteten Tage (`days_observed`) mit. Die Monatsauflösung
  entspricht der Auflösung der Zielgröße (Jahres-/Monatswerte der Wasser-
  temperatur), hält die Datei kompakt und lässt sich über `days_observed` weiter
  gewichten oder ausdünnen. Wer feiner rechnen will, kann die Tageswerte jederzeit
  über dasselbe Skript reproduzieren.
- **Abdeckungsgrenzen:** Der DWD-Tagesextrakt umfasst nur die Jahre **2005–2015**;
  das Fenster materialisiert sich daher als **2006–2015**. Für die Treatment-
  Seite ist **Biblis** durch Stationen der mittleren Rheinschiene abgedeckt,
  **Unterweser** hingegen **nicht** (keine Station innerhalb von 50 km im
  Extrakt). **Offener Punkt:** DWD-Tageswerte bis 2018 nachladen und eine Station
  nahe Unterweser ergänzen.

### 4.5 Kraftwerke — `power_plants_2006_2018_study_sites.csv`

- **Quelle:** `data/processed/conventional_plants_de_relevant_clean.csv`
  (konventionelle Wärmekraftwerke aus OPSD).
- **Filter 1 (Standort):** nur Kraftwerke ≤ 50 km zu einem Studienreaktor.
- **Filter 2 (Fenster):** nur Kraftwerke, deren Betriebszeit das Fenster
  überlappt (Inbetriebnahme spätestens 2018 und Stilllegung nicht vor 2006).
- **Zweck:** Diese thermischen Anlagen sind **potenzielle Störgrößen
  (Confounder)**: Ihre eigene Abwärmeeinleitung bzw. ihre An-/Abschaltungen im
  Fenster können die Wassertemperatur der Studienflüsse unabhängig vom Atom-
  Moratorium beeinflussen und sollten im Modell kontrolliert werden.
- **Abgrenzung:** Die **Kern**kraftwerke der Studie selbst sind nicht in dieser
  Datei, sondern vollständig in `data/processed/group_assignment.csv`
  dokumentiert; „die Kraftwerke" meint hier die konventionellen
  Confounder-Anlagen.

---

## 5. Zusammenfassung der Ausschluss- und Kennzeichnungsentscheidungen

| Einheit | Entscheidung | Begründung |
|---|---|---|
| Grafenrheinfeld | aus Kontrolle entfernt, als `Gestaffeltes Treatment` markiert | Stilllegung 2015 mitten im Fenster |
| Gundremmingen B | aus Kontrolle entfernt, als `Gestaffeltes Treatment` markiert | Stilllegung 2017 mitten im Fenster |
| Krümmel | vollständig ausgeschlossen | faktisch seit 2007/2009 vom Netz, kein 2011-Schock |
| Brunsbüttel | vollständig ausgeschlossen | faktisch seit 2007 vom Netz, kein 2011-Schock |
| Isar 2 / Neckarwestheim 2 / Philippsburg 2 | als Kontrolle geführt, aber Standort-Teilbehandlung 2011 vermerkt | Block lief durchgehend, Schwesterblock 2011 abgeschaltet |
| Wassertemperatur-Stellen > 50 km | herausgefiltert | außerhalb des räumlichen Studienbereichs |
| Wetterstationen (nur bis 2015; keine nahe Unterweser) | verbleibende genutzt, Lücke dokumentiert | Grenze des vorliegenden DWD-Extrakts |

---

## 6. Offene Annahmen und nächste Schritte

1. **Abrufdaten der Rohdaten** sind nicht protokolliert; Datenversionen sind
   dokumentiert, exakte Download-Daten werden nachgetragen (Abschnitt 2).
2. **Kühlungstyp** ist literaturbasiert; für die nicht eindeutig belegten Blöcke
   ist eine Primärquellenprüfung offen (Abschnitt 3.5).
3. **Gelöster Sauerstoff** und **Abfluss** liegen noch nicht als Rohdaten vor;
   Schema und Filter sind als Platzhalter fixiert (Abschnitte 4.2, 4.3).
4. **Zeitliche Abdeckung:** Wassertemperatur ohne 2006/2007/2015, Wetter nur bis
   2015. Vor der finalen Schätzung ist zu klären, ob die Reihen bis 2018
   vervollständigt werden können oder ob das Fenster angepasst wird.
5. **Modellierungsebene:** Reaktor- vs. Standortebene ist eine bewusste
   Designentscheidung (Abschnitt 3.2); die endgültige Wahl ist im Analyseteil zu
   fixieren und zu begründen.

---

## 7. Reproduzierbarkeit

Sämtliche in Abschnitt 3 und 4 beschriebenen Artefakte werden durch ein einziges
Skript erzeugt:

```
python scripts/build_group_assignment_and_filters.py
```

Das Skript nutzt ausschließlich die Python-Standardbibliothek (wie
`scripts/prepare_data.py`), liest die unter Abschnitt 2 genannten Dateien und
schreibt `data/processed/group_assignment.csv` sowie die Dateien in
`data/processed/analysis/`. Der 50-km-Radius und das Fenster 2006–2018 sind als
Konstanten `SITE_RADIUS_KM`, `WINDOW_START` und `WINDOW_END` am Kopf des Skripts
zentral einstellbar.

**Hinweis zu den versionierten Dateien.** Eingecheckt sind das Skript, diese
Dokumentation, `group_assignment.csv` sowie die kompakten Analyse-Dateien
`power_plants_2006_2018_study_sites.csv` und die beiden Platzhalter (gelöster
Sauerstoff, Abfluss). Die beiden größeren Tabellen
`water_temperature_2006_2018_study_sites.csv` (642 Zeilen) und
`weather_2006_2018_study_sites.csv` (3 379 Station-Monat-Zeilen) werden durch
den Aufruf des Skripts **deterministisch neu erzeugt**; ein einmaliger Lauf
stellt sie vollständig wieder her. In dieser Web-Session konnten sie nicht direkt
über die GitHub-API committet werden, weil der Git-Push-Pfad des Sandkastens
schreibgesperrt ist und die Dateien für die API-Übertragung zu groß sind – die
`analysis/README.md` verweist ausdrücklich darauf.
