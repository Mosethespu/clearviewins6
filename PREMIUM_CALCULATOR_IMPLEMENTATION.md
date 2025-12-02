# Premium Calculator Implementation Summary

## Overview
Successfully implemented a comprehensive premium calculator system with insurance company-specific rates, quote generation, and policy pre-fill capabilities.

## Features Implemented

### 1. Database Models

#### PremiumRate Model
- Company-specific rate configurations for all cover types
- Fields:
  - `insurance_company_id` - Links to specific insurance company
  - `cover_type` - Comprehensive, Third-Party Only, Third-Party Fire & Theft, PSV
  - Comprehensive rates: `min_rate`, `max_rate`, `default_rate` (percentages 4-7%)
  - TPO rates: `tpo_flat_rate` (flat KES amount ~8,000)
  - TPFT rates: `tpft_base_rate` + `tpft_percentage` (base + % of value)
  - PSV rates: `psv_taxi_rate`, `psv_matatu_14_rate`, `psv_matatu_25_rate`, `psv_bus_rate`
  - `is_active` - Enable/disable rates
  - Timestamps for tracking

#### Quote Model
- Complete quote management system
- Fields:
  - `quote_number` - Auto-generated format: QT-XXXXXX
  - Company and creator links
  - Customer information (email, name, phone)
  - Vehicle details (value, registration, make/model, year)
  - Coverage details (cover_type, use_category)
  - Premium breakdown (base_premium, rate_applied, final_premium)
  - Add-ons (political_violence, windscreen_cover, passenger_liability, road_rescue)
  - Status tracking (Sent, Accepted, Converted, Expired)
  - Validity period (30 days from creation)

### 2. Forms

#### PremiumCalculatorForm
- Cover type selection (4 options)
- Vehicle value (required, minimum 0)
- Optional vehicle details (registration, make/model, year)
- Use category (dynamic based on cover type):
  - Regular covers: Private, Commercial
  - PSV: PSV-Taxi, PSV-Matatu (14-seater), PSV-Matatu (25-seater), PSV-Bus
- Add-ons with percentage indicators:
  - Political Violence & Terrorism (~5%)
  - Windscreen Cover (~3%)
  - Passenger Liability (~8%)
  - Road Rescue Services (~2%)
- Optional customer information (email, name, phone)

### 3. Routes & Logic

#### `/insurer/premium-calculator` (GET/POST)
- Fetches company-specific rates from PremiumRate table
- Calculates premiums by formula:
  - **Comprehensive**: `vehicle_value * (rate% / 100)`
  - **Third-Party Only**: Flat rate from database
  - **Third-Party Fire & Theft**: `base_rate + (vehicle_value * percentage / 100)`
  - **PSV**: Flat rate based on vehicle category
- Adds optional add-ons (5%, 3%, 8%, 2%)
- Stores calculation result in session
- Displays form and results side-by-side

#### `/insurer/create-quote-from-calculator` (POST)
- Generates unique quote number (QT-XXXXXX format)
- Creates Quote record with all calculation details
- Sets validity period (30 days from creation)
- Clears session data
- Future: Send quote via email

#### `/insurer/create-policy-from-calculator` (POST)
- Stores calculation data in `session['prefill_policy']`
- Redirects to create_policy route
- Policy form auto-populated with calculator data

#### `/insurer/view-quote/<id>` (GET)
- Displays complete quote details
- Shows customer information
- Shows vehicle and coverage details
- Shows premium breakdown
- Shows add-ons selected
- Authorization: Company-specific access only
- Action: Convert to policy button

### 4. Templates

#### `premium_calculator.html`
- Two-column layout:
  - **Left**: Calculation form with all inputs
  - **Right**: Results panel with breakdown
- Dynamic form behavior:
  - Use category options change based on cover type
  - PSV shows vehicle categories (Taxi, Matatu, Bus)
  - Regular covers show Private/Commercial
- Results display:
  - Large final premium amount
  - Detailed breakdown table (cover type, vehicle value, base premium)
  - Add-ons table with individual costs
  - Vehicle details (if provided)
  - Customer details (if provided)
- Action buttons:
  - **Create Quote & Send** - Requires customer email
  - **Create Policy** - Pre-fills policy form
  - **New Calculation** - Clear and start over
  - **Back to Dashboard**

#### `view_quote.html`
- Professional quote display
- Organized sections:
  - Quote information (number, status, validity, company)
  - Customer information (email, name, phone)
  - Vehicle & coverage details
  - Add-ons list
  - Premium summary (sticky sidebar)
- Status badges (Sent, Accepted, Converted, Expired)
- Convert to policy button for Sent quotes

### 5. Integration Updates

#### Updated `create_policy` Route
- Checks for `session['prefill_policy']` on GET requests
- Pre-fills form fields:
  - Vehicle information (value, registration, make/model, year)
  - Cover type → Policy type mapping
  - Use category
  - Premium amount
  - Add-ons (all 4 boolean fields)
  - Customer information (email, name, phone)
- Shows info flash message when pre-filled
- Clears session after pre-filling

#### Updated Dashboard Navigation
- Added "Premium Calculator" link to sidebar
- Icon: calculator (bi-calculator)
- Active link to premium_calculator route

