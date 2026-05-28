# Quantitative Portfolio Optimization Blueprint Skill

GPU-accelerated portfolio optimization using NVIDIA cuOpt and RAPIDS for Mean-CVaR optimization.

## Description

This skill provides tools for portfolio optimization addressing the trade-off between computational speed and model complexity. Leverages NVIDIA accelerated computing to transform robust analysis from slow batch processing into fast, iterative workflows for dynamic decision-making.

## When to Use

- Portfolio optimization and rebalancing
- Risk modeling (CVaR, VaR)
- Efficient frontier analysis
- Scenario generation and stress testing
- Trading strategy backtesting
- Investment research

## Blueprint Source

Based on: [NVIDIA quantitative-portfolio-optimization](https://github.com/NVIDIA-AI-Blueprints/quantitative-portfolio-optimization)

## Tools

### Scenario Generation Tools

| Tool | Description |
|------|-------------|
| `generate_scenarios` | Generate return distribution scenarios |
| `fit_return_distribution` | Fit statistical distributions to returns |
| `sample_scenarios` | Sample scenarios from distributions |
| `apply_constraints` | Apply portfolio constraints |

### Optimization Tools

| Tool | Description |
|------|-------------|
| `optimize_mean_cvar` | Mean-CVaR portfolio optimization |
| `optimize_mean_variance` | Mean-Variance (Markowitz) optimization |
| `compute_efficient_frontier` | Generate efficient frontier |
| `get_optimal_weights` | Get optimal portfolio weights |

### Risk Analysis Tools

| Tool | Description |
|------|-------------|
| `calculate_cvar` | Calculate Conditional Value-at-Risk |
| `calculate_var` | Calculate Value-at-Risk |
| `calculate_sharpe_ratio` | Calculate Sharpe ratio |
| `stress_test_portfolio` | Run portfolio stress tests |

### Backtesting Tools

| Tool | Description |
|------|-------------|
| `backtest_strategy` | Backtest trading strategy |
| `rebalance_portfolio` | Dynamic portfolio rebalancing |
| `evaluate_performance` | Evaluate strategy performance |
| `plot_results` | Visualize backtest results |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Jupyter Notebook Interface                    │
│  ┌─────────────────┐ ┌─────────────────┐ ┌───────────────────┐  │
│  │ cvar_basic      │ │ efficient_      │ │ rebalancing_      │  │
│  │ .ipynb          │ │ frontier.ipynb  │ │ strategies.ipynb  │  │
│  └─────────────────┘ └─────────────────┘ └───────────────────┘  │
└───────────────────────────────────────────────────────────────────┘
        │
        ↓
┌───────────────────────────────────────────────────────────────────┐
│                    CUDA-X Data Science                            │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │ RAPIDS cuDF + cuML                                         │   │
│  │ - GPU-accelerated data preprocessing                      │   │
│  │ - Learning/sampling return distributions                  │   │
│  │ - Up to 100x faster scenario generation                   │   │
│  └───────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────┘
        │
        ↓
┌───────────────────────────────────────────────────────────────────┐
│                    NVIDIA cuOpt                                   │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │ Mean-CVaR Optimization                                     │   │
│  │ - Scenario-based optimization                             │   │
│  │ - Up to 160x faster than CPU solvers                      │   │
│  │ - Large-scale problem support                             │   │
│  └───────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────┘
        │
        ↓
┌───────────────────────────────────────────────────────────────────┐
│                    Backtesting Engine                             │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │ CUDA-X + HPC SDK                                          │   │
│  │ - Strategy testing and refinement                         │   │
│  │ - Performance metrics calculation                         │   │
│  └───────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────┘
```

## Configuration

### Environment Variables

```bash
# CUDA Configuration
CUDA_VISIBLE_DEVICES=0,1,2,3

# Optimization Parameters
NUM_SCENARIOS=10000
CONFIDENCE_LEVEL=0.95
MAX_ITERATIONS=1000
```

### Integration with DeerFlow

```python
from deerflow.blueprints import PortfolioOptimizationBlueprint

optimizer = PortfolioOptimizationBlueprint(
    num_scenarios=10000,
    confidence_level=0.95
)

# Generate scenarios
scenarios = await optimizer.generate_scenarios(
    returns_data=historical_returns,
    distribution="student_t"
)

# Optimize portfolio
result = await optimizer.optimize_mean_cvar(
    expected_returns=mu,
    scenarios=scenarios,
    constraints={"min_weight": 0.0, "max_weight": 0.2}
)

print(f"Optimal weights: {result.weights}")
print(f"Expected return: {result.expected_return}")
print(f"CVaR: {result.cvar}")
```

## GPU Requirements

| Component | Minimum GPU | Recommended |
|-----------|-------------|-------------|
| cuDF/cuML | 1x H100 SXM | 4x H100 SXM |
| cuOpt | 1x A100 | 1x H100 |
| CUDA Version | 12.0 | 13.0 |

**Recommended System:**
- 32+ CPU cores
- 64+ GB RAM
- 100+ GB NVMe SSD

## Performance Benchmarks

| Task | CPU Time | GPU Time | Speedup |
|------|----------|----------|---------|
| Scenario Generation (10K) | 100s | 1s | 100x |
| Mean-CVaR Optimization | 160s | 1s | 160x |
| Efficient Frontier (100 points) | 16,000s | 100s | 160x |

## Example Usage

```python
from deerflow.tools.portfolio import (
    ScenarioGenerator,
    MeanCVaROptimizer,
    EfficientFrontier,
    Backtester
)

# Generate scenarios
generator = ScenarioGenerator()
scenarios = await generator.fit_and_sample(
    returns=historical_returns,
    n_scenarios=10000
)

# Optimize portfolio
optimizer = MeanCVaROptimizer(alpha=0.95)
result = await optimizer.optimize(
    scenarios=scenarios,
    expected_returns=mu,
    constraints={"long_only": True, "max_weight": 0.15}
)

# Compute efficient frontier
frontier = EfficientFrontier()
points = await frontier.compute(
    scenarios=scenarios,
    expected_returns=mu,
    n_points=100
)

# Backtest strategy
backtester = Backtester()
performance = await backtester.run(
    strategy="mean_cvar_rebalance",
    data=price_history,
    rebalance_freq="monthly"
)
```

## Mathematical Models

### Mean-CVaR Optimization
```
minimize    CVaR_α(portfolio_returns)
subject to  E[portfolio_returns] >= target_return
            sum(weights) = 1
            weights >= 0
```

### Supported Distributions
- Normal (Gaussian)
- Student's t
- Historical
- Custom mixture models

## References

- [NVIDIA cuOpt Documentation](https://docs.nvidia.com/cuopt/)
- [RAPIDS cuML](https://docs.rapids.ai/api/cuml/stable/)
- [Markowitz, H. (1952). "Portfolio Selection"](https://www.jstor.org/stable/2975974)
- [Rockafellar & Uryasev (2000). "Optimization of CVaR"](https://www.risk.net/journal-risk/2199279/optimization-conditional-value-risk)
