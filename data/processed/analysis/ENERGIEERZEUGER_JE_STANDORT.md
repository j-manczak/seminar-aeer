# Energieerzeuger am Fluss je Kernkraftwerksstandort

*Erzeugt von `scripts/site_energy_context.py`. Alle Entfernungen sind*
***Flusskilometer entlang des Laufs***, *nicht Luftlinie — berechnet auf dem*
*HydroRIVERS-Netz (siehe METHODS.md §4.7).*

Aufgenommen sind alle Anlagen ab 10 MW auf demselben Fluss innerhalb von 50 km entlang des Laufs vom Kernkraftwerk; wo ein Messpegel weiter entfernt liegt, wird der Radius auf die gesamte Messstrecke erweitert. Kernkraftwerke selbst sind ausgenommen.

**Kühlwasserspalte:** eine Einschätzung aus der Technologie, keine Genehmigungsauskunft. Dampfturbine und GuD haben einen Kondensator und brauchen eine Wärmesenke; offene Gasturbinen und Wasserkraft nicht.

**Was für das 2×2 zählt:** nur Anlagen *zwischen* den beiden Messstellen (`zwischen den Pegeln = ja`) sitzen in der behandelten Strecke. Alles oberhalb der Kontrollmessstelle wärmt beide Pegel gleich und fällt aus der Differenz.

Vollständige Daten: `plant_2x2/energy_producers_by_site.csv`. Karten: `figures/site_context/`.

## Biblis (Rhein)

**Kernkraftwerk:** 49.7094° N, 8.4147° O · Fluss-km 496.2 · Abschaltung 2011

**Bezugspegel:** upstream `MANNHEIM RHEIN`, downstream `—` *(kein schätzbares Paar — nächste verfügbare Pegel)*

