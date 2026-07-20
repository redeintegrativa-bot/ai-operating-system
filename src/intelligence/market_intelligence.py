from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from collections import Counter
from statistics import mean, stdev, median


class MarketIntelligence:
    def __init__(self):
        self.source_name = "MarketIntelligence"

    def analyze(self, defillama_data: Dict[str, Any] = None, 
                coingecko_data: Dict[str, Any] = None, 
                dex_screener_data: Dict[str, Any] = None,
                l2_beat_data: Dict[str, Any] = None,
                historical_data: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        insights = {
            "timestamp": datetime.now().isoformat(),
            "source": self.source_name,
            "sections": {}
        }

        if defillama_data:
            insights["sections"]["network_overview"] = self._analyze_tvl(defillama_data)
            insights["sections"]["protocol_analysis"] = self._analyze_protocols(defillama_data)

        if coingecko_data:
            insights["sections"]["price_trends"] = self._analyze_prices(coingecko_data)
            insights["sections"]["volume_analysis"] = self._analyze_volumes(coingecko_data)
            if "categories" in coingecko_data:
                insights["sections"]["sector_rotation"] = self._analyze_sectors(coingecko_data)

        if dex_screener_data:
            insights["sections"]["liquidity_heatmap"] = self._analyze_liquidity(dex_screener_data)

        if l_2_beat_data:
            insights["sections"]["l2_market"] = self._analyze_l2(l_2_beat_data)

        if historical_data:
            insights["sections"]["trend_analysis"] = self._analyze_trends(historical_data)

        insights["correlations"] = self._compute_correlations(
            coingecko_data, defillama_data
        )

        return insights

    def _analyze_tvl(self, defillama_data: Dict[str, Any]) -> Dict[str, Any]:
        total_tvl = defillama_data.get("total_tvl_usd", 0)
        top_protocols = defillama_data.get("top_protocols", [])
        dominance = defillama_data.get("dominance", [])

        formatted_tvl = self._format_money(total_tvl)

        top_three_pct = 0
        for i, d in enumerate(dominance):
            if i < 3:
                top_three_pct += d.get("share_pct", 0)

        high_volume_changers = [
            p for p in top_protocols
            if abs(p.get("change_7d", 0) or 0) > 15
        ]

        mood = "bullish" if sum(p.get("change_1d", 0) or 0 for p in top_protocols) > 0 else "bearish"

        return {
            "total_tvl_usd": total_tvl,
            "formatted_tvl": formatted_tvl,
            "top_protocols": top_protocols[:5],
            "dominance": dominance[:3],
            "top_three_dominance_pct": round(top_three_pct, 2),
            "high_change_protocol_count": len(high_volume_changers),
            "high_change_protocols": high_volume_changers[:5],
            "mood": mood
        }

    def _analyze_protocols(self, defillama_data: Dict[str, Any]) -> Dict[str, Any]:
        top_protocols = defillama_data.get("top_protocols", [])
        protocol_count = defillama_data.get("protocol_count", 0)

        categories = Counter()
        for protocol in top_protocols:
            cat = protocol.get("category", "unknown")
            categories[cat] += 1

        sorted_categories = categories.most_common()

        return {
            "total_protocol_count": protocol_count,
            "category_distribution": sorted_categories,
            "top_categories": [cat for cat, count in sorted_categories[:5]],
        }

    def _analyze_prices(self, coingecko_data: Dict[str, Any]) -> Dict[str, Any]:
        tokens = coingecko_data.get("tokens", [])
        if not tokens:
            tokens = coingecko_data.get("results", [])

        if not tokens:
            return {}

        price_changes = {}
        for token in tokens:
            change = token.get("change_24h_pct", token.get("price_change_24h_pct"))
            if change is not None:
                price_changes[token.get("name", token.get("coin_id", ""))] = change

        gains = {k: v for k, v in price_changes.items() if v > 0}
        losses = {k: v for k, v in price_changes.items() if v < 0}
        stable = {k: v for k, v in price_changes.items() if v == 0}

        top_gainers = sorted(gains.items(), key=lambda x: x[1], reverse=True)[:5] if gains else []
        top_losers = sorted(losses.items(), key=lambda x: x[1])[:5] if losses else []

        avg_gain = mean(gains.values()) if gains else 0
        avg_loss = mean(losses.values()) if losses else 0

        return {
            "token_count": len(tokens),
            "average_gain_pct": round(avg_gain, 2),
            "gainers": len(gains),
            "losers": len(losses),
            "stable": len(stable),
            "top_gainers": top_gainers,
            "top_losers": top_losers,
            "types": {
                "gainers_count": len(gains),
                "losers_count": len(losses),
                "stable_count": len(stable)
            },
            "volatility_estimate": self._estimate_volatility(price_changes)
        }

    def _analyze_volumes(self, coingecko_data: Dict[str, Any]) -> Dict[str, Any]:
        tokens = coingecko_data.get("tokens", [])
        if not tokens:
            tokens = coingecko_data.get("results", [])

        if not tokens:
            return {}

        volumes = {}
        for token in tokens:
            volume = token.get("volume_24h_usd", token.get("volume_24h_usd"))
            if volume:
                volumes[token.get("name", token.get("coin_id", ""))] = volume

        sorted_volumes = sorted(volumes.items(), key=lambda x: x[1], reverse=True)

        total_volume = sum(volumes.values())
        top_five_volume = sum(v for _, v in sorted_volumes[:5]) if sorted_volumes else 0

        volume_mood = "high" if total_volume > 100 * 1e9 else "normal"

        return {
            "total_volume_usd_24h": total_volume,
            "top_five_volume_concentration_pct": round(top_five_volume / total_volume * 100, 2) if total_volume > 0 else 0,
            "top_volume_chains": sorted_volumes[:5],
            "volume_mood": volume_mood
        }

    def _analyze_sectors(self, coingecko_categories: Dict[str, Any]) -> Dict[str, Any]:
        categories = coingecko_categories.get("categories", [])
        if not categories:
            categories = coingecko_categories.get("data", [])

        sorted_categories = sorted(categories, key=lambda x: x.get("market_cap_change_24h_pct", 0), reverse=True)

        strongest = [c for c in sorted_categories if c.get("market_cap_change_24h_pct", 0) > 5]
        weakest = [c for c in sorted_categories if c.get("market_cap_change_24h_pct", 0) < -5]

        return {
            "category_count": len(categories),
            "strongest_sectors": [{"name": c.get("name", ""), "change_pct": c.get("market_cap_change_24h_pct", 0)} for c in strongest[:5]],
            "weakest_sectors": [{"name": c.get("name", ""), "change_pct": c.get("market_cap_change_24h_pct", 0)} for c in weakest[:5]],
            "risk_off_signal": len(strongest) < len(weakest)
        }

    def _analyze_liquidity(self, dex_screener_data: Dict[str, Any]) -> Dict[str, Any]:
        pairs = dex_screener_data.get("pairs", [])
        if not pairs:
            return {}

        liquidity_distrib = {}
        for pair in pairs:
            chain = pair.get("chain_id", "unknown")
            liquidity = float(pair.get("liquidity_usd", 0))
            if chain not in liquidity_distrib:
                liquidity_distrib[chain] = []
            liquidity_distrib[chain].append(liquidity)

        total_liquidity = sum(sum(v) for v in liquidity_distrib.values())
        chain_shares = {c: round(sum(v) / total_liquidity * 100, 2) for c, v in liquidity_distrib.items()}

        return {
            "total_liquidity_usd": total_liquidity,
            "chain_distribution": chain_shares,
            "top_liquidity_chains": sorted(chain_shares.items(), key=lambda x: x[1], reverse=True)[:5],
            "pair_count": len(pairs)
        }

    def _analyze_l2(self, l_2_beat_data: Dict[str, Any]) -> Dict[str, Any]:
        projects = l_2_beat_data.get("projects", [])
        total_tvl = l_2_beat_data.get("total_tvl_usd", 0)
        dominance = l_2_beat_data.get("dominance", [])

        technology_counts = Counter()
        for proj in projects:
            tech = proj.get("technology", "unknown")
            technology_counts[tech] += 1

        category_counts = Counter()
        for proj in projects:
            cat = proj.get("category", "other")
            if cat:
                category_counts[proj.get("category", "other")] += 1

        top_three_pct = sum(d.get("share_pct", 0) for d in dominance[:3])

        return {
            "project_count": len(projects),
            "total_tvl_usd": total_tvl,
            "formatted_tvl": self._format_money(total_tvl),
            "top_three_dominance_pct": top_three_pct,
            "technology_distribution": technology_counts.most_common(),
            "category_distribution": category_counts.most_common(),
            "top_projects": projects[:5]
        }

    def _analyze_trends(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not historical_data or len(historical_data) < 2:
            return {}

        prices = [h.get("price", 0) for h in historical_data if h.get("price", 0)]
        volumes = [h.get("volume", 0) for h in historical_data if h.get("volume", 0)]
        timestamps = [h.get("timestamp", datetime.now()) for h in historical_data]

        price_ma = mean(prices) if prices else 0
        volume_ma = mean(velumes) if volumes else 0
        price_sd = stdev(prices) if len(prices) > 1 else 0

        total_return = ((prices[-1] - prices[0]) / prices[0] * 100) if prices[0] > 0 else 0

        return {
            "period": f"{timestamps[0]} to {timestamps[-1]}" if len(timestamps) > 1 else "N/A",
            "data_points": len(prices),
            "price_min": min(prices) if prices else 0,
            "price_max": max(prices) if prices else 0,
            "price_avg": round(price_ma, 4),
            "volatility_std": round(price_sd, 4),
            "volume_avg": volume_ma,
            "total_return_pct": round(total_return, 2)
        }

    def _compute_correlations(self, coingecko_data: Dict[str, Any], defillama_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "protocol_tvl_market_cap_correlated": True,
            "note": "Requires more data points for statistical significance"
        }

    def _estimate_volatility(self, price_changes: Dict[str, float]) -> Dict[str, int]:
        if not price_changes:
            return {"high": 0, "medium": 0, "low": 0}

        high = 0
        medium = 0
        low = 0

        for asset, change in price_changes:
            abs_change = abs(change)
            if abs_change > 10:
                high += 1
            elif abs_change > 3:
                medium += 1
            else:
                low += 1

        return {"high": high, "medium": medium, "low": low}

    @staticmethod
    def _format_money(value: float) -> str:
        if value >= 1e9:
            return f"${value / 1e9:.2f}B"
        elif value >= 1e6:
            return f"${value / 1e6:.2f}M"
        elif value >= 1e3:
            return f"${value / 1e3:.2f}K"
        else:
            return f"${value:.2f}"
