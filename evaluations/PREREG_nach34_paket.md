# Vorregistrierung: Nach-#34-Paket in EINEM Zug (#9, #12, #29)

**Angelegt 2026-08-06, VOR allen Laeufen** (Nutzer-Erinnerung: "denk an
das Ein-Zug-Paket (#9, #12, #29) -> #14-Entscheidung"). Die
Arena-Konvention/Aggressions-Neukartierung ist per Nutzer-Entscheid in
den v20-Zyklus verschoben und NICHT Teil dieses Pakets.

## Gemeinsame Randbedingungen

- Basis-Rezept = #34-Verdikts-Konfiguration: warm von `v19_2d_best`, 2D,
  Seed 2, lr 5e-5 cosine, `--value-head wdl --wdl-bootstrap-destretch
  --select-by-brier`, VALUE_WEIGHT 0,2, 900er-Fenster.
- Referenz-Arm existiert: `t34_wdldestretch` (identisches Rezept ohne den
  jeweiligen Zusatz-Kopf) -- jeder Paket-Arm ist eine EIN-Faktor-Ablation
  dagegen.
- **Aufloesungs-Regel** (Lehren 8pp-Seed-Streuung + 8x Arena-Paritaet):
  Gatings bis 200 Paare, SPRT; ein H0 bedeutet "kein Beleg", NICHT
  "widerlegt". Effekte unterhalb der Aufloesung werden als solche
  berichtet. Offline-Kennzahlen (Brier auf 90-Dateien-Messset, Platt-B)
  nur deskriptiv.
- Blend bleibt ueberall AUS (w=0, Nutzer-Entscheid nach Audit-F1).

## Arm 1 — #12 Distributionaler Punkte-Kopf (`t12_dist`)

`--points-dist-bins 51` (C51, Wert des #12-Erstversuchs `v18_dist`) zusaetzlich.
Alt-Befund (geschlossen): "mehr Punkte in beiden Arena-Bloecken, ohne
Siege daraus zu machen" -- gemessen am ALTEN Value-Ziel. Neue These:
mit echter Sieg-Wahrscheinlichkeit im Value-Kopf ist
P(Sieg) + Score-VERTEILUNG erstmals die KataGo-Kombination zweier
wirklich verschiedener Groessen.
Entscheid: Gating vs `t34_wdldestretch` (Ein-Faktor) und vs
`v19_2d_best` (Kontext). Uebernahme in die v20-Konfiguration nur bei
SPRT-H1 oder klarer, replizierter Tendenz + intaktem Brier.

## Arm 2 — #9 Ownership-Kopf (`t9_own`)

`--ownership-weight 0.3` (Wert des #9-Erstversuchs, beste Tendenz
+0,0017 bei 5:1/p=0,22) zusaetzlich (Kopf ist inert vorhanden). Schliessungsregel von 2026-07-28 wird eingehalten:
Wiedereroeffnung NUR mit Arena-Instrument -- genau das ist dieses
Gating. Zusatzargument seit #34: binaeres Hauptziel liefert weniger
Gradientensignal, Hilfsziele koennten MEHR beitragen (KataGo).
Entscheid: wie Arm 1. Bleibt es bei H0, wird #9 wieder geschlossen und
der Eintrag um "auch am neuen Ziel kein Arena-Beleg" ergaenzt.

## #29 Rangmetrik — Instrument JA, Validierung VERTAGT (ehrlich benannt)

Die Semantik-Huerde ist mit #34 weg (Value = P(Sieg) wie Orakel-Q).
ABER: eine VALIDIERUNG der Metrik braucht Arm-Paare mit BEKANNTEM
Arena-Unterschied -- in der WDL-Aera gibt es bisher KEINE (8x
Paritaet). Daher in diesem Paket nur:
1. Orakel-Q-Referenzen NEU erzeugen (Audit-Auflage: die alten stammen
   aus Alt-Kopf-Suchen) -- auf dem NEUEN frozen-Set, sobald es gebaut
   ist; Referenz-Suche mit `v19_2d_best`@5000 (unabhaengig von den
   gerankten WDL-Armen, kein Selbstbezug).
2. Rangmetrik deskriptiv fuer alle Paket-Arme berechnen und ARCHIVIEREN.
3. Validierungs-Entscheid faellt erst, wenn arena-differenzierte Paare
   existieren (fruehestens v20-Gating). #29 bleibt bis dahin formal
   geschlossen.

## Reihenfolge & Kosten

Nach #36-Auswertung: Trainings Arm 1 + Arm 2 (GPU, je ~35 min,
sequenziell), Gatings (CPU, je ~1-2h, sequenziell), parallel R4b-Lauf
nur auf sonst idler CPU (Betriebsregel Ground-Truth). Danach
#14-Entscheid gemaess seinen drei Bedingungen (#36-Ausgang, Durchsatz
end-to-end). Frozen-Set-Neubau (v19-Aera) vor Punkt #29.1.

---
**STATUS (Stand 2026-08-08): ENTSCHIEDEN** -- Arm 2 (`t9_own`) erneut
geschlossen (Paritaet 197:193 und 145:145, beide H0). Arm 1 (`t12_dist`)
zeigte zunaechst SPRT-H1 (54:26 gegen die Referenz), erwies sich in der
vorregistrierten Frisch-Seed-Replikation aber als Seed-Satz-Rauschen
(206:194 bzw. 181:179, beide n.s.) -> ebenfalls geschlossen. #29 (die
Rangmetrik-Instrumentierung) bleibt formal vertagt -- reines Instrument,
Validierung wartet weiterhin auf arena-differenzierte Paare nach dem
Frozen-Set-Neubau. Paket-Fazit: kein Aux-Kopf-Hebel am neuen #34-Ziel;
einziger belegter Hebel bleibt die Spielzahl (#36). Belegstelle:
archive/history.md, Abschnitt "Nach-#34-Paket ERGEBNISSE (2026-08-06,
PREREG_nach34_paket.md)", Zeile ~10005-10039.