| Erzeuger | Ort | Koordinaten | km zum AKW | Lage zum AKW | km zu UP | Lage zu UP | km zu DOWN | Lage zu DOWN | zwischen den Pegeln | Erzeugungsart | MW | Flusskühlwasser |
|---|---|---|---:|---|---:|---|---:|---|:---:|---|---:|---|
| GKM (Block 3) | Mannheim | 49.44569, 8.49044 | 39.8 | upstream | 8.5 | upstream |  |  | nein | Steam turbine (Hard coal), KWK | 202.5 | ja |
| GKM (Block 4) | Mannheim | 49.44569, 8.49044 | 39.8 | upstream | 8.5 | upstream |  |  | nein | Steam turbine (Hard coal), KWK | 202.5 | ja |
| GKM (Block 6) | Mannheim | 49.44569, 8.49044 | 39.8 | upstream | 8.5 | upstream |  |  | nein | Steam turbine (Hard coal), KWK | 255.0 | ja |
| GKM (Block 7) | Mannheim | 49.44569, 8.49044 | 39.8 | upstream | 8.5 | upstream |  |  | nein | Steam turbine (Hard coal), KWK | 425.0 | ja |
| GKM (Block 8) | Mannheim | 49.44569, 8.49044 | 39.8 | upstream | 8.5 | upstream |  |  | nein | Steam turbine (Hard coal), KWK | 435.0 | ja |
| GKM (Block 9) | Mannheim | 49.44569, 8.49044 | 39.8 | upstream | 8.5 | upstream |  |  | nein | Steam turbine (Hard coal), KWK | 843.0 | ja |
| BHKW Ludwigshafen (BHKW ) | Ludwigshafen | 49.45308, 8.43364 | 35.8 | upstream | 4.5 | upstream |  |  | nein | Steam turbine (Natural gas), KWK | 12.5 | ja |
| Industriekraftwerk Ludwigshafen (GuD) | Ludwigshafen | 49.45318, 8.43359 | 35.8 | upstream | 4.5 | upstream |  |  | nein | Combined cycle (Natural gas), KWK | 12.0 | ja |
| FHKW Ludwigshafen (FHKW) | Ludwigshafen | 49.48505, 8.42622 | 30.1 | upstream | 1.3 | downstream |  |  | nein | Steam turbine (Waste), KWK | 28.0 | ja |
| KW Mitte (GT 1) | Ludwigshafen | 49.51395, 8.43151 | 27.4 | upstream | 3.9 | downstream |  |  | nein | Gas turbine (Natural gas), KWK | 47.0 | nein |
| Kraftwerk Mitte (GUD A 800  GT 11, GT 12, DT 10) | Ludwigshafen | 49.51373, 8.43156 | 27.4 | upstream | 3.9 | downstream |  |  | nein | Combined cycle (Natural gas), KWK | 497.5 | ja |
| Kraftwerk Süd (GUD C 200 GT 1, GT 2, DT 1) | Ludwigshafen | 49.51362, 8.4316 | 27.4 | upstream | 3.9 | downstream |  |  | nein | Combined cycle (Natural gas), KWK | 410.0 | ja |
| HKW Mannheim (Turbine 60) | Mannheim | 49.5224, 8.45294 | 27.0 | upstream | 4.3 | downstream |  |  | nein | Steam turbine (Waste), KWK | 22.1 | ja |
| SCA Mannheim (SCA Mannheim) | Mannheim | 49.5349, 8.46358 | 26.0 | upstream | 5.3 | downstream |  |  | nein | Steam turbine (Biomass and biogas), KWK | 40.0 | ja |
| Co-Generation (-) | Worms | 49.66328, 8.35894 | 8.7 | upstream | 22.6 | downstream |  |  | nein | Steam turbine (Natural gas), KWK | 11.5 | ja |
| Kraftwerk Mainz (KW2) | Mainz | 50.0252, 8.24292 | 47.1 | downstream | 78.5 | downstream |  |  | nein | Combined cycle (Natural gas), KWK | 335.0 | ja |
| MHKW Mainz | Mainz | 50.02594, 8.24183 | 47.3 | downstream | 78.6 | downstream |  |  | nein | Steam turbine (Waste), KWK | 15.6 | ja |
| Kraftwerk Mainz (KW3) | Mainz | 50.02643, 8.23794 | 47.4 | downstream | 78.8 | downstream |  |  | nein | Combined cycle (Natural gas), KWK | 434.2 | ja |
| Biomasseheizkraftwerk Wiesbaden | Wiesbaden | 50.04213, 8.26116 | 48.0 | downstream | 79.3 | downstream |  |  | nein | Steam turbine (Waste), KWK | 10.5 | ja |
| Wi-Biebrich (Block 1) | Wiesbaden | 50.04055, 8.25325 | 48.2 | downstream | 79.5 | downstream |  |  | nein | Steam turbine (Natural gas), KWK | 25.0 | ja |

## Brokdorf (Elbe)

**Kernkraftwerk:** 53.8511° N, 9.3459° O · Fluss-km 46.7 · Abschaltung 2021

**Bezugspegel:** upstream `FLUSS`, downstream `—` *(kein schätzbares Paar — nächste verfügbare Pegel)*

