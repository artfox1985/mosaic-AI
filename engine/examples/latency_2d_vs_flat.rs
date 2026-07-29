//! Task #11, Phase-2-Vorentscheidung: was kostet ein 2D-Forward-Pass in tract
//! (CPU) gegenueber dem flachen MLP?
//!
//! Entscheidet das Kanalbudget und die Broadcast-vs-Zwei-Input-Frage, BEVOR
//! trainiert wird: ist die Conv-Inferenz z.B. 5x teurer, wird schon die
//! Gating-Arena zaeh und Self-Play spaeter unrealistisch.
//!
//! MESSDESIGN: die Netze werden INTERLEAVED evaluiert (Runde fuer Runde je ein
//! Aufruf pro Netz). Auf einer Maschine, auf der parallel ein Arena-Lauf
//! rechnet, sind die Absolutzeiten dadurch zwar inflationiert, das
//! VERHAELTNIS -- die eigentliche Entscheidungsgroesse -- bleibt aber robust,
//! weil Lastschwankungen beide Netze gleichermassen treffen.
//!
//! Aufruf:  cargo run --release --example latency_2d_vs_flat -- \
//!              name=pfad.onnx:eingabelaenge  [weitere ...]

use mosaic_rust::net::Net;
use std::time::Instant;

fn median(v: &mut Vec<f64>) -> f64 {
    v.sort_by(|a, b| a.partial_cmp(b).unwrap());
    v[v.len() / 2]
}

fn p90(v: &mut Vec<f64>) -> f64 {
    v.sort_by(|a, b| a.partial_cmp(b).unwrap());
    v[(v.len() as f64 * 0.9) as usize]
}

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    if args.is_empty() {
        eprintln!("Nutzung: latency_2d_vs_flat name=pfad.onnx:len [...]");
        std::process::exit(1);
    }
    let mut nets: Vec<(String, Net, Vec<f32>)> = Vec::new();
    for a in &args {
        let (name, rest) = a.split_once('=').expect("name=pfad:len");
        let (path, len) = rest.rsplit_once(':').expect("pfad:len");
        let len: usize = len.parse().expect("len");
        let net = Net::load_auto(path).expect("load_auto");
        // Deterministische Pseudo-Zufallseingabe (kein rand-Import noetig).
        let feats: Vec<f32> = (0..len)
            .map(|i| ((i as f32 * 12.9898).sin() * 43758.547).fract().abs())
            .collect();
        nets.push((name.to_string(), net, feats));
    }

    const WARMUP: usize = 30;
    const RUNS: usize = 300;

    for (name, net, feats) in &nets {
        for _ in 0..WARMUP {
            let _ = net.eval(feats).expect("warmup eval");
        }
        let _ = name;
    }

    let mut times: Vec<Vec<f64>> = vec![Vec::with_capacity(RUNS); nets.len()];
    let mut times_pair: Vec<Vec<f64>> = vec![Vec::with_capacity(RUNS); nets.len()];
    for _ in 0..RUNS {
        for (i, (_, net, feats)) in nets.iter().enumerate() {
            let t = Instant::now();
            let _ = net.eval(feats).expect("eval");
            times[i].push(t.elapsed().as_secs_f64() * 1000.0);
            let t = Instant::now();
            let _ = net.eval_pair(feats, feats).expect("eval_pair");
            times_pair[i].push(t.elapsed().as_secs_f64() * 1000.0);
        }
    }

    println!("{:<22}{:>12}{:>12}{:>14}{:>14}", "Netz", "eval med", "eval p90", "pair med", "pair p90");
    let mut base_med = None;
    for (i, (name, _, _)) in nets.iter().enumerate() {
        let m = median(&mut times[i].clone());
        let p = p90(&mut times[i].clone());
        let mp = median(&mut times_pair[i].clone());
        let pp = p90(&mut times_pair[i].clone());
        let ratio = match base_med {
            None => {
                base_med = Some(m);
                "1.00x (Basis)".to_string()
            }
            Some(b) => format!("{:.2}x", m / b),
        };
        println!("{:<22}{:>10.3}ms{:>10.3}ms{:>12.3}ms{:>12.3}ms   {}", name, m, p, mp, pp, ratio);
    }
}
