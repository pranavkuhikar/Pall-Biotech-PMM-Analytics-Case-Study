
import pandas as pd
import numpy as np
from pathlib import Path

np.random.seed(42)

OUT_DIR = Path(__file__).resolve().parent.parent / "Data"
OUT_DIR.mkdir(parents=True, exist_ok=True)

business_units = {
    "Biopharma Consumables":25,
    "Medical":20,
    "Industrial":20,
    "Food & Beverage":15
}

product_families = {
    "Biopharma Consumables":["Kleenpak","Pegasus","Cadence"],
    "Medical":["IV Filters","Sterile Sets","Diagnostics"],
    "Industrial":["Membranes","Cartridges","Gas Filters"],
    "Food & Beverage":["Beer","Wine","Dairy"]
}

owners=[f"PMM_{i:02d}" for i in range(1,21)]
regions=["North America","EMEA","APAC"]
quarters=pd.period_range("2024Q1","2025Q4",freq="Q")

months={1:["M1","M2","M3"],2:["M1","M2","M3"],3:["M1","M2","M3"],4:["M1","M2","M3"]}

rows=[]
init_no=1

for bu,n in business_units.items():
    fams=product_families[bu]
    for i in range(n):
        init=f"INIT-{init_no:04d}"
        family=np.random.choice(fams)
        region=np.random.choice(regions,p=[0.4,0.3,0.3])
        owner=np.random.choice(owners)
        priority=np.random.choice(["High","Medium","Low"],p=[0.3,0.5,0.2])
        stage=np.random.choice(["Launch","Growth","Mature","Decline"],p=[0.25,0.35,0.30,0.10])
        base=np.random.uniform(3e5,9e5)

        for q in quarters:
            q_growth={"Launch":1.08,"Growth":1.15,"Mature":1.02,"Decline":0.95}[stage]
            base*=q_growth*np.random.uniform(0.97,1.03)

            for m in ["Month1","Month2","Month3"]:
                planned=base/3*np.random.uniform(0.95,1.05)

                if stage=="Launch":
                    otd=np.random.uniform(82,93)
                    backlog=np.random.randint(20,70)
                    rev_factor=np.random.uniform(0.82,0.96)
                elif stage=="Growth":
                    otd=np.random.uniform(90,97)
                    backlog=np.random.randint(8,35)
                    rev_factor=np.random.uniform(0.95,1.08)
                elif stage=="Mature":
                    otd=np.random.uniform(95,99)
                    backlog=np.random.randint(0,12)
                    rev_factor=np.random.uniform(0.98,1.04)
                else:
                    otd=np.random.uniform(85,94)
                    backlog=np.random.randint(15,45)
                    rev_factor=np.random.uniform(0.80,0.95)

                if region=="APAC":
                    backlog+=np.random.randint(5,15)
                    otd-=np.random.uniform(1,3)
                elif region=="North America":
                    otd+=np.random.uniform(0.5,2)

                actual=planned*rev_factor
                adoption=np.clip(np.random.normal(78 if stage!="Launch" else 55,10),20,100)
                margin=np.clip(np.random.normal(
                    {"Medical":42,"Biopharma Consumables":38,"Industrial":30,"Food & Beverage":28}[bu],3),15,60)
                budget=np.clip(np.random.normal(92,8),60,110)

                score=(actual/planned)*0.5+(otd/95)*0.3+(1-min(backlog,90)/90)*0.2
                risk="Low" if score>=0.9 else "Medium" if score>=0.75 else "High"

                rows.append({
                    "initiative_id":init,
                    "initiative_name":f"{family} Initiative {i+1}",
                    "business_unit":bu,
                    "product_family":family,
                    "region":region,
                    "owner":owner,
                    "priority":priority,
                    "lifecycle_stage":stage,
                    "quarter":str(q),
                    "checkpoint":m,
                    "planned_revenue":round(planned,2),
                    "actual_revenue":round(actual,2),
                    "planned_otd_pct":95,
                    "actual_otd_pct":round(otd,1),
                    "backlog_days":backlog,
                    "customer_adoption_pct":round(adoption,1),
                    "gross_margin_pct":round(margin,1),
                    "budget_utilization_pct":round(budget,1),
                    "risk_level":risk
                })
        init_no+=1

df=pd.DataFrame(rows)
outfile=OUT_DIR/"initiatives.csv"
df.to_csv(outfile,index=False)

print(f"Rows generated: {len(df):,}")
print(f"Unique initiatives: {df['initiative_id'].nunique()}")
print(f"Saved to: {outfile}")