| Erzeuger | Ort | Koordinaten | km zum AKW | Lage zum AKW | km zu UP | Lage zu UP | km zu DOWN | Lage zu DOWN | zwischen den Pegeln | Erzeugungsart | MW | Flusskühlwasser |
|---|---|---|---:|---|---:|---|---:|---|:---:|---|---:|---|
| Wedel (GT A) | Wedel | 53.56625, 9.72848 | 43.4 | upstream | 10.4 | downstream |  |  | nein | Gas turbine (Oil) | 50.5 | nein |
| Wedel (GT B) | Wedel | 53.56625, 9.72848 | 43.4 | upstream | 10.4 | downstream |  |  | nein | Gas turbine (Oil) | 50.5 | nein |
| Wedel (Wedel 2) | Wedel | 53.56696, 9.72445 | 43.1 | upstream | 10.6 | downstream |  |  | nein | Steam turbine (Hard coal), KWK | 123.0 | ja |
| Wedel (Wedel 1) | Wedel | 53.56696, 9.72445 | 43.1 | upstream | 10.6 | downstream |  |  | nein | Steam turbine (Hard coal), KWK | 137.0 | ja |
| Dow Stade (Kraftwärmekopplungsanlage) | Stade | 53.65192, 9.50787 | 25.2 | upstream | 28.6 | downstream |  |  | nein | Steam turbine (Natural gas), KWK | 190.0 | ja |
| Dow Stade (Cogen Dow Stade) | Stade | 53.65192, 9.50787 | 25.2 | upstream | 28.6 | downstream |  |  | nein | Combined cycle (Natural gas), KWK | 157.0 | ja |
| KWK AOS GmbH (GT 1/2) | Stade- Bützfleth | 53.65752, 9.50198 | 24.5 | upstream | 29.3 | downstream |  |  | nein | Gas turbine (Natural gas), KWK | 30.7 | nein |
| Steinbeis Energie | Glückstadt | 53.78181, 9.42577 | 8.7 | upstream | 45.0 | downstream |  |  | nein | Steam turbine (Waste), KWK | 17.0 | ja |
| Brunsbüttel (GT A) | Brunsbüttel | 53.89252, 9.20114 | 10.0 | downstream | 63.7 | downstream |  |  | nein | Gas turbine (Oil) | 63.5 | nein |
| Brunsbüttel (GT B) | Brunsbüttel | 53.89252, 9.20114 | 10.0 | downstream | 63.7 | downstream |  |  | nein | Gas turbine (Oil) | 63.5 | nein |
| Brunsbüttel (GT C) | Brunsbüttel | 53.89252, 9.20114 | 10.0 | downstream | 63.7 | downstream |  |  | nein | Gas turbine (Oil) | 63.5 | nein |
| Brunsbüttel (GT D) | Brunsbüttel | 53.89252, 9.20114 | 10.0 | downstream | 63.7 | downstream |  |  | nein | Gas turbine (Oil) | 63.5 | nein |

## Emsland (Ems)

**Kernkraftwerk:** 52.4819° N, 7.3067° O · Fluss-km 127.6 · Abschaltung 2023

**Bezugspegel:** upstream `E 1A  UH KA RHEINENORD  EU`, downstream `HERBRUM` *(kein schätzbares Paar — nächste verfügbare Pegel)*

| Erzeuger | Ort | Koordinaten | km zum AKW | Lage zum AKW | km zu UP | Lage zu UP | km zu DOWN | Lage zu DOWN | zwischen den Pegeln | Erzeugungsart | MW | Flusskühlwasser |
|---|---|---|---:|---|---:|---|---:|---|:---:|---|---:|---|
| Emsland (C1) | Lingen | 52.48188, 7.30666 | 0.0 | am Standort | 24.9 | downstream | 79.1 | upstream | **ja** | Combined cycle (Natural gas), KWK | 116.0 | ja |
| Emsland (B1) | Lingen | 52.48188, 7.30666 | 0.0 | am Standort | 24.9 | downstream | 79.1 | upstream | **ja** | Combined cycle (Natural gas), KWK | 116.0 | ja |
| Emsland (B2) | Lingen | 52.48188, 7.30666 | 0.0 | am Standort | 24.9 | downstream | 79.1 | upstream | **ja** | Combined cycle (Natural gas), KWK | 359.0 | ja |
| Emsland (C2) | Lingen | 52.48188, 7.30666 | 0.0 | am Standort | 24.9 | downstream | 79.1 | upstream | **ja** | Combined cycle (Natural gas), KWK | 359.0 | ja |
| Emsland (D) | Lingen | 52.48188, 7.30666 | 0.0 | am Standort | 24.9 | downstream | 79.1 | upstream | **ja** | Combined cycle (Natural gas), KWK | 887.0 | ja |
| BP Werk Lingen | Lingen | 52.56061, 7.29516 | 11.4 | downstream | 36.4 | downstream | 67.7 | upstream | **ja** | Steam turbine (Natural gas), KWK | 66.0 | ja |

