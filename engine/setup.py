"""
Spielaufbau (Setup) für Mosaic-AI.

Verantwortlich für:
  1. Beutel + Ablageturm + Special-Vorrat erstellen
  2. Fabriken aufbauen und befüllen
  3. Große Fabrik (Tischmitte) initialisieren
  4. Spielerbretter aufbauen
  5. Kuppelplatten mischen und verteilen
  6. Bonusplättchen mischen und bereitstellen
  7. Startspieler festlegen

Mosaic-AI hat genau 2 Spieler und genau 5 Runden.
"""

from __future__ import annotations
import random
from dataclasses import dataclass, field

from engine.tile import TileColor, NORMAL_COLORS
from engine.dome import build_dome_tile_pool, build_bonus_chip_pool, DomeTile, BonusChip
from engine.factory import Factory, LargeFactory
from engine.board import PlayerBoard
from engine.supply import Bag, Tower, SpecialSupply


# Spielkonstanten
NUM_PLAYERS             = 2
NUM_ROUNDS              = 5
NUM_SMALL_FACTORIES     = 4   # kleine Fabriken
TILES_PER_SMALL_FACTORY = 4   # Steine pro kleiner Fabrik (Sun-Seite)
TILES_PER_LARGE_FACTORY = 5   # Steine in der großen Fabrik zu Rundenbeginn
DOME_TILES_EACH         = 9   # Kuppelplatten pro Spieler


@dataclass
class GameState:
    """
    Vollständiger Spielzustand von Mosaic-AI.

    Alle veränderlichen Zustände werden hier gehalten —
    Engine-Logik greift ausschließlich auf dieses Objekt zu.
    """
    # Steinvorräte
    bag:            Bag
    tower:          Tower
    special_supply: SpecialSupply

    # Fabriken
    factories:      list[Factory]      # 4 kleine Fabriken
    large_factory:  LargeFactory       # Tischmitte

    # Spielerbretter
    players:        list[PlayerBoard]  # immer 2 Spieler

    # Kuppelplatten
    dome_tile_pool:  list[DomeTile]    # verdeckter Stapel (F)
    dome_display:    list[DomeTile]    # 3 offen ausgelegte Kuppelplatten (G)

    # Bonusplättchen-Vorrat
    bonus_chip_pool: list[BonusChip]

    # Rundeninfo
    round_number:    int = 1
    current_player:  int = 0   # Index in players (0 oder 1)
    first_player_next_round: int = 0  # wer beginnt die nächste Runde

    # Spielphase
    phase: str = "drafting"   # "drafting" | "tiling" | "scoring" | "end"

    # Spiellog
    log: list[str] = field(default_factory=list)

    def log_event(self, msg: str) -> None:
        self.log.append(f"[R{self.round_number}] {msg}")

    @property
    def active_player(self) -> PlayerBoard:
        return self.players[self.current_player]

    @property
    def inactive_player(self) -> PlayerBoard:
        return self.players[1 - self.current_player]

    def switch_player(self) -> None:
        self.current_player = 1 - self.current_player

    def all_factories_empty(self) -> bool:
        """True wenn alle Fabriken und die Tischmitte leer sind."""
        return (
            all(f.is_fully_empty for f in self.factories)
            and self.large_factory.is_empty
        )

    def __repr__(self) -> str:
        lines = [
            f"=== Mosaic-AI — Runde {self.round_number}/5 ===",
            f"Phase: {self.phase}  |  Am Zug: {self.active_player.name}",
            f"Beutel: {self.bag.count}  Turm: {self.tower.count}  "
            f"Weiße Steine: {self.special_supply.count}",
            "",
        ]
        for f in self.factories:
            lines.append(f"  {f}")
        lines.append(f"  {self.large_factory}")
        lines.append("")
        for p in self.players:
            lines.append(repr(p))
        return "\n".join(lines)

    def clone(self) -> "GameState":
        # 1. Den State wie gewohnt erstellen
        new_state = GameState(
            bag=self.bag.clone(),
            tower=self.tower.clone(),
            special_supply=self.special_supply.clone(),
            factories=[f.clone() for f in self.factories],
            large_factory=self.large_factory.clone(),
            players=[p.clone() for p in self.players],
            dome_tile_pool=[t.clone() for t in self.dome_tile_pool],
            dome_display=[t.clone() for t in self.dome_display],
            bonus_chip_pool=list(self.bonus_chip_pool),
            round_number=self.round_number,
            current_player=self.current_player,
            first_player_next_round=self.first_player_next_round,
            phase=self.phase,
            log=[]  # Log für Performance leeren
        )

        # 2. Dynamisch hinzugefügte Attribute (wie die Wertungsplatten) manuell kopieren!
        if hasattr(self, 'scoring_tile_ids'):
            new_state.scoring_tile_ids = list(self.scoring_tile_ids)

        return new_state

