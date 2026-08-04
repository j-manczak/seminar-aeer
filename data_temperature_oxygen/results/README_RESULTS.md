# 2×2-DiD auf `data_temperature_oxygen/` — Abschaltungen 2011, ±5 Jahre

Dieselbe Analyse wie in [`demo-bavaria/results`](../../demo-bavaria/results/README_RESULTS.md),
aber auf den neuen Rohdaten, mit einem **Fenster von fünf Jahren vor und fünf
Jahren nach August 2011** und **beiden Zielgrößen, Temperatur und Sauerstoff**.

**Datenbasis: ausschließlich die Dateien in `data_temperature_oxygen/`.** Es wird
keine Messstelle von außerhalb dieses Ordners herangezogen. Wo der Ordner eine
Größe nicht hergibt, steht ein Hinweis statt einer Zahl (§ 5.2 und
`not_estimable.csv`).

*Analysedatum: 4. August 2026.*

---

## 1. Frage, Schnitt und Fenster

Die **13. AtG-Novelle trat am 6. August 2011 in Kraft** und entzog Isar 1,
Neckarwestheim 1 und Philippsburg 1 endgültig die Betriebsgenehmigung. Dieses
Datum ist der Schnitt. Das Fenster ist **2006-08-06 bis 2016-08-05**, also genau
fünf Jahre davor und fünf Jahre danach.

Die drei Blöcke gingen schon durch das **Moratorium am 14. März 2011** vom Netz.
Der März ist deshalb als alternativer Schnitt und die Monate dazwischen als Donut
mitgerechnet — beide stehen in `DiD_robustness.csv`.

## 2. Dateibenennung und Inhalt

Die Buchstaben im Dateinamen sagen, welche Parameter drinstehen:

| Buchstabe | Parameter | Einheit |
|---|---|---|
| `C` | Wassertemperatur | °C |
| `P` | Pegel / Wasserstand | cm |
| `O` | Sauerstoff | mg/l |

Jede Datei wurde einzeln geprüft und, wo nötig, umbenannt. **Keine Datei enthält
alle drei Größen**, es gibt also kein `_CPO`:

| Datei | Format | Enthält |
|---|---|---|
| `Landshut_Birket_2011-5_C.csv` | GKD Bayern | Wassertemperatur |
| `Landshut_Birket_2011-5_P.csv` | GKD Bayern | Wasserstand |
| `Landau_2011-5_C.csv` | GKD Bayern | Wassertemperatur |
| `Landau_2011-5_P.csv` | GKD Bayern | Wasserstand |
| `Donauworth_2011-5_C.csv` | GKD Bayern | Wassertemperatur |
| `Donauworth_2011-5_P.csv` | GKD Bayern | Wasserstand |
| `Neu_Ulm_2001-5_C.csv` | GKD Bayern | Wassertemperatur |
| `Besigheim-2011-5_CO.csv` | LUBW, Langformat | Temperatur **und** Sauerstoff |
| `Lauffen-2011-5_CO.csv` | LUBW, Langformat | Temperatur **und** Sauerstoff |
| `Mannheim-2011-5_CO.csv` | LUBW, Langformat | Temperatur **und** Sauerstoff |
| `Karlsruhe_2011-5_CO.csv` | LUBW, Langformat | Temperatur **und** Sauerstoff |

Umbenannt wurden `_CP → _CO` (Besigheim, Lauffen, Mannheim, Karlsruhe — die
LUBW-Dateien führen Sauerstoff, keinen Pegel) und `-C → _C` (Neu-Ulm, nur der
Trenner).

**Folge für das Design:** die bayerischen Pegel haben Temperatur und Pegel, aber
**keinen Sauerstoff**; die baden-württembergischen Gütemessstellen haben
Temperatur und Sauerstoff, aber **keinen Pegel**. Der Sauerstoffkanal ist damit
genau an dem Standort nicht messbar, an dem es einen Temperatureffekt gibt
(§ 7.2).

## 3. Spezifikation

Beide Pegel eines Paares liegen am selben Fluss und werden am selben Tag
gelesen. Die schärfste Schreibweise des 2×2 ist deshalb die **gepaarte
Tagesdifferenz** — dieselbe Spezifikation wie in
[`DATENAUDIT_UND_2x2.md`](../../data/processed/analysis/DATENAUDIT_UND_2x2.md):

```
Lücke_t = y_unterhalb,t − y_oberhalb,t
Lücke_t = a + b · post_t + Monatsdummies + e_t
```

