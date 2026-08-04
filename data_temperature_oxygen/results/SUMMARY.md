# Kurzfassung — 2×2 DiD, Abschaltungen 2011, ±5 Jahre

Schnitt **06.08.2011** (13. AtG-Novelle), Fenster **2006-08-06 bis 2016-08-05**.
Gepaarte Tagesdifferenz unterhalb − oberhalb, Monats-FE, Newey-West.
Datenbasis ausschließlich `data_temperature_oxygen/`.
Details: [`README_RESULTS.md`](README_RESULTS.md).

---

## Dateibenennung

`C` = Wassertemperatur, `P` = Pegel, `O` = Sauerstoff. Jede Datei geprüft,
**keine enthält alle drei** — kein `_CPO`. Umbenannt: die vier LUBW-Dateien von
`_CP` auf **`_CO`** (sie führen Sauerstoff, keinen Pegel), Neu-Ulm von `-C` auf
`_C`.

Daraus folgt die zentrale Einschränkung: **Bayern hat C + P, Baden-Württemberg
hat C + O.** Sauerstoff gibt es also nur am Neckar und Rhein — und dort nur an
Standorten mit Kühlturm.

---

## Ein Ergebnis, ein Nullbefund, eine offene Frage

| | DiD | Placebo-Bandbreite | Urteil |
|---|---:|---:|---|
| **Isar 1** — Durchlaufkühlung, Landshut-Birket → Landau | **−1,77 °C** (Donut −2,09) | ±0,3 °C | **Effekt** |
| **Neckarwestheim 1** — Kühlturm, Besigheim → Lauffen | −0,35 °C | ±0,6 °C | im Rauschen |
| **Sauerstoff** — Neckar und Rhein | +0,06 bis +0,27 mg/l | ±0,3 mg/l | im Rauschen |
| **Sauerstoff** — Isar | — | — | **keine Daten im Ordner** |
| **Philippsburg 1** | — | — | nicht identifiziert |

---

## 1. Isar 1: −1,77 °C, robust

Die Temperaturlücke Landau − Landshut-Birket:

* vorher **+1,73 °C**, nachher **−0,05 °C** → **DiD −1,77 °C**, 95 %-KI [−2,03; −1,52]
* Donut (Übergangsmonate raus): −1,92 · Donut ±1 Jahr: **−2,09** · Moratoriumsschnitt: −1,90
* **Placebo-Schnitt 2008: +0,08 °C (p = 0,67)**
* mit Wasserstand beider Pegel kontrolliert: unverändert −1,77
* Winter −2,08, Sommer −1,19 (im Sommer war die zulässige Aufwärmung gedeckelt)

Passt zur genehmigten Aufwärmspanne von Isar 1 (bis 2,5 K) und bestätigt das
±3-Jahres-Ergebnis des Repos (−1,93 °C) auf dem doppelten Fenster.

⚠️ Der Abfall beginnt schon vor August 2011 — das letzte Vorjahr liegt bei
+0,80 statt +1,7…+2,4 °C. Moratorium ab März 2011 plus die reduzierte
Verfügbarkeit von Isar 1 ab 2010. Deshalb ist der Donut-Wert die ehrlichere Zahl.

## 2. Sauerstoff: an der Isar nicht messbar, sonst null

**Die interessante Frage lässt sich mit diesem Ordner nicht beantworten.**
Landshut-Birket und Landau liegen nur als `_C` und `_P` vor. Ausgerechnet am
einzigen Standort mit Durchlaufkühlung und echtem Temperatureffekt fehlt der
Sauerstoff. Zur Einordnung: bei 14 °C und −1,8 K erwartet die
Löslichkeitsrechnung rund **+0,42 mg/l** — das wäre der Zielwert einer künftigen
Isar-`_O`-Reihe.

