import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import matplotlib
matplotlib.use('Agg')
import tracemalloc
tracemalloc.start()

from fastapi import FastAPI, APIRouter, HTTPException, Query, Depends, WebSocket, WebSocketDisconnect, Response, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional
import logging
from logging.handlers import RotatingFileHandler
import importlib
import os
from fastapi.responses import FileResponse, HTMLResponse
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
import asyncio

from core.registry import StrategyRegistry, BrokerRegistry
from core.base import BrokerBase
from data.data_manager import DataManager

# --- Broker and Strategy Registration ---
# Import the modules containing brokers and strategies to ensure they are registered.
from brokers import paper_broker
# Import available strategies
import strategies.rsi_vwap_strategy
import strategies.Supertrend
import strategies.SwingFailure
import strategies.Support_Resiatance
import strategies.Bollinger_5EMA
import strategies.Turtle
import strategies.Pivot
import strategies.Fibonnaci

# Ensure strategies are registered
print(f"Registered strategies: {StrategyRegistry.list()}")
print(f"Registered brokers: {BrokerRegistry.list()}")

# --- Logging Setup ---
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log_file = 'fastapi_server.log'
file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.INFO)
root_logger = logging.getLogger()
root_logger.addHandler(file_handler)
root_logger.setLevel(logging.INFO)
# --- End Logging Setup ---

# --- App Lifespan Management ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create instances and connect to services here
    app.state.data_manager = DataManager()
    print("DataManager initialized.")
    
    print("Application starting up...")
    
    yield
    
    # Shutdown
    print("Application shutting down...")

app = FastAPI(
    title="TradeFlow AI: Algo Trading Platform",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Custom exception handler to match Flutter error format
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": str(exc)}
    )

# In-memory store for running strategies and brokers
running_strategies = {}
broker_instances: Dict[str, BrokerBase] = {}

# --- Dependency ---
def get_broker(broker_name: str) -> BrokerBase:
    """
    Dependency to get or create a broker instance.
    This ensures a single instance per broker type.
    """
    if broker_name in broker_instances:
        return broker_instances[broker_name]
    
    try:
        broker_cls = BrokerRegistry.get(broker_name)
        broker_instance = broker_cls(name=broker_name)
        broker_instances[broker_name] = broker_instance
        return broker_instance
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Broker '{broker_name}' not found.")

def get_data_manager(request: Request) -> DataManager:
    return request.app.state.data_manager

# Routers
strategy_router = APIRouter(prefix="/api/v1/strategies", tags=["Strategies"])
broker_router = APIRouter(prefix="/api/v1/broker", tags=["Brokers"])
data_router = APIRouter(prefix="/api/v1/data", tags=["Data"])

# --- Pydantic Models ---

# -- API Response Models --
class HealthStatus(BaseModel):
    status: str
    paper_broker_available: bool

class StrategyList(BaseModel):
    strategies: List[str]

class BrokerList(BaseModel):
    brokers: List[str]

class AccountSummaryItem(BaseModel):
    tag: str
    value: str
    currency: str
    account: str

class AccountInfo(BaseModel):
    account_summary: List[AccountSummaryItem]

class Position(BaseModel):
    symbol: str
    exchange: str
    currency: str
    position: float
    avg_cost: float

class OpenOrder(BaseModel):
    orderId: int
    symbol: str
    action: str
    totalQuantity: float
    lmtPrice: float
    orderType: str
    status: str

class SimpleOrderResult(BaseModel):
    order_id: int
    status: str

class BracketOrderChild(BaseModel):
    id: int
    type: str
    status: str

class BracketOrderResult(BaseModel):
    parent_order_id: int
    status: str
    children: List[BracketOrderChild]

class CancelledOrderItem(BaseModel):
    order_id: int
    status: str

class CancelAllOrdersResult(BaseModel):
    status: str
    message: str
    cancelled_orders: List[CancelledOrderItem]

class HistoricalDataItem(BaseModel):
    date: str
    Open: float
    High: float
    Low: float
    Close: float
    Volume: float

class HistoricalData(BaseModel):
    symbol: str
    data: List[HistoricalDataItem]