## Grafenrheinfeld (Main)

**Kernkraftwerk:** 49.9844° N, 10.1818° O · Fluss-km 328.5 · Abschaltung 2015

**Bezugspegel:** upstream `Schweinfurt`, downstream `Astheim`

| Erzeuger | Ort | Koordinaten | km zum AKW | Lage zum AKW | km zu UP | Lage zu UP | km zu DOWN | Lage zu DOWN | zwischen den Pegeln | Erzeugungsart | MW | Flusskühlwasser |
|---|---|---|---:|---|---:|---|---:|---|:---:|---|---:|---|
| HKW Eltmann | Eltmann | 49.984, 10.65137 | 44.9 | upstream | 38.8 | upstream | 63.5 | upstream | nein | Steam turbine (Natural gas), KWK | 57.0 | ja |
| GKS (entfällt) | Schweinfurt | 50.02969, 10.224 | 6.1 | upstream | 0.0 | am Standort | 24.7 | upstream | **ja** | Steam turbine (Waste), KWK | 24.4 | ja |
| Pielweichs (Pielweichs) | Plattling | 49.79434, 10.1813 | 34.4 | downstream | 40.5 | downstream | 15.8 | downstream | nein | Run-of-river (Hydro) | 12.6 | nein |

## Grohnde (Weser)

**Kernkraftwerk:** 52.0356° N, 9.4135° O · Fluss-km 355.9 · Abschaltung 2021

**Bezugspegel:** upstream `HEMELN`, downstream `HESS OLDENDORFFUHLEN` *(kein schätzbares Paar — nächste verfügbare Pegel)*

| Erzeuger | Ort | Koordinaten | km zum AKW | Lage zum AKW | km zu UP | Lage zu UP | km zu DOWN | Lage zu DOWN | zwischen den Pegeln | Erzeugungsart | MW | Flusskühlwasser |
|---|---|---|---:|---|---:|---|---:|---|:---:|---|---:|---|
| Enertec Hameln (Block 7) | Hameln | 52.09875, 9.38821 | 8.1 | downstream | 113.6 | downstream | 12.9 | upstream | **ja** | Steam turbine (Biomass and biogas) | 14.5 | ja |
| Enertec Hameln (Linien 1,3,4) | Hameln | 52.09875, 9.38821 | 8.1 | downstream | 113.6 | downstream | 12.9 | upstream | **ja** | Steam turbine (Waste), KWK | 13.2 | ja |
| Kraftwerk Veltheim (2) | Porta Westfalica | 52.19004, 8.93318 | 47.8 | downstream | 153.3 | downstream | 26.8 | downstream | nein | Steam turbine (Hard coal) | 93.0 | ja |
| Kraftwerk Veltheim (3) | Porta Westfalica | 52.19004, 8.93318 | 47.8 | downstream | 153.3 | downstream | 26.8 | downstream | nein | Steam turbine (Hard coal) | 303.0 | ja |
| Kraftwerk Veltheim (4 GT) | Porta Westfalica | 52.19004, 8.93318 | 47.8 | downstream | 153.3 | downstream | 26.8 | downstream | nein | Gas turbine (Natural gas) | 65.0 | nein |
| Kraftwerk Veltheim (4 DT) | Porta Westfalica | 52.18696, 8.93018 | 48.0 | downstream | 153.5 | downstream | 27.0 | downstream | nein | Steam turbine (Natural gas) | 335.0 | ja |
| Heyden (4) | Petershagen | 52.38279, 8.996 | 83.7 | downstream | 189.2 | downstream | 62.7 | downstream | nein | Steam turbine (Hard coal) | 875.0 | ja |

## Gundremmingen (Donau)

**Kernkraftwerk:** 48.51555° N, 10.3999° O · Fluss-km 585.7 · Abschaltung 2017, 2021

**Bezugspegel:** upstream `Neu-Ulm`, downstream `Donauwörth`

