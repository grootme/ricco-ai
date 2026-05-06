# Web Commerce Structure Unification Migration Plan

**Created:** 2024
**Task ID:** 2-c
**Status:** PLANNING (No files modified - analysis only)

---

## Executive Summary

This document details the migration plan for unifying duplicate web commerce structures in the RICCO ecosystem. The goal is to consolidate redundant directories into a single, well-organized structure under `web/commerce/`.

---

## Current Structure Analysis

### Duplicate Directories Identified

| Directory | Purpose | Status |
|-----------|---------|--------|
| `web/mall/` | Original mall implementation with backend + storefront | DUPLICATE - TO DELETE |
| `web/mall-storefront/` | Standalone mall storefront | DUPLICATE - TO DELETE |
| `web/commerce/backend/` | Unified backend for all commerce | CANONICAL - KEEP |
| `web/commerce/wholesale/` | Wholesale B2B storefront | DUPLICATE - TO DELETE |
| `web/commerce/storefronts/mall/` | Mall storefront in unified structure | CANONICAL - KEEP |
| `web/commerce/storefronts/wholesale/` | Wholesale B2B storefront in unified structure | CANONICAL - KEEP |

---

## Detailed Comparison

### 1. Backend Comparison: `web/mall/backend/` vs `web/commerce/backend/`

#### Modules Comparison