class StrategyStatus(BaseModel):
    status: str
    strategy: str
    run_id: Optional[str] = None
    message: Optional[str] = None

class RunningStrategies(BaseModel):
    running_strategies: List[str]

# -- Backtest Results Models --
class Trade(BaseModel):
    entry_time: str
    exit_time: str
    symbol: str
    quantity: float
    side: str
    entry_price: float
    exit_price: float
    pnl: float

class BacktestSummary(BaseModel):
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    average_trade_pnl: float

class BacktestResult(BaseModel):
    run_id: str
    strategy_name: str
    start_time: Optional[str]
    end_time: Optional[str]
    initial_capital: float
    final_equity: float
    total_return: float
    total_return_pct: float
    equity_curve: List[List[str]]
    trades: List[Trade]
    summary: BacktestSummary
    parameters: Dict[str, Any]

class BacktestResultsList(BaseModel):
    run_ids: List[str]

# -- API Request Models --
class FlutterOrderRequest(BaseModel):
    symbol: str = Field(..., example="AAPL", description="The ticker symbol for the order.")
    qty: float = Field(..., example=10, description="The quantity of shares to trade.")
    side: str = Field(..., example="buy", description="The side of the order ('buy' or 'sell').")
    type: str = Field(..., example="market", description="The order type ('market' or 'limit').")

class OrderDetails(BaseModel):
    symbol: str = Field(..., example="AAPL", description="The ticker symbol for the order.")
    qty: float = Field(..., example=10, description="The quantity of shares to trade.")
    side: str = Field(..., example="buy", description="The side of the order ('buy' or 'sell').")
    order_type: str = Field(..., example="MKT", description="The order type ('MKT' for market, 'LMT' for limit).")
    limit_price: Optional[float] = Field(None, example=150.0, description="The limit price, required for LMT orders.")

class PlaceOrderRequest(BaseModel):
    order: OrderDetails
    stop_loss: Optional[float] = Field(None, example=145.0, description="The stop-loss price for a bracket order.")
    take_profit: Optional[float] = Field(None, example=155.0, description="The take-profit price for a bracket order.")

class CancelOrderRequest(BaseModel):
    order_id: int

# --- Data Endpoints ---
@data_router.get("/{symbol}/{timeframe}", summary="Fetch historical data from Polygon.io")
async def get_smart_data(
    symbol: str,
    timeframe: str, # e.g., "1min", "5min", "1h", "1d"
    start_date: str, # YYYY-MM-DD
    end_date: str,   # YYYY-MM-DD
    data_manager: DataManager = Depends(get_data_manager)
):
    """
    This endpoint fetches historical data directly from Polygon.io.
    """
    try:
        from data.polygon_data import PolygonDataProvider
        from datetime import datetime
        
        # Create Polygon data provider
        data_provider = PolygonDataProvider()
        
        # Convert dates to datetime objects
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Convert timeframe to Polygon format
        timeframe_map = {
            "1min": "1",
            "5min": "5", 
            "15min": "15",
            "30min": "30",
            "1h": "60",
            "2h": "120",
            "3h": "180",
            "4h": "240",
            "1d": "1D",
            "1w": "1W",
            "1m": "1M"
        }
        
        interval = timeframe_map.get(timeframe.lower(), "1D")
        
        # Fetch data from Polygon
        df = await data_provider.get_historical_bars(
            symbol=symbol,
            from_date=start_dt,
            to_date=end_dt,
            interval=interval
        )
        
        if df is not None and not df.empty:
            # Ensure proper column names
            if 'date' in df.columns:
                df.set_index('date', inplace=True)
            elif 'timestamp' in df.columns:
                df.set_index('timestamp', inplace=True)
            
            # Standardize column names to match expected format
            column_mapping = {
                'open': 'open', 'high': 'high', 'low': 'low', 
                'close': 'close', 'volume': 'volume'
            }
            df.rename(columns=column_mapping, inplace=True)
            
            # Return data in Flutter spec format
            json_data = df.reset_index()
        json_data.columns = [col.lower() if col != 'timestamp' else 'timestamp' for col in json_data.columns]
        
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "data": json_data.to_dict(orient='records')
        }
    else:
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "data": []
        }
            
    except Exception as e:
        logging.error(f"Error fetching data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch data: {str(e)}")

