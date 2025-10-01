# analyzers/engagement_analyzer.py
"""Engagement and economy analysis for Counter-Strike players."""

from __future__ import annotations

import ast
import json
import numpy as np
import pandas as pd

from data_structures import EngagementSignature, DemoData
import config


def _normalize_weapon_label(label: str | None) -> str:
    if not label:
        return ""
    cleaned = ''.join(ch.lower() for ch in str(label) if ch.isalnum())
    for prefix in ('weapon', 'item'):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):]
    return cleaned


_RAW_WEAPON_PRICES: dict[str, int] = {
    # Pistols
    "Glock-18": 200,
    "USP-S": 200,
    "P250": 300,
    "P2000": 200,
    "Five-SeveN": 500,
    "Tec-9": 500,
    "Dual Berettas": 300,
    "Desert Eagle": 700,
    "CZ75-Auto": 500,
    "R8 Revolver": 600,
    # SMGs
    "MAC-10": 1050,
    "MP9": 1250,
    "MP7": 1500,
    "MP5-SD": 1500,
    "UMP-45": 1200,
    "P90": 2350,
    "PP-Bizon": 1400,
    # Rifles
    "Galil AR": 1800,
    "FAMAS": 1950,
    "AK-47": 2700,
    "M4A1-S": 2900,
    "M4A4": 2900,
    "SG 553": 3000,
    "AUG": 3300,
    # Sniper Rifles
    "SSG 08": 1700,
    "AWP": 4750,
    "G3SG1": 5000,
    "SCAR-20": 5000,
    # Shotguns
    "Nova": 1050,
    "XM1014": 2000,
    "MAG-7": 1300,
    "Sawed-Off": 1100,
    # Machine Guns
    "Negev": 1700,
    "M249": 5200,
    # Misc
    "Zeus x27": 200,
}


WEAPON_PRICES: dict[str, int] = {
    _normalize_weapon_label(name): price for name, price in _RAW_WEAPON_PRICES.items()
}

_WEAPON_ALIASES: dict[str, str] = {
    'glock': 'glock18',
    'usp': 'usps',
    'usps': 'usps',
    'uspsilencer': 'usps',
    'uspsilenceroff': 'usps',
    'cz75a': 'cz75auto',
    'cz75': 'cz75auto',
    'dualberettas': 'dualberettas',
    'duelberettas': 'dualberettas',
    'elite': 'dualberettas',
    'five7': 'fiveseven',
    'tec9': 'tec9',
    'deagle': 'deserteagle',
    'revolver': 'r8revolver',
    'mac10': 'mac10',
    'mp5': 'mp5sd',
    'bizon': 'ppbizon',
    'ppbizon': 'ppbizon',
    'galil': 'galilar',
    'famas': 'famas',
    'ak': 'ak47',
    'sg556': 'sg553',
    'm4a1s': 'm4a1s',
    'm4a1silencer': 'm4a1s',
    'm4a1silenceroff': 'm4a1s',
    'm4a1': 'm4a4',
    'm4': 'm4a4',
    'scar20': 'scar20',
    'g3sg1': 'g3sg1',
    'mag7': 'mag7',
    'sawedoff': 'sawedoff',
    'ssg08': 'ssg08',
    'scout': 'ssg08',
    'zeus': 'zeusx27',
    'zeusx': 'zeusx27',
    'hkp2000': 'p2000',
}

for alias, base in _WEAPON_ALIASES.items():
    normalized_alias = _normalize_weapon_label(alias)
    normalized_base = _normalize_weapon_label(base)
    price = WEAPON_PRICES.get(normalized_base)
    if price is not None:
        WEAPON_PRICES.setdefault(normalized_alias, price)


