# CLAUDE.md Trading UI Review Configuration

Add this section to your project's CLAUDE.md file to enable automated trading UI reviews:

```markdown
## Trading UI Design Review

This project uses automated design review workflows for all trading interface changes.
The review system ensures high standards for financial UX, real-time performance, and regulatory compliance.

### Automated Review Triggers

Automatically review changes to these components:
- `/frontend/app/markets/*` - Market data displays and tickers
- `/frontend/app/strategies/*` - Strategy configuration interfaces  
- `/frontend/app/bots/*` - Bot management and monitoring
- `/frontend/app/analytics/*` - Charts and technical analysis
- `/frontend/app/risk-management/*` - Risk dashboards and alerts
- `/frontend/components/BotCreator/*` - Order placement forms
- `/frontend/components/Dashboard/*` - Portfolio views

### Design Standards

Follow these core principles:

1. **Financial Data Display**
   - Use monospace fonts for numbers: `font-family: 'JetBrains Mono'`
   - Right-align numeric columns in tables
   - Format prices with appropriate decimal places
   - Color code P&L: Green (#22C55E) for profit, Red (#EF4444) for loss

2. **Real-time Updates**
   - Price updates must render within 50ms
   - Use WebSocket for live data, never polling
   - Show connection status indicator at all times
   - Implement graceful reconnection with exponential backoff

3. **Risk Communication**
   - Display leverage and margin prominently
   - Show liquidation price when applicable
   - Require confirmation for orders >10% of portfolio
   - Use progressive color coding for risk levels

4. **Order Placement**
   - Two-step confirmation for market orders
   - Show estimated cost and fees upfront
   - Validate against available balance
   - Display slippage warnings for large orders

5. **Mobile Experience**
   - Minimum 44px touch targets
   - Bottom sheet pattern for order forms
   - Swipe gestures for chart navigation
   - Landscape mode for detailed charts

### Review Commands

Use these commands for different review types:

```bash
# Full trading UI review
/trading-ui-review

# Chart-specific review
/trading-ui-review --focus charts

# Order flow review
/trading-ui-review --focus orders

# Mobile experience review
/trading-ui-review --mobile

# Performance profiling
/trading-ui-review --performance
```

### Performance Targets

All trading interfaces must meet these benchmarks:
- Price update latency: <50ms
- Chart render time: <100ms
- Order placement: <200ms
- Memory usage: <500MB
- CPU usage: <30%

### Compliance Requirements

Ensure all trading UIs include:
- Risk warnings on leveraged products
- Data source attribution
- Timestamp precision to milliseconds
- Audit trail for all user actions
- Terms of service acceptance tracking

### Testing Checklist

Before merging any trading UI changes:
- [ ] Test with live WebSocket data
- [ ] Verify calculations with known test cases
- [ ] Check mobile experience on actual devices
- [ ] Test error states and edge cases
- [ ] Profile performance under load
- [ ] Validate accessibility compliance
- [ ] Review with simulated slow network

### Component Library

Use these pre-reviewed components when possible:
- `<PriceTicker />` - Real-time price display
- `<OrderForm />` - Standard order placement
- `<PositionCard />` - Position summary
- `<RiskMeter />` - Visual risk indicator
- `<Chart />` - TradingView-based charts

### Resources

- [Trading Design Principles](./trading-ui-review/trading-design-principles.md)
- [Chart Review Checklist](./trading-ui-review/chart-review-checklist.md)
- [Order Flow Checklist](./trading-ui-review/order-flow-checklist.md)
- [Performance Guide](./trading-ui-review/docs/performance-guide.md)
```

## Integration Instructions

1. Copy the above content into your project's CLAUDE.md file
2. Customize the file paths to match your project structure
3. Adjust color codes and fonts to match your design system
4. Update performance targets based on your requirements
5. Add project-specific compliance requirements

## Usage with Claude Code

Once integrated, Claude Code will:
- Automatically reference these guidelines during code reviews
- Apply the review checklist to relevant file changes
- Suggest improvements based on the design principles
- Flag violations of performance targets
- Ensure compliance requirements are met

## Customization

Modify the configuration to match your needs:
- Add custom review focus areas
- Define project-specific metrics
- Include additional compliance requirements
- Specify technology-specific guidelines
- Add team conventions and preferences