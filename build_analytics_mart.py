from pathlib import Path
import shutil

# ============================================================
# PROJECT ROOT
# ============================================================

ROOT = Path(__file__).resolve().parent.parent

MART = ROOT / "Analytics_mart"

# ============================================================
# CREATE MART STRUCTURE
# ============================================================

PRICING_SCENARIOS = MART / "Pricing" / "Pricing_Scenarios"
PRICING_ROBUSTNESS = MART / "Pricing" / "Robustness"
PRICING_REPORTS = MART / "Pricing" / "Reports"

PLCM_DASHBOARDS = MART / "Product_Lifecycle" / "Dashboards"
PLCM_RISK = MART / "Product_Lifecycle" / "Risk"
PLCM_REPORTS = MART / "Product_Lifecycle" / "Reports"

CI_DASHBOARDS = MART / "Competitive_Intelligence" / "Dashboards"
CI_REPORTS = MART / "Competitive_Intelligence" / "Reports"
CI_BATTLECARDS = MART / "Competitive_Intelligence" / "Battlecards"

for folder in [

    PRICING_SCENARIOS,
    PRICING_ROBUSTNESS,
    PRICING_REPORTS,

    PLCM_DASHBOARDS,
    PLCM_RISK,
    PLCM_REPORTS,

    CI_DASHBOARDS,
    CI_REPORTS,
    CI_BATTLECARDS

]:

    folder.mkdir(parents=True, exist_ok=True)

# ============================================================
# FILE MAP
# ============================================================

FILES = {

# ============================================================
# PRICING SCENARIOS
# ============================================================

ROOT / "1.Pricing/Outputs/pricing_scenarios/overall_pricing_scenarios.csv":
PRICING_SCENARIOS,

ROOT / "1.Pricing/Outputs/pricing_scenarios/business_unit_pricing_scenarios.csv":
PRICING_SCENARIOS,

ROOT / "1.Pricing/Outputs/pricing_scenarios/region_pricing_scenarios.csv":
PRICING_SCENARIOS,

ROOT / "1.Pricing/Outputs/pricing_scenarios/sku_pricing_scenarios.csv":
PRICING_SCENARIOS,

ROOT / "1.Pricing/Outputs/pricing_scenarios/pricing_scenarios.csv":
PRICING_SCENARIOS,

ROOT / "1.Pricing/Outputs/pricing_scenarios/segment_pricing_opportunities.csv":
PRICING_SCENARIOS,

ROOT / "1.Pricing/Outputs/pricing_scenarios/sku_pricing_opportunities.csv":
PRICING_SCENARIOS,

ROOT / "1.Pricing/Outputs/pricing_scenarios/discount_profile.csv":
PRICING_SCENARIOS,

ROOT / "1.Pricing/Outputs/pricing_scenarios/elasticity_sensitivity.csv":
PRICING_SCENARIOS,

# ============================================================
# PRICING REPORTS
# ============================================================

ROOT / "1.Pricing/Outputs/pricing_scenarios/pricing_scenario_summary.txt":
PRICING_REPORTS,

ROOT / "1.Pricing/Outputs/elasticity_summary.txt":
PRICING_REPORTS,

# ============================================================
# ROBUSTNESS
# ============================================================

ROOT / "1.Pricing/Outputs/robustness/robustness_results.csv":
PRICING_ROBUSTNESS,

ROOT / "1.Pricing/Outputs/robustness/robustness_results_summary.csv":
PRICING_ROBUSTNESS,

ROOT / "1.Pricing/Outputs/robustness/robustness_summary.txt":
PRICING_ROBUSTNESS,

# ============================================================
# PRODUCT LIFECYCLE DASHBOARDS
# ============================================================

ROOT / "2.Product_lifecycle/Outputs/dashboards/executive_kpis.csv":
PLCM_DASHBOARDS,

ROOT / "2.Product_lifecycle/Outputs/dashboards/business_unit_dashboard.csv":
PLCM_DASHBOARDS,

ROOT / "2.Product_lifecycle/Outputs/dashboards/region_dashboard.csv":
PLCM_DASHBOARDS,

ROOT / "2.Product_lifecycle/Outputs/dashboards/owner_dashboard.csv":
PLCM_DASHBOARDS,

ROOT / "2.Product_lifecycle/Outputs/dashboards/lifecycle_dashboard.csv":
PLCM_DASHBOARDS,

# ============================================================
# PRODUCT LIFECYCLE RISK
# ============================================================

ROOT / "2.Product_lifecycle/Outputs/Risk/business_unit_risk.csv":
PLCM_RISK,

ROOT / "2.Product_lifecycle/Outputs/Risk/executive_watchlist.csv":
PLCM_RISK,

ROOT / "2.Product_lifecycle/Outputs/Risk/high_risk_initiatives.csv":
PLCM_RISK,

ROOT / "2.Product_lifecycle/Outputs/Risk/owner_performance.csv":
PLCM_RISK,

ROOT / "2.Product_lifecycle/Outputs/Risk/regional_risk.csv":
PLCM_RISK,

# ============================================================
# PRODUCT LIFECYCLE REPORTS
# ============================================================

ROOT / "2.Product_lifecycle/Outputs/Risk/risk_summary.txt":
PLCM_REPORTS

}

# ============================================================
# COPY FILES
# ============================================================

print("="*80)
print("BUILDING ANALYTICS MART")
print("="*80)

copied = 0
missing = 0

for source, destination in FILES.items():

    if source.exists():

        shutil.copy2(source, destination / source.name)

        print(f"✓ {source.name}")

        copied += 1

    else:

        print(f"✗ Missing : {source}")

        missing += 1

print("\n" + "="*80)
print("Analytics Mart Build Complete")
print("="*80)
print(f"Files Copied : {copied}")
print(f"Missing Files: {missing}")
print(f"Location      : {MART}")
print("="*80)