`b` ist numerisch der DiD-Schätzer, entfernt aber Wetter, Saison und
flussweiten Trend vor der Schätzung. Standardfehler Newey-West (HAC),
Bandbreite 30 Tage.

Vier Zielgrößen:

* `temperature` — Tagesmittel der Wassertemperatur, °C
* `oxygen` — Tagesmittel gelöster Sauerstoff, mg/l
* `o2_saturation` — derselbe Sauerstoff als **Prozent des temperaturbedingten
  Gleichgewichtswerts** (Benson-Krause). Trennt den reinen Löslichkeitskanal
  (wärmeres Wasser hält weniger O₂) von allem anderen.
* `level` — Wasserstand, cm. Keine Zielgröße, sondern eine Kontrolle, dass die
  Hydrologie der beiden Pegel nicht auseinanderläuft.

## 4. Die Paare

| Fall | Block, Kühlung | oberhalb (Kontrolle) | unterhalb (Treatment) | Zielgrößen |
|---|---|---|---|---|
| **A1** | Isar 1, **Durchlaufkühlung** | Landshut-Birket (15 km) | Landau a.d. Isar (30 km) | Temp, Pegel |
| **B1** | Neckarwestheim 1, **Kühlturm** | Besigheim (5 km) | Lauffen (4 km) | Temp, O₂, O₂-Sätt. |
| B2 | Neckarwestheim 1, Fernfeld | Besigheim (5 km) | Mannheim (72 km) | Temp, O₂, O₂-Sätt. |
| **C1** | Philippsburg 1, hybrid | Karlsruhe, **Rhein** | Mannheim, **Neckar** | Temp, O₂, O₂-Sätt. |
| P1 | Placebo Donau | Neu-Ulm | Donauwörth | Temp |
| P2 | Placebo Kontrolle↔Kontrolle | Karlsruhe (Rhein) | Besigheim (Neckar) | Temp, O₂, O₂-Sätt. |

Entfernungen sind Luftlinie zum Kraftwerk (`station_pairs.csv`, dort steht auch
je Messstelle, aus welcher Datei sie kommt).

### Zwei Paare, die keine sind — bitte vor dem Zitieren lesen

**C1 ist kein Oberlauf/Unterlauf-Paar.** Die LUBW-Station `CYY003` heißt
„Mannheim, **Neckar**" und misst den Neckar kurz vor der Mündung. Philippsburg
liegt am **Rhein**, rheinaufwärts von Mannheim. Rheinwasser fließt nicht in den
Neckar — die Abwärme von KKP 1 kann diese Messstelle also gar nicht erreichen.
In `demo-bavaria/results` wurde dasselbe Paar als „Philippsburg 1" geführt; das
war ein Flussverwechsler. Der Fall ist hier als `not_identified` markiert und
wird nur mitgerechnet, damit der Vergleich zur alten Auswertung möglich bleibt.

**P1 ist ein echter Placebo.** Gundremmingen B lief bis Ende 2017, Block C bis
Ende 2021 — im Fenster 2006–2016 gab es an der Donau **keine** Abschaltung. Was
dieses Paar am 6.8.2011 zeigt, ist per Konstruktion Drift.

---

## 5. Abdeckung und Lücken

### 5.1 Zeitliche Abdeckung

Vollständig in `data_coverage.csv`. Die zwei Stellen, an denen es klemmt:

* **Lauffen** (B1) beginnt erst am **16.03.2010**. Von den fünf Vorjahren sind
  nur **492 Tage (27 %)** belegt, gegen 1 716 Tage danach. Parallel-Trends ist
  damit nicht prüfbar, ein Placebo-Schnitt in der Vorperiode nicht rechenbar.
* **Landau** (A1) beginnt am 16.05.2007 — 83 % der Vorperiode, gut genug.

Alle übrigen Paare decken beide Hälften zu über 90 % ab.

### 5.2 Was der Ordner nicht hergibt

Maschinenlesbar in `not_estimable.csv`.

| Fall | fehlende Zielgröße | Grund |
|---|---|---|
| **A1 Isar 1** | **Sauerstoff, O₂-Sättigung** | Landshut-Birket und Landau liegen nur als `_C` und `_P` vor. Ohne `_O`-Datei für beide Pegel ist der Sauerstoffkanal am **einzigen Standort mit Durchlaufkühlung** nicht schätzbar. |
| B1, B2, C1, P2 | Pegel | Die LUBW-Dateien sind `_CO`, es gibt keine Pegelreihe. Für alle Neckar- und Rheinpaare fehlt die Abflusskontrolle. |
| P1 Donau | Pegel | Neu-Ulm hat keine `_P`-Datei, also kein Pegelpaar an der Donau (Donauwörth allein reicht nicht). |

