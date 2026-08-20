<!-- STATUS: OFFEN | Frage: Findet ein UNGEPRIMTER Reviewer (ohne unsere Hypothesen, Verdachtsflaechen und Schlussfolgerungen) Korrektheitsfehler in der KI selbst -- Suche, Netz-Integration, Self-Play, Trainingsziele? | Beleg: offen, nichts gestartet. Anlass: Nutzer-Auftrag 2026-08-20; alle bisherigen Reviews waren vom Koordinator gebrieft und damit auf dessen Verdachtsflaechen verengt. -->

# PREREG: Ungeprimter Implementierungs-Review der KI

Stand **2026-08-20**, **ENTWURF, nichts gestartet.** Durchgehend Plan-Zeitform.

**Anlass (Nutzer, woertlich sinngemaess):** ein zweiter Review-Track, "den du
weniger biast", der sich "den KI-Agenten an sich ansieht". Der Punkt ist
methodisch: jeder vom Koordinator gebriefte Reviewer erbt dessen
Verdachtsflaechen und Blindstellen. Die teuersten Fehler dieses Projekts
sassen wiederholt DORT, wo niemand hinsah (policy-maskierter Korpus fiel
durch eine Nutzer-Frage auf, nicht durch eine Messung). Ein ungeprimter
Blick ist die einzige Suchstrategie, die nicht von der Karte des
Koordinators begrenzt ist.

---

## par.1 AUFTRAG AN DEN REVIEWER (bewusst offen)

Pruefe die KI selbst — Suchalgorithmus, Netz-Integration, Self-Play-
Datenerzeugung, Trainingsziele, Bewertungspfade — auf KORREKTHEITSFEHLER,
insbesondere solche, die still die Spielstaerke schwaechen oder Lernsignale
verfaelschen (Perspektiven-/Vorzeichenfehler, Index-Versaetze, Lecks
verdeckter Information, RNG-/Determinismus-Probleme, Trainings-/Inferenz-
Diskrepanzen). Der Reviewer waehlt selbst, wo er tief geht.

## par.2 BIAS-SCHUTZ (der Kern dieser Registrierung)

1. **Kein Briefing ueber Verdachtsflaechen, Hypothesen oder juengste
   Aenderungen.** Der Prompt nennt nur: was das System ist, wo der Code
   liegt, was als Fehlerklasse interessiert (par.1-Wortlaut), und die
   Schutzregeln unten. KEINE Erwaehnung von k1, Ownership-Kampagne,
   par.14 oder einzelnen Dateien.
2. **Quarantaene der eigenen Schlussfolgerungen:** `evaluations/` und
   `archive/` sind fuer den Reviewer TABU, bis seine Befundliste als
   Entwurf steht; danach darf er sie lesen, ausschliesslich um Duplikate
   zu markieren ("bereits bekannt laut X"). `docs/engine_manual.md`
   (Spielregeln) ist von Anfang an erlaubt — Regeln sind Fakten, keine
   Schlussfolgerungen.
3. **Staerkstes verfuegbares Modell** (Opus), EIN Agent, grosszuegiges
   Zeitbudget — Tiefe schlaegt hier Redundanz, weil der Wert gerade in
   der unvorhersehbaren Schwerpunktwahl liegt.
4. **Belegpflicht wie ueberall:** `datei:zeile` je Behauptung, Mini-Repro
   wo moeglich (Lesesonden erlaubt), Schwere + Konfidenz je Befund.
   "Keine kritischen Befunde, geprueft wurden X/Y/Z" ist ein vollwertiges
   Ergebnis — der Auftrag verlangt ausdruecklich, nichts zu erfinden.
5. **Strikt read-only**, kein Wheel-Bau, kein Training, keine Arena;
   waehrenddessen laeuft nichts anderes (Exklusivitaets-Regel).

## par.3 VORAB-REGELN

> **VERWERTUNG:** Befunde des ungeprimten Reviewers sind Behauptungen
> (Regel 0). Jeder Befund mit Schwere "kritisch" oder "mittel" durchlaeuft
> denselben adversarialen Verifikations-Schritt wie im gezielten Review
> (`PREREG_implementation_review_targeted.md` par.3) — erst dann wird er
> verrechnet.
>
> **KONSEQUENZ-REGEL, vorab:** bestaetigte kritische Befunde werden je nach
> Traeger behandelt: beruehrt er eine abgeschlossene Messung, wird deren
> Prereg annotiert und die Messung eingeplant wiederholt; beruehrt er den
> Elo-Anker oder das Heuristik-Parameterpaket, gilt die stehende
> NICHT-ANFASSEN-Regel und der Befund wird nur protokolliert (Nutzer
> entscheidet); sonst: Fix mit eigenem Arena-Gating nach Bestandsregeln.

## par.4 WAS DIESER REVIEW NICHT ENTSCHEIDET

- Keine Strategie- oder Priorisierungsfragen.
- Kein Urteil ueber die Ownership-Kampagne — falls der Reviewer von allein
  dort landet, zaehlt das als unabhaengige Konvergenz und wird so vermerkt.
- Keine Stil-/Architektur-Empfehlungen (nur Korrektheit).

## par.5 ABGRENZUNG ZUM GEZIELTEN REVIEW

Beide Reviews koennen dieselben Stellen treffen — das ist erwuenscht:
unabhaengige Konvergenz auf denselben Befund ist der staerkste Beleg, den
dieses Format liefern kann. Sie laufen deshalb GETRENNT (keine geteilten
Zwischenstaende) und werden erst nach Abschluss beider zusammengefuehrt.

## par.6 KOSTEN

Ein Opus-Agent, grosszuegig bemessen (Richtwert 30-90 min Agentenzeit),
keine GPU. Der Nutzen haengt nicht am Erwartungswert eines Funds, sondern
an der Abdeckung der Flaechen, die auf keiner Verdachtskarte stehen.

## par.7 ERGEBNIS (leer bei Registrierung)
