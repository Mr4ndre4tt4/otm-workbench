# GUI Exceptions Register

**Status:** active  
**Branch:** `codex/gui-exceptions-register`  
**Scope:** governed exceptions for custom GUI patterns and module-specific interaction departures.

## 1. Purpose

This register tracks approved departures from the shared GUI shell, UI kit, and
backend-owned contract patterns.

Default rule:

```text
No module should create a custom visual or interaction pattern unless the
exception is recorded here with a reason, owner, review path, and rollback or
standardization plan.
```

## 2. Current Exceptions

```text
None approved.
```

## 3. Required Entry Format

New exceptions must use this format:

```text
ID:
Status: Proposed | Approved | Retired
Module or area:
Owner:
Date:
Pattern being bypassed:
Reason:
Backend contract impact:
Accessibility impact:
Responsive impact:
Dark/light mode impact:
Test coverage:
Review trigger:
Standardization or rollback plan:
```

## 4. Approval Rules

An exception is allowed only when:

```text
- existing shared components cannot express the workflow clearly
- the need is tied to real module behavior, not aesthetics alone
- backend ownership remains explicit
- accessibility, responsive behavior, and theme behavior are covered
- the exception has a path to become a shared pattern or be retired
```

## 5. Examples That Require Registration

```text
- custom canvas/diagram editors
- bespoke mapping table interactions
- XML/JSON tree editors with special keyboard behavior
- drag/drop sequencing surfaces
- module-specific toolbars that bypass ActionBar
- custom status badges or module-specific color semantics
- module-specific list/detail layouts outside the shared shell patterns
```

## 6. Examples That Do Not Require Registration

```text
- passing different backend data into existing shared components
- adding a new backend-owned action to ActionBar
- adding a new DetailList section
- adding a new ModuleObjectList collection
- using existing CSS tokens through shared classes
```

## 7. Backend Ownership Reminder

Exceptions must not move these decisions into the frontend:

```text
- permissions
- lifecycle gates
- OTM dependency rules
- validation decisions
- available actions
- disabled reasons
- active context
- user preferences
```
