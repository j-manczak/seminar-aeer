# Anmerkungen zu den Abbildungen

Die Abbildungen in [`figures/`](figures/) tragen nur Beschriftungen und Zahlen.
Jede interpretierende Aussage steht hier — so lässt sich eine Bildunterschrift
ändern, ohne ein PNG neu zu rendern.

Je Abbildung gibt es eine **Caption (EN)** zum direkten Einfügen ins Paper und
darunter die längere Erklärung für uns.

Zahlen: Schnitt 06.08.2011, Fenster 2006-08-06 bis 2016-08-05, gepaarte
Tagesdifferenz mit Monats-FE und Newey-West HAC(30). Vollständig in
`DiD_summary.csv` und `DiD_robustness.csv`.

---

## `figures/Isar-1.png`

> **Caption (EN).** Isar 1, once-through cooling. The downstream–upstream
> temperature gap falls from +1.73 °C to −0.05 °C at the shutdown and stays flat
> for four more years; DiD −1.77 °C (95% CI [−2.03, −1.52]). A placebo cut-off in
> August 2008, using pre-period data only, yields +0.08 °C (p = 0.67). The Isar
> gauges carry no dissolved-oxygen series, so the oxygen channel cannot be
> estimated at the only site with a temperature effect.

Das ist unser Ergebnis. Die Größenordnung passt zur genehmigten Aufwärmspanne
von Isar 1 (bis 2,5 K). Robust über alle Spezifikationen: ohne Monats-FE −1,78,
Schnitt am Moratorium −1,90, Donut −1,92, Donut ±1 Jahr −2,09, mit beiden
Pegelständen als Kovariate unverändert −1,77.

**Zur Ereignisstudie:** das letzte Vorjahr (Referenzjahr, offener Punkt) liegt
schon bei +0,80 °C statt der +1,7 bis +2,4 °C der Jahre davor. Der Abfall beginnt
also vor August 2011 — Moratorium ab März 2011 plus die schon 2010 reduzierte
Verfügbarkeit von Isar 1. Deshalb ist der Donut-Wert (−2,09 °C) die ehrlichere
Zahl, nicht die Basisschätzung.

**Saisonalität:** Winter −2,08 °C, Sommer −1,19 °C. Beides signifikant. Für die
sommerfokussierte Forschungsfrage ist der Sommerwert die relevante Zahl.

---

## `figures/Neckarwestheim-1.png`

> **Caption (EN).** Neckarwestheim 1, wet cooling tower. DiD −0.35 °C
> (p = 0.011) for temperature and +0.27 mg/l (p = 0.067) for dissolved oxygen.
> Both estimates lie inside the drift band of the placebo pairs (±0.2 to ±0.8 °C
> and ±0.3 mg/l), and Lauffen covers only 27% of the pre-period, so neither is
> read as an effect.

Kein Widerspruch zum Mechanismus: ein Nasskühlturm gibt den Großteil der Abwärme
an die Luft ab, in den Neckar ging kaum etwas. Ein Nullbefund ist hier die
Erwartung.

Zwei Gründe, warum wir die −0,35 °C nicht als Effekt berichten:

* Lauffen beginnt erst am **16.03.2010**. Von der Vorperiode sind nur 492 Tage
  belegt, ein Placebo-Schnitt ist damit nicht rechenbar und Parallel-Trends nicht
  prüfbar. Der Donut ±1 Jahr drückt die Schätzung auf −0,17 °C (n.s.).
* Das Fernfeld Besigheim → Mannheim (72 km) liefert −0,38 °C, aber dort gibt der
  Placebo-Schnitt 2008 **−0,56 °C** — größer als der „Effekt". Das Paar driftet
  ohnehin in diese Richtung.

---

## `figures/Philippsburg-1.png`

> **Caption (EN).** Philippsburg 1. The pair is shown for comparability with
> earlier work but is **not identified**: station CYY003 measures the Neckar,
> while Philippsburg discharges into the Rhine, so Rhine water never reaches the
> downstream gauge. A placebo cut-off in 2008 gives −0.82 °C for the same pair,
> larger than the estimate itself.

Der Rhein fließt an Philippsburg vorbei nach Norden Richtung Mannheim; der Neckar
mündet dort in den Rhein. Wasser fließt also vom Neckar in den Rhein, nicht
umgekehrt. Die Abwärme von KKP 1 kann eine Neckar-Messstelle nicht erreichen.

In `demo-bavaria/results` lief dasselbe Paar als „Philippsburg 1" — das war ein
Flussverwechsler, den wir hier korrigieren. Um den Fall zu schätzen, bräuchten
wir eine Rhein-Messstelle unterhalb des Standorts (Mannheim-Rheinau, Speyer oder
Worms). Karlsruhe als Kontrolle oberhalb liegt bereits vor.

---

## `figures/Placebo-Gundremmingen-Danube.png`