# ---------------------------------------------------------------------------
# Setup-Funktionen
# ---------------------------------------------------------------------------

def _draw_with_refill(n: int, bag: Bag, tower: Tower) -> list:
    """Zieht n Steine; füllt Beutel aus Turm auf falls nötig."""
    drawn = bag.draw(n)
    if len(drawn) < n and not tower.is_empty:
        bag.refill_from_tower(tower)
        drawn += bag.draw(n - len(drawn))
    return drawn


def _fill_large_factory(large_factory: LargeFactory, bag: Bag, tower: Tower) -> None:
    """
    Befüllt die große Fabrik mit 5 Steinen.
    Sonderfall laut Regelwerk: Sind alle 5 Steine dieselbe Farbe,
    werden sie zurück in den Beutel gelegt und erneut gezogen —
    so lange bis mindestens 2 verschiedene Farben dabei sind.
    """
    while True:
        tiles = _draw_with_refill(TILES_PER_LARGE_FACTORY, bag, tower)
        if len(set(tiles)) >= 2:
            large_factory.sun_tiles = tiles
            return
        # Alle gleiche Farbe → zurück in den Beutel
        bag._tiles.extend(tiles)
        random.shuffle(bag._tiles)


def _fill_factories(
    factories: list[Factory],
    large_factory: LargeFactory,
    bag: Bag,
    tower: Tower,
    bonus_chip_pool: list | None = None,
) -> None:
    """
    Befüllt die 4 kleinen Fabriken mit je 4 Steinen und je 1 verdeckten Bonusplättchen
    und die große Fabrik mit 5 Steinen aus dem Beutel.
    Wenn der Beutel zwischendurch leer wird, wird er aus dem Turm
    aufgefüllt und weitergemacht.
    """
    for factory in factories:
        factory.sun_tiles = []
        factory.moon_stacks = []
        factory.bonus_chip_revealed = False
        factory.sun_tiles = _draw_with_refill(TILES_PER_SMALL_FACTORY, bag, tower)
        # Neues Bonusplättchen aus Pool (Regelwerk S.10 Phase 3)
        if bonus_chip_pool:
            factory.bonus_chip = bonus_chip_pool.pop()
        elif factory.bonus_chip is not None:
            # Altes Chip-Objekt behalten falls Pool leer (sollte nicht passieren)
            pass

    # Große Fabrik mit 5 Steinen befüllen (mit Sonderfall-Prüfung)
    _fill_large_factory(large_factory, bag, tower)


def _distribute_dome_tiles(
    players: list[PlayerBoard],
    dome_pool: list[DomeTile],
) -> list[DomeTile]:
    """
    Mischt den Kuppelplatten-Pool und gibt jedem Spieler seine
    Starthand. In Mosaic-AI wählen Spieler Kuppelplatten während
    des Spiels — sie werden hier noch nicht auf das Brett gelegt,
    sondern als verfügbarer Pool gehalten.
    Gibt den verbleibenden Pool zurück.
    """
    shuffled = list(dome_pool)
    random.shuffle(shuffled)
    return shuffled