Damit bleibt die Sauerstofffrage für Isar 1 **offen**. Beantwortbar wäre sie mit
einer `_O`-Reihe für zwei Isar-Messstellen ober- und unterhalb von Ohu.

---

## 6. Hauptergebnisse

Schnitt 06.08.2011, Monats-FE, Newey-West. Vollständig in `DiD_summary.csv`,
alle Spezifikationen in `DiD_robustness.csv`, Abbildung
`figures/Overview-all-DiD.png`.

### Temperatur

| Fall | Lücke vorher | Lücke nachher | **DiD** | 95 %-KI | p | Placebo-Schnitt 2008 |
|---|---:|---:|---:|---|---:|---:|
| **A1 Isar 1 → Landau** | **+1,73 °C** | **−0,05 °C** | **−1,77 °C** | [−2,03; −1,52] | <0,0001 | **+0,08 (n.s.)** |
| B1 GKN 1 → Lauffen | +0,44 | +0,11 | −0,35 | [−0,62; −0,08] | 0,011 | nicht rechenbar |
| B2 GKN 1 → Mannheim | +0,70 | +0,31 | −0,38 | [−0,52; −0,23] | <0,0001 | **−0,56** |
| C1 KKP 1 → Mannheim *(n.i.)* | −0,17 | −0,27 | −0,08 | [−0,30; +0,14] | 0,46 | **−0,82** |
| P1 Placebo Donau | +1,06 | +0,88 | −0,18 | [−0,29; −0,06] | 0,003 | −0,30 |
| P2 Placebo Karlsruhe→Besigheim | −0,86 | −0,57 | +0,30 | [+0,11; +0,49] | 0,002 | −0,25 |

### Sauerstoff und Sättigung

Nur an den vier `_CO`-Messstellen — an der Isar gibt es keine Sauerstoffreihe.

| Fall | O₂ DiD [mg/l] | p | Placebo 2008 | Sättigung DiD [%] | p | Placebo 2008 |
|---|---:|---:|---:|---:|---:|---:|
| B1 GKN 1 → Lauffen | +0,27 | 0,067 | nicht rechenbar | +1,70 | 0,30 | nicht rechenbar |
| B2 GKN 1 → Mannheim | +0,06 | 0,76 | +0,11 | −0,58 | 0,78 | −0,02 |
| C1 KKP 1 → Mannheim *(n.i.)* | +0,18 | 0,29 | +0,27 | +1,96 | 0,28 | +0,83 |
| P2 Placebo Karlsruhe→Besigheim | +0,11 | 0,65 | +0,16 | +2,29 | 0,35 | +0,83 |

---

## 7. Interpretation

### 7.1 Isar 1 ist das Ergebnis — und jetzt über zehn Jahre

Die Lücke Landau − Landshut-Birket liegt 2007–2010 stabil bei **+1,7 bis
+2,4 °C** und ab 2012 bei **null**, mit flacher Nachperiode über vier weitere
Jahre (`figures/Isar-1.png`, mittleres Panel links). Die Größenordnung passt zur
genehmigten Aufwärmspanne von Isar 1 (bis 2,5 K bei Durchlaufkühlung).

Robust in jede Richtung:

| Spezifikation | DiD |
|---|---:|
| Basis (Schnitt 06.08.2011) | −1,77 °C |
| ohne Monats-FE (klassisches 2×2) | −1,78 °C |
| Schnitt am Moratorium (14.03.2011) | −1,90 °C |
| Donut: Übergangsmonate raus | −1,92 °C |
| Donut: ±1 Jahr raus | **−2,09 °C** |
| mit Wasserstand beider Pegel als Kovariate | −1,77 °C |
| **Placebo-Schnitt 06.08.2008 (nur Vorperiode)** | **+0,08 °C (p = 0,67)** |

Das ist konsistent mit dem ±3-Jahres-Ergebnis des Repos (−1,93 °C); das breitere
Fenster ändert die Zahl kaum und macht die Nachperiode deutlich belastbarer.

**Die Sprungstelle liegt trotzdem nicht sauber im August 2011.** Die
Ereignisstudie zeigt für das letzte Vorjahr (Aug 2010 – Aug 2011) schon **+0,80 °C**
statt der +1,7 bis +2,4 °C der Jahre davor. Zwei Gründe, beide bekannt: das
Moratorium ab März 2011, und die schon 2010 reduzierte Verfügbarkeit von Isar 1.
Die Donut-Spezifikation ist deshalb die ehrlichere Zahl — sie ist mit −2,09 °C
etwas **größer**.