Wo der Ordner Sauerstoff hat (Neckar, Rhein), zeigt sich nichts: +0,27 mg/l bei
Lauffen (p = 0,067), +0,06 bei Mannheim (p = 0,76), +0,11 beim reinen
Kontrollpaar. Der größte Ausschlag (B2 Sommer, −0,90 mg/l) ist kleiner als das,
was das Kontrollpaar im selben Fenster produziert (+1,26 mg/l). Passt zum
Mechanismus — dort standen Kühltürme, es ging kaum Wärme in den Fluss.

## 3. Neckarwestheim 1: null, wie erwartet

−0,35 °C nah (Lauffen), −0,38 °C fern (Mannheim). Der Placebo-Schnitt 2008 gibt
für das Fernpaar **−0,56 °C** — größer als der „Effekt". Nasskühlturm: es ging
kaum Wärme in den Neckar. Dazu beginnt Lauffen erst im **März 2010**, es sind nur
**27 % der Vorperiode** belegt.

## 4. Philippsburg 1 ist nicht identifiziert

Die Station „Mannheim, Neckar (CYY003)" liegt am **Neckar**, Philippsburg am
**Rhein**. Rheinwasser fließt nicht in den Neckar — dieses Paar kann die Abwärme
von KKP 1 nicht sehen. In `demo-bavaria/results` lief dasselbe Paar als
„Philippsburg 1"; das war ein Flussverwechsler. Für den Fall fehlt eine
Rhein-Messstelle unterhalb des Standorts.

## 5. Die Placebos setzen den Maßstab

| Placebo | DiD Temperatur | p |
|---|---:|---:|
| Donau Neu-Ulm → Donauwörth (Gundremmingen lief weiter) | −0,18 °C | 0,003 |
| Karlsruhe → Besigheim (beide Pegel unbehandelt) | +0,30 °C | 0,002 |

Beide „signifikant" — bei 3 600 Tagesbeobachtungen wird jede Drift signifikant.
**Der p-Wert ist nicht der Test, der Abstand zur Placebo-Bandbreite ist es.**
Isar 1 liegt rund sechsmal darüber, alles andere darin.

---

## Was dem Ordner fehlt

1. **`_O` für zwei Isar-Messstellen** ober- und unterhalb von Ohu — die größte Lücke.
2. **Eine Rhein-Messstelle unterhalb von Philippsburg** (Karlsruhe als Kontrolle liegt vor).
3. **Lauffen vor März 2010.**
4. **Pegel für die Neckar-/Rheinpaare** — die `_CO`-Dateien haben keinen Wasserstand.

Siehe `not_estimable.csv`.

---

## Abbildungen

Ein Blatt je Anlage, benannt nach der Anlage. Jedes Blatt stellt **links die
Temperatur, rechts den Sauerstoff** nebeneinander, mit dem DiD-Ergebnis über
jeder Spalte, darunter Messstellenvergleich, Lücke und Ereignisstudie.

Die Beschriftung ist **englisch** (die Abbildungen gehen ins Paper). Die
Abbildungen tragen nur Beschriftungen und Zahlen — jede interpretierende Aussage
steht in [`FIGURE_NOTES.md`](FIGURE_NOTES.md), dort jeweils mit fertiger
englischer Bildunterschrift.

| Datei | Zeigt |
|---|---|
| `figures/Isar-1.png` | Isar 1 — der einzige Effekt; Sauerstoffspalte erklärt, warum sie leer ist |
| `figures/Neckarwestheim-1.png` | Neckarwestheim 1 — Temperatur und Sauerstoff, beides im Rauschen |
| `figures/Philippsburg-1.png` | Philippsburg 1 — als nicht identifiziert gekennzeichnet |
| `figures/Placebo-Gundremmingen-Danube.png` | Placebo Donau |
| `figures/Placebo-Control-Karlsruhe-Besigheim.png` | Placebo Kontrolle ↔ Kontrolle |
| `figures/Overview-all-DiD.png` | alle Schätzer mit 95 %-KI, je ein Panel für °C, mg/l, % |
| `figures/Isar-1_stage-check.png` | Temperatursprung gegen ausbleibenden Pegelsprung |

Reproduzieren: `python did_analysis.py && python make_figures.py` im Ordner
`data_temperature_oxygen/results`.
