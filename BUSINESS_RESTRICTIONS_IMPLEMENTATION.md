# Business Restrictions Implementation

## Overview
This document describes the implementation of business logic restrictions for the ClearView Insurance system to ensure data integrity and enforce business rules.

## Implemented Restrictions

### 1. One Claim Per Policy
**Rule:** Only one claim can be made per policy.

**Implementation:**
- Location: `app.py` - `create_claim()` route
- Check: Queries database for existing claims with same policy_id before creating new claim
- User Feedback: Flash message with existing claim number if policy already has a claim
- Code:
```python
existing_claim = Claim.query.filter_by(policy_id=policy_id).first()
if existing_claim:
    flash(f'This policy already has a claim (Claim No: {existing_claim.claim_number}). Only one claim can be made per policy.', 'danger')
    return render_template('insurer/create_claim.html', form=form, datetime=datetime)
```

### 2. One Vehicle Per Active Policy
**Rule:** A registration number can only be used in one active policy at a time.

**Implementation:**
- Location: `app.py` - `create_policy()` route
- Check: Queries database for active policies with same registration_number before creating new policy
- Status Filter: Only checks policies with `status='Active'`
- User Feedback: Flash message showing existing policy number and vehicle registration
- Code:
```python
registration_number = form.registration_number.data.upper()
existing_policy = Policy.query.filter_by(
    registration_number=registration_number,
    status='Active'
).first()

if existing_policy:
    flash(f'Registration number {registration_number} is already used in an active policy (Policy No: {existing_policy.policy_number}). A vehicle can only be in one active policy at a time.', 'danger')
    return render_template('insurer/create_policy.html', form=form)
```

### 3. Vehicle Reuse After Cancellation/Expiry
**Rule:** Registration numbers can be reused in new policies if the previous policy is expired or cancelled.

**Implementation:**
- The validation only checks for `status='Active'` policies
- Cancelled and Expired policies are excluded from the duplicate check
- This allows registration numbers to be reused automatically

### 4. Policy Cancellation by Insurer
**Rule:** Insurers can cancel active policies with a mandatory reason.

**Implementation:**
- Route: `/insurer/cancel-policy/<policy_id>` (POST)
- Location: `app.py` - `cancel_policy()` route
- Authorization: Verifies policy belongs to insurer's company
- Validation:
  - Cannot cancel already cancelled policies
  - Cannot cancel expired policies
  - Requires cancellation reason (mandatory)
- Database Updates:
  - Sets `status` to 'Cancelled'
  - Records `cancelled_by` (insurer ID)
  - Records `cancellation_date` (timestamp)
  - Stores `cancellation_reason` (text)

**UI Components:**
- Cancel button: Only visible for Active policies in view_policy.html
- Modal dialog: Collects cancellation reason with warning message
- Cancellation display: Shows cancellation details in policy view for cancelled policies

### 5. Policy Status Tracking
**Rule:** Policies have three states: Active, Expired, Cancelled

**Implementation:**
- Database: New `status` field in Policy model (VARCHAR(20), default='Active')
- Values: 'Active', 'Expired', 'Cancelled'
- Display:
  - Active: Green badge
  - Cancelled: Yellow/Warning badge
  - Expired: Red badge
- Filters: Added 'Cancelled' option to status filter in manage_policies
- Statistics: Dashboard shows counts for all three statuses

## Database Changes

### Migration: `84c616989a45_add_policy_status_and_cancellation_.py`

**New Fields Added to Policy Model:**
```python
status = db.Column(db.String(20), default='Active', nullable=False)
cancelled_by = db.Column(db.Integer, db.ForeignKey('insurer.id'), nullable=True)
cancellation_date = db.Column(db.DateTime, nullable=True)
cancellation_reason = db.Column(db.Text, nullable=True)
```

**Relationships Updated:**
```python
creator = db.relationship('Insurer', backref='created_policies', lazy=True, foreign_keys=[created_by])
canceller = db.relationship('Insurer', backref='cancelled_policies', lazy=True, foreign_keys=[cancelled_by])
```

**Migration Applied:** ✅ Successfully applied on 2025-12-02

## File Changes Summary

### Models (`models.py`)
- Added 4 new fields to Policy model
- Updated relationships with foreign_keys parameter to handle multiple FKs to Insurer table

