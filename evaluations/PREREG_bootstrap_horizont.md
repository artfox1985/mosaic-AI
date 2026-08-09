# Vorregistrierung: Bootstrap-Horizont (2 vs 3) -- Option fuer den v22-Zuschnitt

**Angelegt 2026-08-09, VOR jeder Messung und VOR dem v22-Self-Play.**
Nutzer-Auftrag: *"takte es ein"*, nach der Feststellung, dass der
Horizont nur beim Erzeugen neuer Partien ueberhaupt aenderbar ist.

## Warum der Horizont nur JETZT aenderbar ist

`BOOTSTRAP_HORIZON_ROUNDS = 2` liegt in
`engine/src/round_transition_deep.rs:153`, ist also **engine-seitig** und
wird beim Self-Play in die Records geschrieben. Er steckt **nicht** im
Cache-Schluessel (`str(files)+INPUT_SIZE+NUM_ACTIONS+VALUE_SCHEMA_VERSION+
POLICY_TARGET_SHARPEN_EXPONENT+TD_LAMBDA+...`) -- zwei Konsequenzen:

1. Auf einem bestehenden Fenster ist er **nicht sweepbar**. Eine Aenderung
   verlangt NEUES Self-Play.
2. **Fussangel**: wer die Konstante aendert, ohne neu zu generieren,
   bekommt stillschweigend den alten Cache und merkt nichts. Gehoert in
   die geltenden Regeln.

Damit ist der v22-Generierungsstart der einzige Zeitpunkt dieser
Generation, an dem die Frage ohne zusaetzliche Generierungskosten
beantwortbar ist -- danach ist das Fenster geschrieben.

## Warum die Frage heute mehr Gewicht hat als beim Parken

Der Horizont wurde in der v12-Aera geparkt ("teuer, Noise-Floor stuetzt
2"). Damals lief `rtv` parallel und teilte die Arbeit. Seit `nortv`
(v13-Champion) ist der TD-Bootstrap das **einzige** Mittel, das die
Fabrik-Neubefuellung mittelt -- der Zufallsknoten, den der Nutzer als die
stark zufaellige Komponente benannt hat. Die Parkbegruendung ist also
schwaecher geworden, ohne dass es nachgezogen wurde.

## Das Problem des rotierenden Fensters

v22 hat 12.000 neue von 29.450 Partien, in der Value-Klasse 8.000 von
23.650. Uebernommene Partien tragen ihre Labels mit dem ALTEN Horizont
fuer immer. Ein "v22 mit Horizont 3" haette also nur ~34% behandelte
Value-Labels -- konfundiert, und ein Nullergebnis waere nicht von "Dosis
zu klein" zu unterscheiden. Genau die Falle, die heute schon bei λ ueber
die Aussagekraft entschied.

## Zuschnitt: BEIDE Labels mitschreiben, dann zwei Arme auf identischen Partien

Waehrend der v22-Generierung wird je Rundenuebergang der Bootstrap-Wert
fuer Horizont 2 **und** Horizont 3 in denselben Record geschrieben. Dann:

- ein Cache (Schema-Bump, neues Feld), **zwei Trainings-Arme**, die sich
  ausschliesslich darin unterscheiden, welches Feld sie als Value-Ziel
  lesen;
- die uebernommenen Alt-Partien sind in BEIDEN Armen identisch (Horizont
  2, unveraenderbar) -- die Differenz zwischen den Armen ist damit
  **exakt** der Horizont auf dem neuen Drittel.

Das behebt die Konfundierung, nicht die Verduennung: der Effekt bleibt
auf ein Drittel der Value-Labels beschraenkt. **Vorab festgehalten**: ein
H0 ist deshalb ein SCHWACHER Beleg gegen den Horizont, kein starker. Wer
ihn spaeter als "Horizont 3 widerlegt" zitiert, zitiert falsch.

## Stufe 1 (GATE, vor allem anderen): Kosten des zweiten Rollouts

Der Bootstrap ist ein Netz-Rollout ueber N Runden, ~4x je Partie. Der
rtv-Praezedenzfall zeigt, dass Rollouts teuer werden koennen: 24 Samples
kosteten **81% der Self-Play-Zeit**. Ein zweiter Rollout je Uebergang ist
also nicht selbstverstaendlich billig -- das wird GEMESSEN, nicht
geschaetzt: Self-Play-Zeit je Partie mit einem Rollout gegen zwei
(kleine Stichprobe, ~50 Partien, gleicher Seed).

**Entscheidungsregeln (vorab):**
1. Aufschlag **<= +25%** Self-Play-Zeit ⇒ Stufe 2 wird gefahren.
2. Aufschlag **> +25%** ⇒ **verworfen**, ohne Rueckfrage. Begruendung: bei
   12.000 Partien und ~10h Generierung ist mehr als ein Viertel
   Aufschlag fuer eine Frage, deren Effekt ohnehin auf ein Drittel der
   Labels verduennt ist, nicht vertretbar. Der Nutzer hat diese
   Verwerfungs-Option ausdruecklich verlangt.
3. Der Horizont-3-Rollout darf die Horizont-2-Werte **nicht** veraendern
   (Paritaets-Nachweis am Label: dieselben Partien, Horizont-2-Feld
   bit-identisch zum Einzel-Rollout-Lauf). Sonst ist der Vergleich
   wertlos.

## Stufe 2 (nur nach Stufe 1): zwei Arme

Training beider Arme mit identischem Rezept, Fenster und Seed; Gating
jedes Arms gegen den dann amtierenden Champion (Standard-SPRT, 400 Sims,
Block-Ebene, Fruehstopp-Replikationsregel).

- **Ein Arm gewinnt** ⇒ dieser Horizont wird Standard fuer kuenftige
  Generationen. Hinweis fuer die Umsetzung: die Umstellung wirkt nur auf
  NEUE Partien, das Fenster laeuft also ueber ~3 Generationen hinweg
  gemischt -- das ist dokumentiert und kein Fehler.
- **Beide H0** ⇒ Horizont 2 bleibt, Frage fuer die Aera geschlossen, mit
  dem Verduennungs-Vorbehalt oben.

## Nicht Teil davon

- Kein Sweep weiterer Horizonte (4+). Jeder zusaetzliche Wert kostet
  einen weiteren Rollout je Uebergang.
- Keine Aenderung an `TD_LAMBDA` (entschieden: Sweep empfahl 0,7, die
  Arena verwarf es 30:70, λ=0,5 bleibt).
- Keine Aenderung am v22-Fenster-Zuschnitt selbst (`PREREG_v22_fenster.md`
  bleibt gueltig; dieses Dokument ergaenzt nur eine Label-Option).
