# Pall Biotech Product Marketing Analytics Case Study

An end to end **Product Marketing Analytics** case study combining **Pricing Analytics, Product Lifecycle Analytics, Competitive Intelligence, and Strategic Decision Support** into a single analytical framework.

## 1. What is this project?

This project evaluates how commercial, operational, and external market signals can be combined to support **Product Marketing Management (PMM)** decisions.

The framework is built around three analytical pillars:

**Pillar 1: Pricing Analytics**

Analyses price realization, discounts, discount creep, ASP trends, revenue concentration, pricing versus input cost benchmarks, and price elasticity.

**Pillar 2: Product Lifecycle and Execution Analytics**

Evaluates product and initiative health using revenue attainment, customer adoption, execution score, On Time Delivery, backlog, gross margin, and lifecycle indicators.

**Pillar 3: Competitive Intelligence**

Compares Pall pricing against competitor benchmarks and incorporates market share, industry growth, and product to industry mapping.

These three pillars are combined into a **104 row strategic decision surface** at the product family, region, and quarter level.

The final layer assigns **priority scores and recommended PMM actions** rather than presenting individual metrics in isolation.

## 2. Why was it done?

The core business question was:

**Where is there sufficient evidence to change commercial strategy, and what conditions must be satisfied before taking action?**

A pricing gap alone does not automatically justify a price increase. A product may be priced below competitors because of market positioning, weak external evidence, execution constraints, or a deliberate share strategy.

The framework therefore connects:

**Commercial opportunity → Execution readiness → Competitive context → Recommended action**

This allows pricing and portfolio decisions to be evaluated using multiple sources of evidence instead of a single metric.

## 3. What was done?

### Pricing Analytics

A transactional pricing dataset containing **4,787 order records** was analysed across business unit, SKU, region, channel, customer tier, list price, net price, discount, quantity, and revenue.

The analysis produced reusable SQL views for:

**Price Realization, Discount Matrix, Price vs PPI, Discount Creep, High Discount Ranking, ASP Movement, and Revenue Pareto Analysis.**

Python was then used for **price elasticity modelling, statistical analysis, scenario analysis, and robustness testing**.

### Product Lifecycle Analytics

Product and initiative performance was analysed using:

**Customer Adoption, Revenue Attainment, On Time Delivery, Backlog, Gross Margin, Execution Score, AOS Health, and Lifecycle Stage.**

These measures were converted into portfolio and execution health indicators.

### Competitive Intelligence

Competitive analysis incorporated:

**Competitor Pricing, Market Share, Industry Growth, and Product to Industry Mapping.**

The analysis calculated competitor price gaps and identified products where pricing opportunity existed but required validation against execution and market evidence.

### Strategic Decision Engine

The three pillars were combined into a **104 row product × region × quarter decision surface**.

Each combination receives:

**Strategic Priority Score → Priority Band → Final PMM Action**

The final model contains **7 PMM action categories** covering growth, protection, execution, pricing, profitability, and monitoring decisions.

## 4. How was it done?

The project separates data ingestion, analytical processing, business logic, decision rules, and visualization.

### Technology Stack

**Python**

Used for data generation, ingestion, validation, segmentation, statistical modelling, scenario analysis, robustness testing, and final analytical exports.

**PostgreSQL**

Used as the central analytical layer for joins, aggregations, window functions, ranking logic, reusable business rules, and cross pillar views.

**SQL**

Used to create reusable analytical views for pricing, product lifecycle, competitive intelligence, and the strategic decision layer.

**Power BI**

Used as the executive presentation layer for KPI tracking, filtering, product family comparisons, pricing analysis, competitive benchmarking, priority analysis, and recommended PMM actions.

### End to End Architecture

```text
Source Data
    ↓
Python ETL and Validation
    ↓
PostgreSQL Source Tables
    ↓
SQL Analytical Views
    ↓
Pricing Analytics
Product Lifecycle Analytics
Competitive Intelligence
    ↓
Cross Pillar Decision Engine
    ↓
Priority Score + PMM Action
    ↓
Power BI Executive Dashboard
