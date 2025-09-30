# analyzers/utility_analyzer.py
"""Utility usage analysis for Counter-Strike players."""

from __future__ import annotations

import numpy as np
import pandas as pd

from data_structures import UtilitySignature, DemoData
import config

FLASH_TYPES = {"CFlashbang", "CFlashbangProjectile"}
SMOKE_TYPES = {"CSmokeGrenade", "CSmokeGrenadeProjectile"}
MOLOTOV_TYPES = {"CMolotovGrenade", "CMolotovProjectile", "CIncendiaryGrenade", "CIncendiaryProjectile"}
HE_TYPES = {"CHEGrenade", "CHEGrenadeProjectile"}

UTILITY_DAMAGE_WEAPONS = {"hegrenade", "inferno", "molotov"}
HE_WEAPONS = {"hegrenade"}


class UtilityAnalyzer:
    """Computes grenade usage and effectiveness metrics."""

    def __init__(self, tick_rate: int | None = None):
        self.tick_rate = tick_rate or getattr(config, "TICKS_PER_SECOND", 128)
        self.default_smoke_ticks = getattr(config, "DEFAULT_SMOKE_DURATION_SECONDS", 18) * self.tick_rate
        self.default_molotov_ticks = getattr(config, "DEFAULT_MOLOTOV_DURATION_SECONDS", 7) * self.tick_rate

    def analyze(self, demo_data: DemoData, player_steamid: str) -> UtilitySignature:
        total_rounds = max(demo_data.total_rounds, 1)
        player_id = int(player_steamid)

        grenades_df = self._prepare_df(demo_data.grenades)
        smokes_df = self._prepare_df(demo_data.smokes)
        infernos_df = self._prepare_df(demo_data.infernos)
        kills_df = self._prepare_df(demo_data.kills)
        assisted_kills_df = self._prepare_df(demo_data.assisted_kills)
        damages_df = self._prepare_df(demo_data.damages)

        flashes_thrown = self._count_unique_grenades(grenades_df, FLASH_TYPES)
        smokes_thrown = self._count_unique_grenades(grenades_df, SMOKE_TYPES)
        molotovs_thrown = self._count_unique_grenades(grenades_df, MOLOTOV_TYPES)
        he_thrown = self._count_unique_grenades(grenades_df, HE_TYPES)

        flash_assists = self._count_flash_assists(assisted_kills_df, player_id)
        flash_assists_per_round = flash_assists / total_rounds
        flashes_thrown_per_round = flashes_thrown / total_rounds
        enemies_flashed_per_round = flash_assists_per_round  # Proxy: flash assists imply at least one enemy flashed
        flash_to_frag_rate = flash_assists / max(flashes_thrown, 1)

        smoke_seconds_total = self._compute_entity_duration(smokes_df)
        smoke_coverage_seconds_per_round = smoke_seconds_total / total_rounds

        inferno_seconds_total = self._compute_entity_duration(infernos_df, default_ticks=self.default_molotov_ticks)
        area_denial_seconds_per_round = inferno_seconds_total / total_rounds

        kills_through_smoke = self._count_kills_through_smoke(kills_df, player_id)
        kills_through_smoke_per_round = kills_through_smoke / total_rounds

        he_damage_total = self._sum_weapon_damage(damages_df, player_id, HE_WEAPONS)
        he_damage_per_round = he_damage_total / total_rounds

        utility_damage_total = self._sum_weapon_damage(damages_df, player_id, UTILITY_DAMAGE_WEAPONS)
        damage_grenade_throws = he_thrown + molotovs_thrown
        utility_damage_per_grenade = utility_damage_total / max(damage_grenade_throws, 1)

        return UtilitySignature(
            flashes_thrown_per_round=float(flashes_thrown_per_round),
            enemies_flashed_per_round=float(enemies_flashed_per_round),
            flash_assists_per_round=float(flash_assists_per_round),
            flash_to_frag_rate=float(flash_to_frag_rate),
            smokes_thrown_per_round=float(smokes_thrown / total_rounds),
            smoke_coverage_seconds_per_round=float(smoke_coverage_seconds_per_round),
            kills_through_smoke_per_round=float(kills_through_smoke_per_round),
            molotovs_thrown_per_round=float(molotovs_thrown / total_rounds),
            area_denial_seconds_per_round=float(area_denial_seconds_per_round),
            he_damage_per_round=float(he_damage_per_round),
            utility_damage_per_grenade=float(utility_damage_per_grenade),
        )

    def _prepare_df(self, df: pd.DataFrame | None) -> pd.DataFrame:
        if df is None or df.empty:
            return pd.DataFrame()
        return df.copy()

    def _count_unique_grenades(self, grenades_df: pd.DataFrame, types: set[str]) -> int:
        if grenades_df.empty:
            return 0
        filtered = grenades_df[grenades_df['grenade_type'].isin(types)]
        if filtered.empty:
            return 0
        return filtered['entity_id'].dropna().nunique()

    def _count_flash_assists(self, assists_df: pd.DataFrame, player_id: int) -> int:
        if assists_df.empty:
            return 0
        assists = assists_df[(assists_df['assistedflash']) & (pd.to_numeric(assists_df['assister_steamid'], errors='coerce') == player_id)]
        return len(assists)

    def _compute_entity_duration(self, df: pd.DataFrame, default_ticks: int | None = None) -> float:
        if df.empty:
            return 0.0
        if 'start_tick' not in df.columns:
            return 0.0
        durations = df[['start_tick', 'end_tick']].copy()
        if default_ticks is None:
            default_ticks = getattr(config, "DEFAULT_SMOKE_DURATION_SECONDS", 18) * self.tick_rate
        durations['end_tick'] = durations['end_tick'].fillna(durations['start_tick'] + default_ticks)
        durations['duration_ticks'] = (durations['end_tick'] - durations['start_tick']).clip(lower=0)
        total_ticks = durations['duration_ticks'].sum()
        return float(total_ticks / self.tick_rate)

    def _count_kills_through_smoke(self, kills_df: pd.DataFrame, player_id: int) -> int:
        if kills_df.empty:
            return 0
        through_smoke = kills_df[
            (pd.to_numeric(kills_df['attacker_steamid'], errors='coerce') == player_id)
            & (kills_df['thrusmoke'])
        ]
        return len(through_smoke)

    def _sum_weapon_damage(self, damages_df: pd.DataFrame, player_id: int, weapons: set[str]) -> float:
        if damages_df.empty:
            return 0.0
        filtered = damages_df[
            (pd.to_numeric(damages_df['attacker_steamid'], errors='coerce') == player_id)
            & (damages_df['weapon'].isin(weapons))
        ]
        if filtered.empty:
            return 0.0
        return float(filtered['dmg_health'].sum())