### Routes (`app.py`)
1. **create_policy()**: Added registration number validation
2. **create_claim()**: Added policy claim count validation
3. **cancel_policy()**: New route for policy cancellation
4. **manage_policies()**: Updated to filter by status field (Active/Cancelled/Expired)
5. **view_policy()**: Added canceller information to template context

### Templates
1. **manage_policies.html**:
   - Added 'Cancelled' to status filter dropdown
   - Changed statistics cards from 3 to 4 (added cancelled_policies)
   - Updated status badges to show database status
   - Changed badge colors (Cancelled = warning/yellow)

2. **view_policy.html**:
   - Added "Cancel Policy" button (only for Active policies)
   - Added cancellation modal with reason textarea
   - Updated status alert to show Cancelled status with details
   - Shows cancellation date, canceller name, and reason for cancelled policies

## User Experience

### Policy Creation
- **Success Flow**: Create policy → Validate registration → Save with status='Active'
- **Duplicate Vehicle**: Shows error with existing policy number → User must cancel old policy first
- **Previous Cancelled/Expired**: Allows creation without error

### Claims Creation
- **Success Flow**: Select policy → Validate claim count → Create claim
- **Duplicate Claim**: Shows error with existing claim number → User cannot proceed

### Policy Cancellation
- **Success Flow**: View Policy → Click Cancel → Enter Reason → Confirm → Policy status = Cancelled
- **Validation**: Cannot cancel already cancelled or expired policies
- **Audit Trail**: Records who cancelled, when, and why

### Policy Filtering
- **All Status**: Shows all policies regardless of status
- **Active**: Shows only active policies (status='Active')
- **Cancelled**: Shows only cancelled policies (status='Cancelled')
- **Expired**: Shows only expired policies (status='Expired')

## Business Logic Flow

```
New Policy Creation
├── Validate Form Data
├── Check Registration Number
│   ├── Query: Policy.filter_by(registration_number=X, status='Active')
│   ├── If Found: Reject with error
│   └── If Not Found: Continue
├── Generate Policy Number
├── Set status='Active'
└── Save to Database

New Claim Creation
├── Validate Form Data
├── Verify Policy Belongs to Company
├── Check Claim Count
│   ├── Query: Claim.filter_by(policy_id=X)
│   ├── If Exists: Reject with error
│   └── If None: Continue
├── Generate Claim Number
└── Save to Database

Policy Cancellation
├── Verify Policy Belongs to Company
├── Check Policy Status
│   ├── If Already Cancelled: Reject
│   ├── If Expired: Reject
│   └── If Active: Continue
├── Validate Cancellation Reason
├── Update Policy
│   ├── Set status='Cancelled'
│   ├── Set cancelled_by=current_user.id
│   ├── Set cancellation_date=now()
│   └── Set cancellation_reason=form_input
└── Save to Database
```

## Testing Checklist

- [x] Create new policy with unique registration number → Success
- [ ] Try to create second policy with same registration (while first is Active) → Error
- [ ] Cancel first policy → Success
- [ ] Create new policy with same registration number → Success (previous cancelled)
- [ ] Create claim for policy → Success
- [ ] Try to create second claim for same policy → Error
- [ ] Cancel active policy with reason → Success
- [ ] Try to cancel already cancelled policy → Error
- [ ] Try to cancel expired policy → Error
- [ ] Filter policies by Cancelled status → Shows only cancelled
- [ ] View cancelled policy → Shows cancellation details

## Future Enhancements

### Suggested Improvements
1. **Automatic Expiry**: Background job to set status='Expired' when expiry_date < current_date
2. **Policy Renewal**: Allow renewing expired policies (resets status to Active)
3. **Partial Cancellation**: Refund calculation and partial premium return
4. **Audit Log**: Detailed history of all status changes
5. **Email Notifications**: Send email when policy is cancelled
6. **Reactivation**: Allow reactivating cancelled policies within grace period
7. **Bulk Operations**: Cancel multiple policies at once
8. **Dashboard Analytics**: Charts showing cancellation trends

## Notes

- All validation is done server-side for security
- User-friendly error messages guide users to correct actions
- Audit trail preserved for all cancellations
- Registration numbers are case-insensitive (converted to uppercase)
- Cancellation reason is mandatory (cannot be empty)
- Multiple people can have policies (no restriction on person duplication)
- Person can have multiple policies simultaneously (explicitly allowed)
