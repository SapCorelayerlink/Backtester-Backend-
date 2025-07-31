# ApexAlgo Trading Framework

ApexAlgo is a Python-based algorithmic trading framework designed for backtesting, analyzing, and deploying trading strategies. It features a modular architecture that separates concerns between data handling, strategy logic, broker integrations, and API services.

## 1. How to Get Started

### Prerequisites
- Python 3.8+
- `pip` for package management

### Installation
1.  Clone the repository to your local machine.
2.  Install the required Python packages:
    ```sh
    pip install -r requirements.txt
    ```

### Running the Application
1.  Start the main application server:
    ```sh
    ./start_server.sh
    ```
    This script will first ensure no old processes are running on port 8000, clear any database locks, and then launch the FastAPI server.

2.  Access the API documentation at `http://127.0.0.1:8000/docs`.

## 2. Directory Structure and Implementation

This framework is organized into distinct modules, each with a specific responsibility.

| Directory      | Purpose                                                                                             | Implementation Details                                                                                                                                                             |
| :------------- | :-------------------------------------------------------------------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `api/`         | **API Layer** - Exposes the framework's features via a FastAPI web server.                          | `main.py` contains all the API endpoints for running backtests, managing strategies, and interacting with brokers. It uses `Jinja2` to serve HTML templates from the `templates/` directory. |
| `brokers/`     | **Broker Integration** - Manages connections to live or paper trading accounts.                       | Contains a `ibkr_broker.py` for Interactive Brokers and a `mock_broker.py` for simulated trading. This modular design allows for easy addition of new brokers.                     |
| `core/`        | **Core Logic** - Contains the foundational building blocks of the framework.                        | `base.py` likely defines `BaseStrategy`, an abstract class that all trading strategies must inherit from. `registry.py` probably discovers and registers all available strategies dynamically. |
| `data/`        | **Data Management** - Handles fetching, storing, and retrieving market data.                          | `data_manager.py` is responsible for sourcing historical data (e.g., from Yahoo Finance or other APIs). `tradeflow.db` is a SQLite database for storing trades, results, or other state. |
| `results/`     | **Output Storage** - Stores the output files generated from backtests.                                | Contains HTML reports from `quantstats`, Bokeh plots of trade performance, and detailed trade logs. This keeps the project's root directory clean.                                   |
| `scripts/`     | **Utility Scripts** - Holds helper scripts for maintenance and operational tasks.                     | Includes scripts like `clear_db_locks.sh` for database maintenance.                                                                                                                |
| `strategies/`  | **Trading Strategies** - Contains the logic for individual trading algorithms.                      | Each `.py` file represents a distinct strategy (e.g., `macrossover_strategy.py`). They inherit from `core.base.BaseStrategy` and implement the core `init()` and `next()` methods. |
| `tests/`       | **Testing Suite** - Contains scripts for testing various parts of the application.                   | Currently holds manual testing scripts but should be expanded with automated unit and integration tests.                                                                           |

## 3. Suggestions for Improvement

The framework is well-structured, but it can be enhanced with modern development practices to improve scalability, maintainability, and ease of use.

### High-Priority Improvements
1.  **Configuration Management**:
    - **Problem**: Critical information like API keys or strategy parameters might be hardcoded.
    - **Solution**: Create a `config.py` file or use a `.env` file (with `python-dotenv`) to centralize all configuration. This separates configuration from code, making it safer and easier to manage different environments (development vs. production).

2.  **Add a Robust Testing Suite**:
    - **Problem**: The `tests/` folder contains manual scripts, which are not scalable.
    - **Solution**: Implement a formal testing suite using `pytest`. Add **unit tests** for individual functions (e.g., strategy calculations) and **integration tests** for workflows like running a full backtest through the API.

3.  **Dockerize the Application**:
    - **Problem**: Setting up the development environment can be error-prone and inconsistent across different machines.
    - **Solution**: Create a `Dockerfile` and a `docker-compose.yml`. This will containerize the entire application and its dependencies, allowing anyone to get it running with a single command: `docker-compose up`.

### Medium-Priority Improvements
4.  **Implement a CI/CD Pipeline**:
    - **Problem**: Code quality and tests are not automatically enforced.
    - **Solution**: Set up a GitHub Actions workflow (`.github/workflows/main.yml`) that automatically runs linting (with `flake8` or `black`) and the `pytest` suite on every push or pull request. This ensures code quality and prevents regressions.

5.  **Refine Real-Time Trading Engine**:
    - **Problem**: The `websocket_client.py` suggests a real-time component, but it's not fully integrated into the core engine.
    - **Solution**: Design a dedicated real-time trading engine that can run strategies against a live data stream from a broker. This would involve managing state, handling live events, and executing orders in a robust, fault-tolerant manner.

6.  **Improve Dependency Management**:
    - **Problem**: `requirements.txt` can sometimes lead to dependency conflicts in complex projects.
    - **Solution**: Migrate to a modern dependency management tool like **Poetry** or **Pipenv**. These tools provide more deterministic builds and better environment isolation.

7.  **Enhance Documentation**:
    - **Problem**: While the structure is good, inline documentation is sparse.
    - **Solution**: Add detailed docstrings to all major classes and functions explaining their purpose, arguments, and return values. This makes the codebase much easier for new developers to understand.
