# Trading UX Best Practices Guide

## Core Principles

### 1. Speed Over Everything
In trading, milliseconds matter. Every interaction should feel instant.

**Key Guidelines:**
- Price updates must be perceived as real-time (<50ms)
- Order placement should require minimum clicks (ideally 2-3)
- Keyboard shortcuts for all critical actions
- Optimistic UI updates with rollback on failure
- Pre-fetch likely next actions

### 2. Clarity in Chaos
Markets are chaotic. The interface should bring order.

**Key Guidelines:**
- Clear visual hierarchy (price > change > volume > others)
- Consistent color coding across all components
- Sufficient whitespace to prevent information overload
- Group related information logically
- Progressive disclosure for advanced features

### 3. Safety by Design
Prevent costly mistakes through thoughtful UX.

**Key Guidelines:**
- Confirmation for irreversible actions
- Clear differentiation between buy/sell
- Prominent display of leverage and risk
- Warnings for unusual values
- Undo capability where possible

## Component-Specific Guidelines

### Price Display
```
┌─────────────────────────┐
│ BTC/USD                 │
│ $67,453.21  ▲           │ <- Large, bold, monospace
│ +2,341.50 (+3.47%)      │ <- Clear profit indicator
│ 24h Vol: $28.5B         │ <- Secondary information
└─────────────────────────┘
```

**Best Practices:**
- Largest element on screen
- Monospace font for alignment
- Color indicates direction (not just +/-)
- Animation for changes (subtle pulse)
- Decimal precision based on asset

### Order Forms

#### Simple Mode (Default)
```
┌─────────────────────────┐
│    [BUY]    SELL        │ <- Toggle, not radio
├─────────────────────────┤
│ Amount                  │
│ [___________] USD       │
│                         │
│ ≈ 0.0015 BTC           │ <- Real-time conversion
├─────────────────────────┤
│ [  Place Market Order  ]│ <- Primary action
└─────────────────────────┘
```

#### Advanced Mode (Progressive Disclosure)
```
┌─────────────────────────┐
│    [BUY]    SELL        │
├─────────────────────────┤
│ Order Type: [Limit   ▼] │
│                         │
│ Amount: [_______] USD   │
│ Price:  [_______] USD   │
│                         │
│ [Stop Loss] [Take Profit]│ <- Optional but visible
├─────────────────────────┤
│ Total: $1,000.00        │
│ Fees:  $2.50            │
├─────────────────────────┤
│ [ Review Order → ]      │
└─────────────────────────┘
```

### Position Cards
```
┌─────────────────────────────┐
│ ETH/USD     LONG    2.5x    │
├─────────────────────────────┤
│ Entry:  $3,200              │
│ Current: $3,450  ▲          │
│ P&L: +$625.00 (+7.81%)      │
├─────────────────────────────┤
│ [Partial Close] [Close All] │
└─────────────────────────────┘
```

## Color System

### Semantic Colors
```scss
// Profit/Loss (Western Markets)
$color-profit: #10B981;     // Green
$color-loss: #EF4444;       // Red

// Profit/Loss (Asian Markets)
$color-profit-alt: #3B82F6; // Blue
$color-loss-alt: #F59E0B;   // Orange

// Actions
$color-buy: #10B981;        // Green
$color-sell: #EF4444;       // Red
$color-neutral: #6B7280;    // Gray

// Risk Levels
$risk-safe: #10B981;        // Green
$risk-caution: #F59E0B;     // Amber
$risk-danger: #EF4444;      // Red
$risk-critical: #991B1B;    // Dark Red

// Status
$status-online: #10B981;    // Green
$status-offline: #6B7280;   // Gray
$status-pending: #F59E0B;   // Amber
$status-error: #EF4444;     // Red
```

### Usage Guidelines
- Never rely solely on color (use icons/text too)
- Maintain WCAG AA contrast ratios (4.5:1)
- Provide color blind friendly alternatives
- Test with color blindness simulators

## Typography

### Font Hierarchy
```scss
// Headings
h1 { font-size: 2rem; font-weight: 700; }    // Page titles
h2 { font-size: 1.5rem; font-weight: 600; }  // Section headers
h3 { font-size: 1.25rem; font-weight: 600; } // Card titles

// Prices (Always Monospace)
.price-large { 
  font-family: 'JetBrains Mono', monospace;
  font-size: 2rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.price-medium {
  font-family: 'JetBrains Mono', monospace;
  font-size: 1.25rem;
  font-weight: 600;
}

// Body Text
.body { font-size: 1rem; line-height: 1.5; }
.small { font-size: 0.875rem; }
.tiny { font-size: 0.75rem; }
```

## Interaction Patterns

### Click/Tap Targets
- Minimum 44x44px on mobile
- 32x32px on desktop
- Adequate spacing between targets
- Visual feedback on interaction

