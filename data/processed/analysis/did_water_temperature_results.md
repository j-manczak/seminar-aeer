# DiD: 2011-Abschaltung und Sommer-Wassertemperatur

*Quelle: Waterbase v2025_1 Einzelmessungen → Sommer (Jun–Sep) je Messstelle/Jahr, downstream ≤ 50 km, Fluss geometrisch zugeordnet.*

## Kernbefund
Mit den dichten Einzelmessungen ist die Abdeckung 2008–2024 durchgehend — aber sie ist **stark ungleich über die Gruppen verteilt**. Die sauberen **Treatment**- (Biblis, Unterweser) und **Control**-Reaktoren (Grohnde, Emsland, Brokdorf) sind downstream **kaum gemessen, besonders vor 2011**; die Abdeckung liegt bei **Partial** (Philippsburg, Neckarwestheim; 9 Stellen) und **Gestaffelt** (Grafenrheinfeld 2015, Gundremmingen 2017; 5 Stellen). Eine strikte Treatment-vs-Control-DiD für 2011 ist deshalb **nicht identifiziert** (die Control-Gruppe hat vor 2011 keine Beobachtung). Das gut abgedeckte Experiment sind die **Partial- und gestaffelten Abschaltungen**.

## Datenabdeckung (Messstellen je Gruppe × Jahr)

| Gruppe | 2008 | 2009 | 2010 | 2011 | 2012 | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Treatment | 1 | 1 | 1 | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 1 | 2 | 2 |
| Partial | 0 | 1 | 1 | 1 | 2 | 2 | 1 | 3 | 2 | 2 | 3 | 3 | 7 | 8 | 9 | 6 | 5 |
| Gestaffelt | 2 | 2 | 0 | 0 | 3 | 4 | 3 | 4 | 3 | 3 | 3 | 4 | 4 | 4 | 4 | 4 | 3 |
| Control | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1 | 1 | 2 | 3 | 4 | 4 | 3 | 3 |

Figur: `figures/did_coverage.png` (rote Linie = 2011).

## Versuch: Treatment vs. Control (2×2, Fenster 2008–2020)

Zellbesetzung (Beobachtungen):

| | vor 2011 | ab 2011 |
|---|---|---|
| Control | 0 | 9 |
| Treatment | 3 | 3 |

**Nicht schätzbar:** mindestens eine Zelle ist leer (keine Control-Vorperiode). Der 2×2-DiD ist für dieses Standort-Set nicht definiert.

## Empfehlung (welche DiD die Daten tragen)
1. **Gestaffelte / generalisierte DiD** über alle Abschaltungen: jede Downstream-Stelle wird ab dem Stilllegungsjahr ihres nächsten Oberlieger-AKW behandelt (2011 Partial/Treatment, 2015 Grafenrheinfeld, 2017 Gundremmingen); noch laufende Reaktoren sind die (noch-nicht-)Kontrollen. Nutzt die gesamte Abdeckung (Callaway–Sant'Anna gegen die TWFE-Verzerrung).
2. **Within-River downstream vs. upstream** je Abschaltung (upstream als Kontrolle desselben Flusses).
3. Abfluss als Kovariate/Intensität; Sommer-Fokus (hier schon) beibehalten.

## Vorbehalte
- Kleine, wachsende Stichprobe; Site- + Jahres-FE; wenige Cluster → SE nur näherungsweise.
- Tide-Standorte (Unterweser, Brokdorf) und Kompositionswechsel beachten.

Figuren: `figures/did_coverage.png`, `figures/did_trends.png`.