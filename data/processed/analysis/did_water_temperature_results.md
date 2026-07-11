# DiD: 2011-Abschaltung und Wassertemperatur (Treatment vs. Control)

*Erster, explorativer Durchgang.*

## Kernbefund (ehrlich)
Mit den **jährlichen** Waterbase-Daten ist die Analyse **nicht belastbar**: Die Treatment-Gruppe hat nach 2011 praktisch nur die Jahre [2011, 2018] — eine echte Nachher-Periode fehlt, und der 2×2-/Event-Study-Schätzer wird von Kompositionswechseln (unterschiedliche Messstellen je Jahr) getrieben, nicht von einem Effekt. Für eine belastbare DiD brauchen wir **Waterbase Part 1 (Disaggregated)** — Einzelmessungen für ein dichtes, balanciertes Monats-/Saison-Panel.

## Datenabdeckung (Messstellen × Jahr, Anzahl Beobachtungen)

| Jahr | Control | Treatment |
|---|---|---|
| 2008 | 2 | 1 |
| 2009 | 2 | 1 |
| 2010 | 2 | 1 |
| 2011 | 2 | 1 |
| 2012 | 2 | 0 |
| 2016 | 1 | 0 |
| 2017 | 2 | 0 |
| 2018 | 7 | 6 |

## Stichprobe
- Treatment-Standorte (downstream ≤ 50 km): 6 Messstellen
- Control-Standorte (downstream ≤ 50 km): 7 Messstellen
- Beobachtungen (Messstelle × Jahr): 30
- Jahre: 2008–2018 (ohne 2006/2007/2015)
- Cluster (Messstellen): 13

## 2×2-Mittelwerte (°C)

| | vor 2011 | ab 2011 |
|---|---|---|
| Control | 11.06 | 11.71 |
| Treatment | 14.25 | 12.79 |

Roher 2×2-DiD: **-2.104 °C**

## Two-Way-Fixed-Effects (Messstellen- + Jahres-FE, SE geclustert je Messstelle)

- Treatment-Effekt (treated×post): **-0.089 °C**  (SE 0.236, p = 0.707)
- 95%-KI: [-0.552, +0.375] °C

## Event-Study (Referenz 2010)

| Jahr | Effekt (°C) | SE |
|---|---|---|
| 2008 | +0.640 | 1.039 |
| 2009 | -0.377 | 0.153 |
| 2010 | +0.000 | 0.000 |
| 2011 | +1.560 | 0.348 |
| 2012 | +0.000 | 0.000 |
| 2016 | +0.000 | 0.000 |
| 2017 | +0.000 | 0.000 |
| 2018 | -1.562 | 1.266 |

## Vorbehalte
- Sehr kleine Stichprobe und wenige Cluster → Standardfehler nur näherungsweise; p-Werte vorsichtig interpretieren (idealerweise Wild-Cluster-Bootstrap).
- Nur wenige Vorjahre (2008–2010) → Parallel-Trend-Annahme kaum testbar.
- Jahresmittel; der thermische Effekt ist im Sommer/Niedrigwasser am größten (Waterbase Part 1 nötig).
- Unterweser/Brokdorf sind tidebeeinflusst; Abfluss noch nicht als Kovariate drin.

Figuren: `figures/did_trends.png`, `figures/did_event_study.png`.