> **Caption (EN).** Placebo on the Danube. Gundremmingen units B and C kept
> operating until end-2017 and end-2021, so no shutdown occurs in the 2006–2016
> window; anything this pair shows at the cut-off is drift. DiD −0.18 °C
> (p = 0.003).

Der Wert ist klein, aber „hochsignifikant" — das ist der eigentliche Punkt dieser
Abbildung. Bei 3 600 Tagesbeobachtungen wird auch reine Drift signifikant. Der
p-Wert ist deshalb nicht der Test; der Abstand zur Placebo-Bandbreite ist es.

---

## `figures/Placebo-Control-Karlsruhe-Besigheim.png`

> **Caption (EN).** Placebo control ↔ control. Both gauges lie upstream of their
> respective plant and are untreated, yet the paired difference shifts by
> +0.30 °C (p = 0.002) at the cut-off. This is the drift band of the method
> against which every estimate has to be judged.

Zwei unbehandelte Messstellen an zwei verschiedenen Flüssen. Weil sie nicht am
selben Fluss liegen, heißt die Größe hier „Difference" und nicht „Gap".

Beim Sauerstoff ist dieses Paar besonders aufschlussreich: im Sommerfenster
liefert es **+1,26 mg/l und +14,4 % Sättigung** — mehr als jeder Ausschlag, den
wir an einem Treatment-Paar messen. Damit ist der Sauerstoffkanal bei dieser
Auflösung nicht auflösbar.

---

## `figures/Overview-all-DiD.png`

> **Caption (EN).** All DiD estimates with 95% confidence intervals, one panel
> per unit. Treated pairs in orange, placebo and not-identified pairs in grey.
> Only Isar 1 sits clearly outside the placebo band; the Isar row is empty in
> both oxygen panels because the dataset holds no oxygen for that river.

Die leere Zeile ist Absicht — sie soll sichtbar machen, dass dort Daten fehlen,
statt die Zeile wegzulassen und den Eindruck zu erwecken, es sei gemessen und
null gewesen.

Faustregel zum Lesen:

| | Schätzung | Placebo-Bandbreite | Verhältnis |
|---|---:|---:|---:|
| Isar 1 (Durchlaufkühlung) | −1,8 bis −2,1 °C | ±0,3 °C | ≈ 6× |
| Neckarwestheim 1 (Kühlturm) | −0,35 bis −0,38 °C | ±0,6 °C | < 1 |
| Sauerstoff, alle Paare | +0,06 bis +0,27 mg/l | ±0,3 mg/l | ≤ 1 |

---

## `figures/Isar-1_stage-check.png`

> **Caption (EN).** Confounder check for Isar 1: the temperature gap breaks at
> the cut-off, the stage gap of the same two gauges does not (−0.6 cm,
> p = 0.46). Adding both stage levels as covariates leaves the temperature
> estimate unchanged at −1.77 °C.

Das ist das Argument gegen den Einwand, der Temperatureffekt sei eine verkappte
Abflussänderung. Es ist außerdem unser bestes Argument dafür, dass die an Neckar
und Rhein **fehlenden** Pegeldaten die Ergebnisse dort nicht tragen: dort, wo wir
die Kontrolle testen können, ändert sie nichts.

Zur Vorsicht: der Pegelvergleich ist nicht überall unauffällig — ein
Placebo-Schnitt 2008 gibt für die Pegel-Lücke −5,0 cm. Die Pegeldifferenz wandert
also über die Jahre, nur eben nicht am Schnitt.

---

## Zur Sauerstoffsättigung

Auf den Blättern mit Sauerstoff steht unter dem DiD zusätzlich die Sättigung in
Prozent. Sie ist der gemessene Sauerstoff geteilt durch den Gleichgewichtswert
bei der gleichzeitig gemessenen Temperatur (Benson-Krause,
`didlib.oxygen_saturation_mgl`).

Der Sinn: der reine Löslichkeitskanal — kälteres Wasser hält mehr O₂ — schlägt
sich in mg/l nieder, aber **nicht** in der Sättigung. Bewegt sich nur mg/l, ist es
Physik; bewegt sich auch die Sättigung, steckt mehr dahinter (Abfluss,
Algenproduktion, Einleitungen). Bei uns bewegt sich keines von beiden belastbar.

Zur Einordnung der Größenordnung: bei 14 °C und −1,8 K erwartet die
Löslichkeitsrechnung rund **+0,42 mg/l**. Das ist der Zielwert, gegen den eine
künftige Isar-Sauerstoffreihe zu prüfen wäre — und es liegt unter der Drift, die
unsere Placebo-Paare zeigen.

Die Stationshöhe würde die Sättigung um ein bis zwei Prozent skalieren. Weil
dieser Faktor je Messstelle konstant ist, fällt er aus der Vorher/Nachher-
Differenz heraus und wird deshalb bewusst nicht angewendet.
