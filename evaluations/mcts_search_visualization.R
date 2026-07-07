library(tidyverse)
library(networkD3)
library(plotly)
library(collapsibleTree)
library(data.tree)


setwd("~/Projekte/mosaic-AI/evaluations")

# 1. Parameter definieren
set.seed(42) # Für die Reproduzierbarkeit

if (file.exists("tree.RData")) {
  load("tree.RData")
  
} else {
  df <- 3       # Freiheitsgrade (niedrig sorgt für einen steilen Abfall)
  
  
  x_chi <- c(0.5, 1.2, 1.8, 4, 6, 8, 8.1, 8.2, 8.3, 8.4)
  
  # 3. Dichten (Wahrscheinlichkeitsdichten) berechnen
  chi_dens <- dchisq(x_chi, df = df)
  
  
  root <- tribble(
    ~action,
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "I",
    "J"
  )
  
  root <- root %>%
    mutate(policy = sample((chi_dens / sum(chi_dens) * 0.95)),
           points = 50 + policy * 25 + runif(nrow(root), -2, 2)) %>%
    mutate(points = round(points))
  
  child <- tribble(
    ~action,
    "a",
    "b",
    "c",
    "d",
    "e",
    "f",
    "g",
    "h",
    "i",
    "j"
  )
  
  child_list <- local({
    child <- tribble(
      ~action,
      "a",
      "b",
      "c",
      "d",
      "e",
      "f",
      "g",
      "h",
      "i",
      "j"
    )
    
    out <- map(1:nrow(root), \(i) {
      child %>%
        mutate(policy = sample((chi_dens / sum(chi_dens) * 0.95)),
               points = 50 + policy * 25 + runif(nrow(root), -2, 2)) %>%
        mutate(points = round(points))
    })
    
    names(out) <- root$action
    out
    
  })
  
  grandchild_list <- local({
    grandchild <- tribble(
      ~action,
      "aa",
      "bb",
      "cc",
      "dd",
      "ee"
    )
    
    x_chi_gc <- c(1.4, 1.8, 3, 8, 8.3)
    
    # 3. Dichten (Wahrscheinlichkeitsdichten) berechnen
    chi_dens_gc <- dchisq(x_chi_gc, df = df)
    
    out2 <- map(1:nrow(root), \(i) {
      out1 <- map(1:nrow(child_list[[i]]), \(j) {
        grandchild %>%
          mutate(policy = sample((chi_dens_gc / sum(chi_dens_gc) * 0.95)),
                 points = 56 + policy * 25 + runif(nrow(grandchild), -2, 2)) %>%
          mutate(points = round(points))
        
      })
      names(out1) <- child$action
      out1
    })
    names(out2) <- root$action
    out2
    
  })  
  save(root, child_list, grandchild_list, file = "tree.RData")
}

sims <- 200

# ── Q-Werte anhaengen (== mcts.rs::normalize_score, tanh-Stauchung) ──────────
normalize_score <- function(points, scale = 50) {
  (tanh(points / scale) + 1) / 2
}

root <- root %>% mutate(q = normalize_score(points))
child_list <- map(child_list, ~ .x %>% mutate(q = normalize_score(points)))
grandchild_list <- map(grandchild_list, ~ map(.x, ~ .x %>% mutate(q = normalize_score(points))))

# ── Knoten als Environment (Referenzsemantik -> Mutation ohne Neuzuweisung) ──
new_node <- function(name, depth, prior, q, parent, untried, terminal) {
  e <- new.env()
  e$name     <- name
  e$depth    <- depth
  e$prior    <- prior
  e$q        <- q
  e$parent   <- parent
  e$children <- integer(0)
  e$untried  <- untried
  e$visits   <- 0
  e$value    <- 0
  e$terminal <- terminal
  e
}

init_tree <- function() {
  list(new_node("Wurzel", depth = 0, prior = NA, q = NA, parent = NA,
                untried = root %>% arrange(desc(policy)), terminal = FALSE))
}

# ── Force-Reply: nur Tiefe 0 (Wurzel) und Tiefe 1 (ihre direkten Kinder) ─────
# == net_mcts.rs:433-441. Letztes erzeugtes Kind ohne eigenes Kind UND nicht
# terminal -> muss zuerst seine Antwort bekommen, bevor hier weiter gebreitert wird.
force_reply <- function(nodes, nid) {
  node <- nodes[[nid]]
  if (nid == 1 || (!is.na(node$parent) && node$parent == 1)) {
    if (length(node$children) > 0) {
      last_id    <- tail(node$children, 1)
      last_child <- nodes[[last_id]]
      if (length(last_child$children) == 0 && !last_child$terminal) {
        return(last_id)
      }
    }
  }
  NULL
}

