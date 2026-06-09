import pickle, glob
from agents.neural_net import action_to_id

files = sorted(glob.glob('data/selfplay_v3*.pkl'))[:10]
moon = sun = 0
for f in files:
    with open(f, 'rb') as fh: data = pickle.load(fh)
    for step in data:
        policy = step.get('policy', [])
        if not policy: continue
        top = max(policy, key=lambda p: p['prob'])
        a = top['action']
        if a.get('type') == 'stone':
            if a.get('factory_index') == 5: moon += 1
            else: sun += 1

total = sun + moon
if total:
    print(f'Sonne: {sun} ({sun/total*100:.1f}%)')
    print(f'Mond:  {moon} ({moon/total*100:.1f}%)')
    print(f'Total Stone top-actions: {total}')
else:
    print('Keine Stone Top-Aktionen')