**Der Effekt ist im Winter größer als im Sommer** (−2,08 gegen −1,19 °C). Das
ist mit dem Mechanismus vereinbar: die zulässige Aufwärmung war im Sommer
gedeckelt, die Anlage musste bei warmer Isar drosseln — im Winter ging die volle
Abwärme in den Fluss.

**Der Wasserstand bestätigt das Paar.** Die Pegel-Lücke ändert sich am Schnitt
nur um −0,6 cm (p = 0,46), und die Temperaturschätzung ändert sich in der dritten
Nachkommastelle, wenn man beide Pegelstände als Kovariaten aufnimmt
(`figures/Isar-1_stage-check.png`: links ein Sprung, rechts keiner). Der
Temperatureffekt ist keine verkappte Abflussänderung.

### 7.2 Sauerstoff: an der Isar nicht messbar, am Neckar und Rhein null

**Die interessante Frage lässt sich mit diesem Ordner nicht beantworten.** Isar 1
ist der einzige Standort mit Durchlaufkühlung und der einzige mit einem
Temperatureffekt — und genau dort gibt es nur `_C` und `_P`, keinen Sauerstoff.
Ob die −1,8 K Abkühlung zu mehr gelöstem Sauerstoff geführt haben, ist offen.

Zur Einordnung, was man suchen müsste: die Löslichkeitsrechnung
(`didlib.oxygen_saturation_mgl`) gibt bei 14 °C und −1,8 K rund **+0,42 mg/l**
her. Das ist die Größenordnung, gegen die eine künftige Isar-Sauerstoffreihe
geprüft werden müsste.

Dort, wo der Ordner Sauerstoff hat — Neckar und Rhein —, **gibt es keinen
belastbaren Effekt**:

* B1 (Lauffen, nah): +0,27 mg/l, p = 0,067; Sättigung +1,70 %, p = 0,30. Der
  Placebo-Schnitt ist mangels Vorperiode nicht rechenbar.
* B2 (Mannheim, fern): +0,06 mg/l, p = 0,76. Der größte Ausschlag steht im
  Sommer (−0,90 mg/l; −10,6 % Sättigung) — aber das reine Kontrollpaar P2
  liefert im selben Sommerfenster **+1,26 mg/l und +14,4 %**. Der Rauschpegel
  ist größer als jeder gemessene „Effekt".
* P2 (Kontrolle↔Kontrolle): +0,11 mg/l, p = 0,65 — die Nulllinie, wie erwartet.

Das ist auch physikalisch plausibel: Neckarwestheim 1 hatte einen Kühlturm, gab
also kaum Wärme in den Fluss, und der zugehörige Temperatureffekt (§ 7.3) liegt
selbst im Rauschen. Sauerstoff im Fluss wird von Abfluss, Algenproduktion,
Kläranlagen und Wetter stärker bewegt als von wenigen Zehntel Kelvin.

### 7.3 Neckarwestheim: kein Effekt, und das war zu erwarten

B1 liefert −0,35 °C (p = 0,011), B2 −0,38 °C (p < 0,0001). Beides ist **nicht als
Effekt zu lesen**:

* Der Placebo-Schnitt 2008 gibt für B2 **−0,56 °C** — größer als der „Effekt".
  Das Paar Besigheim↔Mannheim driftet also ohnehin in diese Richtung.
* Für B1 ist der Placebo mangels Vorperiode gar nicht rechenbar; der Donut ±1 Jahr
  drückt die Schätzung auf −0,17 °C (n.s.).
* Die reinen Kontrollpaare P1 und P2 liefern −0,18 und +0,30 °C — bei
  3 600 Tagesbeobachtungen beide „signifikant". **Die Driftbandbreite dieser
  Paare ist ±0,2 bis ±0,8 °C, und die Neckarwestheim-Schätzungen liegen darin.**

Inhaltlich ist das kein Gegenbeweis: Neckarwestheim 1 hatte einen **Nasskühlturm**
und gab kaum Wärme in den Neckar. Ein Nullbefund ist dort die Erwartung.

### 7.4 Philippsburg 1 bleibt offen

Mit dem vorliegenden Stationssatz gibt es keine Rhein-Messstelle **unterhalb**
von Philippsburg. Karlsruhe liegt rheinaufwärts (also richtig als Kontrolle),
aber der Partner Mannheim misst den Neckar. Der Fall ist nicht identifiziert; die
−0,08 °C sind bedeutungslos, und der Placebo-Schnitt 2008 gibt für dasselbe Paar
−0,82 °C.