# ── PUCT-Auswahl unter bereits erzeugten Kindern == net_mcts.rs:280-301 ──────
best_puct <- function(nodes, nid, c_puct = 1.5) {
  node     <- nodes[[nid]]
  psum     <- sum(map_dbl(node$children, ~ nodes[[.x]]$prior))
  sqrt_pv  <- sqrt(max(node$visits, 1))
  scores <- map_dbl(node$children, function(cid) {
    child <- nodes[[cid]]
    q <- if (child$visits > 0) child$value / child$visits else 0
    p <- child$prior / psum
    q + c_puct * p * sqrt_pv / (1 + child$visits)
  })
  node$children[[which.max(scores)]]
}

# ── Expansion: hoechsten verbleibenden Prior aus untried nehmen ──────────────
# Tiefe 0 -> Kind aus child_list[[Aktion]]; Tiefe 1 -> Enkel aus
# grandchild_list[[Wurzel-Aktion]][[Kind-Aktion]]; Tiefe 2 (Enkel) ist terminal.
expand_node <- function(nodes, nid) {
  node <- nodes[[nid]]
  cand <- node$untried[1, ]
  node$untried <- node$untried[-1, ]

  child_untried <- tibble()
  child_terminal <- TRUE
  if (node$depth == 0) {
    child_untried  <- child_list[[cand$action]] %>% arrange(desc(policy))
    child_terminal <- FALSE
  } else if (node$depth == 1) {
    # node$name ist selbst schon die Wurzel-Aktion (z.B. "B") -- NICHT
    # nodes[[node$parent]]$name (das waere "Wurzel", die falsche Ebene).
    child_untried  <- grandchild_list[[node$name]][[cand$action]] %>% arrange(desc(policy))
    child_terminal <- FALSE
  }

  new_id <- length(nodes) + 1
  nodes[[new_id]] <- new_node(cand$action, depth = node$depth + 1, prior = cand$policy,
                               q = cand$q, parent = nid, untried = child_untried,
                               terminal = child_terminal)
  node$children <- c(node$children, new_id)
  list(nodes = nodes, new_id = new_id)
}

# ── Backprop: Pfad zurueck bis zur Wurzel, visits/value erhoehen ────────────
backprop <- function(nodes, nid, value) {
  cur <- nid
  while (!is.na(cur)) {
    nodes[[cur]]$visits <- nodes[[cur]]$visits + 1
    nodes[[cur]]$value  <- nodes[[cur]]$value + value
    cur <- nodes[[cur]]$parent
  }
  nodes
}

# ── Haupt-Sim-Schleife == net_mcts.rs::build_net_tree, sim-loop ─────────────
run_sims <- function(n_sims, c_puct = 1.5) {
  nodes <- init_tree()
  log <- character(n_sims)
  leaf_depths <- integer(n_sims)   # Tiefe des Blatts, das JEDE Sim am Ende erreicht
  for (s in seq_len(n_sims)) {
    nid <- 1
    steps <- character(0)
    repeat {
      fr <- force_reply(nodes, nid)
      if (!is.null(fr)) {
        steps <- c(steps, sprintf("Force-Reply->%s", nodes[[fr]]$name))
        nid <- fr
        next
      }
      node <- nodes[[nid]]
      if (node$terminal) {
        steps <- c(steps, sprintf("[%s terminal]", node$name))
        break
      }
      if (nrow(node$untried) > 0) {
        res   <- expand_node(nodes, nid)
        nodes <- res$nodes
        steps <- c(steps, sprintf("Expand %s->%s(P=%.3f)", node$name,
                                   nodes[[res$new_id]]$name, nodes[[res$new_id]]$prior))
        nid <- res$new_id
        break
      }
      if (length(node$children) == 0) {
        steps <- c(steps, sprintf("[%s keine Kinder]", node$name))
        break
      }
      best  <- best_puct(nodes, nid, c_puct)
      steps <- c(steps, sprintf("PUCT %s->%s", node$name, nodes[[best]]$name))
      nid <- best
    }
    value <- nodes[[nid]]$q
    leaf_depths[s] <- nodes[[nid]]$depth
    nodes <- backprop(nodes, nid, value)
    log[s] <- sprintf("Sim %3d: %s", s, paste(steps, collapse = " | "))
  }
  list(nodes = nodes, log = log, leaf_depths = leaf_depths)
}

