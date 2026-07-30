## Next Tasks

[x] Dissolved Oxygen levels auch noch Analysieren
    → GKD-Chemieprogramm erschlossen (45.336 Werte, 37 Stellen, ab 1990).
      Isar 2011: +0,91 mg/l (p = 0,003) — kühleres Wasser hält mehr Sauerstoff.
      Waterbase war auch hier erst ab 2020 nutzbar.
[x] Sensitivitäts Analyse (Abstand entlang der Flussgeometrie, nicht Luftlinie)
    → scripts/distance_sensitivity.py; Urteil je Schätzung + Mindesteffektgröße.
      Abgeleiteter Radius: 50 km entlang des Flusses (analysis_radius.json).
[x] Dateien die wir nicht mehr benötigen archivieren
    → Archiv/ mit eigener README.md. Nichts gelöscht.
[x] Standort Analyse auf weitere Einflussfaktoren, insbesondere andere Kraftwerke
    → scripts/confounder_report.py. Temperatur-Schätzungen sauber (Isar: kein
      anderes Wärmekraftwerk im 50-km-Radius). Ein Confounder beim Sauerstoff:
      Kraftwerk Plattling (Gas, 2010) — wirkt gegen unseren Befund.
[x] Recherche lokal, ob das erwärmte Kühlwasser wieder in den Fluss gelangt
    → METHODS.md §3.5. Zwei Einträge korrigiert (Biblis = Durchlauf, nicht
      Kühlturm; Philippsburg = hybrid). Feld `river_heat_load` in reactors.py.
[x] in study_map und study_sites_by_reactor einzeichnen, welche Messstation für
    upstream und welche für downstream benutzt wurde + andere Kraftwerke
    → beide Karten neu; benutzte Pegel schwarz umrandet und mit UP/DOWN
      beschriftet, andere Wärmekraftwerke im 50-km-Radius eingezeichnet.
[x] Analyse Erwärmung pro produzierte Menge Strom
    → scripts/effect_per_generation.py. Isar 1 (2011): 0,32 °C je TWh/a bzw.
      1,20 °C je GW flusswirksamer Abwärme.


## Offen / nächste Schritte

[ ] Landesdaten für Rhein, Neckar, Weser, Elbe erschließen — das ist die einzige
    verbleibende Lücke für die übrigen 2011-Standorte (Biblis, Philippsburg,
    Neckarwestheim, Unterweser). Pegel existieren, nur die Archive fehlen uns:
    LUBW/HVZ (BW), HLNUG und LfU RLP (Rhein bei Biblis), NLWKN und FGG Weser,
    FGG Elbe. pipeline/gkd_bayern.py ist die Vorlage.
[ ] Abfluss als Expositionsmaß einbauen — eine Wärmefahne wird von der
    Wassermenge verdünnt, der Effekt sollte bei Niedrigwasser am größten sein.
    Die GRDC-Daten liegen schon in data/raw/discharge/.
[ ] Zweiter Downstream-Pegel an der Isar mit Vorperiode — ohne den lässt sich die
    Abklingkurve genau dort nicht schätzen, wo es einen Effekt gibt.
[ ] Gestaffelter DiD (Callaway–Sant'Anna) als Ergänzung zum paarweisen 2×2;
    Entwurf liegt in Archiv/scripts/did_staggered.py.


## Paper related Tasks

[x] Recherche lokal, ob das erwärmte Kühlwasser wieder in den Fluss gelangt oder
    ob es eher über die Kühltürme verdunstet
    → siehe oben; Quellen in DATENAUDIT_UND_2x2.md §8.
