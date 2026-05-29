# Portfolio Optimization Blueprint Skill

## Overview
NVIDIA Quantitative Portfolio Optimization Blueprint integration for AI-powered financial portfolio management, risk analysis, and investment strategy optimization.

## Description
This skill provides tools for building quantitative finance applications with portfolio optimization, risk management, and algorithmic trading capabilities. It supports:

- **Portfolio Construction**: Build optimal portfolios using various strategies
- **Risk Analysis**: Measure and manage portfolio risk
- **Factor Analysis**: Analyze risk factors and exposures
- **Performance Attribution**: Attribute returns to factors
- **Backtesting**: Test strategies on historical data

## Tools (15)

### portfolio_init
Initialize portfolio optimization system.

**Parameters:**
- `system_name` (required): Name for the system
- `universe` (optional): Asset universe configuration
- `risk_free_rate` (optional): Risk-free rate for calculations
- `base_currency` (optional): Base currency for reporting

### portfolio_create
Create a new portfolio.

**Parameters:**
- `portfolio_name` (required): Name for the portfolio
- `assets` (required): List of assets with weights
- `benchmark` (optional): Benchmark for comparison
- `constraints` (optional): Portfolio constraints

### portfolio_optimize
Optimize portfolio weights.

**Parameters:**
- `portfolio_id` (required): Portfolio to optimize
- `objective` (required): 'max_sharpe', 'min_variance', 'max_return', 'risk_parity'
- `constraints` (optional): Optimization constraints
- `solver` (optional): Optimization solver

### portfolio_rebalance
Rebalance portfolio to target weights.

**Parameters:**
- `portfolio_id` (required): Portfolio to rebalance
- `target_weights` (required): Target allocation
- `method` (optional): 'full', 'partial', 'threshold'
- `transaction_costs` (optional): Cost model

### portfolio_analyze_risk
Analyze portfolio risk.

**Parameters:**
- `portfolio_id` (required): Portfolio to analyze
- `risk_metrics` (optional): Metrics to compute
- `time_horizon` (optional): Analysis time horizon
- `confidence_level` (optional): VaR confidence level

### portfolio_var
Calculate Value at Risk.

**Parameters:**
- `portfolio_id` (required): Portfolio to analyze
- `method` (optional): 'historical', 'parametric', 'monte_carlo'
- `confidence_level` (optional): VaR confidence level
- `time_horizon` (optional): VaR horizon in days

### portfolio_stress_test
Run stress test scenarios.

**Parameters:**
- `portfolio_id` (required): Portfolio to stress test
- `scenarios` (optional): Stress scenarios
- `historical_events` (optional): Historical event scenarios

### portfolio_factor_analysis
Perform factor analysis.

**Parameters:**
- `portfolio_id` (required): Portfolio to analyze
- `factor_model` (optional): Factor model ('fama_french', 'barra', 'custom')
- `time_range` (optional): Analysis period

### portfolio_attribution
Perform performance attribution.

**Parameters:**
- `portfolio_id` (required): Portfolio to attribute
- `benchmark_id` (optional): Benchmark for attribution
- `attribution_type` (optional): 'brinson', 'factor', 'holdings'
- `time_range` (optional): Attribution period

### portfolio_backtest
Backtest portfolio strategy.

**Parameters:**
- `strategy` (required): Strategy configuration
- `time_range` (required): Backtest period
- `initial_capital` (optional): Starting capital
- `transaction_costs` (optional): Cost model
- `slippage_model` (optional): Slippage model

### portfolio_get_data
Get market data.

**Parameters:**
- `symbols` (required): Asset symbols
- `data_type` (optional): 'price', 'volume', 'fundamentals', 'all'
- `time_range` (optional): Data period
- `frequency` (optional): Data frequency

### portfolio_forecast_returns
Forecast asset returns.

**Parameters:**
- `symbols` (required): Assets to forecast
- `model` (optional): Forecasting model
- `horizon` (optional): Forecast horizon
- `include_intervals` (optional): Include confidence intervals

### portfolio_correlation
Analyze asset correlations.

**Parameters:**
- `assets` (required): Assets to analyze
- `time_range` (optional): Analysis period
- `method` (optional): 'pearson', 'spearman', 'kendall'
- `rolling_window` (optional): Rolling correlation window

### portfolio_efficient_frontier
Compute efficient frontier.

**Parameters:**
- `assets` (required): Assets in universe
- `points` (optional): Number of frontier points
- `constraints` (optional): Portfolio constraints

### portfolio_report
Generate portfolio report.

**Parameters:**
- `portfolio_id` (required): Portfolio to report
- `report_type` (optional): 'summary', 'risk', 'performance', 'full'
- `format` (optional): 'pdf', 'html', 'json'

## Optimization Strategies

### Mean-Variance Optimization
```python
portfolio_optimize(
    portfolio_id="my_portfolio",
    objective="max_sharpe",
    constraints={"max_weight": 0.1, "long_only": True}
)
```

### Risk Parity
```python
portfolio_optimize(
    portfolio_id="risk_parity",
    objective="risk_parity",
    constraints={"asset_classes": {"equity": [0.4, 0.6], "bonds": [0.3, 0.5]}}
)
```

### Minimum Variance
```python
portfolio_optimize(
    portfolio_id="defensive",
    objective="min_variance",
    constraints={"min_return": 0.05}
)
```

## Risk Metrics

### Value at Risk (VaR)
```
portfolio_var(
    portfolio_id="growth_portfolio",
    method="monte_carlo",
    confidence_level=0.95,
    time_horizon=10
)
# Returns: {"var": -0.05, "expected_shortfall": -0.07}
```

### Stress Testing
```python
portfolio_stress_test(
    portfolio_id="my_portfolio",
    scenarios=[
        {"name": "market_crash", "equity_shock": -0.30, "bond_shock": -0.05},
        {"name": "rate_hike", "rate_change": 0.02}
    ],
    historical_events=["2008_crisis", "covid_2020"]
)
```

## Factor Models

### Fama-French Factors
- Market (MKT)
- Size (SMB)
- Value (HML)
- Profitability (RMW)
- Investment (CMA)
- Momentum (MOM)

### Factor Exposure Analysis
```python
portfolio_factor_analysis(
    portfolio_id="tech_portfolio",
    factor_model="fama_french",
    time_range="3Y"
)
# Returns factor loadings and R-squared
```

## Backtesting

### Strategy Backtest
```python
portfolio_backtest(
    strategy={
        "type": "momentum",
        "lookback": 252,
        "rebalance_freq": "monthly",
        "universe": ["SPY", "QQQ", "IWM", "TLT"]
    },
    time_range=("2020-01-01", "2024-01-01"),
    initial_capital=100000,
    transaction_costs={"commission": 0.001, "spread": 0.0005}
)
```

### Performance Metrics
- Total Return
- Annualized Return
- Sharpe Ratio
- Sortino Ratio
- Maximum Drawdown
- Calmar Ratio
- Alpha/Beta

## Integration with NVIDIA

- **NVIDIA cuDF**: GPU-accelerated data processing
- **NVIDIA cuML**: GPU-accelerated ML for forecasting
- **NVIDIA RAPIDS**: End-to-end data science pipeline
- **NVIDIA NIM**: Model serving for ML models

## References

- [Portfolio Optimization Blueprint](https://github.com/NVIDIA-AI-Blueprints/quantitative-portfolio-optimization)
- [Risk Models](./references/risk_models.md)
- [Backtesting Guide](./references/backtesting.md)
