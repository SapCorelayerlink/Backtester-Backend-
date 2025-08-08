import asyncio
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple

import pandas as pd
import matplotlib.pyplot as plt

try:
    from ib_insync import IB, Stock, util
except Exception:
    IB = None  # type: ignore
    Stock = None  # type: ignore
    util = None  # type: ignore

from core.base import StrategyBase
from intraday_supertrend_ma_strategy import IntradaySupertrendMA  # type: ignore


class IBKRHistoricalBroker:
    """
    Minimal broker implementation for backtesting using IBKR historical data via ib_insync.
    - get_historical_data: returns 1-min bars between start_date and end_date (UTC dates: YYYY-MM-DD)
    - place_order: no-op during backtest
    """

    def __init__(self, ib: IB, progress_path: str | None = None):
        self.ib = ib
        self.progress_path = progress_path

    async def get_historical_data(self, symbol: str, timeframe: str, start_date: str, end_date: str) -> pd.DataFrame:
        if timeframe != "1min":
            raise ValueError("This backtester fetches 1min data; set base_timeframe='1min'.")

        contract = Stock(symbol, "SMART", "USD")
        self.ib.qualifyContracts(contract)

        # IBKR historical data limits: fetch in chunks
        end_dt = pd.Timestamp(end_date, tz='UTC') + pd.Timedelta(days=1)  # inclusive end
        start_dt = pd.Timestamp(start_date, tz='UTC')
        df_all = []
        cursor = end_dt

        while cursor > start_dt:
            duration = "30 D"  # 30 days per request for 1-min bars
            bars = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.ib.reqHistoricalData(
                    contract,
                    endDateTime=cursor.to_pydatetime(),
                    durationStr=duration,
                    barSizeSetting="1 min",
                    whatToShow="TRADES",
                    useRTH=True,
                    formatDate=1,
                ),
            )
            if not bars:
                break
            df = util.df(bars)
            df.rename(columns={"date": "date", "open": "open", "high": "high", "low": "low", "close": "close", "volume": "volume"}, inplace=True)
            df["date"] = pd.to_datetime(df["date"], utc=True)
            df.set_index(pd.DatetimeIndex(df["date"]), inplace=True)
            df = df[["open", "high", "low", "close", "volume"]]
            df_all.append(df)
            first = df.index[0]
            cursor = first

            if first <= start_dt:
                break

            # Progress status update
            try:
                if self.progress_path:
                    with open(self.progress_path, "w", encoding="utf-8") as f:
                        f.write(f"Fetched up to: {first.isoformat()}. Remaining until: {start_dt.isoformat()}\n")
                        f.write(f"Accumulated chunks: {len(df_all)}\n")
            except Exception:
                pass

        if not df_all:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

        all_df = pd.concat(df_all).sort_index()
        all_df = all_df[(all_df.index >= start_dt) & (all_df.index < end_dt)]
        return all_df

    async def place_order(self, order: Dict, stop_loss: float = None, take_profit: float = None):
        # No-op in backtest
        return None