**web/mall/backend/src/modules/** (9 modules):
- `payment/` - Payment provider, transactions, wallet
- `dropshipping/` - Agent, partnership, commission models
- `erpnext/` - ERP integration sync
- `sharedCategory/` - Shared categories for vendors
- `subscription/` - Full subscription models (6 files)
- `booking/` - Service booking with workflows
- `delivery/` - Delivery tracking and orders
- `channel-config/` - Sales channel configuration
- `vendor/` - Vendor management
- `mall/` - Mall-specific models

**web/commerce/backend/src/modules/** (16 modules - MORE COMPLETE):
- All modules from `web/mall/backend/` PLUS:
- `ricco-integrations/` - RICCO ID and AI client integrations
- `company/` - B2B company management with employees
- `pos/` - Point of Sale terminal and sessions
- `food/` - Restaurant/delivery module
- `tier-pricing/` - B2B tier pricing models
- `approval/` - B2B approval workflow
- `quote/` - RFQ quote management

#### API Routes Comparison

**web/mall/backend/src/api/** (18 routes):
- Admin: custom, shared-categories, payments, vendors, agents
- Store: custom, wholesale/*, vendors, agents
- Auth: ricco-id/validate

**web/commerce/backend/src/api/** (68 routes - MORE COMPLETE):
- All routes from `web/mall/backend/` PLUS:
- Admin: mini-programs, genui/*
- Store: pos/*, payments/*, wallet, wholesale/company, wholesale/credit, wholesale/quotes, food/*, approvals, rewards, a2ui/*, ricco/*
- Auth: ricco-id (main route)

#### Verdict: **web/commerce/backend/ is the canonical version**

---

### 2. Mall Storefront Comparison

#### Directories Compared:
1. `web/mall-storefront/`
2. `web/mall/storefront/`
3. `web/commerce/storefronts/mall/`

#### Package.json Comparison

| Feature | web/mall-storefront | web/mall/storefront | web/commerce/storefronts/mall |
|---------|---------------------|---------------------|-------------------------------|
| name | medusa-next | medusa-next | @ricco/commerce-mall |
| packageManager | npm@11.6.2 | yarn@4.12.0 | npm@11.6.2 |
| RICCO ID config | NO | NO | YES |
| Mall config | NO | NO | YES |

#### lib/config.ts Comparison

**web/mall-storefront & web/mall/storefront**: Basic Medusa SDK configuration only

**web/commerce/storefronts/mall**: Enhanced with:
```typescript
// RICCO ID Configuration
export const riccoIdConfig = {
  url: process.env.NEXT_PUBLIC_RICCO_ID_URL || "https://id.ricco.com",
  clientId: process.env.NEXT_PUBLIC_RICCO_ID_CLIENT_ID || "mall-storefront",
  redirectUri: `${process.env.NEXT_PUBLIC_BASE_URL || "http://localhost:8000"}/auth/callback`,
  scope: "openid profile email",
}

// Mall-specific configuration
export const mallConfig = {
  name: "RICCO Mall",
  tagline: "Your Multi-Vendor Marketplace",
  enableMultiStoreCart: process.env.NEXT_PUBLIC_ENABLE_MULTI_STORE_CART === "true",
  enableRiccoId: process.env.NEXT_PUBLIC_ENABLE_RICCO_ID === "true",
}
```

#### Verdict: **web/commerce/storefronts/mall/ is the canonical version**

---

### 3. Wholesale Storefront Comparison

#### Directories Compared:
1. `web/commerce/wholesale/`
2. `web/commerce/storefronts/wholesale/`

#### Package.json Comparison

| Feature | web/commerce/wholesale | web/commerce/storefronts/wholesale |
|---------|------------------------|-----------------------------------|
| name | @ricco/commerce-wholesale | @ricco/commerce-wholesale |
| react | ^18.2.0 | ^19.0.0 (NEWER) |
| @medusajs/types | MISSING | ^2.0.0 |
| @medusajs/ui | MISSING | ^4.0.0 |
| @medusajs/icons | MISSING | ^2.0.0 |
| @ricco/ricco-id | MISSING | workspace:* |
| Radix UI | MISSING | YES (6 packages) |
| Lucide icons | MISSING | ^0.400.0 |

#### lib/config.ts Comparison

Both directories have **IDENTICAL** configuration files with full B2B features:
- Tier pricing configuration
- Credit terms
- Feature flags
- Helper functions

#### Verdict: **web/commerce/storefronts/wholesale/ is the canonical version (more dependencies)**

---

## Migration Plan

### Phase 1: Backup (Optional)

```bash
# Create backup of directories to be deleted
mkdir -p /home/z/my-project/ecosystem/_backup/web_migration_$(date +%Y%m%d)
cp -r /home/z/my-project/ecosystem/web/mall /home/z/my-project/ecosystem/_backup/web_migration_$(date +%Y%m%d)/
cp -r /home/z/my-project/ecosystem/web/mall-storefront /home/z/my-project/ecosystem/_backup/web_migration_$(date +%Y%m%d)/
cp -r /home/z/my-project/ecosystem/web/commerce/wholesale /home/z/my-project/ecosystem/_backup/web_migration_$(date +%Y%m%d)/
```

### Phase 2: Directories to Delete

```bash
# DELETE: web/mall/ (entire directory)
rm -rf /home/z/my-project/ecosystem/web/mall/

# DELETE: web/mall-storefront/ (entire directory)
rm -rf /home/z/my-project/ecosystem/web/mall-storefront/

# DELETE: web/commerce/wholesale/ (entire directory)
rm -rf /home/z/my-project/ecosystem/web/commerce/wholesale/
```

### Phase 3: Verify Canonical Structure

After deletion, the structure should be:

```
web/
├── commerce/
│   ├── backend/           # Unified Medusa backend
│   ├── storefronts/
│   │   ├── mall/          # B2C Mall storefront
│   │   └── wholesale/     # B2B Wholesale storefront
│   ├── pos/               # Point of Sale
│   ├── food/              # Food delivery storefront
│   ├── ricco-id/          # Identity client library
│   └── docker/            # Docker configuration
├── health/
├── logistics/
├── finance/
├── connect/
├── booking/
└── lib/                   # Shared web libraries
```

---

## Import Path Changes Required

### Backend Changes

No changes required - `web/commerce/backend/` is already the canonical location.

### Frontend Changes

#### Before:
```typescript
// In web/mall-storefront or web/mall/storefront
import { sdk } from "@lib/config"
```

#### After:
```typescript
// In web/commerce/storefronts/mall
import { sdk, riccoIdConfig, mallConfig } from "@lib/config"
```

#### Wholesale (no changes required):
```typescript
// In web/commerce/storefronts/wholesale
import { BACKEND_URL, FEATURES, PRICING_TIERS } from "@/lib/config"
```

---

## Files to Merge

### No Files Need Manual Merging

All files in the duplicate directories have equivalent or inferior versions in the canonical directories. The canonical directories (`web/commerce/backend/`, `web/commerce/storefronts/mall/`, `web/commerce/storefronts/wholesale/`) contain all necessary functionality.

---

## Migration Commands (Step-by-Step)

### Step 1: Pre-Migration Verification

```bash
# Verify canonical directories exist
ls -la /home/z/my-project/ecosystem/web/commerce/backend/
ls -la /home/z/my-project/ecosystem/web/commerce/storefronts/mall/
ls -la /home/z/my-project/ecosystem/web/commerce/storefronts/wholesale/

# Count files in each directory
find /home/z/my-project/ecosystem/web/mall -type f | wc -l
find /home/z/my-project/ecosystem/web/mall-storefront -type f | wc -l
find /home/z/my-project/ecosystem/web/commerce/wholesale -type f | wc -l
```

### Step 2: Create Backup (Recommended)

```bash
BACKUP_DIR="/home/z/my-project/ecosystem/_backup/web_migration_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp -r /home/z/my-project/ecosystem/web/mall "$BACKUP_DIR/"
cp -r /home/z/my-project/ecosystem/web/mall-storefront "$BACKUP_DIR/"
cp -r /home/z/my-project/ecosystem/web/commerce/wholesale "$BACKUP_DIR/"
echo "Backup created at: $BACKUP_DIR"
```

### Step 3: Delete Duplicate Directories

```bash
# Remove web/mall/ (contains duplicate backend and storefront)
rm -rf /home/z/my-project/ecosystem/web/mall/

# Remove web/mall-storefront/ (duplicate of storefronts/mall)
rm -rf /home/z/my-project/ecosystem/web/mall-storefront/

# Remove web/commerce/wholesale/ (duplicate of storefronts/wholesale)
rm -rf /home/z/my-project/ecosystem/web/commerce/wholesale/
```

### Step 4: Post-Migration Verification

```bash
# Verify directories are deleted
ls /home/z/my-project/ecosystem/web/mall 2>/dev/null || echo "web/mall deleted successfully"
ls /home/z/my-project/ecosystem/web/mall-storefront 2>/dev/null || echo "web/mall-storefront deleted successfully"
ls /home/z/my-project/ecosystem/web/commerce/wholesale 2>/dev/null || echo "web/commerce/wholesale deleted successfully"

# Verify canonical structure remains intact
ls /home/z/my-project/ecosystem/web/commerce/backend/
ls /home/z/my-project/ecosystem/web/commerce/storefronts/
```

### Step 5: Update Package Manager Lock Files

```bash
# Regenerate lock files if using workspaces
cd /home/z/my-project/ecosystem/web/commerce/storefronts/mall
npm install

cd /home/z/my-project/ecosystem/web/commerce/storefronts/wholesale
npm install
```

---

## Summary Table

| Action | Directory | Reason |
|--------|-----------|--------|
| DELETE | `web/mall/` | Superseded by `web/commerce/backend/` and `web/commerce/storefronts/mall/` |
| DELETE | `web/mall-storefront/` | Superseded by `web/commerce/storefronts/mall/` |
| DELETE | `web/commerce/wholesale/` | Superseded by `web/commerce/storefronts/wholesale/` |
| KEEP | `web/commerce/backend/` | Canonical backend (16 modules, 68 API routes) |
| KEEP | `web/commerce/storefronts/mall/` | Canonical mall storefront (RICCO ID integrated) |
| KEEP | `web/commerce/storefronts/wholesale/` | Canonical wholesale storefront (full dependencies) |

---

## Risk Assessment

### Low Risk
- All duplicate directories have identical or inferior content compared to canonical versions
- No unique files exist in directories to be deleted

### Mitigation
- Backup recommended before deletion
- Verify backup integrity before proceeding with deletion

---

## Next Steps After Migration

1. Update any CI/CD pipelines that reference deleted paths
2. Update documentation to reflect new structure
3. Run full test suite to verify no broken imports
4. Update developer onboarding documentation

---

## Appendix: File Count Summary

| Directory | Files Count | Action |
|-----------|-------------|--------|
| web/mall/backend/ | ~150 files | DELETE |
| web/mall/storefront/ | ~300 files | DELETE (in web/mall/) |
| web/mall-storefront/ | ~300 files | DELETE |
| web/commerce/backend/ | ~200 files | KEEP |
| web/commerce/storefronts/mall/ | ~300 files | KEEP |
| web/commerce/wholesale/ | ~70 files | DELETE |
| web/commerce/storefronts/wholesale/ | ~70 files | KEEP |

---

**Document End**
