//! Gemeinsame, algorithmus-unabhängige Baum-Hilfsfunktionen für die
//! Heuristik-MCTS (`mcts.rs`, UCB1 + progressive Widening) und die
//! Netz-PUCT-Suche (`net_mcts.rs`, PUCT + Policy-Masse-Cutoff).
//!
//! Beide Bäume teilen dieselbe STRUKTUR (Force-Reply-Garantie an Tiefe 0/1,
//! Nachlauf-Schließung offener Enden, Tiefenberechnung) — nur Selektions-
//! formel, Blattbewertung und Kandidaten-Verwaltung unterscheiden sich
//! fundamental (UCB1 ohne Prior + besuchszahl-getriebenes Widening vs. PUCT
//! mit Netz-Prior + Policy-Masse-Cutoff bei Knoten-Erzeugung). Diese Datei
//! fasst NUR die strukturell identischen Teile zusammen, damit ein Fix daran
//! (wie die Force-Reply-Nachlauf-Ergänzung dieser Session) künftig nur noch
//! EINMAL geschrieben werden muss, statt von Hand in beide Dateien übertragen
//! zu werden — die eigentlichen Suchalgorithmen bleiben bewusst getrennt.

/// Minimale Knoten-Schnittstelle, die beide `Node`-Typen (`mcts::Node`,
/// `net_mcts::Node`) erfüllen — genug, um Baumstruktur (nicht Bewertung)
/// generisch zu behandeln.
pub trait SearchNode {
    fn parent(&self) -> Option<usize>;
    fn children(&self) -> &[usize];
    fn terminal(&self) -> bool;
}

/// Tiefe des Teilbaums unter `nid` (0 = Blatt).
pub fn subtree_depth<T: SearchNode>(nodes: &[T], nid: usize) -> u32 {
    let children = nodes[nid].children();
    if children.is_empty() {
        0
    } else {
        1 + children.iter().map(|&c| subtree_depth(nodes, c)).max().unwrap()
    }
}

/// Force-Reply-Garantie (Tiefe 0/1, Wurzel = Index 0): das zuletzt erzeugte
/// Kind von `nid` muss selbst schon eine eigene Antwort (Kind) haben, bevor
/// `nid` weiterbreitert werden darf — sonst vergliche man Kandidaten nur
/// anhand des rohen Zustands direkt nach dem eigenen Zug, ohne jede
/// Gegner-Reaktion. Gibt den zu erzwingenden Ziel-Index zurück, falls die
/// Garantie noch nicht erfüllt ist (Aufrufer setzt `nid` darauf und
/// wiederholt die Selection-Schleife).
pub fn force_reply_target<T: SearchNode>(nodes: &[T], nid: usize) -> Option<usize> {
    if nid != 0 && nodes[nid].parent() != Some(0) {
        return None;
    }
    let &last_child = nodes[nid].children().last()?;
    if nodes[last_child].children().is_empty() && !nodes[last_child].terminal() {
        Some(last_child)
    } else {
        None
    }
}

/// Nachlauf-Scan NACH Abschluss der regulären Sim-Schleife: die live Force-
/// Reply-Garantie oben greift nur, wenn die Selektion (UCB1/PUCT) einen
/// Knoten je wieder besucht — ein Wurzel-/Tiefe-1-Kandidat mit sehr
/// niedrigem Score/Prior wird u.U. nie erneut selektiert, sein einziges
/// erzwungenes Kind bleibt dann dauerhaft ohne eigene Antwort. Findet alle
/// solchen offenen Enden (Wurzel- und Tiefe-1-Knoten, deren zuletzt
/// hinzugefügtes Kind selbst noch keins hat) und gibt deren Kind-Indizes
/// zurück — das eigentliche Schließen (`expand_and_backprop`, je Algorithmus
/// unterschiedlich: zufällige vs. höchste-Prior-Auswahl, DFS- vs. Netz-Wert)
/// bleibt Sache des Aufrufers. Bewusst NICHT auf tiefere Knoten ausgeweitet:
/// dort ist ein kinderloses letztes Kind die normale, gewollte Baumgrenze,
/// kein offenes Ende.
pub fn nachlauf_targets<T: SearchNode>(nodes: &[T]) -> Vec<usize> {
    let built = nodes.len();
    let mut targets = Vec::new();
    for i in 0..built {
        if i != 0 && nodes[i].parent() != Some(0) {
            continue;
        }
        if nodes[i].terminal() {
            continue;
        }
        let Some(&last_child) = nodes[i].children().last() else { continue };
        if nodes[last_child].terminal() || !nodes[last_child].children().is_empty() {
            continue;
        }
        targets.push(last_child);
    }
    targets
}