def setup_new_game(
    player_names: list[str] | None = None,
    first_player: int = 0,
    seed: int | None = None,
) -> GameState:
    """
    Erstellt einen vollständig initialisierten Spielzustand für eine
    neue Partie Mosaic-AI.

    Args:
        player_names: Namen der 2 Spieler. Standard: ["Spieler 1", "Spieler 2"]
        first_player: Index (0 oder 1) des Startspielers. Standard: 0
        seed: Optionaler Zufalls-Seed für reproduzierbare Spiele (Tests/KI)

    Returns:
        GameState: Vollständiger, spielbereiter Zustand
    """
    if seed is not None:
        random.seed(seed)

    if player_names is None:
        player_names = ["Spieler 1", "Spieler 2"]
    assert len(player_names) == NUM_PLAYERS, "Mosaic-AI ist ein 2-Spieler-Spiel."

    # 1. Steinvorräte
    bag            = Bag.full()
    tower          = Tower()
    special_supply = SpecialSupply()

    # 2. Spielerbretter
    players = [
        PlayerBoard(player_id=i, name=name)
        for i, name in enumerate(player_names)
    ]

    # 3. Fabriken aufbauen + je 1 verdeckten Bonus-Chip
    bonus_pool = build_bonus_chip_pool()
    random.shuffle(bonus_pool)
    factories = [Factory(factory_id=i + 1) for i in range(NUM_SMALL_FACTORIES)]
    for i, factory in enumerate(factories):
        factory.bonus_chip = bonus_pool.pop()
    large_factory = LargeFactory()
    _fill_factories(factories, large_factory, bag, tower)

    # 4. Tischmitte bereits oben erstellt

    # 5. Kuppelplatten: verdeckter Stapel (F) + 3 offen auslegen (G)
    all_dome_tiles = build_dome_tile_pool()
    random.shuffle(all_dome_tiles)

    # Wir geben den Spielern ein einfaches Text-Kürzel mit. 
    # So weiß der Server: "Die Startkuppel muss noch aus der Mitte gezogen werden!"
    for pi in range(NUM_PLAYERS):
        players[pi].start_dome_tile = "Muss_noch_gezogen_werden"

    # Verdeckter Stapel (F) — Rest der Kuppeln
    dome_stack = all_dome_tiles   

    # 3 Kuppeln offen auslegen (G)
    dome_display = []
    for _ in range(3):
        if dome_stack:
            dome_display.append(dome_stack.pop(0))
    # ---> Ab hier liegen jetzt exakt 15 Kuppeln im Stapel!

    # 7. Verbleibende Bonusplättchen als Pool bereithalten

    # 8. Startspieler
    current_player = first_player

    state = GameState(
        bag=bag,
        tower=tower,
        special_supply=special_supply,
        factories=factories,
        large_factory=large_factory,
        players=players,
        dome_tile_pool=dome_stack,     # verdeckter Stapel (F)
        dome_display=dome_display,     # 3 offen ausgelegte Kuppeln
        bonus_chip_pool=bonus_pool,
        round_number=1,
        current_player=current_player,
        first_player_next_round=current_player,
    )

    state.log_event(
        f"Spiel gestartet. {players[first_player].name} beginnt."
    )

    return state


def setup_new_round(state: GameState) -> None:
    """
    Bereitet eine neue Runde vor:
      - Fabriken neu befüllen
      - Tischmitte leeren
      - Startspieler-Marker zurücksetzen
      - Spieler-Tokens zurücksetzen
      - Phase auf 'drafting' setzen
    """
    state.round_number += 1
    state.phase = "drafting"

    # Startspieler-Marker
    state.current_player = state.first_player_next_round
    state.large_factory.reset_for_new_round()

    # Fabriken neu befüllen (inkl. je 1 verdecktem Bonusplättchen)
    _fill_factories(state.factories, state.large_factory, state.bag, state.tower,
                    state.bonus_chip_pool)

    # Dome-Platzierungen zurücksetzen (2 Kuppeln pro Runde)
    for p in state.players:
        p.reset_dome_placements()
        p.holds_first_player_marker = False

    state.log_event(
        f"Runde {state.round_number} beginnt. "
        f"{state.players[state.current_player].name} ist Startspieler."
    )
