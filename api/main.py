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
from backtesting import Backtest
import pandas as pd
import numpy as np
import json
import quantstats as qs
from jinja2 import Environment, FileSystemLoader
from bokeh.embed import components
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
    await ibkr_manager.connect()
    yield
    # Shutdown
    print("Application shutting down...")
    ibkr_manager.disconnect()

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

class RunningStrategies(BaseModel):
    running_strategies: List[str]

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

# --- Strategy Endpoints (To be refactored similarly) ---
# ... (Keeping strategy endpoints as they are for now)
class StartStrategyRequest(BaseModel):
    name: str
    broker: str
    params: dict = {}

class StopStrategyRequest(BaseModel):
    name: str

@strategy_router.post("/start", summary="Start a strategy", response_model=StrategyStatus)
async def start_strategy(req: StartStrategyRequest):
    if req.name in running_strategies:
        raise HTTPException(status_code=400, detail="Strategy is already running.")
    
    try:
        strategy_cls = StrategyRegistry.get(req.name)
        broker_instance = get_broker(req.broker)
        
        # Create a new instance for this run
        strategy_instance = strategy_cls(name=req.name, broker=broker_instance, **req.params)
        
        # Run the strategy in the background
        loop = asyncio.get_running_loop()
        task = loop.create_task(strategy_instance.run())
        running_strategies[req.name] = task
        
        return {"status": "started", "strategy": req.name}
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

@broker_router.get("/{broker_name}/backtest", summary="Run a backtest for a strategy", response_class=HTMLResponse)
async def run_backtest(
    broker: BrokerBase = Depends(get_broker),
    strategy_name: str = Query(..., description="The class name of the strategy to test (e.g., 'MACrossover')."),
    symbol: str = Query(..., description="The ticker symbol to fetch data for."),
    timeframe: str = Query("1 day", description="The bar size (e.g., '1 day', '1 hour')."),
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format."),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format."),
    cash: int = Query(10000, description="Initial cash for the backtest."),
    commission: float = Query(0.002, description="Commission per trade."),
    stop_loss_pct: float = Query(0.05, description="Stop-loss percentage (e.g., 0.05 for 5%).")
):
    try:
        # --- Timeframe Translation ---
        # Translate user-friendly timeframes to library-friendly formats
        timeframe_map = {
            "1 day": "1d",
            "1 hour": "1h",
            "1 minute": "1m"
            # Add other translations as needed
        }
        api_timeframe = timeframe_map.get(timeframe.lower(), timeframe)

        # 1. Fetch data using the smart data endpoint's logic
        data = await get_smart_data(
            symbol=symbol,
            timeframe=api_timeframe, # Use the translated timeframe
            start_date=start_date,
            end_date=end_date,
            broker=broker,
            data_manager=DataManager() # Create a fresh DataManager for the backtest
        )
        # Convert list of dicts back to DataFrame for backtesting.py
        data_df = pd.DataFrame(data)
        if data_df.empty:
            return HTMLResponse(content="<h3>No data available for the selected range.</h3>", status_code=404)
        
        data_df['timestamp'] = pd.to_datetime(data_df['timestamp'])
        data_df.set_index('timestamp', inplace=True)
        # Rename columns to what backtesting.py expects
        data_df.rename(columns={
            'open': 'Open', 'high': 'High', 'low': 'Low',
            'close': 'Close', 'volume': 'Volume'
        }, inplace=True)
        
        # 2. Get the strategy class from the registry
        strategy_cls = StrategyRegistry.get(strategy_name)
        
        # Add stop loss parameter to the strategy
        strategy_cls.stop_loss_pct = stop_loss_pct

        # 3. Run the backtest
        bt = Backtest(data_df, strategy_cls, cash=cash, commission=commission)
        stats = bt.run()
        
        # --- Generate Report ---
        # 1. Create a unique filename for the results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename_base = f"backtest_{strategy_name}_{symbol}_{start_date}_{end_date}_sl_{stop_loss_pct}".replace('.', '_')
        
        # Create a directory for results if it doesn't exist
        results_dir = "results"
        os.makedirs(results_dir, exist_ok=True)

        plot_filename = os.path.join(results_dir, f"{filename_base}_plot.html")
        qs_report_filename = os.path.join(results_dir, f"{filename_base}_qs_report.html")
        trades_filename = os.path.join(results_dir, f"{filename_base}_trades.html")
        
        # 2. Generate Bokeh plot
        bt.plot(filename=plot_filename, open_browser=False)

        # 3. Generate QuantStats report
        returns = stats['Returns']
        qs.reports.html(returns, output=qs_report_filename, title=f'{strategy_name} on {symbol}')

        # 4. Save detailed trades to an HTML table
        trades_df = stats['_trades']
        trades_df.to_html(trades_filename, escape=False, classes='table table-striped text-center')

        # --- Create a combined HTML response ---
        env = Environment(loader=FileSystemLoader('api/templates'))
        template = env.get_template('dashboard.html')

        # Read the content of the generated files
        with open(plot_filename, 'r') as f:
            plot_script, plot_div = components(f.read())
        
        with open(qs_report_filename, 'r') as f:
            qs_report_html = f.read()

        with open(trades_filename, 'r') as f:
            trades_html = f.read()

        html_content = template.render(
            strategy_name=strategy_name,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            stats=stats.to_dict(),
            plot_script=plot_script,
            plot_div=plot_div,
            qs_report_html=qs_report_html,
            trades_html=trades_html
        )
        return HTMLResponse(content=html_content)
    
    except KeyError:
        return HTMLResponse(content=f"<h3>Strategy '{strategy_name}' not found.</h3>", status_code=404)
    except Exception as e:
        logging.error(f"Backtest failed: {e}", exc_info=True)
        return HTMLResponse(content=f"<h3>An error occurred during the backtest: {e}</h3>", status_code=500)

@app.get("/results/{filepath:path}")
async def get_results_file(filepath: str):
    """Serves the generated backtest report files."""
    file_path = os.path.join("results", filepath)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="File not found.")

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
# Import new strategy for auto-discovery, though dynamic import handles it
try:
    import strategies.ma_crossover_strategy
except ImportError:
    pass 