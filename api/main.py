import matplotlib
matplotlib.use('Agg')
import tracemalloc
tracemalloc.start()

from fastapi import FastAPI, APIRouter, HTTPException, Query, Depends, WebSocket, WebSocketDisconnect, Response, Request
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
from brokers.ibkr_manager import ibkr_manager
from data.data_manager import DataManager

# --- Broker and Strategy Registration ---
# Import the modules containing brokers and strategies to ensure they are registered.
from brokers import ibkr_broker, mock_broker
from strategies import macrossover_strategy, sample_strategy

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
    try:
        await ibkr_manager.connect()
    except Exception as e:
        print(f"Warning: IBKR connection failed: {e}")
        print("Continuing without IBKR connection...")
    
    yield
    
    # Shutdown
    print("Application shutting down...")
    try:
        if hasattr(ibkr_manager, 'disconnect'):
            ibkr_manager.disconnect()
    except Exception as e:
        print(f"Warning: Error during IBKR disconnect: {e}")

app = FastAPI(
    title="TradeFlow AI: Algo Trading Platform",
    lifespan=lifespan
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
    ibkr_connected: bool

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
@data_router.get("/{symbol}/{timeframe}", summary="Fetch historical and real-time data with smart backfilling")
async def get_smart_data(
    symbol: str,
    timeframe: str, # e.g., "1min", "5min", "1day"
    start_date: str, # YYYY-MM-DD
    end_date: str,   # YYYY-MM-DD
    broker: BrokerBase = Depends(get_broker),
    data_manager: DataManager = Depends(get_data_manager) # Use the new dependency
):
    """
    This endpoint intelligently fetches data by first checking the local
    database and then backfilling any missing data from the broker API.
    """
    # 1. Fetch what we already have in the database
    db_data = data_manager.fetch_bars(symbol, timeframe, start_date, end_date)
    
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    
    # 2. Analyze for gaps and backfill if necessary
    if db_data.empty or db_data.index[-1] < end_dt:
        # Determine the date from which to fetch new data
        fetch_start_date = db_data.index[-1] + timedelta(seconds=1) if not db_data.empty else start_dt
        
        logging.info(f"Data gap found for {symbol}. Fetching from broker from {fetch_start_date} to {end_date}.")
        
        # Convert timeframe for IBKR API (e.g., '1min' -> '1 min')
        ibkr_timeframe = timeframe.replace('min', ' min').replace('day', ' day')
        
        try:
            # Fetch the missing data from the broker
            broker_data = await broker.get_historical_data(symbol, ibkr_timeframe, fetch_start_date.strftime('%Y-%m-%d'), end_date)
            
            if broker_data is not None and not broker_data.empty:
                # ---> START FIX: Standardize broker data to match DB schema <---
                
                # 1. Rename 'date' column to 'timestamp' if it exists
                if 'date' in broker_data.columns:
                    broker_data.rename(columns={'date': 'timestamp'}, inplace=True)

                # 2. Ensure timestamp is the index
                if 'timestamp' in broker_data.columns:
                    broker_data['timestamp'] = pd.to_datetime(broker_data['timestamp'])
                    broker_data.set_index('timestamp', inplace=True)
                elif not isinstance(broker_data.index, pd.DatetimeIndex):
                     # If no timestamp column, assume index is what we need
                    broker_data.index = pd.to_datetime(broker_data.index)
                
                # 3. Drop columns that don't exist in the DB
                db_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                cols_to_drop = [col for col in broker_data.columns if col not in db_columns and col.lower() not in [c.lower() for c in db_columns]]
                broker_data.drop(columns=cols_to_drop, inplace=True, errors='ignore')

                # 4. Ensure columns are capitalized before saving
                broker_data.rename(columns={
                    'open': 'Open', 'high': 'High', 'low': 'Low',
                    'close': 'Close', 'volume': 'Volume'
                }, inplace=True)
                # ---> END FIX <---

                # Save the newly fetched data to our database
                # Ensure the base timeframe is used for saving
                data_manager.save_bars(symbol, '1min', broker_data)
                
                # Resample the newly fetched data before combining if needed
                if timeframe != '1min':
                     agg_rules = {'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'}
                     broker_data = broker_data.resample(timeframe).agg(agg_rules).dropna()

                # Combine the data
                combined_data = pd.concat([db_data, broker_data])
                # Remove any potential duplicates from the join
                combined_data = combined_data[~combined_data.index.duplicated(keep='last')]
                db_data = combined_data.sort_index()
                
        except Exception as e:
            logging.error(f"Failed to backfill data from broker: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to backfill data from broker: {e}")
    
    # 3. Final resampling to ensure the output matches the requested timeframe
    if not db_data.empty and timeframe != '1min':
        agg_rules = {'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'}
        db_data = db_data.resample(timeframe).agg(agg_rules).dropna()

    # 4. Return the complete data as JSON
    # It's better to reset the index to make the timestamp a regular column for JSON serialization
    if not db_data.empty:
        json_data = db_data.reset_index().to_dict(orient='records')
        return json_data
    else:
        return []

# --- Broker Endpoints ---
@broker_router.get("/{broker_name}/account-info", summary="Get account info from a broker", response_model=AccountInfo)
async def get_account_info(broker_name: str, broker: BrokerBase = Depends(get_broker)):
    try:
        return await broker.get_account_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@broker_router.get("/{broker_name}/positions", summary="Get account positions from a broker", response_model=List[Position])
async def get_positions(broker_name: str, broker: BrokerBase = Depends(get_broker)):
    try:
        return await broker.get_positions()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@broker_router.get("/{broker_name}/open-orders", summary="Get open orders from a broker", response_model=List[OpenOrder])
async def get_open_orders(broker_name: str, broker: BrokerBase = Depends(get_broker)):
    try:
        return await broker.get_open_orders()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@broker_router.post("/{broker_name}/order", summary="Place an order", response_model=Dict[str, Any])
async def place_order(broker_name: str, req: PlaceOrderRequest, broker: BrokerBase = Depends(get_broker)):
    try:
        return await broker.place_order(req.order.dict(), req.stop_loss, req.take_profit)
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

@strategy_router.get("/available", summary="List available strategies", response_model=StrategyList)
def list_available_strategies():
    """List all available strategies that can be run."""
    from core.registry import StrategyRegistry
    strategies = StrategyRegistry.list()
    return {"strategies": strategies}

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

@strategy_router.get("/results/{run_id}", summary="Get backtest results by run ID", response_model=BacktestResult)
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
        
        # Add default values for missing fields to make it more robust
        results.setdefault('start_time', None)
        results.setdefault('end_time', None)
        results.setdefault('equity_curve', [])
        results.setdefault('trades', [])
        results.setdefault('summary', {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0,
            'total_pnl': 0.0,
            'average_trade_pnl': 0.0
        })
        results.setdefault('parameters', {})
        
        return BacktestResult(**results)
    
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Invalid JSON format in results file: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading backtest results: {str(e)}")

@strategy_router.get("/results", summary="List available backtest results", response_model=BacktestResultsList)
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
                return BacktestResultsList(run_ids=[])
            
            # Get all JSON files in the results directory
            for filename in os.listdir(results_dir):
                if filename.endswith('.json'):
                    run_id = filename[:-5]  # Remove .json extension
                    run_ids.append(run_id)
            
            # Sort by creation time (newest first)
            run_ids.sort(key=lambda x: os.path.getctime(os.path.join(results_dir, f"{x}.json")), reverse=True)
        
        return BacktestResultsList(run_ids=run_ids)
    
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

@app.get("/health", summary="Health check", response_model=HealthStatus)
async def health_check():
    return {
        "status": "ok",
        "ibkr_connected": ibkr_manager.is_connected()
    }

# --- Include Routers ---
app.include_router(strategy_router)
app.include_router(broker_router)
app.include_router(data_router)

# Ensure registration of sample broker and strategy
import brokers.mock_broker
import strategies.sample_strategy
import brokers.ibkr_broker
# Import strategies for auto-discovery
import strategies.macrossover_strategy
import strategies.simple_trading_strategy 