| Erzeuger | Ort | Koordinaten | km zum AKW | Lage zum AKW | km zu UP | Lage zu UP | km zu DOWN | Lage zu DOWN | zwischen den Pegeln | Erzeugungsart | MW | Flusskühlwasser |
|---|---|---|---:|---|---:|---|---:|---|:---:|---|---:|---|
| Heizkraftwerk Magirusstraße | Ulm | 48.39704, 9.96484 | 39.1 | upstream | 0.2 | am Standort | 85.2 | upstream | nein | Steam turbine (Hard coal), KWK | 20.7 | ja |
| Faimingen (entfällt) | Lauingen | 48.55839, 10.41176 | 5.5 | downstream | 44.5 | downstream | 40.5 | upstream | **ja** | Run-of-river (Hydro) | 10.1 | nein |
| Höchstädt | Höchstädt | 48.60316, 10.58272 | 21.7 | downstream | 60.7 | downstream | 24.3 | upstream | **ja** | Run-of-river (Hydro) | 10.0 | nein |

## Isar (Isar)

**Kernkraftwerk:** 48.6047° N, 12.2953° O · Fluss-km 63.8 · Abschaltung 2011, 2023

**Bezugspegel:** upstream `Landshut-Birket`, downstream `Landau`

| Erzeuger | Ort | Koordinaten | km zum AKW | Lage zum AKW | km zu UP | Lage zu UP | km zu DOWN | Lage zu DOWN | zwischen den Pegeln | Erzeugungsart | MW | Flusskühlwasser |
|---|---|---|---:|---|---:|---|---:|---|:---:|---|---:|---|
| Uppenborn 1 (1) | Wang | 48.47347, 11.95481 | 34.9 | upstream | 18.4 | upstream | 68.6 | upstream | nein | Run-of-river (Hydro) | 25.0 | nein |
| Uppenborn 2 (2) | Tiefenbach | 48.51523, 12.10104 | 19.6 | upstream | 3.1 | upstream | 53.3 | upstream | nein | Run-of-river (Hydro) | 18.0 | nein |
| KWK Landshut (KWK Landshut) | Landshut | 48.55811, 12.14858 | 13.4 | upstream | 3.0 | downstream | 47.2 | upstream | **ja** | Steam turbine (Natural gas), KWK | 17.6 | ja |
| Niederaichbach (Niederaichbach) | Niederaichbach | 48.60391, 12.30234 | 0.7 | downstream | 17.1 | downstream | 33.1 | upstream | **ja** | Run-of-river (Hydro) | 16.2 | nein |
| Gummering (Gummering) | Niederviehbach | 48.62246, 12.39804 | 8.8 | downstream | 25.2 | downstream | 25.0 | upstream | **ja** | Run-of-river (Hydro) | 14.8 | nein |
| Dingolfing (Dingolfing) | Dingolfing | 48.63404, 12.48369 | 15.8 | downstream | 32.2 | downstream | 18.0 | upstream | **ja** | Run-of-river (Hydro) | 15.0 | nein |
| KWK Dingolfing BA 1 (KWK Dingolfing BA1) | Dingolfing | 48.64456, 12.48293 | 16.0 | downstream | 32.4 | downstream | 17.8 | upstream | **ja** | Steam turbine (Natural gas), KWK | 16.0 | ja |
| Dingolfing BA2 (BA2) | Dingolfing | 48.64456, 12.48293 | 16.0 | downstream | 32.4 | downstream | 17.8 | upstream | **ja** | Steam turbine (Natural gas), KWK | 13.5 | ja |
| Landau (Landau) | Pilsting-Harburg | 48.66786, 12.66003 | 30.8 | downstream | 47.2 | downstream | 3.0 | upstream | **ja** | Run-of-river (Hydro) | 12.6 | nein |
| Ettling (Ettling) | Wallersorf/Ettling | 48.69607, 12.79776 | 42.7 | downstream | 59.2 | downstream | 9.0 | downstream | nein | Run-of-river (Hydro) | 12.6 | nein |

## Neckarwestheim (Neckar)

