# Database Architecture

## Overview
This schema is built around bond lifecycle data:
- Purchase-side records (`download_bonds`)
- Redemption-side records (`redemption_bonds`)
- Canonical bond identity (`bond_master`)
- Event tables (`bond_purchase_event`, `bond_redemption_event`)
- Entity and relation graph tables (`entity`, `entity_alias`, `relationship_edge`)
- Inference output tables (`risk_alert`, `risk_explanation`)

---

## Tables

### 1) `download_bonds`
Raw purchase-side rows loaded from `download.csv`.

**Columns**
- `sr_no` `INTEGER`
- `reference_no_urn` `TEXT`
- `journal_date` `TEXT`
- `purchase_date` `TEXT`
- `expiry_date` `TEXT`
- `purchaser_name` `TEXT`
- `prefix` `TEXT`
- `bond_number` `INTEGER`
- `denomination` `TEXT`
- `issue_branch_code` `TEXT`
- `issue_teller` `TEXT`
- `status` `TEXT`

---

### 2) `redemption_bonds`
Raw redemption-side rows loaded from `redemption.csv`.

**Columns**
- `sr_no` `INTEGER`
- `encashment_date` `TEXT`
- `party_name` `TEXT`
- `account_no` `TEXT`
- `prefix` `TEXT`
- `bond_number` `INTEGER`
- `denomination` `TEXT`
- `pay_branch_code` `TEXT`
- `pay_teller` `TEXT`

---

### 3) `bond_master`
Canonical unique bond table.

**Columns**
- `bond_id` `BIGSERIAL` (PK)
- `prefix` `TEXT` (NOT NULL)
- `bond_number` `INTEGER` (NOT NULL)
- `denomination` `TEXT`

**Constraints**
- Primary Key: `bond_id`
- Unique: (`prefix`, `bond_number`)

---

### 4) `bond_purchase_event`
Normalized purchase events linked to canonical bond id.

**Columns**
- `purchase_event_id` `BIGSERIAL` (PK)
- `bond_id` `BIGINT` (FK -> `bond_master.bond_id`)
- `reference_no_urn` `TEXT`
- `journal_date` `TEXT`
- `purchase_date` `TEXT`
- `expiry_date` `TEXT`
- `purchaser_name` `TEXT`
- `issue_branch_code` `TEXT`
- `issue_teller` `TEXT`
- `status` `TEXT`

---

### 5) `bond_redemption_event`
Normalized redemption events linked to canonical bond id.

**Columns**
- `redemption_event_id` `BIGSERIAL` (PK)
- `bond_id` `BIGINT` (FK -> `bond_master.bond_id`)
- `encashment_date` `TEXT`
- `party_name` `TEXT`
- `account_no_masked` `TEXT`
- `pay_branch_code` `TEXT`
- `pay_teller` `TEXT`

---

### 6) `entity`
Canonical actor/node registry for purchaser, party, branch, account entities.

**Columns**
- `entity_id` `BIGSERIAL` (PK)
- `entity_type` `TEXT`
- `canonical_name` `TEXT`
- `normalized_name` `TEXT`

---

### 7) `entity_alias`
Alternate names mapped to canonical entities.

**Columns**
- `alias_id` `BIGSERIAL` (PK)
- `entity_id` `BIGINT` (FK -> `entity.entity_id`)
- `alias_text` `TEXT`
- `confidence` `NUMERIC(5,4)`

---

### 8) `relationship_edge`
Graph-style relation edges between entities.

**Columns**
- `edge_id` `BIGSERIAL` (PK)
- `src_entity_id` `BIGINT` (FK -> `entity.entity_id`)
- `dst_entity_id` `BIGINT` (FK -> `entity.entity_id`)
- `edge_type` `TEXT`
- `bond_id` `BIGINT` (nullable FK -> `bond_master.bond_id`)
- `event_time` `TIMESTAMP` (nullable)
- `weight` `NUMERIC(12,4)` (nullable)
- `evidence_ref` `TEXT` (nullable)

---

### 9) `risk_alert`
Risk scoring output per entity.

**Columns**
- `alert_id` `BIGSERIAL` (PK)
- `entity_id` `BIGINT` (FK -> `entity.entity_id`)
- `risk_score` `NUMERIC(6,4)`
- `risk_level` `TEXT`
- `generated_at` `TIMESTAMP`

---

### 10) `risk_explanation`
Explanation rows attached to alerts.

**Columns**
- `explanation_id` `BIGSERIAL` (PK)
- `alert_id` `BIGINT` (FK -> `risk_alert.alert_id`)
- `rule_or_model` `TEXT`
- `reason_text` `TEXT`
- `supporting_metrics` `JSONB` (nullable)

---

## Table Relationships

## Core bond lifecycle
- `download_bonds` and `redemption_bonds` are linked by business key:
  - (`prefix`, `bond_number`)
- `bond_master` is the canonical identity table for that key.

## Event linkage
- `bond_master (1) -> (N) bond_purchase_event`
- `bond_master (1) -> (N) bond_redemption_event`

## Entity graph linkage
- `entity (1) -> (N) entity_alias`
- `entity (1) -> (N) relationship_edge` via `src_entity_id`
- `entity (1) -> (N) relationship_edge` via `dst_entity_id`
- `bond_master (1) -> (N) relationship_edge` via nullable `bond_id`

## Inference linkage
- `entity (1) -> (N) risk_alert`
- `risk_alert (1) -> (N) risk_explanation`

---

## ER Summary (Text)
- Bond identity: `bond_master`
- Bond events: `bond_purchase_event`, `bond_redemption_event`
- Raw ingestion tables: `download_bonds`, `redemption_bonds`
- Entity model: `entity`, `entity_alias`
- Graph model: `relationship_edge`
- Inference output: `risk_alert`, `risk_explanation`
