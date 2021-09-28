# Datenablage-Regeln für die automatisierte Prüfung der Testfälle auf der Webseite

- Je Testfall gibt es mehrere Varianten
- Ergebnisdaten werden je Tool und Testfall in separaten Dateien abgelegt
- Fehlt eine Datei, gilt der Testfall als *nicht* gerechnet
- Daten werden als Textdateien im tsv-Format abgelegt

- Dateinamen-Regeln (primär für SimQuality-Verzeichnisstruktur - Webinterface
  kann importierte Dateien intern entsprechend umbenennen)

Schema:

```
<tool+version>.tsv
```

Beispiel:

```
THERAKLES.tsv
```

Testfall selbst muss nicht angegeben werden, da die Ergebnisdateien im
Unterverzeichnis des jeweiligen Testfalls abgelegt werden.


- Je Testfall ist die Kopfzeile (und damit die Spaltenzuordnung)
  in jeder `xxx.tsv`-Datei fest vorgegeben, einschließlich Einheit:

- Beispiel:

```
Time [h]	Var1.Tout [C]	Var1.TRoom [C]	Var2.Tout [C]	Var2.TRoom [C]
```

- Spalten sind tab-getrennt (wie beim Kopieren aus Excel/Calc).
- Variablenbezeichner sind zusammengesetzt aus Variantenpräfix `Var<N>` und Variablennamenkürzel
  (entsprechend Beschreibung und Aufgabenstellung)
- Anzahl der Nachkommastellen ist sinnvoll zu begrenzen (z.B. auf 6 signifikante Stellen)


## Unterscheidung von Stundenmittelwerten oder Momentanwerten

- je nach Programm können einzelne Ausgaben als Stundenmittelwerte oder
  Momentanwerte ausgegeben werden

- Dieses wird in der Spaltenüberschrift in der Kopfzeile durch ein Anhängen
  von `(mean)` nach dem Variablentext angezeigt, beispielsweise:

```
Time [h]	Var1.TRoom [C]	Var1.GlobalSWRad.Roof (mean) [W/m2]	Var1.GlobalSWRad.NorthWall (mean) [W/m2] ...
```

- bei der Auswertung wird der angegebene Wert dann als integraler Mittelwert der angegebenen Stunde interpretiert
  und beim generierten Plot wird der Datenpunkt in der Mitte der Stunde eingetragen und linear verbunden (oder
  alternativ als Stufe angezeigt)

- es ist möglich, nur einige Spalten als `(mean)` zu kennzeichnen

- Bei Stundenmittelwerten gilt die Konvention, dass die Zeit in [h] stets den Anfang der Stunde angibt, d.h.
  1 h bedeutet der Mittelwert gilt für Stunde 0:00-1:00 (rückwirkend). Der Wert bei Stunde 0 h wird nur als Anfangsbedingung interpretiert.
  Beispiel: ein Wert von 500 W bei 1 h bedeutet, dass in der Stunde von 0:00-1:00 im Mittel eine Last von 500 W berechnet wurde.
  
  

## Vollständigkeit der Daten

- abgelegte Testfall-Dateien müssen stets alle Variablen/Spalten enthalten und alle geforderten Zeitpunkte
- falls bestimmte Ergebnisse durch ein Programm nicht geliefert werden können (bspw. Aufteilung der Strahlung in diff. und direkt), 
  müssen die Spalten trotzdem vorhanden sein und mit 0 gefüllt werden.

## Ablage von Referenzwerten

Die Referenzwerte werden analog zu Simulationsergebnissen abgelegt, wobei der Tool-Präfix `Reference` verwendet wird (nur relevant 
für die SimQuality-Cloud-Prüfungsskripte - auf der Webseite als Teil der Testfallspezifikation abgelegt).
