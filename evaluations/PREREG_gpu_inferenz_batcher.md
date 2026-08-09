# Vorregistrierung: Machbarkeitsprobe GPU-Inferenz-Batcher (Alt-Nummer #82)

**Angelegt 2026-08-09, VOR jeder Messung.** Nutzer-Auftrag: *"takte das
ein für #82"*, nach der Aufarbeitung der Nummern-Registratur.

Namenskonvention: dieses Dokument ist die Kennung. `#82` wird nur als
**Rueckwaerts-Referenz** auf die Alt-Fundstellen genannt
(`archive/history.md:2293`, Vorarbeit `#81` Amdahl-Split) -- es wird
keine neue `#NN` vergeben.

## Warum ueberhaupt, und warum jetzt

Die Registratur fuehrte `#82` als **UNKLAR**: Thema klar, aber weder
Umsetzungs- noch Absage-Nachweis. Die Vermutung dort war, die
Dringlichkeit sei mit der rtv-Abschaltung gesunken. Die Zahlen sagen das
Gegenteil:

| Groesse | Wert | Quelle |
|---|---|---|
| Netz-Inferenz-Anteil an der Self-Play-Zeit | **62,0%** (3002 s, 1.314.962 Evals) | `archive/history.md:7427` |
| dito, aktuelle Aera (v20-Kampagne, nach rtv-Abschaltung) | **~81%** | `PREREG_v20_kampagne.md:71` |
| CPU-Durchsatz heute | ~1.600-3.200 Evals/s **je Thread** | `#81`, `archive/history.md:2293` |
| GPU-Behauptung (torch-Benchmark, RTX 3060) | ~203.000 Evals/s **bei Batch 256** | ebenda |

Amdahl-Deckel bei einem Inferenz-Anteil f und einem Inferenz-Speedup s:
Gesamt = 1/((1-f) + f/s). Mit f=0,81: s=2 ⇒ **1,7x**, s=5 ⇒ **2,8x**,
s=∞ ⇒ 5,3x. Das ist der groesste bekannte offene Durchsatz-Hebel --
Self-Play ist der dominante Kostenblock der Spirale (12.000 neue Partien
je Generation).

## Die Frage, die tatsaechlich entscheidet

Nicht "ist die GPU schneller als die CPU" (ja, bei Batch 256), sondern:
**welcher Batch ist in unserer Architektur real erreichbar, und schlaegt
die GPU bei DIESEM Batch den heutigen CPU-Aggregatdurchsatz?**

Der Grund: die Suche ist je Thread tiefen-sequenziell und blockiert auf
ihrer Blattauswertung. Bei 11 Threads liegt der natuerliche Batch bei
~11, nicht bei 256. Und der GPU-Vorteil bricht bei kleinen Batches
zusammen (Kernel-Start, PCIe-Transfer, Python-Grenze). Genau daran ist
schon einmal ein Batching-Versuch gescheitert: **Root-Batching kam mit
1,01x zurueck** -- allerdings CPU-seitig, was die GPU-Praemisse NICHT
testet. Diese Vorgeschichte ist der Grund, die Kennlinie zu messen statt
sie zu rechnen.

## Probe -- zwei Teile, beide billig, KEINE Implementierung

### Teil 1: GPU-Durchsatzkennlinie ueber die Batchgroesse

Champion-Netz (`alphazero_v21_2d_brierbest.pth`, 2D-Encoder) auf der GPU,
Vorwaerts-Pass gemessen bei Batch **1, 2, 4, 8, 11, 16, 32, 64, 128,
256, 512**. Je Punkt: Evals/s, nach Aufwaermlauf, Median ueber mehrere
Wiederholungen, `torch.cuda.synchronize()` vor der Zeitnahme (sonst
misst man die asynchrone Queue statt die Rechenzeit).

**Pflicht-Bedingung**: nur bei IDLER GPU messen. Laeuft ein Training,
ist die Zahl wertlos (Nutzer-Erfahrung: GPU-Teilung kostete einmal den
Faktor 9). Die Probe wartet daher auf ein freies GPU-Fenster.

Gemeldet wird zusaetzlich der **Break-even-Batch**: die kleinste
Batchgroesse, ab der die GPU den CPU-Aggregatdurchsatz von 11 Threads
(17.600-35.200 Evals/s) uebertrifft.

### Teil 2: erreichbarer Batch OHNE Umbau der Suche

Reine Bestandsaufnahme, kein Code: wie viele Blattauswertungen sind im
heutigen Self-Play gleichzeitig in der Luft? Erwartung aus der
Architektur = Anzahl paralleler Suchthreads (11 gemessen stabil, 8->11
brachte 1,39x). Zu dokumentieren ist, WAS es braeuchte, um 256 zu
fuellen -- deutlich mehr gleichzeitige Partien (RAM je Suchbaum ist die
Grenze) oder blatt-parallele Auswertung innerhalb einer Suche
(Virtual-Loss-Klasse Umbau). Beides ist NICHT Teil dieser Probe.

## Entscheidungsregeln (vorab)

1. **GPU-Durchsatz beim erreichbaren Batch (~11-16) < CPU-Aggregat**
   ⇒ ein zentraler Batcher ohne Such-Umbau ist sinnlos. `#82` wird
   **geschlossen** mit dem Vermerk "nur zusammen mit blatt-paralleler
   Auswertung sinnvoll" -- und ist damit kein UNKLAR mehr, sondern
   entschieden.
2. **GPU-Durchsatz beim erreichbaren Batch >= 2x CPU-Aggregat**
   ⇒ der Umbau ist gerechtfertigt; er bekommt eine EIGENE
   Vorregistrierung (Architektur, Cross-Language-Queue, Fallback,
   Paritaets-Nachweis dass die Suchergebnisse unveraendert bleiben).
   Diese Probe entscheidet NICHT ueber die Umsetzung.
3. **Dazwischen (1x bis 2x)** ⇒ zurueckgestellt mit dokumentierter Zahl.
   Begruendung vorab: ein Aufwand dieser Groesse (Cross-Language-Batching
   im heissesten Pfad, plus Paritaets-Risiko an der Suche) rechtfertigt
   sich nicht fuer weniger als eine Verdopplung, wenn der Amdahl-Deckel
   die Gesamtwirkung ohnehin auf 1,7x bei s=2 begrenzt.
4. **Deskriptiv mitfuehren, keine Entscheidungsgroesse**: Speicherbedarf
   je Batchgroesse (falls 256 am VRAM scheitert, ist die 203k-Zahl aus
   `#81` ohnehin unerreichbar).

## Ausdruecklich NICHT Teil dieser Probe

- Keine Implementierung, kein Prototyp, keine Aenderung an
  `self_play.py` oder der Engine.
- Keine Neubewertung des Root-Batchings (CPU-seitig gemessen, 1,01x,
  bleibt geschlossen).
- Kein Vergleich gegen tract-CPU-Zahlen aus der Literatur -- der
  CPU-Bezugswert ist ausschliesslich unsere eigene Messung.

## Kosten und Einplanung

Teil 1: ~15 min bei freier GPU. Teil 2: Dokumentation, kein Rechenbedarf.
**Einplanung: im ersten freien GPU-Fenster nach dem Gewichts-Sweep**
(`PREREG_task_d_gewichte.md`) -- eine Messung zwischen zwei Sweep-Armen
waere zwar zeitlich moeglich, verschiebt aber den Sweep und liefert bei
konkurrierender Last ohnehin keine gueltige Zahl.
