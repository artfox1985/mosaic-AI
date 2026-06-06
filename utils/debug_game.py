"""
debug_game.py — Interaktives Diagnose-Tool für mosaic-AI

Verwendung:
    python debug_game.py [--seed N] [--rounds N] [--agent0 random|greedy] [--agent1 random|greedy]

Zeigt jeden Schritt mit Phase, Aktion, Fehler, und Spielzustand.
Bei Fehler oder Freeze wird der vollständige Kontext ausgegeben.
"""
import sys, argparse, traceback
sys.path.insert(0, '.')

from agents.agent_env import MosaicEnv
from agents.agents import GreedyAgent, RandomAgent
from engine.round_end import check_drafting_complete
from engine.game import generate_dome_moves, generate_bonus_chip_moves
from engine.validation import generate_valid_moves


def make_agent(name):
    return GreedyAgent() if name == 'greedy' else RandomAgent()


def dump_state(env, label="STATE"):
    state = env.state
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"  Round={state.round_number}  Phase={state.phase}  CurrentPlayer=P{state.current_player}")
    print(f"  Scores: P0={state.players[0].score}  P1={state.players[1].score}")
    print(f"  Dome display: {[t.tile_id for t in state.dome_display]}")
    print(f"  Dome pool remaining: {len(state.dome_tile_pool)}")

    for fi, f in enumerate(state.factories):
        print(f"  Fab {f.factory_id}: fully_empty={f.is_fully_empty}  chip={f.bonus_chip}  revealed={f.bonus_chip_revealed}")
    print(f"  Large factory: empty={state.large_factory.is_empty}")

    for i, p in enumerate(state.players):
        complete = [(j, str(r.color), f"{len(r.tiles)}/{r.capacity}") 
                    for j, r in enumerate(p.pattern_lines) if r.tiles]
        broken = len(p.broken_tiles)
        tokens = p.player_tokens_used
        print(f"  P{i} ({p.name}): tokens_used={tokens}  broken={broken}  "
              f"has_used_all={p.has_used_all_tokens(state.round_number)}")
        if complete:
            print(f"       pattern rows: {complete}")
        dome_slots = [(sr, sc) for sr in range(3) for sc in range(3)
                      if p.dome_grid.dome_slots[sr][sc] is not None]
        print(f"       dome slots filled: {dome_slots}")

    print(f"  check_drafting_complete: {check_drafting_complete(state)}")
    orig = state.current_player
    for pi in range(2):
        state.current_player = pi
        vm = len(generate_valid_moves(state))
        dm = len(generate_dome_moves(state))
        bm = len(generate_bonus_chip_moves(state))
        print(f"  P{pi} possible moves: stone={vm}  dome={dm}  bonus={bm}")
    state.current_player = orig
    print(f"{'='*60}\n")


def dump_tiling(env):
    ta = env._tiling_actions()
    print(f"  Tiling actions ({len(ta)}):")
    for a in ta:
        print(f"    {a}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed',   type=int, default=0)
    parser.add_argument('--steps',  type=int, default=500)
    parser.add_argument('--agent0', default='random', choices=['random', 'greedy'])
    parser.add_argument('--agent1', default='greedy', choices=['random', 'greedy'])
    parser.add_argument('--verbose', action='store_true', help='Print every step')
    parser.add_argument('--freeze-threshold', type=int, default=15,
                        help='Steps in same phase before declaring freeze')
    args = parser.parse_args()

    env = MosaicEnv(random_scoring_tiles=False)
    env.reset(seed=args.seed)
    agents = [make_agent(args.agent0), make_agent(args.agent1)]

    print(f"🎮 Debug run: seed={args.seed}  agents=[{args.agent0}, {args.agent1}]")
    print(f"   max_steps={args.steps}  freeze_threshold={args.freeze_threshold}\n")

    done = False
    steps = 0
    last_phase = env.state.phase
    last_round = env.state.round_number
    same_state_count = 0
    errors = []

    while not done and steps < args.steps:
        phase_before = env.state.phase
        round_before = env.state.round_number
        actions = env.valid_actions()
        pi = env.state.current_player
        action = agents[pi].choose(actions, {})

        try:
            obs, reward, done, info = env.step(action)
        except Exception as e:
            print(f"\n💥 UNCAUGHT EXCEPTION at step {steps+1}:")
            traceback.print_exc()
            dump_state(env, "STATE AT CRASH")
            print(f"  Action that caused crash: {action}")
            sys.exit(1)

        steps += 1
        has_error = 'error' in info

        # Track freeze
        if (env.state.phase == phase_before and 
            env.state.round_number == round_before):
            same_state_count += 1
        else:
            same_state_count = 0
            last_phase = env.state.phase
            last_round = env.state.round_number

        # Print every step if verbose
        if args.verbose or has_error:
            status = "❌ ERROR" if has_error else "  "
            print(f"Step {steps:4d} | P{pi} {action.get('type','?'):12s} | "
                  f"r={reward:+.1f} | scores={env.scores()} | "
                  f"phase={env.state.phase} R{env.state.round_number} {status}")
            if has_error:
                print(f"         Error: {info['error']}")
                errors.append((steps, action, info['error']))

        elif steps % 20 == 0:
            print(f"Step {steps:4d} | P{pi} {action.get('type','?'):12s} | "
                  f"r={reward:+.1f} | scores={env.scores()} | "
                  f"phase={env.state.phase} R{env.state.round_number}")

        # Detect freeze
        if same_state_count >= args.freeze_threshold:
            print(f"\n🧊 FREEZE DETECTED at step {steps} "
                  f"(stuck {same_state_count} steps in {env.state.phase}/R{env.state.round_number})")
            dump_state(env, "FROZEN STATE")
            if env.state.phase == 'tiling':
                dump_tiling(env)
            print(f"\n  Last action: {action}")
            if has_error:
                print(f"  Last error:  {info['error']}")
            sys.exit(1)

    # Summary
    print(f"\n{'='*60}")
    if done:
        print(f"✅ GAME COMPLETED in {steps} steps")
    else:
        print(f"⏱️  TIMEOUT after {steps} steps (max={args.steps})")

    print(f"  Final scores: P0={env.scores()[0]}  P1={env.scores()[1]}")
    print(f"  Final phase: {env.state.phase}  Round: {env.state.round_number}")

    if errors:
        print(f"\n⚠️  {len(errors)} error(s) during game:")
        for s, a, e in errors:
            print(f"  step {s}: {a.get('type')} → {e}")

    dump_state(env, "FINAL STATE")


if __name__ == '__main__':
    main()
