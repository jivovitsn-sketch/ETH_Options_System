# Complete Trading Guide

## 🎯 Strategy Selection

### Market Conditions
| Condition | IV Level | Recommended Strategy | Win Rate | Use Case |
|-----------|----------|---------------------|----------|----------|
| High Volatility | >80% | Long Straddle | 72.7% | Big moves expected |
| Normal Market | 40-80% | Bull/Bear Spreads | 45.5% | Directional bias |
| Low Volatility | <40% | Iron Condor | 27.3% | Range-bound |

### Entry Signals
- **Bull Call Spread**: Price breaks above resistance + bullish momentum
- **Bear Put Spread**: Price breaks below support + bearish momentum  
- **Long Straddle**: High IV + expecting earnings/events
- **Iron Condor**: Low IV + sideways market

## 💰 Position Sizing

### Capital Allocation
```
Total Capital: $50,000
Max per trade: $1,500 (3%)
Max open positions: 3
Reserve cash: $5,000 (10%)
```

### Risk Calculations
```python
# Long Straddle Example
position_size = min(capital * 0.03, 1500)
max_loss = premium_paid
profit_target = premium_paid * 2

# Spread Example  
position_size = min(capital * 0.05, 2500)
max_loss = net_debit
profit_target = net_debit * 0.5
```

## 📊 Trade Management

### Entry Checklist
- [ ] Strategy matches market condition
- [ ] Position size within limits
- [ ] Clear profit/loss targets set
- [ ] Adequate time to expiration (21+ days)

### Exit Rules
1. **Profit Targets**
   - Long Straddle: 100-200% of premium
   - Spreads: 25-50% of max profit
   - Iron Condor: 25% of credit received

2. **Stop Losses**
   - 50% of premium for bought strategies
   - 200% of credit for sold strategies

3. **Time Decay**
   - Close all positions 21 days before expiration
   - Roll if still bullish/bearish

### Rolling Strategies
```bash
# Close current position
python3 trade_commands.py close CURRENT_TRADE_ID exit_price "roll_forward"

# Open new position with later expiration
python3 trade_commands.py open "Bull Call Spread" "BTC" current_price "rolled_position"
```

## 📈 Performance Tracking

### Key Metrics
- **Win Rate**: Target >50% for spreads, >30% for straddles
- **Average P&L**: Track per strategy
- **Maximum Drawdown**: Keep under 20%
- **Sharpe Ratio**: Risk-adjusted returns

### Monthly Review
```bash
# Generate performance report
python3 -c "
import pandas as pd
df = pd.read_csv('data/paper_trades.csv')
closed = df[df['status'] == 'CLOSED']
monthly_stats = closed.groupby(pd.to_datetime(closed['timestamp']).dt.to_period('M')).agg({
    'pnl': ['sum', 'count', 'mean'],
    'pnl_percent': 'mean'
})
print(monthly_stats)
"
```

## ⚠️ Risk Management

### Portfolio Rules
1. **Diversification**: Max 2 positions in same asset
2. **Correlation**: Avoid similar strategies simultaneously  
3. **Volatility**: Reduce size during high volatility
4. **Drawdown**: Stop trading after 15% portfolio loss

### Warning Signs
- Win rate drops below 30%
- Average loss exceeds average win
- Emotional decision making
- Ignoring stop losses

## 🎓 Common Mistakes

### Beginner Errors
- Oversizing positions
- Holding losing trades too long
- Not having exit plan
- Trading against trend

### Advanced Pitfalls
- Over-optimizing based on backtest
- Ignoring implied volatility changes
- Not adjusting for market regime changes
- Revenge trading after losses