### Keyboard Shortcuts
```
Essential Shortcuts:
B - Buy order
S - Sell order
M - Market order
L - Limit order
Esc - Cancel/Close
Enter - Confirm
Space - Toggle selection
/ - Focus search
? - Show shortcuts
```

### Gesture Support
- Swipe left/right: Navigate tabs
- Swipe down: Refresh
- Pinch: Zoom charts
- Long press: Context menu
- Double tap: Quick action

## Loading & Feedback

### Loading States
```tsx
// Skeleton Loading
<div className="skeleton-price">
  <div className="skeleton-line h-8 w-32" />
  <div className="skeleton-line h-6 w-24" />
</div>

// Progressive Loading
1. Show skeleton
2. Load critical data (price)
3. Load secondary data (volume)
4. Load tertiary data (charts)
```

### User Feedback
```tsx
// Success
toast.success('Order placed successfully', {
  duration: 3000,
  position: 'top-center'
});

// Error
toast.error('Insufficient balance', {
  action: {
    label: 'Add Funds',
    onClick: () => navigate('/deposit')
  }
});

// Loading
const toastId = toast.loading('Placing order...');
// Later...
toast.success('Order filled!', { id: toastId });
```

## Mobile Considerations

### Layout Adaptations
```scss
// Desktop: Multi-column
.desktop-layout {
  display: grid;
  grid-template-columns: 300px 1fr 300px;
}

// Mobile: Stacked
@media (max-width: 768px) {
  .mobile-layout {
    display: flex;
    flex-direction: column;
  }
}
```

### Touch Optimizations
- Larger tap targets
- Swipe gestures
- Bottom sheet modals
- Thumb-zone navigation
- Haptic feedback

## Error Prevention

### Input Validation
```tsx
// Real-time validation
const validateAmount = (value) => {
  if (value > balance) {
    return 'Insufficient balance';
  }
  if (value < minOrder) {
    return `Minimum order: ${minOrder}`;
  }
  return null;
};
```

### Confirmation Dialogs
```tsx
// Smart confirmations (only for risky actions)
const needsConfirmation = (order) => {
  return (
    order.value > portfolio.value * 0.1 || // >10% of portfolio
    order.leverage > 10 ||                  // High leverage
    order.type === 'market'                 // Market orders
  );
};
```

## Accessibility

### ARIA Labels
```tsx
<button
  aria-label="Buy Bitcoin"
  aria-pressed={side === 'buy'}
  aria-describedby="buy-tooltip"
>
  BUY
</button>
```

### Focus Management
```tsx
// Trap focus in modals
const trapFocus = (element) => {
  const focusable = element.querySelectorAll(
    'button, input, select, textarea, a[href]'
  );
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  
  element.addEventListener('keydown', (e) => {
    if (e.key === 'Tab') {
      if (e.shiftKey && document.activeElement === first) {
        last.focus();
        e.preventDefault();
      } else if (!e.shiftKey && document.activeElement === last) {
        first.focus();
        e.preventDefault();
      }
    }
  });
};
```

## Dark Mode

### Implementation
```scss
// Use CSS variables for theming
:root {
  --bg-primary: #ffffff;
  --text-primary: #1a1a1a;
  --border: #e5e5e5;
}

[data-theme="dark"] {
  --bg-primary: #0a0a0a;
  --text-primary: #ffffff;
  --border: #262626;
}

// Apply variables
.card {
  background: var(--bg-primary);
  color: var(--text-primary);
  border: 1px solid var(--border);
}
```

## Testing Your UX

### Usability Testing Checklist
- [ ] Can place an order in <3 clicks?
- [ ] Are profits/losses immediately clear?
- [ ] Can navigate with keyboard only?
- [ ] Works on 320px wide screen?
- [ ] Readable at arm's length?
- [ ] Functions with JS disabled?
- [ ] Handles network interruption?
- [ ] Prevents accidental orders?
- [ ] Accessible with screen reader?
- [ ] Works with one hand on mobile?

### Performance Testing
- [ ] Time to first trade <5 seconds
- [ ] Price updates feel instant
- [ ] No jank during scrolling
- [ ] Charts pan smoothly
- [ ] Forms validate instantly

## Common UX Mistakes to Avoid

1. **Too Many Confirmations**: Balance safety with speed
2. **Hidden Critical Information**: Always show P&L, leverage
3. **Unclear Order Status**: Use clear states (pending, filled, failed)
4. **Poor Mobile Experience**: Test on actual devices
5. **Overwhelming New Users**: Progressive disclosure
6. **Ignoring Keyboard Users**: Full keyboard support
7. **Cryptic Error Messages**: Be specific and helpful
8. **No Visual Feedback**: Every action needs response
9. **Inconsistent Patterns**: Maintain consistency
10. **Forgetting Edge Cases**: Handle all scenarios