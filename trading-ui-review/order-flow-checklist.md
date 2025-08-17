# Order Flow Review Checklist

## Order Entry Interface
- [ ] **Order Type Selection**
  - [ ] Clear distinction between Market/Limit/Stop
  - [ ] Advanced types available (Stop-Limit, OCO, Iceberg)
  - [ ] Tooltips explain each order type
  - [ ] Visual indicators for selected type
  - [ ] Keyboard shortcuts functional

- [ ] **Buy/Sell Toggle**
  - [ ] Prominent color differentiation (Green/Red)
  - [ ] Clear active state indication
  - [ ] Prevents accidental side selection
  - [ ] Keyboard shortcut (B/S keys)
  - [ ] Animation on state change

- [ ] **Quantity Input**
  - [ ] Supports decimal places for crypto
  - [ ] Min/max validation
  - [ ] Quick percentage buttons (25%, 50%, 75%, 100%)
  - [ ] USD value calculation shown
  - [ ] Lot size compliance for traditional markets

## Price Management
- [ ] **Limit Price Entry**
  - [ ] Pre-fills with current market price
  - [ ] +/- buttons for quick adjustment
  - [ ] Percentage from market price shown
  - [ ] Validation against market price
  - [ ] Historical price chart reference

- [ ] **Stop Price Configuration**
  - [ ] Clear when stop is triggered
  - [ ] Distance from current price shown
  - [ ] Trailing stop option available
  - [ ] Stop-limit spread configuration
  - [ ] Visual indicator on chart

## Risk Controls
- [ ] **Position Sizing**
  - [ ] Shows position value in base currency
  - [ ] Displays percentage of portfolio
  - [ ] Leverage indicator if applicable
  - [ ] Margin requirement calculation
  - [ ] Warning for large positions (>10% portfolio)

- [ ] **Stop-Loss Integration**
  - [ ] Optional but encouraged
  - [ ] Shows potential loss amount
  - [ ] Percentage loss calculation
  - [ ] Risk/reward ratio display
  - [ ] One-click stop-loss templates

- [ ] **Take-Profit Levels**
  - [ ] Multiple TP levels supported
  - [ ] Shows potential profit
  - [ ] Percentage gain calculation
  - [ ] Partial close options
  - [ ] Visual on chart

## Order Confirmation
- [ ] **Pre-Submit Review**
  - [ ] Complete order summary
  - [ ] Total cost including fees
  - [ ] Estimated slippage warning
  - [ ] Balance check passed
  - [ ] Margin impact shown

- [ ] **Confirmation Dialog**
  - [ ] Cannot be dismissed accidentally
  - [ ] Shows all order parameters
  - [ ] Highlights unusual values
  - [ ] Time to review (no instant confirm)
  - [ ] Cancel clearly available

- [ ] **Warning Messages**
  - [ ] High leverage warning (>10x)
  - [ ] Large order warning (high slippage)
  - [ ] Outside market hours notice
  - [ ] Insufficient balance clear
  - [ ] Pattern day trader warning

## Order Submission
- [ ] **Submit Button**
  - [ ] Disabled until valid
  - [ ] Loading state during submission
  - [ ] Clear success feedback
  - [ ] Error messages actionable
  - [ ] Retry mechanism available

- [ ] **Keyboard Shortcuts**
  - [ ] Enter to submit (with safety)
  - [ ] Escape to cancel
  - [ ] Tab navigation works
  - [ ] Shortcuts documented
  - [ ] Can be customized

## Post-Order Experience
- [ ] **Order Confirmation**
  - [ ] Order ID displayed
  - [ ] Timestamp recorded
  - [ ] Link to order details
  - [ ] Add to watchlist option
  - [ ] Share capability

- [ ] **Order Tracking**
  - [ ] Real-time status updates
  - [ ] Partial fill indicators
  - [ ] Cancel button accessible
  - [ ] Modify order available
  - [ ] Time in force shown

- [ ] **Notifications**
  - [ ] Order filled notification
  - [ ] Partial fill alerts
  - [ ] Order rejected reason
  - [ ] Stop triggered alert
  - [ ] Connection lost warning

## Advanced Features
- [ ] **Order Templates**
  - [ ] Save frequently used orders
  - [ ] Quick order from templates
  - [ ] Template management interface
  - [ ] Import/export capability
  - [ ] Sharing between accounts

- [ ] **Algorithmic Orders**
  - [ ] TWAP/VWAP options
  - [ ] Iceberg order configuration
  - [ ] Conditional order builder
  - [ ] Schedule order execution
  - [ ] Smart order routing

- [ ] **One-Click Trading**
  - [ ] Optional activation
  - [ ] Clear enabled indicator
  - [ ] Safeguards in place
  - [ ] Quick disable option
  - [ ] Audit trail maintained

## Mobile Considerations
- [ ] **Touch Optimization**
  - [ ] Large tap targets (min 44px)
  - [ ] Swipe to cancel order
  - [ ] Bottom sheet for order form
  - [ ] Haptic feedback on submit
  - [ ] Prevents accidental orders

- [ ] **Simplified Flow**
  - [ ] Essential fields only
  - [ ] Progressive disclosure
  - [ ] Market orders prominent
  - [ ] Quick buy/sell buttons
  - [ ] Voice input support

## Error Handling
- [ ] **Validation Errors**
  - [ ] Inline error messages
  - [ ] Field highlighting
  - [ ] Clear correction guidance
  - [ ] Prevents submission
  - [ ] Accessible error announcements

- [ ] **Submission Failures**
  - [ ] Clear failure reason
  - [ ] Retry button available
  - [ ] Order saved as draft
  - [ ] Support contact option
  - [ ] Detailed error logs

## Performance Requirements
- [ ] Order form loads <100ms
- [ ] Validation feedback <50ms
- [ ] Order submission <200ms
- [ ] Real-time price updates
- [ ] No UI blocking during submission

## Compliance & Audit
- [ ] **Regulatory Requirements**
  - [ ] Best execution disclosure
  - [ ] Order type restrictions
  - [ ] Trading hours enforcement
  - [ ] Position limits checked
  - [ ] Suitability warnings

- [ ] **Audit Trail**
  - [ ] All orders logged
  - [ ] Modifications tracked
  - [ ] Cancellations recorded
  - [ ] IP address captured
  - [ ] Device fingerprinting

## Testing Checklist
- [ ] Test all order types
- [ ] Verify calculations accuracy
- [ ] Test with insufficient balance
- [ ] Check connection loss handling
- [ ] Validate on multiple devices
- [ ] Test rapid order entry
- [ ] Verify order modification flow
- [ ] Test order cancellation
- [ ] Check partial fill handling
- [ ] Test with various account types