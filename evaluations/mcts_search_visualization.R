library(tidyverse)


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