### 7.5 Wie man diese Tabelle liest

Bei 3 600 Tagesbeobachtungen wird auch eine Drift von 0,2 °C „hoch signifikant".
**Der p-Wert ist hier nicht der Test.** Der Test ist der Abstand zur
Placebo-Bandbreite:

| | Effektschätzung | Placebo-Bandbreite | Verhältnis |
|---|---:|---:|---:|
| Isar 1 (Durchlauf) | −1,8 bis −2,1 °C | ±0,3 °C | **≈ 6×** |
| Neckarwestheim 1 (Kühlturm) | −0,35 bis −0,38 °C | ±0,6 °C | < 1 |
| Sauerstoff, alle Paare | +0,06 bis +0,27 mg/l | ±0,3 mg/l | ≤ 1 |

Nur die erste Zeile ist ein Ergebnis.

---

## 8. Dateien

| Datei | Inhalt |
|---|---|
| `didlib.py` | Lader für beide Rohformate, Sättigungsrechnung, Schätzer |
| `did_analysis.py` | Fallkonfiguration, alle Spezifikationen, schreibt die CSVs |
| `make_figures.py` | Abbildungen |
| `run_log.txt` | vollständige Konsolenausgabe des letzten Laufs |
| [`FIGURE_NOTES.md`](FIGURE_NOTES.md) | Interpretation je Abbildung, mit fertiger englischer Bildunterschrift |
| `DiD_summary.csv` | Basisspezifikation je Fall und Zielgröße, mit 2×2-Zellmitteln |
| `DiD_robustness.csv` | alle neun Spezifikationen je Fall und Zielgröße |
| `event_study.csv` | Jahresbins mit KI, Referenzjahr −1 |
| `data_coverage.csv` | gepaarte Tage, Abdeckung vor/nach dem Schnitt |
| `not_estimable.csv` | Fall-Zielgröße-Kombinationen, die der Ordner nicht hergibt, mit Grund |
| `station_pairs.csv` | Rolle, Fluss, Quelle, Koordinaten, Entfernung, **Quelldatei** |
| `figures/Isar-1.png` | **ein Blatt je Anlage, Beschriftung englisch**: links Temperatur, rechts Sauerstoff, je mit DiD, Lücke und Ereignisstudie |
| `figures/Neckarwestheim-1.png` | dasselbe für Neckarwestheim 1 |
| `figures/Philippsburg-1.png` | dasselbe für Philippsburg 1, als nicht identifiziert gekennzeichnet |
| `figures/Placebo-Gundremmingen-Danube.png` | Placebo Donau — Gundremmingen lief im Fenster weiter |
| `figures/Placebo-Control-Karlsruhe-Besigheim.png` | Placebo Kontrolle ↔ Kontrolle |
| `figures/Overview-all-DiD.png` | alle Schätzer mit 95 %-KI, ein Panel je Einheit |
| `figures/Isar-1_stage-check.png` | Temperatursprung gegen ausbleibenden Pegelsprung |

Reproduzieren:

```bash
cd data_temperature_oxygen/results
python did_analysis.py
python make_figures.py
```

---

## 9. Was fehlt

Alles hier ist eine Aussage darüber, welche **Dateien im Ordner** fehlen — nicht
über Daten, die woanders gesucht werden sollten.

1. **Sauerstoff an der Isar.** Zwei `_O`-Reihen ober- und unterhalb von Ohu
   würden den einzigen Fall mit echtem Temperatureffekt auf den zweiten Kanal
   ausdehnen. Das ist die größte Lücke.
2. **Eine Rhein-Messstelle unterhalb von Philippsburg.** Dann wäre KKP 1 —
   hybride Kühlung, mittlere Wärmelast — der zweite schätzbare 2011-Fall.
   Karlsruhe als Kontrolle liegt schon vor.
3. **Lauffen vor März 2010.** Ohne Vorperiode ist B1 nicht prüfbar.
4. **Pegel für die Neckar- und Rheinpaare.** Die `_CO`-Dateien haben keinen
   Wasserstand; die Abflusskontrolle, die den Isar-Fall absichert, fehlt dort.

---

**Datenquellen:** Bayerisches Landesamt für Umwelt (GKD Bayern, `gkd.bayern.de`)
und Landesanstalt für Umwelt Baden-Württemberg (LUBW). Abfragedaten laut
Dateikopf 3.–4. August 2026.
