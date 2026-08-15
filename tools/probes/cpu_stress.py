import multiprocessing as mp
import time
import sys

def burn(seconds):
    end = time.time() + seconds
    x = 0
    while time.time() < end:
        x = (x * 1103515245 + 12345) & 0xFFFFFFFF

if __name__ == "__main__":
    seconds = float(sys.argv[1]) if len(sys.argv) > 1 else 600
    n = int(sys.argv[2]) if len(sys.argv) > 2 else (mp.cpu_count() or 4)
    print(f"CPU-Stress: {n} Prozesse fuer {seconds}s", file=sys.stderr)
    procs = [mp.Process(target=burn, args=(seconds,)) for _ in range(n)]
    for p in procs:
        p.start()
    for p in procs:
        p.join()