class EngagementAnalyzer:
    """Derives first-duel, trade, and economy metrics."""

    def __init__(self):
        self.tick_rate = getattr(config, "TICKS_PER_SECOND", 128)
        self.trade_window_seconds = getattr(config, "TRADE_WINDOW_SECONDS", 5)
        self.trade_window_ticks = self.trade_window_seconds * self.tick_rate

    def analyze(self, demo_data: DemoData, player_steamid: str) -> EngagementSignature:
        total_rounds = max(demo_data.total_rounds, 1)
        player_id = int(player_steamid)

        kills_all = self._prepare_df(demo_data.all_kills)
        ticks_df = self._prepare_df(demo_data.ticks)

        first_duel_attempts, first_duel_wins = self._compute_first_duels(kills_all, player_id)
        trade_latencies = self._compute_trade_latencies(kills_all, player_id)
        economy_stats = self._compute_economy_stats(ticks_df, player_id)
        weapon_value_stats = self._compute_weapon_value_stats(ticks_df, player_id)

        first_duel_attempts_per_round = first_duel_attempts / total_rounds
        first_duel_wins_per_round = first_duel_wins / total_rounds
        first_duel_win_rate = (first_duel_wins / first_duel_attempts) if first_duel_attempts else 0.0

        trades_per_round = len(trade_latencies) / total_rounds
        trade_latency_avg = float(np.mean(trade_latencies)) if trade_latencies else 0.0
        trade_latency_median = float(np.median(trade_latencies)) if trade_latencies else 0.0
        trade_latency_p90 = float(np.percentile(trade_latencies, 90)) if len(trade_latencies) >= 1 else 0.0

        return EngagementSignature(
            first_duel_attempts_per_round=float(first_duel_attempts_per_round),
            first_duel_wins_per_round=float(first_duel_wins_per_round),
            first_duel_win_rate=float(first_duel_win_rate),
            trades_per_round=float(trades_per_round),
            trade_latency_average=float(trade_latency_avg),
            trade_latency_median=float(trade_latency_median),
            trade_latency_p90=float(trade_latency_p90),
            economy_avg_cash_spent=float(economy_stats.get('mean', 0.0)),
            economy_median_cash_spent=float(economy_stats.get('median', 0.0)),
            economy_std_cash_spent=float(economy_stats.get('std', 0.0)),
            economy_avg_weapon_value=float(weapon_value_stats.get('mean', 0.0)),
            economy_median_weapon_value=float(weapon_value_stats.get('median', 0.0)),
            economy_std_weapon_value=float(weapon_value_stats.get('std', 0.0)),
        )

    def _prepare_df(self, df: pd.DataFrame | None) -> pd.DataFrame:
        if df is None or df.empty:
            return pd.DataFrame()
        return df.copy()

    def _compute_first_duels(self, kills_df: pd.DataFrame, player_id: int) -> tuple[int, int]:
        if kills_df.empty:
            return 0, 0

        kills_df['attacker_steamid'] = pd.to_numeric(kills_df['attacker_steamid'], errors='coerce')
        kills_df['victim_steamid'] = pd.to_numeric(kills_df['victim_steamid'], errors='coerce')
        kills_df['round_num'] = pd.to_numeric(kills_df['round_num'], errors='coerce')
        kills_df['match_id'] = pd.to_numeric(kills_df.get('match_id', 0), errors='coerce')

        kills_df = kills_df.dropna(subset=['round_num', 'tick'])

        kills_df.sort_values(['match_id', 'round_num', 'tick'], inplace=True)
        first_tick = kills_df.groupby(['match_id', 'round_num'])['tick'].transform('min')
        first_events = kills_df[kills_df['tick'] == first_tick]

        attempts = ((first_events['attacker_steamid'] == player_id) | (first_events['victim_steamid'] == player_id)).sum()
        wins = (first_events['attacker_steamid'] == player_id).sum()
        return int(attempts), int(wins)

    def _compute_trade_latencies(self, kills_df: pd.DataFrame, player_id: int) -> list[float]:
        if kills_df.empty:
            return []

        kills_df = kills_df.copy()
        kills_df['attacker_steamid'] = pd.to_numeric(kills_df['attacker_steamid'], errors='coerce')
        kills_df['victim_steamid'] = pd.to_numeric(kills_df['victim_steamid'], errors='coerce')
        kills_df['round_num'] = pd.to_numeric(kills_df['round_num'], errors='coerce')
        kills_df['match_id'] = pd.to_numeric(kills_df.get('match_id', 0), errors='coerce')

        player_kills = kills_df[kills_df['attacker_steamid'] == player_id]
        if player_kills.empty:
            return []

        latencies = []
        for _, kill in player_kills.iterrows():
            round_mask = (
                (kills_df['match_id'] == kill['match_id']) &
                (kills_df['round_num'] == kill['round_num']) &
                (kills_df['tick'] < kill['tick'])
            )
            potential = kills_df[round_mask]
            if potential.empty:
                continue
            traded = potential[
                (potential['victim_side'] == kill.get('attacker_side')) &
                (potential['attacker_steamid'] == kill['victim_steamid'])
            ]
            if traded.empty:
                continue
            traded = traded.sort_values('tick', ascending=False)
            trade_event = traded.iloc[0]
            tick_delta = kill['tick'] - trade_event['tick']
            if tick_delta <= 0 or tick_delta > self.trade_window_ticks:
                continue
            latencies.append(float(tick_delta / self.tick_rate))
        return latencies

    def _compute_economy_stats(self, ticks_df: pd.DataFrame, player_id: int) -> dict[str, float]:
        if ticks_df.empty:
            return {'mean': 0.0, 'median': 0.0, 'std': 0.0}

        ticks_df = ticks_df.copy()
        ticks_df['steamid'] = pd.to_numeric(ticks_df['steamid'], errors='coerce')
        ticks_df = ticks_df[ticks_df['steamid'] == player_id]
        if ticks_df.empty:
            return {'mean': 0.0, 'median': 0.0, 'std': 0.0}

        cash_column = None
        for candidate in ['total_cash_spent', 'cash', 'equipment_value']:
            if candidate in ticks_df.columns:
                cash_column = candidate
                break

        if cash_column is None:
            return {'mean': 0.0, 'median': 0.0, 'std': 0.0}

        if 'round_id' not in ticks_df.columns:
            ticks_df['round_id'] = (
                pd.to_numeric(ticks_df.get('match_id', 0), errors='coerce') * 1000
                + pd.to_numeric(ticks_df['round_num'], errors='coerce')
            )

        ticks_df.sort_values(['match_id', 'round_id', 'tick'], inplace=True)
        per_round_cash = (
            ticks_df.groupby(['match_id', 'round_id'])[cash_column]
            .first()
            .dropna()
            .sort_index()
        )
        if per_round_cash.empty:
            return {'mean': 0.0, 'median': 0.0, 'std': 0.0}

        # Convert cumulative spend to per-round amount within each match
        per_round_spend = []
        for match_id, series in per_round_cash.groupby(level=0):
            values = series.values.astype(float)
            if len(values) == 0:
                continue
            diff = np.diff(values, prepend=0)
            # Guard against negative diffs (possible reset); clamp at zero
            diff = np.clip(diff, a_min=0.0, a_max=None)
            per_round_spend.extend(diff.tolist())

        if not per_round_spend:
            return {'mean': 0.0, 'median': 0.0, 'std': 0.0}

        per_round_spend = np.array(per_round_spend, dtype=float)
        return {
            'mean': float(per_round_spend.mean()),
            'median': float(np.median(per_round_spend)),
            'std': float(per_round_spend.std(ddof=0)),
        }

    def _compute_weapon_value_stats(self, ticks_df: pd.DataFrame, player_id: int) -> dict[str, float]:
        default = {'mean': 0.0, 'median': 0.0, 'std': 0.0}
        if ticks_df.empty or 'inventory' not in ticks_df.columns:
            return default

        ticks_df = ticks_df.copy()
        ticks_df['steamid'] = pd.to_numeric(ticks_df['steamid'], errors='coerce')
        ticks_df = ticks_df[ticks_df['steamid'] == player_id]
        if ticks_df.empty:
            return default

        if 'round_id' not in ticks_df.columns:
            match_ids = pd.to_numeric(ticks_df.get('match_id', 0), errors='coerce').fillna(0).astype(int)
            round_nums = pd.to_numeric(ticks_df.get('round_num', 0), errors='coerce').fillna(0).astype(int)
            ticks_df['round_id'] = match_ids * 1000 + round_nums

        ticks_df['round_id'] = pd.to_numeric(ticks_df['round_id'], errors='coerce')
        ticks_df['tick'] = pd.to_numeric(ticks_df['tick'], errors='coerce')
        ticks_df = ticks_df.dropna(subset=['round_id', 'tick', 'inventory'])
        if ticks_df.empty:
            return default

        ticks_df['round_id'] = ticks_df['round_id'].astype(int)

        per_round_values: list[float] = []
        for _, round_ticks in ticks_df.groupby('round_id'):
            round_ticks = round_ticks.sort_values('tick')
            if round_ticks.empty:
                continue
            start_tick = round_ticks['tick'].iloc[0]
            window_ticks = round_ticks[round_ticks['tick'] <= start_tick + 16]
            values = [self._calc_inventory_value(inv) for inv in window_ticks['inventory']]
            values = [value for value in values if value > 0]
            if not values:
                continue
            mode_value = max(set(values), key=values.count)
            per_round_values.append(float(mode_value))

        if not per_round_values:
            return default

        per_round_values = np.array(per_round_values, dtype=float)
        return {
            'mean': float(per_round_values.mean()),
            'median': float(np.median(per_round_values)),
            'std': float(per_round_values.std(ddof=0)),
        }

    def _calc_inventory_value(self, inventory: object) -> int:
        items = self._coerce_inventory_items(inventory)
        if not items:
            return 0

        total_value = 0
        for item in items:
            name = None
            if isinstance(item, dict):
                name = (
                    item.get('name')
                    or item.get('weapon_name')
                    or item.get('item_name')
                    or item.get('weapon')
                )
            elif isinstance(item, str):
                name = item
            if not name:
                continue
            normalized = _normalize_weapon_label(name)
            total_value += WEAPON_PRICES.get(normalized, 0)
        return total_value

    def _coerce_inventory_items(self, inventory: object) -> list:
        if inventory is None:
            return []

        parsed = inventory
        if isinstance(parsed, str):
            parsed = parsed.strip()
            if not parsed:
                return []
            raw_text = parsed
            parsed_obj = None
            for loader in (json.loads, ast.literal_eval):
                try:
                    parsed_obj = loader(raw_text)
                    break
                except Exception:
                    continue
            if parsed_obj is None:
                return [raw_text]
            parsed = parsed_obj

        if isinstance(parsed, dict):
            return [parsed]
        if isinstance(parsed, (list, tuple, set)):
            return list(parsed)
        if hasattr(np, 'ndarray') and isinstance(parsed, np.ndarray):
            return parsed.tolist()
        return []