def _ensure_output_dir(base_dir: str) -> str:
    os.makedirs(base_dir, exist_ok=True)
    run_dir = os.path.join(base_dir, datetime.now().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(run_dir, exist_ok=True)
    return run_dir


def _save_trades_csv(trades: List[Dict], path: str) -> None:
    if not trades:
        pd.DataFrame(columns=["entry_time","exit_time","symbol","quantity","side","entry_price","exit_price","pnl"]).to_csv(path, index=False)
        return
    df = pd.DataFrame(trades)
    # Ensure ISO strings for datetimes
    for col in ("entry_time", "exit_time"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], utc=True, errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S%z")
    df.to_csv(path, index=False)


def _build_equity_curve(trades: List[Dict], starting_equity: float) -> pd.Series:
    if not trades:
        return pd.Series([starting_equity], index=[pd.Timestamp.now(tz=timezone.utc)])
    # Use exit times as equity steps
    rows: List[Tuple[pd.Timestamp, float]] = []
    equity = starting_equity
    for t in sorted(trades, key=lambda x: pd.to_datetime(x.get("exit_time"))):
        pnl = float(t.get("pnl", 0.0))
        exit_time = pd.to_datetime(t.get("exit_time"), utc=True)
        equity += pnl
        rows.append((exit_time, equity))
    idx = pd.DatetimeIndex([ts for ts, _ in rows])
    vals = [val for _, val in rows]
    return pd.Series(vals, index=idx)


def _plot_equity_curve(equity_series: pd.Series, out_path: str) -> None:
    if equity_series.empty:
        return
    plt.figure(figsize=(12, 6))
    plt.plot(equity_series.index, equity_series.values, label="Equity", color="tab:blue")
    plt.title("Equity Curve")
    plt.xlabel("Time")
    plt.ylabel("Equity")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


async def run_backtest(symbol: str = "QQQ", days: int = 1826, starting_equity: float = 100000.0, output_base: str = "backtests/QQQ"):
    if IB is None:
        raise RuntimeError("ib_insync not installed. pip install ib_insync")

    ib = IB()
    # Allow env overrides
    env_host = os.environ.get("IB_HOST", "127.0.0.1")
    env_port = os.environ.get("IB_PORT")
    env_client_id = int(os.environ.get("IB_CLIENT_ID", "20"))

    # Prepare output folder and placeholders EARLY so artifacts appear immediately
    run_dir = _ensure_output_dir(output_base)
    print(f"Saving results to: {run_dir}")
    trades_csv = os.path.join(run_dir, "trades.csv")
    equity_csv = os.path.join(run_dir, "equity_curve.csv")
    equity_png = os.path.join(run_dir, "equity_curve.png")
    _save_trades_csv([], trades_csv)
    placeholder_equity = pd.Series([starting_equity], index=[pd.Timestamp.now(tz=timezone.utc)])
    placeholder_equity.to_csv(equity_csv, header=["equity"])
    _plot_equity_curve(placeholder_equity, equity_png)
    progress_path = os.path.join(run_dir, "status.txt")
    try:
        with open(progress_path, "w", encoding="utf-8") as f:
            f.write("Starting backtest...\n")
    except Exception:
        progress_path = None

    connected = False
    tried_ports: list[int] = []
    ports_to_try: list[int] = []
    if env_port:
        try:
            ports_to_try.append(int(env_port))
        except ValueError:
            pass
    # Try common ports: TWS (7497 paper, 7496 live), Gateway (4002 paper, 4001 live)
    ports_to_try.extend([7497, 7496, 4002, 4001])

    for port in ports_to_try:
        if port in tried_ports:
            continue
        tried_ports.append(port)

        # Try a set of client IDs in case the default is in use
        client_ids_to_try = [env_client_id] + list(range(env_client_id + 1, env_client_id + 6))
        for cid in client_ids_to_try:
            try:
                msg = f"Connecting to IBKR at {env_host}:{port} (clientId={cid})..."
                print(msg)
                if progress_path:
                    try:
                        with open(progress_path, "a", encoding="utf-8") as f:
                            f.write(msg + "\n")
                    except Exception:
                        pass
                await ib.connectAsync(env_host, port, clientId=cid)
                if ib.isConnected():
                    ok = f"Connected to IBKR on port {port} with clientId={cid}."
                    print(ok)
                    if progress_path:
                        try:
                            with open(progress_path, "a", encoding="utf-8") as f:
                                f.write(ok + "\n")
                        except Exception:
                            pass
                    connected = True
                    break
            except Exception as e:
                err_text = str(e)
                err = f"API connection failed: {e}\nMake sure API port on TWS/IBG is open\n"
                print(err)
                if progress_path:
                    try:
                        with open(progress_path, "a", encoding="utf-8") as f:
                            f.write(err + "\n")
                    except Exception:
                        pass

                # If client ID is in use, try next client ID on the same port
                if "client id is already in use" in err_text.lower() or "clientId" in err_text:
                    continue
                # Otherwise, move to next port
                else:
                    break
        if connected:
            break
    if not connected:
        raise RuntimeError("Unable to connect to IBKR Gateway/TWS. Ensure it is running and API enabled.")

    broker = IBKRHistoricalBroker(ib, progress_path=progress_path)
    params = {
        "symbol": symbol,
        "backfill_days": days,
        "starting_equity": starting_equity,
        "use_bracket_orders": False,
        "place_market_orders": True,
        "persist_resampled": True,
    }
    strat = IntradaySupertrendMA("IntradaySupertrendMA", broker, params)
    await strat.init()

    # Fetch requested minute data and store
    end_dt = datetime.now(timezone.utc)
    start_dt = end_dt - timedelta(days=days)
    df = await broker.get_historical_data(symbol, "1min", start_dt.strftime("%Y-%m-%d"), end_dt.strftime("%Y-%m-%d"))
    from data.data_manager import DataManager
    dm = DataManager()
    if not df.empty:
        dm.save_bars(symbol, "1min", df)
        minute_df = df
    else:
        minute_df = dm.load_bars(symbol, "1min")

    for ts, row in minute_df.iterrows():
        bar = pd.Series({
            "timestamp": ts,
            "open": float(row.open),
            "high": float(row.high),
            "low": float(row.low),
            "close": float(row.close),
            "volume": float(row.volume or 0),
        })
        await strat.on_bar(bar)

    await strat.cleanup()

    # Save trades
    _save_trades_csv(strat.trades, trades_csv)

    # Build and save equity curve
    equity_series = _build_equity_curve(strat.trades, starting_equity)
    equity_series.to_csv(equity_csv, header=["equity"])
    _plot_equity_curve(equity_series, equity_png)

    # Print simple results
    print(f"Total trades: {len(strat.trades)}")
    print(f"Ending equity: {strat.current_equity:.2f}")
    print(f"Saved: {trades_csv}, {equity_csv}, {equity_png}")


if __name__ == "__main__":
    # Support environments where an event loop is already running (e.g., notebooks)
    try:
        import nest_asyncio  # type: ignore
        nest_asyncio.apply()
    except Exception:
        pass

    loop = asyncio.get_event_loop()
    try:
        # 5 years ≈ 1826 days
        loop.run_until_complete(run_backtest(symbol="QQQ", days=1826, starting_equity=100000.0, output_base="backtests/QQQ"))
    except RuntimeError:
        asyncio.run(run_backtest(symbol="QQQ", days=1826, starting_equity=100000.0, output_base="backtests/QQQ"))


