# Trading UI Review Workflow

An automated design review system specifically tailored for trading platform interfaces, inspired by the design-review patterns from [claude-code-workflows](https://github.com/ibz22/claude-code-workflows). This workflow ensures that trading UI components meet high standards for data visualization, real-time updates, risk communication, and financial UX best practices.

## Overview

This workflow provides comprehensive automated reviews for trading platform UI changes, focusing on:
- **Real-time data visualization** quality and performance
- **Risk indicators** clarity and prominence
- **Trading controls** accessibility and error prevention
- **Financial data** accuracy and formatting
- **Mobile responsiveness** for on-the-go trading
- **Regulatory compliance** UI requirements

## Core Principles

### 1. Financial UX Excellence
- Clear profit/loss visualization with appropriate color coding
- Intuitive order placement with confirmation flows
- Risk warnings and position size calculators
- Market depth and order book clarity

### 2. Real-time Performance
- Smooth price ticker updates without flicker
- Efficient chart rendering for large datasets
- WebSocket connection status indicators
- Graceful handling of connection loss

### 3. Risk Communication
- Prominent display of leverage and margin requirements
- Clear stop-loss and take-profit indicators
- Portfolio exposure visualization
- Alert systems for significant market moves

### 4. Accessibility & Compliance
- WCAG AA+ compliance for financial applications
- Keyboard navigation for rapid trading
- Screen reader support for price updates
- Regulatory disclaimers and risk warnings

## Workflow Components

### Templates & Configurations
- [`trading-design-principles.md`](./trading-design-principles.md) - Comprehensive design principles for trading interfaces
- [`trading-review-agent.yaml`](./trading-review-agent.yaml) - Claude Code agent configuration for automated reviews
- [`trading-review-command.yaml`](./trading-review-command.yaml) - Slash command setup for on-demand reviews
- [`claude-md-snippet.md`](./claude-md-snippet.md) - CLAUDE.md configuration for project integration

### Review Checklists
- [`chart-review-checklist.md`](./chart-review-checklist.md) - Technical chart and indicator review
- [`order-flow-checklist.md`](./order-flow-checklist.md) - Order placement and execution flow review
- [`portfolio-view-checklist.md`](./portfolio-view-checklist.md) - Portfolio and position management review
- [`risk-dashboard-checklist.md`](./risk-dashboard-checklist.md) - Risk metrics and alerts review

## Usage

### 1. Quick Start

Add the trading review configuration to your project's `CLAUDE.md`:

```markdown
# Trading UI Review Configuration
Use the trading-ui-review workflow for all frontend changes affecting:
- Trading interfaces and order forms
- Chart components and technical indicators
- Portfolio views and position tables
- Risk dashboards and alert systems
```

### 2. Automated Review with Agent

Tag the specialized agent in your PR or code review:

```
@agent-trading-ui-review Please review the new order placement component
```

### 3. On-Demand Review

Use the slash command for immediate feedback:

```
/trading-ui-review
```

### 4. CI/CD Integration

Add to your GitHub Actions workflow:

```yaml
- name: Trading UI Design Review
  uses: ./.github/actions/trading-ui-review
  with:
    components: 'charts,orders,portfolio'
    compliance: 'sec,mifid2'
```

## Review Process

### Phase 1: Static Analysis
- Component structure and prop validation
- Design token usage and consistency
- Accessibility attributes and ARIA labels
- Performance optimization checks

### Phase 2: Interactive Testing
- Live preview with Playwright automation
- Order flow simulation
- Real-time data update testing
- Responsive behavior verification

### Phase 3: Compliance Check
- Regulatory UI requirements
- Risk disclosure verification
- Data accuracy validation
- Audit trail completeness

### Phase 4: Performance Profiling
- Chart rendering performance
- WebSocket message handling
- Memory leak detection
- Bundle size analysis

## Trading-Specific Review Areas

### 1. Market Data Display
- Price precision and formatting
- Bid/ask spread visualization
- Volume and liquidity indicators
- Market status badges

### 2. Order Management
- Order type selection clarity
- Validation and error messages
- Confirmation dialogs
- Order history and status

### 3. Risk Metrics
- P&L calculations and display
- Margin and leverage indicators
- Exposure breakdown
- Alert thresholds

### 4. Chart Components
- Candlestick rendering quality
- Indicator overlay management
- Zoom and pan interactions
- Drawing tools usability

## Best Practices

1. **Always test with live market data** to ensure real-world performance
2. **Simulate various market conditions** including high volatility
3. **Verify mobile experience** for critical trading functions
4. **Test failover scenarios** for connection issues
5. **Validate calculations** against known test cases

## Resources

- [Original Design Review Workflow](https://github.com/ibz22/claude-code-workflows/tree/main/design-review)
- [Trading UX Best Practices](./docs/trading-ux-guide.md)
- [Regulatory UI Requirements](./docs/regulatory-requirements.md)
- [Performance Optimization Guide](./docs/performance-guide.md)

## Contributing

To improve this workflow:
1. Add new checklist items based on trading platform requirements
2. Update agent prompts for emerging patterns
3. Share successful review outcomes
4. Report false positives or missed issues

## License

MIT - Adapted from [claude-code-workflows](https://github.com/ibz22/claude-code-workflows)