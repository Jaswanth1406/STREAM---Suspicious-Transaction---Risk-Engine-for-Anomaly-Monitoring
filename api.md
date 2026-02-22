
# STREAM API Reference

> **S**uspicious **T**ransaction **R**isk **E**ngine for **A**nomaly **M**onitoring
>
> Anti-Corruption Intelligence Platform — REST API Documentation

**Base URL:** `http://localhost:8000`

**Framework:** FastAPI (Python)

**Authentication:** None (internal use / hackathon demo)

---

## Table of Contents

- [Health \& Info](#health--info)
  - [GET /](#get-)
  - [GET /model/info](#get-modelinfo)
- [Dashboard](#dashboard)
  - [GET /dashboard/kpis](#get-dashboardkpis)
- [Fraud Alerts](#fraud-alerts)
  - [GET /alerts](#get-alerts)
- [Vendor Profile](#vendor-profile)
  - [GET /vendor/{vendor\_id}](#get-vendorvendor_id)
  - [GET /vendor/search/{query}](#get-vendorsearchquery)
  - [GET /vendor/{vendor\_id}/connections](#get-vendorvendor_idconnections)
- [Network Graph](#network-graph)
  - [GET /network/graph](#get-networkgraph)
- [Bid Analysis](#bid-analysis)
  - [GET /bid-analysis](#get-bid-analysis)
  - [GET /bid-analysis/summary](#get-bid-analysissummary)
- [Activity Feed](#activity-feed)
  - [GET /activity/recent](#get-activityrecent)
- [Statistics](#statistics)
  - [GET /stats/risk-distribution](#get-statsrisk-distribution)
  - [GET /stats/top-risk-buyers](#get-statstop-risk-buyers)
  - [GET /stats/bond-summary](#get-statsbond-summary)
- [ML Predictions](#ml-predictions)
  - [POST /predict](#post-predict)
  - [POST /predict/batch](#post-predictbatch)
  - [POST /predict/batch/json](#post-predictbatchjson)
- [Data Sources](#data-sources)
- [Risk Scoring Methodology](#risk-scoring-methodology)

---

## Health & Info

### GET /

**Health check — confirms server is running and data is loaded.**

#### Request

```
GET /
```

No parameters required.

#### Response `200 OK`

```json
{
  "status": "STREAM Anti-Corruption Engine is running",
  "model_loaded": true,
  "data_loaded": {
    "procurement_tenders": 29542,
    "companies": 20249,
    "vendor_profiles": 20333,
    "bond_flows": 1654
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Server status message |
| `model_loaded` | boolean | Whether the ML model artifacts were loaded successfully |
| `data_loaded.procurement_tenders` | integer | Total procurement tenders loaded from CSVs |
| `data_loaded.companies` | integer | Total companies from registry |
| `data_loaded.vendor_profiles` | integer | Total vendor profiles generated |
| `data_loaded.bond_flows` | integer | Total electoral bond flows loaded |

---

### GET /model/info

**Returns ML model performance metrics and configuration.**

#### Request

```
GET /model/info
```

No parameters required.

#### Response `200 OK`

```json
{
  "model_type": "GradientBoostingClassifier",
  "roc_auc": 0.9936,
  "accuracy": 0.96,
  "precision": 0.93,
  "recall": 0.91,
  "f1_score": 0.92,
  "features_used": [
    "amount",
    "num_tenderers",
    "duration_days",
    "log_amount",
    "is_round_amount",
    "amount_vs_buyer_avg",
    "procurementMethod_enc",
    "tenderclassification_enc",
    "buyer_enc"
  ],
  "feature_importance": {
    "num_tenderers": 0.60,
    "amount_vs_buyer_avg": 0.12,
    "log_amount": 0.08,
    "duration_days": 0.06,
    "is_round_amount": 0.04,
    "amount": 0.03,
    "procurementMethod_enc": 0.03,
    "tenderclassification_enc": 0.02,
    "buyer_enc": 0.02
  },
  "training_samples": 23633,
  "test_samples": 5909,
  "cv_roc_auc_mean": 0.9841,
  "cv_roc_auc_std": 0.0097
}
```

| Field | Type | Description |
|-------|------|-------------|
| `model_type` | string | Best model class selected during training |
| `roc_auc` | float | ROC-AUC score on test set |
| `accuracy` | float | Classification accuracy on test set |
| `precision` | float | Precision for suspicious class |
| `recall` | float | Recall for suspicious class |
| `f1_score` | float | F1 score for suspicious class |
| `features_used` | array[string] | Feature names used for training |
| `feature_importance` | object | Feature name → importance score mapping |
| `training_samples` | integer | Number of training samples |
| `test_samples` | integer | Number of test samples |
| `cv_roc_auc_mean` | float | Mean ROC-AUC from 5-fold cross-validation |
| `cv_roc_auc_std` | float | Std deviation of cross-validation ROC-AUC |

---

## Dashboard

### GET /dashboard/kpis

**Top-bar summary statistics for the dashboard header.**

#### Request

```
GET /dashboard/kpis
```

No parameters required.

#### Response `200 OK`

```json
{
  "active_flags": 6480,
  "at_risk_value_cr": 4240.57,
  "vendors_tracked": 20342,
  "precision_rate": 94.2,
  "bid_rigging_detected": 330,
  "shell_networks_mapped": 1247,
  "political_connections": 156,
  "false_positive_control": 94.2,
  "total_tenders_analyzed": 29542,
  "high_risk_tenders": 5,
  "medium_risk_tenders": 1480,
  "low_risk_tenders": 28057,
  "total_bond_value_cr": 12141.23,
  "unique_bond_purchasers": 1316,
  "political_parties_linked": 23
}
```

| Field | Type | Description |
|-------|------|-------------|
| `active_flags` | integer | Count of tenders with `risk_score ≥ 20` |
| `at_risk_value_cr` | float | Sum of amounts (in crores) for flagged tenders |
| `vendors_tracked` | integer | Unique buyers from procurement + company registry |
| `precision_rate` | float | Model precision percentage from training report |
| `bid_rigging_detected` | integer | Tenders with `flag_single_bidder = 1` |
| `shell_networks_mapped` | integer | Companies with `shell_risk_score > threshold` |
| `political_connections` | integer | Cross-referenced bond purchasers ↔ procurement buyers |
| `false_positive_control` | float | Same as `precision_rate` |
| `total_tenders_analyzed` | integer | Total tenders in the dataset |
| `high_risk_tenders` | integer | Tenders with risk tier = High |
| `medium_risk_tenders` | integer | Tenders with risk tier = Medium |
| `low_risk_tenders` | integer | Tenders with risk tier = Low |
| `total_bond_value_cr` | float | Total electoral bond value in crores |
| `unique_bond_purchasers` | integer | Unique bond purchaser entities |
| `political_parties_linked` | integer | Unique political parties receiving bonds |

---

## Fraud Alerts

### GET /alerts

**Paginated list of fraud alerts with filtering, search, and sorting.**

#### Request

```
GET /alerts?alert_type=bid_rigging&risk_tier=high&page=1&page_size=10&sort_by=risk_score&sort_order=desc
```

#### Query Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `page` | integer | `1` | No | Page number (1-indexed) |
| `page_size` | integer | `20` | No | Items per page (max 100) |
| `alert_type` | string | `null` | No | Filter by alert type. One of: `bid_rigging`, `shell_network`, `political_connection`, `high_value`, `short_window` |
| `risk_tier` | string | `null` | No | Filter by risk tier. One of: `high`, `medium`, `low` |
| `search` | string | `null` | No | Free-text search across tender ID, buyer name, title, category |
| `sort_by` | string | `"risk_score"` | No | Sort field. One of: `risk_score`, `amount`, `num_tenderers`, `duration_days` |
| `sort_order` | string | `"desc"` | No | Sort direction: `asc` or `desc` |
| `min_risk_score` | float | `null` | No | Minimum risk score filter (0–100) |
| `max_risk_score` | float | `null` | No | Maximum risk score filter (0–100) |

#### Response `200 OK`

```json
{
  "total": 330,
  "page": 1,
  "page_size": 10,
  "total_pages": 33,
  "alerts": [
    {
      "id": "ocds-123-001",
      "tender_id": "GEM/2024/B/4521897",
      "title": "Road Construction Work in Chennai",
      "buyer_name": "Tamil Nadu PWD",
      "category": "Road Construction",
      "procurement_method": "Limited Tender",
      "amount": 340000000,
      "amount_display": "₹340.00 Cr",
      "num_tenderers": 1,
      "duration_days": 3,
      "risk_score": 87.43,
      "risk_tier": "🔴 High",
      "confidence": 0.91,
      "alert_type": "bid_rigging",
      "alert_type_display": "BID RIGGING",
      "flags": {
        "flag_single_bidder": 1,
        "flag_zero_bidders": 0,
        "flag_short_window": 1,
        "flag_non_open": 1,
        "flag_high_value": 1,
        "flag_buyer_concentration": 0,
        "flag_round_amount": 1,
        "ml_anomaly_flag": 1
      },
      "risk_explanation": "Only 1 bidder submitted (possible bid-rigging); Very short tender window (3 days); Non-open procurement method: Limited Tender; Contract value above 95th percentile; ML model flagged as statistical outlier",
      "evidence_strength": 87
    }
  ]
}
```

#### Alert Object Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | OCDS contract ID |
| `tender_id` | string | Tender reference number |
| `title` | string | Tender title/description |
| `buyer_name` | string | Procuring entity name |
| `category` | string | Tender classification category |
| `procurement_method` | string | Method used (Open, Limited, etc.) |
| `amount` | float | Contract value in INR |
| `amount_display` | string | Human-readable amount (e.g., "₹340.00 Cr") |
| `num_tenderers` | integer | Number of bidders |
| `duration_days` | integer | Tender window duration in days |
| `risk_score` | float | Composite risk score (0–100) |
| `risk_tier` | string | Risk tier: `🟢 Low`, `🟡 Medium`, `🔴 High` |
| `confidence` | float | ML model confidence (0.0–1.0) |
| `alert_type` | string | Primary alert classification |
| `alert_type_display` | string | Display label for alert type |
| `flags` | object | Individual flag values (0 or 1) |
| `risk_explanation` | string | Human-readable explanation of triggered flags |
| `evidence_strength` | integer | Evidence strength score (0–100), same as risk_score |

#### Alert Types

| Value | Display | Trigger Condition |
|-------|---------|-------------------|
| `bid_rigging` | `BID RIGGING` | `flag_single_bidder = 1` or `flag_zero_bidders = 1` |
| `shell_network` | `SHELL NETWORK` | Company has `shell_risk_score > 25` |
| `political_connection` | `POLITICAL CONNECTION` | Bond purchaser matched to procurement buyer |
| `high_value` | `HIGH VALUE` | `flag_high_value = 1` |
| `short_window` | `SHORT WINDOW` | `flag_short_window = 1` |

---

## Vendor Profile

### GET /vendor/{vendor_id}

**Full vendor risk profile with sub-scores and connections.**

#### Request

```
GET /vendor/U45200TN2018PTC123456
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `vendor_id` | string | Company CIN, buyer name (URL-encoded), or internal ID |

#### Response `200 OK`

```json
{
  "vendor_id": "U45200TN2018PTC123456",
  "company_name": "INFRATECH SOLUTIONS PVT LTD",
  "cin": "U45200TN2018PTC123456",
  "status": "Active",
  "registered_address": "123 Anna Salai, Chennai 600002",
  "authorized_capital": 10000000,
  "paidup_capital": 5000000,
  "industry": "Construction",
  "date_of_registration": "2018-03-15",
  "overall_risk_score": 87,
  "risk_tier": "High",
  "sub_scores": {
    "bid_pattern": 90,
    "shell_risk": 75,
    "political": 68,
    "financials": 82
  },
  "total_tenders": 47,
  "total_contract_value": 2840000000,
  "flags_triggered": 12,
  "connections_count": 6,
  "connections": [
    {
      "type": "political_bond",
      "entity_name": "BJP",
      "detail": "Electoral Bond",
      "amount": "₹12Cr",
      "date": "Mar 2023",
      "risk_level": "HIGH"
    },
    {
      "type": "co_bidder",
      "entity_name": "BUILDSMART PVT LTD",
      "detail": "Same registered address",
      "amount": null,
      "date": null,
      "risk_level": "MED"
    }
  ],
  "recent_tenders": [
    {
      "tender_id": "GEM/2024/B/4521897",
      "title": "Road Construction",
      "amount": 340000000,
      "risk_score": 87,
      "date": "2024-08-15"
    }
  ]
}
```

#### Sub-Scores Breakdown

| Sub-Score | Range | Source | Description |
|-----------|-------|--------|-------------|
| `bid_pattern` | 0–100 | `tender_risk_table.csv` | Average anomaly score across tenders involving this buyer |
| `shell_risk` | 0–100 | `company_risk_table.csv` | Shell company risk (low capital, dormant status, address clustering) |
| `political` | 0–100 | Neon DB `relationship_edge` | Normalized bond donation amount to political parties |
| `financials` | 0–100 | `companies.csv` | Capital adequacy, company status, registration age |

#### Connection Types

| Type | Description |
|------|-------------|
| `political_bond` | Electoral bond link (purchaser → political party) |
| `co_bidder` | Companies appearing in same tenders |
| `shared_address` | Companies registered at same address |
| `shared_director` | Companies sharing common directors (future) |

#### Response `404 Not Found`

```json
{
  "detail": "Vendor not found: UNKNOWN_COMPANY"
}
```

---

### GET /vendor/search/{query}

**Search vendors by name or CIN (partial match, case-insensitive).**

#### Request

```
GET /vendor/search/infratech?limit=10
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `query` | string | Search string (minimum 2 characters) |

#### Query Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `limit` | integer | `20` | No | Maximum number of results to return |

#### Response `200 OK`

```json
{
  "query": "infratech",
  "count": 3,
  "results": [
    {
      "vendor_id": "U45200TN2018PTC123456",
      "company_name": "INFRATECH SOLUTIONS PVT LTD",
      "cin": "U45200TN2018PTC123456",
      "overall_risk_score": 87,
      "risk_tier": "High",
      "source": "company_registry"
    },
    {
      "vendor_id": "U45200KA2020PTC234567",
      "company_name": "INFRATECH BUILDERS LTD",
      "cin": "U45200KA2020PTC234567",
      "overall_risk_score": 42,
      "risk_tier": "Medium",
      "source": "company_registry"
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `query` | string | The original search term |
| `count` | integer | Number of results returned |
| `results[].vendor_id` | string | Vendor identifier |
| `results[].company_name` | string | Full company name |
| `results[].cin` | string | Corporate Identification Number |
| `results[].overall_risk_score` | integer | Composite risk score (0–100) |
| `results[].risk_tier` | string | Risk tier: `High`, `Medium`, `Low` |
| `results[].source` | string | Data source: `company_registry`, `procurement_buyer`, `bond_purchaser` |

---

### GET /vendor/{vendor_id}/connections

**Detailed connections for a specific vendor, grouped by type.**

#### Request

```
GET /vendor/U45200TN2018PTC123456/connections
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `vendor_id` | string | Company CIN, buyer name, or internal ID |

#### Response `200 OK`

```json
{
  "vendor_id": "U45200TN2018PTC123456",
  "company_name": "INFRATECH SOLUTIONS PVT LTD",
  "total_connections": 6,
  "connections": {
    "political_bonds": [
      {
        "party_name": "BJP",
        "total_amount": 120000000,
        "total_amount_display": "₹12.00 Cr",
        "bond_count": 3,
        "date_range": "2019-2023",
        "risk_level": "HIGH"
      }
    ],
    "co_bidders": [
      {
        "company_name": "BUILDSMART PVT LTD",
        "shared_tenders": 8,
        "shared_categories": ["Road Construction", "Bridge Work"],
        "risk_level": "MED"
      }
    ],
    "shared_address": [
      {
        "company_name": "ROADTECH INDIA LTD",
        "address": "123 Anna Salai, Chennai",
        "risk_level": "LOW"
      }
    ],
    "shared_directors": []
  }
}
```

---

## Network Graph

### GET /network/graph

**Full network graph as D3.js / Cytoscape.js-ready JSON.**

#### Request

```
GET /network/graph?min_risk_score=30&include_bonds=true&include_cobidders=true&limit_nodes=200
```

#### Query Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `min_risk_score` | float | `0` | No | Only include nodes with risk score ≥ this value |
| `include_bonds` | boolean | `true` | No | Include electoral bond edges |
| `include_cobidders` | boolean | `true` | No | Include co-bidder edges |
| `limit_nodes` | integer | `500` | No | Maximum number of nodes to return |

#### Response `200 OK`

```json
{
  "nodes": [
    {
      "id": "company_U45200TN2018PTC123456",
      "label": "INFRATECH SOLUTIONS PVT LTD",
      "type": "company",
      "risk_score": 87,
      "risk_tier": "High",
      "size": 87,
      "color": "#ff4444"
    },
    {
      "id": "party_BJP",
      "label": "BJP",
      "type": "political_party",
      "risk_score": null,
      "risk_tier": null,
      "size": 50,
      "color": "#ff8800"
    }
  ],
  "edges": [
    {
      "source": "company_U45200TN2018PTC123456",
      "target": "party_BJP",
      "type": "electoral_bond",
      "weight": 120000000,
      "label": "₹12Cr (3 bonds)",
      "color": "#ff8800"
    },
    {
      "source": "company_U45200TN2018PTC123456",
      "target": "company_BUILDSMART123",
      "type": "co_bidder",
      "weight": 8,
      "label": "8 shared tenders",
      "color": "#4488ff"
    }
  ],
  "stats": {
    "total_nodes": 234,
    "total_edges": 567,
    "node_types": {
      "company": 210,
      "political_party": 24
    },
    "edge_types": {
      "electoral_bond": 456,
      "co_bidder": 89,
      "shared_address": 22
    }
  }
}
```

#### Node Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique node identifier (prefixed by type) |
| `label` | string | Display name |
| `type` | string | Node type: `company`, `political_party` |
| `risk_score` | float \| null | Risk score (null for parties) |
| `risk_tier` | string \| null | Risk tier label |
| `size` | integer | Visual size hint (based on risk score or importance) |
| `color` | string | Hex color code for rendering |

#### Edge Object

| Field | Type | Description |
|-------|------|-------------|
| `source` | string | Source node ID |
| `target` | string | Target node ID |
| `type` | string | Edge type: `electoral_bond`, `co_bidder`, `shared_address` |
| `weight` | float | Edge weight (amount in INR or count) |
| `label` | string | Display label |
| `color` | string | Hex color code for rendering |

#### Node Colors

| Risk Tier | Color |
|-----------|-------|
| High | `#ff4444` |
| Medium | `#ffaa00` |
| Low | `#44ff44` |
| Political Party | `#ff8800` |

#### Edge Colors

| Edge Type | Color |
|-----------|-------|
| Electoral Bond | `#ff8800` |
| Co-bidder | `#4488ff` |
| Shared Address | `#88ff44` |

---

## Bid Analysis

### GET /bid-analysis

**Paginated list of tender-level bid analysis data.**

#### Request

```
GET /bid-analysis?category=Road+Construction&risk_tier=high&fiscal_year=2020_2021&page=1&page_size=20
```

#### Query Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `page` | integer | `1` | No | Page number |
| `page_size` | integer | `20` | No | Items per page |
| `category` | string | `null` | No | Filter by tender classification category |
| `buyer` | string | `null` | No | Filter by buyer name (partial match) |
| `risk_tier` | string | `null` | No | Filter: `high`, `medium`, `low` |
| `min_amount` | float | `null` | No | Minimum tender amount in INR |
| `max_amount` | float | `null` | No | Maximum tender amount in INR |
| `fiscal_year` | string | `null` | No | Filter by fiscal year (e.g., `2020_2021`) |
| `sort_by` | string | `"risk_score"` | No | Sort field: `risk_score`, `amount`, `num_tenderers`, `duration_days` |
| `sort_order` | string | `"desc"` | No | Sort direction: `asc` or `desc` |

#### Response `200 OK`

```json
{
  "total": 1576,
  "page": 1,
  "page_size": 20,
  "total_pages": 79,
  "tenders": [
    {
      "ocid": "ocds-123-001",
      "tender_id": "GEM/2024/B/4521897",
      "title": "Road Construction Work",
      "buyer_name": "Tamil Nadu PWD",
      "category": "Road Construction",
      "procurement_method": "Limited Tender",
      "amount": 340000000,
      "amount_display": "₹340.00 Cr",
      "num_tenderers": 1,
      "duration_days": 3,
      "risk_score": 87.43,
      "risk_tier": "🔴 High",
      "anomaly_score": 0.89,
      "flags": {
        "flag_single_bidder": 1,
        "flag_zero_bidders": 0,
        "flag_short_window": 1,
        "flag_non_open": 1,
        "flag_high_value": 1,
        "flag_buyer_concentration": 0,
        "flag_round_amount": 1,
        "ml_anomaly_flag": 1
      },
      "risk_explanation": "Only 1 bidder submitted (possible bid-rigging); Very short tender window (3 days); Non-open procurement method: Limited Tender; Contract value above 95th percentile; ML model flagged as statistical outlier",
      "predicted_suspicious": 1,
      "suspicion_probability": 0.94
    }
  ]
}
```

#### Tender Object Fields

| Field | Type | Description |
|-------|------|-------------|
| `ocid` | string | OCDS contract identifier |
| `tender_id` | string | Tender reference number |
| `title` | string | Tender title |
| `buyer_name` | string | Procuring entity |
| `category` | string | Tender classification |
| `procurement_method` | string | Procurement method used |
| `amount` | float | Contract value in INR |
| `amount_display` | string | Formatted amount string |
| `num_tenderers` | integer | Number of bidders |
| `duration_days` | integer | Tender window in days |
| `risk_score` | float | Rule-based composite risk score (0–100) |
| `risk_tier` | string | Risk tier with emoji indicator |
| `anomaly_score` | float | Isolation Forest anomaly score (0.0–1.0) |
| `flags` | object | Individual flag values (0 or 1) |
| `risk_explanation` | string | Human-readable flag explanations |
| `predicted_suspicious` | integer | ML prediction: 1 = suspicious, 0 = clean |
| `suspicion_probability` | float | ML confidence score (0.0–1.0) |

---

### GET /bid-analysis/summary

**Aggregate statistics for the bid analysis tab header cards.**

#### Request

```
GET /bid-analysis/summary
```

No parameters required.

#### Response `200 OK`

```json
{
  "total_tenders": 29542,
  "total_value_cr": 15420.87,
  "avg_risk_score": 22.4,
  "risk_distribution": {
    "high": 5,
    "medium": 1480,
    "low": 28057
  },
  "flag_counts": {
    "single_bidder": 6156,
    "zero_bidders": 3421,
    "short_window": 892,
    "non_open": 12450,
    "high_value": 1477,
    "buyer_concentration": 234,
    "round_amount": 4521,
    "ml_anomaly": 2954
  },
  "top_categories": [
    {
      "category": "Road Construction",
      "count": 3421,
      "avg_risk": 34.5
    },
    {
      "category": "IT Services",
      "count": 2890,
      "avg_risk": 18.2
    }
  ],
  "top_buyers": [
    {
      "buyer": "Tamil Nadu PWD",
      "count": 567,
      "avg_risk": 28.9,
      "total_value_cr": 890.4
    }
  ],
  "fiscal_year_breakdown": [
    {
      "year": "2016-2017",
      "tenders": 1576,
      "avg_risk": 23.1
    },
    {
      "year": "2017-2018",
      "tenders": 6234,
      "avg_risk": 21.8
    },
    {
      "year": "2018-2019",
      "tenders": 7891,
      "avg_risk": 22.0
    },
    {
      "year": "2019-2020",
      "tenders": 8234,
      "avg_risk": 21.5
    },
    {
      "year": "2020-2021",
      "tenders": 5607,
      "avg_risk": 23.8
    }
  ]
}
```

---

## Activity Feed

### GET /activity/recent

**Combined timeline of recent events across all data sources, sorted by impact/recency.**

#### Request

```
GET /activity/recent?limit=50&event_type=flag_raised
```

#### Query Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `limit` | integer | `50` | No | Maximum events to return |
| `event_type` | string | `null` | No | Filter by event type: `flag_raised`, `contract_awarded`, `bond_purchased`, `prediction_made` |

#### Response `200 OK`

```json
{
  "total": 50,
  "events": [
    {
      "event_type": "flag_raised",
      "icon": "🚩",
      "title": "Bid rigging flag raised",
      "subtitle": "GEM/2024/B/4521897 · Road Construction · TN",
      "timestamp": "2024-08-15T10:30:00",
      "time_ago": "2 hours ago",
      "risk_score": 87,
      "amount": 340000000,
      "amount_display": "₹340Cr",
      "related_entity": "Tamil Nadu PWD",
      "detail_id": "ocds-123-001"
    },
    {
      "event_type": "contract_awarded",
      "icon": "📄",
      "title": "Contract awarded ₹340Cr",
      "subtitle": "3 days ago · Road Construction TN",
      "timestamp": "2024-08-12T00:00:00",
      "time_ago": "3 days ago",
      "risk_score": 87,
      "amount": 340000000,
      "amount_display": "₹340Cr",
      "related_entity": "INFRATECH SOLUTIONS PVT LTD",
      "detail_id": "ocds-123-001"
    },
    {
      "event_type": "bond_purchased",
      "icon": "🏦",
      "title": "Electoral bond purchased",
      "subtitle": "Mar 2023 · ₹12Cr donation",
      "timestamp": "2023-03-15T00:00:00",
      "time_ago": "Mar 2023",
      "risk_score": null,
      "amount": 120000000,
      "amount_display": "₹12Cr",
      "related_entity": "INFRATECH SOLUTIONS → BJP",
      "detail_id": "bond-456"
    },
    {
      "event_type": "prediction_made",
      "icon": "🤖",
      "title": "ML flagged as suspicious",
      "subtitle": "Suspicion probability: 94%",
      "timestamp": "2024-08-15T10:30:00",
      "time_ago": "2 hours ago",
      "risk_score": 87,
      "amount": 340000000,
      "amount_display": "₹340Cr",
      "related_entity": "Tamil Nadu PWD",
      "detail_id": "ocds-123-001"
    }
  ]
}
```

#### Event Types

| Type | Icon | Source | Description |
|------|------|--------|-------------|
| `flag_raised` | 🚩 | `procurement_risk_scores.csv` | A rule-based flag was triggered |
| `contract_awarded` | 📄 | `procurement_risk_scores.csv` | A contract was awarded |
| `bond_purchased` | 🏦 | Neon DB `bond_purchase_event` | An electoral bond was purchased |
| `prediction_made` | 🤖 | `*_predictions.csv` | ML model flagged as suspicious |

---

## Statistics

### GET /stats/risk-distribution

**Histogram data for risk score distribution chart.**

#### Request

```
GET /stats/risk-distribution
```

No parameters required.

#### Response `200 OK`

```json
{
  "bins": [
    { "range": "0-10", "count": 18234 },
    { "range": "10-20", "count": 4832 },
    { "range": "20-30", "count": 3511 },
    { "range": "30-40", "count": 1245 },
    { "range": "40-50", "count": 834 },
    { "range": "50-60", "count": 401 },
    { "range": "60-70", "count": 312 },
    { "range": "70-80", "count": 124 },
    { "range": "80-90", "count": 44 },
    { "range": "90-100", "count": 5 }
  ],
  "mean": 22.4,
  "median": 15.8,
  "std": 18.7,
  "p95": 58.2,
  "p99": 78.1
}
```

| Field | Type | Description |
|-------|------|-------------|
| `bins` | array | Histogram bins with range and count |
| `mean` | float | Mean risk score across all tenders |
| `median` | float | Median risk score |
| `std` | float | Standard deviation |
| `p95` | float | 95th percentile risk score |
| `p99` | float | 99th percentile risk score |

---

### GET /stats/top-risk-buyers

**Top buyers ranked by average risk score.**

#### Request

```
GET /stats/top-risk-buyers?limit=20&min_tenders=5
```

#### Query Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `limit` | integer | `20` | No | Number of buyers to return |
| `min_tenders` | integer | `5` | No | Minimum number of tenders to qualify for ranking |

#### Response `200 OK`

```json
{
  "buyers": [
    {
      "buyer_name": "Tamil Nadu PWD",
      "avg_risk_score": 38.9,
      "max_risk_score": 87.4,
      "total_tenders": 567,
      "flagged_tenders": 89,
      "total_value_cr": 890.4,
      "dominant_category": "Road Construction",
      "top_flags": ["single_bidder", "non_open"]
    },
    {
      "buyer_name": "Ministry of Defence",
      "avg_risk_score": 35.2,
      "max_risk_score": 72.8,
      "total_tenders": 234,
      "flagged_tenders": 45,
      "total_value_cr": 2340.1,
      "dominant_category": "Defence Equipment",
      "top_flags": ["non_open", "high_value"]
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `buyer_name` | string | Procuring entity name |
| `avg_risk_score` | float | Average risk score across all their tenders |
| `max_risk_score` | float | Highest single tender risk score |
| `total_tenders` | integer | Total number of tenders by this buyer |
| `flagged_tenders` | integer | Tenders with risk_score ≥ 20 |
| `total_value_cr` | float | Total contract value in crores |
| `dominant_category` | string | Most frequent tender category |
| `top_flags` | array[string] | Most frequently triggered flags |

---

### GET /stats/bond-summary

**Electoral bond flow statistics by political party.**

#### Request

```
GET /stats/bond-summary
```

No parameters required.

#### Response `200 OK`

```json
{
  "total_bond_value_cr": 12141.23,
  "total_bonds": 18871,
  "unique_purchasers": 1316,
  "parties": [
    {
      "party_name": "BHARATIYA JANATA PARTY",
      "total_received_cr": 6060.54,
      "bond_count": 8234,
      "unique_donors": 456,
      "avg_bond_cr": 0.74,
      "max_single_bond_cr": 25.0,
      "procurement_links": 12
    },
    {
      "party_name": "INDIAN NATIONAL CONGRESS",
      "total_received_cr": 1952.34,
      "bond_count": 3456,
      "unique_donors": 234,
      "avg_bond_cr": 0.56,
      "max_single_bond_cr": 15.0,
      "procurement_links": 8
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `total_bond_value_cr` | float | Total value of all electoral bonds in crores |
| `total_bonds` | integer | Total number of bonds |
| `unique_purchasers` | integer | Unique purchaser entities |
| `parties[].party_name` | string | Political party name |
| `parties[].total_received_cr` | float | Total bonds received in crores |
| `parties[].bond_count` | integer | Number of bonds received |
| `parties[].unique_donors` | integer | Unique purchasers donating to this party |
| `parties[].avg_bond_cr` | float | Average bond value in crores |
| `parties[].max_single_bond_cr` | float | Largest single bond in crores |
| `parties[].procurement_links` | integer | Number of cross-referenced procurement buyers |

---

## ML Predictions

### POST /predict

**Score a single tender via live ML model inference.**

#### Request

```
POST /predict
Content-Type: application/json
```

#### Request Body

```json
{
  "tender/value/amount": 340000000,
  "tender/numberOfTenderers": 1,
  "tender/tenderPeriod/durationInDays": 3,
  "tender/procurementMethod": "Limited Tender",
  "tenderclassification/description": "Road Construction",
  "buyer/name": "Tamil Nadu PWD"
}
```

#### Request Body Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `tender/value/amount` | float | Yes | Contract value in INR |
| `tender/numberOfTenderers` | integer | Yes | Number of bidders |
| `tender/tenderPeriod/durationInDays` | integer | Yes | Tender window duration in days |
| `tender/procurementMethod` | string | Yes | Procurement method (e.g., "Open Tender", "Limited Tender") |
| `tenderclassification/description` | string | Yes | Tender category |
| `buyer/name` | string | Yes | Procuring entity name |

#### Response `200 OK`

```json
{
  "predicted_suspicious": 1,
  "suspicion_probability": 0.94,
  "predicted_risk_tier": "High",
  "risk_factors": {
    "amount": 340000000,
    "num_tenderers": 1,
    "duration_days": 3,
    "log_amount": 19.64,
    "is_round_amount": 1,
    "amount_vs_buyer_avg": 2.34
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `predicted_suspicious` | integer | Binary prediction: `1` = suspicious, `0` = clean |
| `suspicion_probability` | float | Model confidence (0.0–1.0) |
| `predicted_risk_tier` | string | Risk tier: `High` (≥0.7), `Medium` (≥0.3), `Low` (<0.3) |
| `risk_factors` | object | Computed feature values used for prediction |

#### Response `400 Bad Request`

```json
{
  "detail": "Missing required field: tender/value/amount"
}
```

#### Response `503 Service Unavailable`

```json
{
  "detail": "Model not loaded. Run ml_model.py first."
}
```

---

### POST /predict/batch

**Upload a CSV file → get back a CSV file with predictions appended.**

#### Request

```
POST /predict/batch
Content-Type: multipart/form-data
```

#### Form Data

| Field | Type | Description |
|-------|------|-------------|
| `file` | file (CSV) | CSV file with tender data. Must contain columns matching the training schema. |

#### Required CSV Columns

| Column | Description |
|--------|-------------|
| `tender/value/amount` | Contract value |
| `tender/numberOfTenderers` | Number of bidders |
| `tender/tenderPeriod/durationInDays` | Tender window |
| `tender/procurementMethod` | Procurement method |
| `tenderclassification/description` | Category |
| `buyer/name` | Buyer name |

#### Response `200 OK`

**Returns:** CSV file download

The response CSV contains all original columns plus:

| Added Column | Type | Description |
|-------------|------|-------------|
| `predicted_suspicious` | integer | 0 or 1 |
| `suspicion_probability` | float | 0.0–1.0 |
| `predicted_risk_tier` | string | High / Medium / Low |

#### Response Headers

```
Content-Type: text/csv
Content-Disposition: attachment; filename="predictions.csv"
```

---

### POST /predict/batch/json

**Upload a CSV file → get back a JSON summary with predictions.**

#### Request

```
POST /predict/batch/json
Content-Type: multipart/form-data
```

#### Form Data

Same as [POST /predict/batch](#post-predictbatch).

#### Response `200 OK`

```json
{
  "total_records": 500,
  "suspicious_count": 112,
  "clean_count": 388,
  "suspicion_rate": 0.224,
  "risk_distribution": {
    "High": 5,
    "Medium": 107,
    "Low": 388
  },
  "avg_suspicion_probability": 0.34,
  "predictions": [
    {
      "row": 0,
      "predicted_suspicious": 1,
      "suspicion_probability": 0.94,
      "predicted_risk_tier": "High"
    },
    {
      "row": 1,
      "predicted_suspicious": 0,
      "suspicion_probability": 0.12,
      "predicted_risk_tier": "Low"
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `total_records` | integer | Total rows in uploaded CSV |
| `suspicious_count` | integer | Rows predicted as suspicious |
| `clean_count` | integer | Rows predicted as clean |
| `suspicion_rate` | float | Fraction of suspicious predictions |
| `risk_distribution` | object | Count per risk tier |
| `avg_suspicion_probability` | float | Average suspicion probability across all rows |
| `predictions` | array | Per-row prediction details |

---

## Data Sources

### Procurement Data (OCDS Format)

Five fiscal years of government procurement tenders in Open Contracting Data Standard format:

| File | Fiscal Year | Records |
|------|-------------|---------|
| `ocds_mapped_procurement_data_fiscal_year_2016_2017.csv` | 2016–2017 | 1,576 |
| `ocds_mapped_procurement_data_fiscal_year_2017_2018.csv` | 2017–2018 | 6,234 |
| `ocds_mapped_procurement_data_fiscal_year_2018_2019.csv` | 2018–2019 | 7,891 |
| `ocds_mapped_procurement_data_fiscal_year_2019_2020.csv` | 2019–2020 | 8,234 |
| `ocds_mapped_procurement_data_fiscal_year_2020_2021.csv` | 2020–2021 | 5,607 |
| **Total** | | **29,542** |

### Company Registry

| File | Records | Description |
|------|---------|-------------|
| `companies.csv` | 20,249 | MCA company registry data (CIN, capital, address, status) |

### Electoral Bonds (Neon PostgreSQL)

| Table | Records | Description |
|-------|---------|-------------|
| `bond_master` | 18,871 | Bond lifecycle records |
| `bond_purchase_event` | 18,871 | Purchase events with purchaser details |
| `bond_redemption_event` | 20,416 | Redemption events with party details |
| `entity` | 12,528 | Buyers, companies, purchasers, parties |
| `relationship_edge` | 1,654 | Purchaser → party bond flow edges |
| `risk_alert` | 17,221 | Generated risk alerts |
| `risk_explanation` | 37,861 | Detailed explanations per alert |

---

## Risk Scoring Methodology

### Stage 1: Rule-Based Flags

Seven expert-defined heuristic flags, each with a weight:

| Flag | Weight | Trigger Condition |
|------|--------|-------------------|
| `flag_single_bidder` | 25 | Only 1 bidder (bid-rigging signal) |
| `flag_zero_bidders` | 20 | No bidders recorded (pre-awarded) |
| `flag_short_window` | 15 | Tender period < 7 days |
| `flag_non_open` | 10 | Non-open procurement method |
| `flag_high_value` | 10 | Amount > 95th percentile for category |
| `flag_buyer_concentration` | 10 | Buyer handles > 70% of a category |
| `flag_round_amount` | 5 | Amount divisible by 100,000 |
| `ml_anomaly_flag` | 15 | Isolation Forest statistical outlier |

### Stage 2: Composite Score

```
risk_score = (weighted_flag_sum / max_possible_weight) × 85 + anomaly_score × 15
```

Normalized to 0–100 range.

### Stage 3: Risk Tiers

| Tier | Score Range | Label |
|------|-------------|-------|
| Low | 0–30 | 🟢 Low |
| Medium | 30–60 | 🟡 Medium |
| High | 60–100 | 🔴 High |

### Stage 4: Supervised ML

- **Model:** GradientBoostingClassifier (200 trees, depth 4, lr 0.1)
- **Label:** `is_suspicious = 1` if `risk_score ≥ 20`
- **Features:** 9 features (numeric + label-encoded categoricals)
- **Performance:** ROC-AUC 0.9936, Precision 93%, Recall 91%
- **Cross-validation:** 5-fold CV ROC-AUC 0.9841 ± 0.0097

---

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common HTTP Status Codes

| Code | Description |
|------|-------------|
| `200` | Success |
| `400` | Bad request (missing or invalid parameters) |
| `404` | Resource not found (vendor ID, etc.) |
| `422` | Validation error (invalid query parameter types) |
| `500` | Internal server error |
| `503` | Service unavailable (model not loaded) |

---

## Running the Server

```bash
# 1. Train the model (first time only)
python ml_model.py

# 2. Start the API server
uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# 3. Open interactive docs
# Swagger UI: http://localhost:8000/docs
# ReDoc:      http://localhost:8000/redoc
```

---

*STREAM — Suspicious Transaction Risk Engine for Anomaly Monitoring*
*AIA-26 Hackathon — Anna University*