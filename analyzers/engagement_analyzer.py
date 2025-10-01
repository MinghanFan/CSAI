# analyzers/engagement_analyzer.py
"""Engagement and economy analysis for Counter-Strike players."""

from __future__ import annotations

import numpy as np
import pandas as pd

from data_structures import EngagementSignature, DemoData
import config


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