**Kernkraftwerk:** 49.0411° N, 9.175° O · Fluss-km 124.5 · Abschaltung 2011, 2023

**Bezugspegel:** upstream `BESIGHEIM`, downstream `KOCHENDORF` *(kein schätzbares Paar — nächste verfügbare Pegel)*

| Erzeuger | Ort | Koordinaten | km zum AKW | Lage zum AKW | km zu UP | Lage zu UP | km zu DOWN | Lage zu DOWN | zwischen den Pegeln | Erzeugungsart | MW | Flusskühlwasser |
|---|---|---|---:|---|---:|---|---:|---|:---:|---|---:|---|
| Restmüll-Heizkraftwerk Stuttgart-Münster (MÜN DT19 neu) | Stuttgart | 48.81253, 9.21895 | 46.3 | upstream | 40.4 | upstream | 70.2 | upstream | nein | Steam turbine (Waste), KWK | 19.5 | ja |
| Restmüll-Heizkraftwerk Stuttgart-Münster (MÜN DT12) | Stuttgart | 48.81583, 9.22111 | 45.8 | upstream | 39.9 | upstream | 69.7 | upstream | nein | Steam turbine (Hard coal), KWK | 45.0 | ja |
| Restmüll-Heizkraftwerk Stuttgart-Münster (MÜN DT15) | Stuttgart | 48.81583, 9.22111 | 45.8 | upstream | 39.9 | upstream | 69.7 | upstream | nein | Steam turbine (Hard coal), KWK | 45.0 | ja |
| Restmüll-Heizkraftwerk Stuttgart-Münster (MÜN GT16) | Stuttgart | 48.81583, 9.22111 | 45.8 | upstream | 39.9 | upstream | 69.7 | upstream | nein | Steam turbine (Oil) | 23.3 | ja |
| Restmüll-Heizkraftwerk Stuttgart-Münster (MÜN GT17) | Stuttgart | 48.81583, 9.22111 | 45.8 | upstream | 39.9 | upstream | 69.7 | upstream | nein | Steam turbine (Oil) | 23.3 | ja |
| Restmüll-Heizkraftwerk Stuttgart-Münster (MÜN GT18) | Stuttgart | 48.81583, 9.22111 | 45.8 | upstream | 39.9 | upstream | 69.7 | upstream | nein | Steam turbine (Oil) | 23.3 | ja |
| Dampfkraftwerk Marbach am Neckar (Marbach II GT) | Marbach | 48.9275, 9.23001 | 26.3 | upstream | 20.4 | upstream | 50.2 | upstream | nein | Gas turbine (Oil) | 77.4 | nein |
| Dampfkraftwerk Marbach am Neckar (Marbach III GT (solo)) | Marbach | 48.9275, 9.23001 | 26.3 | upstream | 20.4 | upstream | 50.2 | upstream | nein | Combined cycle (Oil) | 85.0 | ja |
| Dampfkraftwerk Marbach am Neckar (MAR III DT) | Marbach | 48.9275, 9.23001 | 26.3 | upstream | 20.4 | upstream | 50.2 | upstream | nein | Combined cycle (Oil) | 263.5 | ja |
| Kraftwerk Walheim (WAL 1) | Walheim | 49.01747, 9.15739 | 4.7 | upstream | 1.2 | downstream | 28.6 | upstream | **ja** | Steam turbine (Hard coal) | 96.0 | ja |
| Kraftwerk Walheim (WAL 2) | Walheim | 49.01747, 9.15739 | 4.7 | upstream | 1.2 | downstream | 28.6 | upstream | **ja** | Steam turbine (Hard coal) | 148.0 | ja |
| Kraftwerk Walheim (WAL GT D) | Walheim | 49.01747, 9.15739 | 4.7 | upstream | 1.2 | downstream | 28.6 | upstream | **ja** | Gas turbine (Oil) | 136.0 | nein |
| Heizkraftwerk Heilbronn (HLB 5) | Heilbronn | 49.17733, 9.20632 | 19.3 | downstream | 25.2 | downstream | 4.6 | upstream | **ja** | Steam turbine (Hard coal) | 125.0 | ja |
| Heizkraftwerk Heilbronn (HLB 6) | Heilbronn | 49.17733, 9.20632 | 19.3 | downstream | 25.2 | downstream | 4.6 | upstream | **ja** | Steam turbine (Hard coal) | 125.0 | ja |
| Heizkraftwerk Heilbronn (HLB 7) | Heilbronn | 49.17733, 9.20632 | 19.3 | downstream | 25.2 | downstream | 4.6 | upstream | **ja** | Steam turbine (Hard coal), KWK | 778.0 | ja |