# --- Broker Endpoints ---
@broker_router.get("/{broker_name}/account-info", summary="Get account info from a broker")
async def get_account_info(broker_name: str, broker: BrokerBase = Depends(get_broker)):
    try:
        account_data = await broker.get_account_info()
        
        # Transform to match Flutter spec
        cash_balance = 0.0
        equity = 0.0
        buying_power = 0.0
        
        for item in account_data.get('account_summary', []):
            if item.get('tag') == 'AvailableFunds':
                cash_balance = float(item.get('value', 0))
            elif item.get('tag') == 'NetLiquidation':
                equity = float(item.get('value', 0))
            elif item.get('tag') == 'BuyingPower':
                buying_power = float(item.get('value', 0))
        
        return {
            "account_id": "PAPER-123",
            "cash_balance": cash_balance,
            "equity": equity,
            "buying_power": buying_power
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@broker_router.get("/{broker_name}/positions", summary="Get account positions from a broker")
async def get_positions(broker_name: str, broker: BrokerBase = Depends(get_broker)):
    try:
        positions_data = await broker.get_positions()
        
        # Transform to match Flutter spec
        positions = []
        for pos in positions_data:
            # Get current market price (you might need to implement this)
            market_price = pos.get('avg_cost', 0.0)  # Default to avg_cost for now
            quantity = abs(pos.get('position', 0.0))
            avg_price = pos.get('avg_cost', 0.0)
            unrealized_pl = (market_price - avg_price) * quantity
            
            positions.append({
                "symbol": pos.get('symbol', ''),
                "quantity": quantity,
                "avg_price": avg_price,
                "market_price": market_price,
                "unrealized_pl": unrealized_pl
            })
        
        return positions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@broker_router.get("/{broker_name}/open-orders", summary="Get open orders from a broker", response_model=List[OpenOrder])
async def get_open_orders(broker_name: str, broker: BrokerBase = Depends(get_broker)):
    try:
        return await broker.get_open_orders()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@broker_router.post("/{broker_name}/order", summary="Place an order", response_model=Dict[str, Any])
async def place_order(broker_name: str, req: FlutterOrderRequest, broker: BrokerBase = Depends(get_broker)):
    try:
        # Transform Flutter request to internal format
        order_dict = {
            "symbol": req.symbol,
            "qty": req.qty,
            "side": req.side,
            "order_type": "MKT" if req.type == "market" else "LMT"
        }
        
        result = await broker.place_order(order_dict)
        
        # Transform response to match Flutter spec
        if "order_id" in result:
            return {
                "status": "filled" if result.get("status") == "Filled" else "submitted",
                "symbol": req.symbol,
                "qty": req.qty,
                "filled_price": result.get("fill_price", 0.0)
            }
        else:
            return {
                "status": "error",
                "symbol": req.symbol,
                "qty": req.qty,
                "filled_price": 0.0
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@broker_router.post("/{broker_name}/cancel-order", summary="Cancel an open order", response_model=SimpleOrderResult)
async def cancel_order(broker_name: str, req: CancelOrderRequest, broker: BrokerBase = Depends(get_broker)):
    try:
        return await broker.cancel_order(req.order_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@broker_router.post("/{broker_name}/cancel-all-orders", summary="Cancel all open orders", response_model=CancelAllOrdersResult)
async def cancel_all_orders(broker_name: str, broker: BrokerBase = Depends(get_broker)):
    try:
        return await broker.cancel_all_orders()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@broker_router.get("/{broker_name}/historical-data", summary="Get historical market data", response_model=HistoricalData)
async def get_historical_data(
    broker_name: str, 
    symbol: str = Query(..., description="The ticker symbol to fetch data for."),
    timeframe: str = Query("1 day", description="The bar size (e.g., '1 day', '1 hour')."),
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format."),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format."),
    broker: BrokerBase = Depends(get_broker)
):
    try:
        data = await broker.get_historical_data(symbol, timeframe, start_date, end_date)
        # Convert DataFrame to list of dicts for JSON response
        if data is not None and not data.empty:
            data_list = data.reset_index().to_dict(orient="records")
            return {"symbol": symbol, "data": data_list}
        return {"symbol": symbol, "data": []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/{broker_name}/market-data/{asset_type}/{symbol}")
async def websocket_market_data(
    websocket: WebSocket,
    broker: BrokerBase = Depends(get_broker),
    asset_type: str = "stock", # stock or forex
    symbol: str = "AAPL"
):
    await websocket.accept()
    
    # Define the callback that sends data over the WebSocket
    async def on_data(data):
        try:
            await websocket.send_text(json.dumps(data, default=str))
        except WebSocketDisconnect:
            logging.info(f"WebSocket disconnected for {symbol}.")
        except Exception as e:
            logging.error(f"Error sending data on WebSocket for {symbol}: {e}")

    stream_task = None
    try:
        # Start the broker's data stream
        stream_task = asyncio.create_task(
            broker.stream_market_data(symbol, on_data, asset_type)
        )
        
        # Keep the connection open and listen for client messages
        while True:
            # This is a simple way to keep the connection alive.
            # You could also implement logic to handle incoming messages.
            await websocket.receive_text()
            
    except WebSocketDisconnect:
        logging.info(f"Client disconnected from {symbol} stream.")
    except Exception as e:
        logging.error(f"An error occurred in the WebSocket for {symbol}: {e}")
    finally:
        # Clean up the streaming task when the connection closes
        if stream_task:
            stream_task.cancel()
            await asyncio.sleep(1) # Give a moment for cleanup
        logging.info(f"WebSocket for {symbol} closed and cleaned up.")

# --- Strategy Endpoints ---
class StartStrategyRequest(BaseModel):
    name: str
    broker: str
    params: dict = {}

class StopStrategyRequest(BaseModel):
    name: str

@strategy_router.post("/start", summary="Start a strategy backtest", response_model=StrategyStatus)
async def start_strategy(req: StartStrategyRequest):
    """
    Start a strategy backtest using the custom engine.
    This runs a complete backtest and saves results to JSON.
    """
    if req.name in running_strategies:
        raise HTTPException(status_code=400, detail="Strategy is already running.")
    
    try:
        strategy_cls = StrategyRegistry.get(req.name)
        broker_instance = get_broker(req.broker)
        
        # Create a new instance for this run, passing params as a single dictionary
        strategy_instance = strategy_cls(name=req.name, broker=broker_instance, params=req.params)
        
        # Run the strategy in a background task to avoid blocking the API response
        async def run_strategy_background():
            try:
                run_id = await strategy_instance.run()
                if run_id:
                    print(f"Strategy {req.name} completed successfully with run_id: {run_id}")
                else:
                    print(f"Strategy {req.name} failed: No data available")
            except Exception as e:
                print(f"Strategy {req.name} failed with error: {e}")
            finally:
                # Clean up from running strategies
                if req.name in running_strategies:
                    del running_strategies[req.name]
        
        # Start the background task
        task = asyncio.create_task(run_strategy_background())
        running_strategies[req.name] = task
        
        # Return immediately with a "started" status
        return {"status": "started", "strategy": req.name, "message": "Strategy backtest started successfully"}
            
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Strategy '{req.name}' not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@strategy_router.post("/stop", summary="Stop a running strategy", response_model=StrategyStatus)
async def stop_strategy(req: StopStrategyRequest):
    task = running_strategies.get(req.name)
    if not task:
        raise HTTPException(status_code=404, detail="Strategy not found or not running.")
    
    try:
        task.cancel()
        del running_strategies[req.name]
        return {"status": "stopped", "strategy": req.name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@strategy_router.get("/running", summary="List running strategies", response_model=RunningStrategies)
def list_running_strategies():
    return {"running_strategies": list(running_strategies.keys())}

@strategy_router.get("/available", summary="List available strategies")
def list_available_strategies():
    """List all available strategies that can be run."""
    from core.registry import StrategyRegistry
    strategies = StrategyRegistry.list()
    
    # Transform to match Flutter spec with descriptions and timeframes
    strategy_descriptions = {
        "IntradaySupertrendMA": "Intraday SuperTrend with Moving Averages (1min base, 30min MAs, 3h SuperTrend)",
        "TurtleStrategy": "Turtle Trading System (1h timeframe)",
        "BB5EMAStrategy": "Bollinger Bands with 5-period EMA (4h timeframe)",
        "SRTrend4H": "Support and Resistance Trend Strategy (4h timeframe)",
        "SwingFailureStrategy": "Swing Failure Pattern Strategy (1h timeframe)",
        "RSIVWAPStrategy": "RSI with VWAP Strategy (4h timeframe)",
        "PivotStrategy": "Pivot Point Strategy (15min timeframe)",
        "FibonacciStrategy": "Fibonacci Retracement Strategy (4h timeframe)"
    }
    
    return [
        {"name": strategy, "description": strategy_descriptions.get(strategy, f"{strategy} trading strategy")}
        for strategy in strategies
    ]

@strategy_router.get("/status/{strategy_name}", summary="Get strategy status", response_model=StrategyStatus)
async def get_strategy_status(strategy_name: str):
    """Get the status of a running strategy."""
    if strategy_name in running_strategies:
        task = running_strategies[strategy_name]
        if task.done():
            try:
                # Task completed, check if there are any new results
                result = task.result()
                return {"status": "completed", "strategy": strategy_name, "message": "Strategy completed successfully"}
            except Exception as e:
                return {"status": "failed", "strategy": strategy_name, "message": f"Strategy failed: {str(e)}"}
        else:
            return {"status": "running", "strategy": strategy_name, "message": "Strategy is currently running"}
    else:
        return {"status": "not_found", "strategy": strategy_name, "message": "Strategy not found or not running"}

@strategy_router.get("/results/{run_id}", summary="Get backtest results by run ID")
async def get_backtest_results(run_id: str):
    """
    Retrieve backtest results for a specific run ID from database.
    """
    try:
        from data.backtest_database import BacktestDatabase
        db = BacktestDatabase()
        
        # Try to get from database first
        results = db.get_backtest_result(run_id)
        
        if not results:
            # Fallback to JSON file for backward compatibility
            results_dir = "backtest_results"
            filepath = os.path.join(results_dir, f"{run_id}.json")
            
            if not os.path.exists(filepath):
                raise HTTPException(status_code=404, detail=f"Backtest results for run ID '{run_id}' not found.")
            
            with open(filepath, 'r') as f:
                results = json.load(f)
        
        # Transform to match Flutter spec
        trades = []
        for trade in results.get('trades', []):
            trades.append({
                "symbol": trade.get('symbol', ''),
                "side": trade.get('side', ''),
                "qty": trade.get('quantity', 0),
                "price": trade.get('entry_price', 0.0),
                "time": trade.get('entry_time', '')
            })
        
        # Transform equity curve to match Flutter spec
        equity_curve = []
        for point in results.get('equity_curve', []):
            if isinstance(point, list) and len(point) >= 2:
                equity_curve.append({
                    "timestamp": point[0],
                    "equity": float(point[1]) if isinstance(point[1], str) else point[1]
                })
        
        return {
            "run_id": results.get('run_id', run_id),
            "strategy": results.get('strategy_name', ''),
            "status": "completed",
            "start_date": results.get('start_time', '').split('T')[0] if results.get('start_time') else '',
            "end_date": results.get('end_time', '').split('T')[0] if results.get('end_time') else '',
            "initial_capital": results.get('initial_capital', 0.0),
            "final_capital": results.get('final_equity', 0.0),
            "total_trades": results.get('summary', {}).get('total_trades', 0),
            "trades": trades,
            "equity_curve": equity_curve,
            "pnl": {
                "total": results.get('total_return', 0.0),
                "percentage": results.get('total_return_pct', 0.0)
            }
        }
    
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Invalid JSON format in results file: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading backtest results: {str(e)}")

@strategy_router.get("/results", summary="List available backtest results")
async def list_backtest_results():
    """
    List all available backtest result run IDs from database.
    """
    try:
        from data.backtest_database import BacktestDatabase
        db = BacktestDatabase()
        
        # Get run IDs from database
        run_ids = db.list_backtest_runs()
        
        if not run_ids:
            # Fallback to JSON files for backward compatibility
            results_dir = "backtest_results"
            
            if not os.path.exists(results_dir):
                return []
            
            # Get all JSON files in the results directory
            for filename in os.listdir(results_dir):
                if filename.endswith('.json'):
                    run_id = filename[:-5]  # Remove .json extension
                    run_ids.append(run_id)
            
            # Sort by creation time (newest first)
            run_ids.sort(key=lambda x: os.path.getctime(os.path.join(results_dir, f"{x}.json")), reverse=True)
        
        # Transform to match Flutter spec
        results = []
        for run_id in run_ids:
            # Try to get strategy name from database or filename
            strategy_name = "Unknown"
            try:
                result_data = db.get_backtest_result(run_id)
                if result_data:
                    strategy_name = result_data.get('strategy_name', 'Unknown')
            except:
                # Extract strategy name from run_id if possible
                if '_' in run_id:
                    strategy_name = run_id.split('_')[0]
            
            results.append({
                "run_id": run_id,
                "strategy": strategy_name,
                "status": "completed"
            })
        
        return results
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing backtest results: {str(e)}")

@strategy_router.get("/database/stats", summary="Get database statistics")
async def get_database_stats():
    """
    Get comprehensive database statistics.
    """
    try:
        from data.backtest_database import BacktestDatabase
        db = BacktestDatabase()
        stats = db.get_database_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting database stats: {str(e)}")

@strategy_router.get("/database/strategy/{strategy_name}/performance", summary="Get strategy performance history")
async def get_strategy_performance(strategy_name: str):
    """
    Get performance history for a specific strategy.
    """
    try:
        from data.backtest_database import BacktestDatabase
        db = BacktestDatabase()
        performance = db.get_strategy_performance(strategy_name)
        return {"strategy_name": strategy_name, "performance_history": performance}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting strategy performance: {str(e)}")

@strategy_router.get("/database/runs/{run_id}/trades", summary="Get detailed trade history")
async def get_trade_history(run_id: str):
    """
    Get detailed trade history for a specific backtest run.
    """
    try:
        from data.backtest_database import BacktestDatabase
        db = BacktestDatabase()
        trades = db.get_trade_history(run_id)
        return {"run_id": run_id, "trades": trades}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting trade history: {str(e)}")

@strategy_router.delete("/database/runs/{run_id}", summary="Delete backtest run")
async def delete_backtest_run(run_id: str):
    """
    Delete a backtest run and all associated data from the database.
    """
    try:
        from data.backtest_database import BacktestDatabase
        db = BacktestDatabase()
        success = db.delete_backtest_run(run_id)
        if success:
            return {"message": f"Backtest run {run_id} deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"Backtest run {run_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting backtest run: {str(e)}")

# Remove the obsolete backtesting.py endpoint
# @broker_router.get("/{broker_name}/backtest", summary="Run a backtest for a strategy", response_class=HTMLResponse)
# async def run_backtest(...) - REMOVED

@app.get("/results/{filepath:path}")
async def get_results_file(filepath: str):
    """Serves the generated backtest report files."""
    file_path = os.path.join("results", filepath)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="File not found.")

@app.get("/backtest-report", summary="Backtest Report Frontend")
async def get_backtest_report():
    """Serves the backtest report frontend."""
    file_path = "frontend/backtest_report.html"
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Backtest report frontend not found.")

# --- Root and Health Check ---
@app.get("/", summary="Root endpoint with links to API docs")
async def read_root():
    return {"message": "Welcome to TradeFlow AI", "docs": "/docs"}

@app.get("/health", summary="Health check")
async def health_check():
    return {
        "status": "ok"
    }

# --- Include Routers ---
app.include_router(strategy_router)
app.include_router(broker_router)
app.include_router(data_router)

# Ensure registration of broker
import brokers.paper_broker

# --- Server Startup ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 