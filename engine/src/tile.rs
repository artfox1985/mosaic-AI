//! Farben und Steinvorrats-Konstanten — Port von engine/tile.py.

/// Die 5 normalen Spielfarben + WILD (nur Dome-Space-Marker, kein physischer Stein).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum TileColor {
    Blau,
    Gelb,
    Rot,
    Schwarz,
    Tuerkis,
    /// "bunt" laut Regelwerk — kein ziehbarer Stein.
    Wild,
}

impl TileColor {
    /// Die 5 ziehbaren Farben (ohne WILD), in fester Reihenfolge.
    pub const NORMAL: [TileColor; 5] = [
        TileColor::Blau,
        TileColor::Gelb,
        TileColor::Rot,
        TileColor::Schwarz,
        TileColor::Tuerkis,
    ];

    /// String-Wert wie in der Python-Enum (für Serialisierung/Parität).
    pub fn value(self) -> &'static str {
        match self {
            TileColor::Blau => "blau",
            TileColor::Gelb => "gelb",
            TileColor::Rot => "rot",
            TileColor::Schwarz => "schwarz",
            TileColor::Tuerkis => "türkis",
            TileColor::Wild => "bunt",
        }
    }

    /// Umkehrung von `value()`.
    pub fn from_value(s: &str) -> Option<TileColor> {
        match s {
            "blau" => Some(TileColor::Blau),
            "gelb" => Some(TileColor::Gelb),
            "rot" => Some(TileColor::Rot),
            "schwarz" => Some(TileColor::Schwarz),
            "türkis" => Some(TileColor::Tuerkis),
            "bunt" => Some(TileColor::Wild),
            _ => None,
        }
    }
}

// Steinzahlen (engine/tile.py)
pub const TILES_PER_COLOR: usize = 13;
pub const SPECIAL_TILES: usize = 9;
pub const FIRST_PLAYER_MARKERS: usize = 1;
pub const NORMAL_TILES: usize = TILES_PER_COLOR * 5; // 65
pub const TOTAL_TILES: usize = NORMAL_TILES + SPECIAL_TILES + FIRST_PLAYER_MARKERS; // 75

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn value_roundtrip() {
        for c in TileColor::NORMAL {
            assert_eq!(TileColor::from_value(c.value()), Some(c));
        }
        assert_eq!(TileColor::from_value("bunt"), Some(TileColor::Wild));
        assert_eq!(TileColor::from_value("weiß"), None);
        assert_eq!(TileColor::Tuerkis.value(), "türkis");
    }

    #[test]
    fn tile_counts() {
        assert_eq!(NORMAL_TILES, 65);
        assert_eq!(TOTAL_TILES, 75);
    }
}