### 6. Database Seeding

#### `seed_premium_rates.py` Script
- Seeds default rates for all insurance companies
- Default configurations:
  - **Comprehensive**: 4-7% (default 5.5%)
  - **Third-Party Only**: KES 8,000 flat
  - **Third-Party Fire & Theft**: KES 8,000 base + 1.5% of value
  - **PSV**:
    - Taxi: KES 25,000
    - Matatu (14-seater): KES 70,000
    - Matatu (25-seater): KES 95,000
    - Bus: KES 135,000
- Checks for existing rates (no duplicates)
- Successfully seeded 136 rates for 34 insurance companies

## Premium Calculation Formulas

### Comprehensive Cover
```
base_premium = vehicle_value * (rate_percentage / 100)
final_premium = base_premium + (base_premium * add_ons_total_percentage / 100)
```

### Third-Party Only
```
base_premium = flat_rate (from database)
final_premium = base_premium + (base_premium * add_ons_total_percentage / 100)
```

### Third-Party Fire & Theft
```
base_premium = tpft_base_rate + (vehicle_value * tpft_percentage / 100)
final_premium = base_premium + (base_premium * add_ons_total_percentage / 100)
```

### PSV (Public Service Vehicle)
```
base_premium = psv_rate (based on vehicle category: Taxi, Matatu 14, Matatu 25, Bus)
final_premium = base_premium + (base_premium * add_ons_total_percentage / 100)
```

### Add-ons Percentages
- Political Violence & Terrorism: 5%
- Windscreen Cover: 3%
- Passenger Liability: 8%
- Road Rescue Services: 2%

## User Workflow

### Calculate Premium
1. Insurer selects cover type
2. Enters vehicle value
3. Selects use category (dynamic based on cover type)
4. Optionally enters vehicle details
5. Selects optional add-ons
6. Optionally enters customer information
7. Clicks "Calculate Premium"
8. Views detailed breakdown with final premium

### Create Quote
1. After calculation, clicks "Create Quote & Send to Customer"
2. System generates unique quote number (QT-XXXXXX)
3. Quote saved to database with 30-day validity
4. Redirects to view_quote page
5. Future: Automatically emails quote to customer

### Create Policy from Calculator
1. After calculation, clicks "Create Policy from This Calculation"
2. System stores data in session
3. Redirects to create_policy form
4. Form automatically pre-filled with:
   - Vehicle information
   - Cover type and use category
   - Premium amount
   - Add-ons
   - Customer information
5. Insurer completes remaining required fields
6. Submits to create active policy

## Authorization & Security

- **Company-Specific Access**: Insurers only see rates for their company
- **Approved Users Only**: Must be approved insurer to access calculator
- **Quote Authorization**: Can only view quotes created by own company
- **Session Security**: Calculator data stored in secure Flask session
- **Data Validation**: All inputs validated with WTForms validators

## Database Status

✅ **PremiumRate Table**: Created with 136 rate configurations (34 companies × 4 cover types)
✅ **Quote Table**: Created and ready for quote storage
✅ **Default Rates**: All insurance companies seeded with baseline rates

## Testing Checklist

- [x] Premium calculator form displays correctly
- [x] Dynamic use_category options work (PSV vs regular)
- [x] Comprehensive calculation (percentage-based)
- [x] Third-Party Only calculation (flat rate)
- [x] Third-Party Fire & Theft calculation (base + percentage)
- [x] PSV calculation (by vehicle category)
- [x] Add-ons calculation (all 4 types)
- [x] Quote generation with unique number
- [x] Quote viewing with authorization
- [x] Policy pre-fill from calculator
- [x] Dashboard navigation link
- [x] Database seeding completed

## Next Steps (Optional Enhancements)

1. **Email Integration**: Send quotes to customers via email
2. **Quotes Management Page**: List and filter all quotes
3. **Rate Management Interface**: Admin page to adjust company rates
4. **Quote Status Updates**: Mark quotes as Accepted/Converted/Expired
5. **PDF Generation**: Export quotes as PDF documents
6. **Quote Analytics**: Track quote conversion rates
7. **Customer Portal**: Allow customers to accept/view quotes
8. **Rate Comparison**: Show premium comparison across companies
9. **Discount Logic**: Apply discounts based on claim history, vehicle age, etc.
10. **Payment Integration**: Link quotes to payment processing

## Files Modified/Created

### Created Files
- `models.py` - Added PremiumRate and Quote models
- `forms.py` - Added PremiumCalculatorForm
- `templates/insurer/premium_calculator.html` - Full calculator interface
- `templates/insurer/view_quote.html` - Quote display page
- `seed_premium_rates.py` - Database seeding script

### Modified Files
- `app.py` - Added 4 calculator routes, updated create_policy
- `templates/insurer/insurerdashboard.html` - Added navigation link

## Conclusion

The premium calculator system is fully functional and ready for production use. All insurance companies have default rates configured, and the system supports the complete workflow from calculation to quote generation to policy creation. The formula-based approach ensures accurate and transparent premium calculations while maintaining flexibility for company-specific pricing strategies.
