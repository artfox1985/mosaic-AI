# Loeschvorschlag: der legacy-mirror-Stand im restic-Repo (2026-09-07, 15:50)

**Anlass:** Nutzer 2026-09-07: *"schau in das restic repo archiv. dort liegen viele self
play leichen herum"* und *"den ganzen snapshot raeumst sicher nicht weg. wenn dann einzelne
dateien daraus. der loewenanteil werden die self plays und die modelle sein."*

**Betroffen ist genau EIN Stand:** `61579f2e`, 31.08. 01:02, Tag `legacy-mirror`,
**100,60 GiB**. Alle uebrigen 36 Staende liegen zwischen 0,2 und 7,9 GiB. Er ist der
einmalige Import des stillgelegten Spiegels `D:\Archiv-Spiegel`
([[project_archiv_mirror_retired]]) und enthaelt den kompletten Projektbaum, wie er am
31.08. aussah, unter `mirror/`.

**Die Vermutung des Nutzers ist gemessen bestaetigt** (`tools/restic_legacy_inventory.sh`,
rein lesend): **97,40 GiB der 100,60 sind `.pkl`**, also 9.437 Self-Play-Korpora. Modelle
sind mit 1,78 GiB (107 `.onnx` plus 107 `.pth`) der zweitgroesste, aber kleine Posten.

## Was gestrichen werden koennte (rund 92 GiB)

### a) Lose Korpora der Aeren v18 bis v20 in `mirror/data/` (49,6 GiB)

| Generator | Groesse | Dateien |
| --- | --- | --- |
| `v20wdlsw` | 12,61 GiB | 800 |
| `v19wdlsw` | 12,49 GiB | 800 |
| `v18` | 9,00 GiB | 600 |
| `v20wdl` | 6,21 GiB | 400 |
| `v19wdl` | 6,17 GiB | 400 |
| `v19wdlann` | 3,11 GiB | 200 |

Begruendung: Alt-Regel-Korpora werden nie wieder ins Fenster genommen
([[project_replay_window_strategy]]). Sie sind aus dem Baum verschwunden -- der Stand ist
ihre einzige Kopie.

### b) Geschlossene Untersuchungslinien (36,3 GiB)

| Verzeichnis | Groesse | Dateien | Status der Linie |
| --- | --- | --- | --- |
| `mirror/data/asym_corpus/` | 24,77 GiB | 1.605 | Asym-Befund NULL ([[project_asym_null_and_seeding_plan]]) |
| `mirror/data/ownership_corpus/` | 11,28 GiB | 807 | Ownership-Kopf geschlossen, Gewicht 0 ([[project_ownership_head_closed]]) |
| `mirror/data/archive_v18_ausserhalb_v21fenster_20260809/` | 0,83 GiB | 56 | schon damals als ausserhalb des Fensters abgelegt |
| `mirror/data/corpus_probe/` | 0,21 GiB | 10 | Sondenmaterial |

**Alle vier sind aus dem Baum verschwunden** (geprueft 2026-09-07). Der Stand ist ihre
einzige Kopie. Ihre ERGEBNISSE stehen in den Preregs; verloren gingen die Rohdaten, aus
denen man sie neu berechnen koennte.

## Was NICHT gestrichen werden sollte

| Pfad | Groesse | Warum |
| --- | --- | --- |
| `mirror/models/` | 1,76 GiB | 107 Modelle gegen 23 im heutigen Baum. Billige Versicherung fuer die Elo-Leiter: Cross-Aera-Vergleiche sind Normalfall ([[project_anchor_era_rule]]), und ein Modell, das fehlt, macht eine Kante unwiederholbar |
| `mirror/data/holdout/` | 4,17 GiB | Referenzsatz, LEBT im Baum (305 Dateien) und wird von mindestens acht Sonden gelesen. Streichen brauchte es nicht -- er liegt ohnehin in den Tagesstaenden |
| **`mirror/data/seed_corpus/`** | **5,39 GiB** | **904 Dateien, aus dem Baum verschwunden -- ABER die Seeding-Linie ist NICHT geschlossen.** Sie ist die einzige Intervention mit positivem Value-Zustandssignal (p 0,017). Weg B ersetzt zwar den Offline-Weg, braucht aber keine alten Korpora. **Nutzer-Entscheid** |

## Der Vorbehalt, der jede Groessenangabe oben relativiert

**restic dedupliziert, und die genannten GiB sind NOMINALE Groessen, nicht der
freiwerdende Platz.** Ein Blob verschwindet erst, wenn KEIN verbleibender Stand ihn mehr
referenziert. Der aelteste Tagesstand ist vom 31.08. 01:55, der Spiegel-Import vom 31.08.
01:02 -- lagen `asym_corpus` und Co. an dem Tag noch im Baum, stecken sie auch in
Tagesstaenden und ein Prune gibt sie nicht frei.

**Deshalb wird vor jeder Loeschung gemessen, nicht geschaetzt:**

```
restic rewrite --dry-run --exclude '<muster>' 61579f2e
restic prune --dry-run
```

Beide sind rein lesend. Erst ihr Ergebnis sagt, wie viel ein Prune wirklich holt.

## Ablauf, wenn freigegeben

1. `restic rewrite --dry-run` mit den Mustern -- zeigt, was herausfiele.
2. `restic prune --dry-run` -- zeigt den tatsaechlich freiwerdenden Platz.
3. Ergebnis dem Nutzer vorlegen. **Erst dann** `rewrite --forget` und `prune`.
4. `restic check` danach, weil ein Prune Pack-Dateien umschreibt.

**Nichts davon passiert ohne pfadgenaue Freigabe.** Ein Prune ist endgueltig, und fuer
alles unter (a) und (b) ist dieser Stand die einzige Kopie im Haus.