# ── Zusammenfassung: gewaehlter Pfad, maximale Tiefe, Tiefenverteilung ──────
# "Gewaehlter Pfad" == best_root_child-Logik (mcts.rs:563-568): an jeder Ebene
# das meistbesuchte Kind, absteigend bis kein Kind mehr existiert.
chosen_path <- function(nodes) {
  path <- character(0)
  nid <- 1
  repeat {
    node <- nodes[[nid]]
    if (length(node$children) == 0) break
    best_child <- node$children[[which.max(map_dbl(node$children, ~ nodes[[.x]]$visits))]]
    path <- c(path, nodes[[best_child]]$name)
    nid <- best_child
  }
  path
}

summarize_tree <- function(result) {
  nodes  <- result$nodes
  depths <- map_dbl(nodes, ~ .x$depth)

  cat("Gewaehlter Pfad (meistbesuchter Ast je Ebene):",
      paste(chosen_path(nodes), collapse = " -> "), "\n\n")

  cat("Maximale Tiefe im Baum:", max(depths), "\n\n")

  cat("Erzeugte Knoten je Tiefe (wie viele verschiedene Knoten existieren):\n")
  print(table(depths))
  cat("\n")

  cat("Blatt-Tiefe je Simulation (wie oft endete eine Sim in dieser Tiefe):\n")
  print(table(result$leaf_depths))
}

result <- run_sims(sims)
#cat(result$log, sep = "\n")
summarize_tree(result)

# ==============================================================================
# 1. KNOTEN IN EINE ECHTE BAUMSTRUKTUR UMSETZEN (Kein bind_rows-Fehler möglich)
# ==============================================================================

# Wir lesen die Environments flach aus
nodes_list <- list()
for (i in seq_along(result$nodes)) {
  node <- result$nodes[[i]]
  q_val <- if (node$visits > 0) node$value / node$visits else 0
  
  # Wir erstellen hier nur eine Standard-Liste (kein Dataframe!)
  nodes_list[[i]] <- list(
    id        = i,
    name      = as.character(node$name),
    depth     = as.integer(node$depth),
    visits    = as.integer(node$visits),
    q         = q_val,
    prior     = if (is.na(node$prior)) 0 else as.numeric(node$prior),
    parent_id = if (is.na(node$parent)) NA else as.integer(node$parent)
  )
}

# Wir erstellen ein leeres data.tree-Objekt für die Wurzel (Knoten 1)
root_node <- nodes_list[[1]]
root_label <- sprintf("Wurzel (Sims=%d)", root_node$visits)
tree_root  <- Node$new(root_label)
tree_root$visits <- root_node$visits

# Ein Hilfs-Verzeichnis, um erstellte Baumknoten direkt wiederzufinden
node_mapping <- list()
node_mapping[[1]] <- tree_root

# Wir hängen alle weiteren Knoten (ab Index 2) an ihre jeweiligen Eltern an
if (length(nodes_list) > 1) {
  for (i in 2:length(nodes_list)) {
    curr <- nodes_list[[i]]
    parent_id <- curr$parent_id
    
    if (!is.na(parent_id) && !is.null(node_mapping[[parent_id]])) {
      parent_tree_node <- node_mapping[[parent_id]]
      
      # Schönes Label für den aktuellen MCTS-Zustand bauen
      child_label <- sprintf("%s (N=%d, Q=%.2f, P=%.2f)", curr$name, curr$visits, curr$q, curr$prior)
      
      # Knoten im Baum einfügen
      child_tree_node <- parent_tree_node$AddChild(child_label)
      child_tree_node$visits <- curr$visits
      
      # Für eventuelle Kinder dieses Knotens abspeichern
      node_mapping[[i]] <- child_tree_node
    }
  }
}

# ==============================================================================
# 2. BAUM RNDERN MIT VOLLER KLAPP- UND ZOOM-INTERAKTIVITÄT
# ==============================================================================

# collapsibleTree erkennt das data.tree-Format automatisch und schaltet 
# die native JavaScript-Klicklogik für alle Ebenen (inkl. Tiefe 3) frei.
tree_widget <- collapsibleTree(
  tree_root,
  attribute = "visits",  # Knotengröße skaliert nach MCTS-Besuchen (N)
  zoomable = TRUE,       # Aktiviert Mausrad-Zoom & Drag-and-Drop
  fontSize = 11,
  width = 1100,
  height = 700
)

# Widget anzeigen
tree_widget