## Philippsburg (Rhein)

**Kernkraftwerk:** 49.2527° N, 8.4354° O · Fluss-km 563.8 · Abschaltung 2011, 2019

**Bezugspegel:** upstream `KARLSRUHE`, downstream `MANNHEIM RHEIN` *(kein schätzbares Paar — nächste verfügbare Pegel)*

| Erzeuger | Ort | Koordinaten | km zum AKW | Lage zum AKW | km zu UP | Lage zu UP | km zu DOWN | Lage zu DOWN | zwischen den Pegeln | Erzeugungsart | MW | Flusskühlwasser |
|---|---|---|---:|---|---:|---|---:|---|:---:|---|---:|---|
| Rheinhafen-Dampfkraftwerk (RDK 7) | Karlsruhe | 49.0125, 8.30278 | 31.5 | upstream | 15.1 | downstream | 67.7 | upstream | **ja** | Steam turbine (Hard coal), KWK | 517.0 | ja |
| Rheinhafen-Dampfkraftwerk (RDK 8) | Karlsruhe | 49.0125, 8.30278 | 31.5 | upstream | 15.1 | downstream | 67.7 | upstream | **ja** | Steam turbine (Hard coal), KWK | 834.0 | ja |
| Rheinhafen-Dampfkraftwerk (RDK 4S) | Karlsruhe | 49.0125, 8.30278 | 31.5 | upstream | 15.1 | downstream | 67.7 | upstream | **ja** | Combined cycle (Natural gas) | 353.0 | ja |
| Stora Enso Maxau | Karlsruhe | 49.0393, 8.31134 | 28.3 | upstream | 18.3 | downstream | 64.5 | upstream | **ja** | Steam turbine (Biomass and biogas), KWK | 78.0 | ja |
| BHKW | Woerth | 49.04747, 8.2816 | 27.8 | upstream | 18.8 | downstream | 64.0 | upstream | **ja** | Steam turbine (Natural gas), KWK | 13.0 | ja |
| MiRO (Kesselhaus Werk 1) | Karlsruhe | 49.06081, 8.32439 | 25.4 | upstream | 21.2 | downstream | 61.6 | upstream | **ja** | Steam turbine (Oil), KWK | 45.0 | ja |
| MiRO (Kesselhaus Werk 2) | Karlsruhe | 49.06081, 8.32439 | 25.4 | upstream | 21.2 | downstream | 61.6 | upstream | **ja** | Steam turbine (Oil), KWK | 25.0 | ja |
| HKW Wörth | Wörth | 49.06996, 8.30702 | 25.3 | upstream | 21.3 | downstream | 61.5 | upstream | **ja** | Steam turbine (Natural gas), KWK | 59.0 | ja |
| GKM (Block 3) | Mannheim | 49.44569, 8.49044 | 27.7 | downstream | 74.3 | downstream | 8.5 | upstream | **ja** | Steam turbine (Hard coal), KWK | 202.5 | ja |
| GKM (Block 4) | Mannheim | 49.44569, 8.49044 | 27.7 | downstream | 74.3 | downstream | 8.5 | upstream | **ja** | Steam turbine (Hard coal), KWK | 202.5 | ja |
| GKM (Block 6) | Mannheim | 49.44569, 8.49044 | 27.7 | downstream | 74.3 | downstream | 8.5 | upstream | **ja** | Steam turbine (Hard coal), KWK | 255.0 | ja |
| GKM (Block 7) | Mannheim | 49.44569, 8.49044 | 27.7 | downstream | 74.3 | downstream | 8.5 | upstream | **ja** | Steam turbine (Hard coal), KWK | 425.0 | ja |
| GKM (Block 8) | Mannheim | 49.44569, 8.49044 | 27.7 | downstream | 74.3 | downstream | 8.5 | upstream | **ja** | Steam turbine (Hard coal), KWK | 435.0 | ja |
| GKM (Block 9) | Mannheim | 49.44569, 8.49044 | 27.7 | downstream | 74.3 | downstream | 8.5 | upstream | **ja** | Steam turbine (Hard coal), KWK | 843.0 | ja |
| BHKW Ludwigshafen (BHKW ) | Ludwigshafen | 49.45308, 8.43364 | 31.7 | downstream | 78.3 | downstream | 4.5 | upstream | **ja** | Steam turbine (Natural gas), KWK | 12.5 | ja |
| Industriekraftwerk Ludwigshafen (GuD) | Ludwigshafen | 49.45318, 8.43359 | 31.7 | downstream | 78.3 | downstream | 4.5 | upstream | **ja** | Combined cycle (Natural gas), KWK | 12.0 | ja |
| FHKW Ludwigshafen (FHKW) | Ludwigshafen | 49.48505, 8.42622 | 37.4 | downstream | 84.0 | downstream | 1.3 | downstream | nein | Steam turbine (Waste), KWK | 28.0 | ja |
| KW Mitte (GT 1) | Ludwigshafen | 49.51395, 8.43151 | 40.1 | downstream | 86.6 | downstream | 3.9 | downstream | nein | Gas turbine (Natural gas), KWK | 47.0 | nein |
| Kraftwerk Mitte (GUD A 800  GT 11, GT 12, DT 10) | Ludwigshafen | 49.51373, 8.43156 | 40.1 | downstream | 86.6 | downstream | 3.9 | downstream | nein | Combined cycle (Natural gas), KWK | 497.5 | ja |
| Kraftwerk Süd (GUD C 200 GT 1, GT 2, DT 1) | Ludwigshafen | 49.51362, 8.4316 | 40.1 | downstream | 86.6 | downstream | 3.9 | downstream | nein | Combined cycle (Natural gas), KWK | 410.0 | ja |
| HKW Mannheim (Turbine 60) | Mannheim | 49.5224, 8.45294 | 40.5 | downstream | 87.1 | downstream | 4.3 | downstream | nein | Steam turbine (Waste), KWK | 22.1 | ja |
| SCA Mannheim (SCA Mannheim) | Mannheim | 49.5349, 8.46358 | 41.5 | downstream | 88.1 | downstream | 5.3 | downstream | nein | Steam turbine (Biomass and biogas), KWK | 40.0 | ja |

## Unterweser (Weser)

**Kernkraftwerk:** 53.4286° N, 8.4769° O · Fluss-km 50.9 · Abschaltung 2011

**Bezugspegel:** upstream `FARGE`, downstream `—` *(kein schätzbares Paar — nächste verfügbare Pegel)*

| Erzeuger | Ort | Koordinaten | km zum AKW | Lage zum AKW | km zu UP | Lage zu UP | km zu DOWN | Lage zu DOWN | zwischen den Pegeln | Erzeugungsart | MW | Flusskühlwasser |
|---|---|---|---:|---|---:|---|---:|---|:---:|---|---:|---|
| Farge (Farge) | Bremen | 53.20207, 8.51615 | 26.3 | downstream | 71.0 | downstream |  |  | nein | Steam turbine (Hard coal) | 350.0 | ja |
| KWK-Anlage (GT 1-3, DT) | Bremen | 53.12099, 8.73478 | 45.2 | downstream | 89.9 | downstream |  |  | nein | Combined cycle (Natural gas), KWK | 14.8 | ja |
