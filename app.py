import streamlit as st
import pandas as pd
import warnings
warnings.filterwarnings("ignore")
from core import run_analysis

st.set_page_config(page_title="Fortune FFM",page_icon="",layout="wide")

def score_high(x,g,w):
    if x is None or pd.isna(x): return "---",0.0
    if x>=g: return "Tot",1.0
    if x>=w: return "Chu y",0.5
    return "Nguy hiem",0.0

def score_low(x,g,w):
    if x is None or pd.isna(x): return "---",0.0
    if x<=g: return "Tot",1.0
    if x<=w: return "Chu y",0.5
    return "Nguy hiem",0.0

def score_range(x,gl,gh,wh):
    if x is None or pd.isna(x): return "---",0.0
    if gl<=x<=gh: return "Tot",1.0
    if x<gl or x<=wh: return "Chu y",0.5
    return "Nguy hiem",0.0

KPI_CONFIG = [
    (1,"ROIC","NOPAT / Invested Capital","ROIC","%","high",0.15,0.08),
    (2,"Gross Margin","Gross Profit / Net Revenue","Gross Margin","%","high",0.35,0.20),
    (3,"CCQ","CFO / EBITDA","CCQ","x","high",0.85,0.60),
    (4,"CCC","DSO + DIO - DPO","CCC","ngay","low",45,90),
    (5,"Revenue Growth YoY","(Rev_n - Rev_n-1) / Rev_n-1","Rev Growth","%","high",0.15,0.05),
    (6,"EBITDA Margin","EBITDA / Net Revenue","EBITDA Margin","%","high",0.15,0.08),
    (7,"Net Debt / EBITDA","(Total Debt - Cash) / EBITDA","Net Debt/EBITDA","x","low",2.0,3.5),
    (8,"Fixed Cost Coverage","EBIT / Total Fixed Cost","Fixed Cost Cov","x","high",2.0,1.2),
    (9,"Customer Concentration","Top-1 Client Rev / Net Rev",None,"%","na",0,0),
    (10,"Reinvestment Rate","(Capex + dWC) / NOPAT","Reinvest Rate","%","range",0.20,0.60),
    (11,"Operating Leverage","FC / (FC + VC)","Op Leverage","%","low",0.40,0.65),
    (12,"Margin of Safety","1 - FC / CM","Margin Safety","%","high",0.25,0.10),
    (13,"CMR","(Rev - VC) / Rev","CMR","%","high",0.40,0.25),
]

M2_CONFIG = [
    (1,"DSCR","EBITDA / Debt Service","DSCR","x","high",1.25,1.00),
    (2,"Current Ratio","CA / CL","Current Ratio","x","high",1.5,1.0),
    (3,"Collateral Coverage","Assets / Debt","Collateral Cov","x","high",1.5,1.0),
]

def build_module(config, kpis_y1, kpis_y2):
    rows = []
    for no,name,formula,kpi_key,unit,rule,g,w in config:
        if kpi_key is None:
            rows.append({"#":no,"KPI":name,"Formula":formula,"Y1":"N/A","Y2":"N/A","Trend":"","Status":"---","Score":None})
            continue
        v1 = kpis_y1.get(kpi_key,0)
        v2 = kpis_y2.get(kpi_key,0)
        if rule=="high": s,sc=score_high(v2,g,w)
        elif rule=="low": s,sc=score_low(v2,g,w)
        elif rule=="range": s,sc=score_range(v2,g,0.60,0.80)
        else: s,sc="---",0.0
        if v2>v1*1.02: tr="up"
        elif v2<v1*0.98: tr="down"
        else: tr="flat"
        rows.append({"#":no,"KPI":name,"Formula":formula,"Y1":v1,"Y2":v2,"Unit":unit,"Trend":tr,"Status":s,"Score":sc})
    df=pd.DataFrame(rows)
    valid=df["Score"].dropna()
    score=valid.mean() if len(valid)>0 else 0
    return df,score

def fmt(val,unit):
    if val is None or pd.isna(val) or val=="N/A": return "N/A"
    if unit=="%": return f"{val*100:.1f}%"
    if unit=="ngay": return f"{val:.0f}"
    return f"{val:.2f}x"

def color_status(s):
    if "Tot" in str(s): return "#059669","#ecfdf5"
    if "Chu y" in str(s): return "#d97706","#fffbeb"
    if "Nguy" in str(s): return "#dc2626","#fef2f2"
    return "#94a3b8","#f1f5f9"

def trend_arrow(t,rule):
    if t=="up": return "<span style='color:#059669'>&#9650;</span>"
    if t=="down": return "<span style='color:#dc2626'>&#9660;</span>"
    return "<span style='color:#94a3b8'>&#8594;</span>"

def render_table(df,title,score,y1,y2):
    if score>=0.7: bc,bb="#059669","#ecfdf5"
    elif score>=0.4: bc,bb="#d97706","#fffbeb"
    else: bc,bb="#dc2626","#fef2f2"
    h=f'<div style="background:white;border:1px solid #e2e8f0;border-radius:12px;overflow:hidden;margin-bottom:24px">'
    h+=f'<div style="padding:14px 20px;border-bottom:1px solid #e2e8f0;display:flex;justify-content:space-between;align-items:center">'
    h+=f'<b style="font-size:15px;color:#1e293b">{title}</b>'
    h+=f'<span style="background:{bb};color:{bc};padding:5px 12px;border-radius:16px;font-size:13px;font-weight:600">Score: {score*100:.0f}%</span></div>'
    h+='<table style="width:100%;border-collapse:collapse;font-size:13px">'
    h+='<tr style="background:#f1f5f9">'
    for col in ["#","KPI","Formula",str(y1),str(y2),"Trend","Status","Score"]:
        al="left" if col in ["KPI","Formula"] else "center"
        h+=f'<th style="padding:10px 12px;text-align:{al};color:#64748b;font-weight:600">{col}</th>'
    h+='</tr>'
    for i,row in df.iterrows():
        bg="white" if i%2==0 else "#f8fafc"
        tc,tb=color_status(row["Status"])
        sv="" if row["Score"] is None or pd.isna(row["Score"]) else f"{row['Score']:.1f}"
        unit=row.get("Unit","%")
        v1s=fmt(row["Y1"],unit)
        v2s=fmt(row["Y2"],unit)
        tr=trend_arrow(row.get("Trend",""),row.get("Status",""))
        h+=f'<tr style="background:{bg}">'
        h+=f'<td style="padding:10px 12px;text-align:center;color:#94a3b8">{row["#"]}</td>'
        h+=f'<td style="padding:10px 12px;font-weight:600;color:#1e293b">{row["KPI"]}</td>'
        h+=f'<td style="padding:10px 12px;color:#64748b;font-size:12px">{row["Formula"]}</td>'
        h+=f'<td style="padding:10px 12px;text-align:center;font-family:monospace;color:#94a3b8">{v1s}</td>'
        h+=f'<td style="padding:10px 12px;text-align:center;font-family:monospace;font-weight:600">{v2s}</td>'
        h+=f'<td style="padding:10px 12px;text-align:center">{tr}</td>'
        h+=f'<td style="padding:10px 12px;text-align:center"><span style="background:{tb};color:{tc};padding:3px 10px;border-radius:10px;font-size:12px;font-weight:600">{row["Status"]}</span></td>'
        h+=f'<td style="padding:10px 12px;text-align:center;font-family:monospace">{sv}</td></tr>'
    h+='</table></div>'
    st.markdown(h,unsafe_allow_html=True)

def render_pl(pl_df,y1,y2):
    h='<div style="background:white;border:1px solid #e2e8f0;border-radius:12px;overflow:hidden;margin-bottom:24px">'
    h+='<div style="padding:14px 20px;border-bottom:1px solid #e2e8f0"><b style="font-size:15px;color:#1e293b">P&L Summary (ty VND)</b></div>'
    h+='<table style="width:100%;border-collapse:collapse;font-size:13px">'
    h+=f'<tr style="background:#f1f5f9"><th style="padding:10px 16px;text-align:left;color:#64748b">Khoan muc</th>'
    h+=f'<th style="padding:10px 12px;text-align:right;color:#64748b">{y1}</th>'
    h+=f'<th style="padding:10px 12px;text-align:right;color:#64748b">{y2}</th>'
    h+=f'<th style="padding:10px 12px;text-align:right;color:#64748b">YoY</th></tr>'
    for i,row in pl_df.iterrows():
        bg="white" if i%2==0 else "#f8fafc"
        v1=row[str(y1)]; v2=row[str(y2)]; yoy=row["YoY"]
        v1s=f"{v1:,.1f}" if pd.notna(v1) else "N/A"
        v2s=f"{v2:,.1f}" if pd.notna(v2) else "N/A"
        if pd.notna(yoy):
            yc="#059669" if yoy>0 else "#dc2626" if yoy<0 else "#94a3b8"
            ys=f"{yoy*100:+.1f}%"
        else:
            yc="#94a3b8"; ys="N/A"
        h+=f'<tr style="background:{bg}">'
        label = row.iloc[0]
        h+=f'<td style="padding:10px 16px;font-weight:500;color:#1e293b">{label}</td>'
        h+=f'<td style="padding:10px 12px;text-align:right;font-family:monospace;color:#94a3b8">{v1s}</td>'
        h+=f'<td style="padding:10px 12px;text-align:right;font-family:monospace;font-weight:600">{v2s}</td>'
        h+=f'<td style="padding:10px 12px;text-align:right;font-family:monospace;color:{yc}">{ys}</td></tr>'
    h+='</table></div>'
    st.markdown(h,unsafe_allow_html=True)

# ============ APP ============
st.markdown("<h1>Fortune Financial Fitness Model</h1>",unsafe_allow_html=True)
st.markdown("<p style='color:#64748b'>Nhap ma co phieu - xem suc khoe tai chinh</p>",unsafe_allow_html=True)

c1,c2,c3=st.columns([1,1,4])
with c1:
    ticker=st.text_input("Ma co phieu",value="VNM").strip().upper()
with c2:
    st.markdown("<br>",unsafe_allow_html=True)
    go=st.button("Phan tich",type="primary")

if go and ticker:
    with st.spinner(f"Dang phan tich {ticker}..."):
        try:
            result=run_analysis(ticker)
            y1,y2=result["years"]
            k1=result["kpis"][y1]
            k2=result["kpis"][y2]
            d1=result["year_data"][y1]
            d2=result["year_data"][y2]

            m1_df,m1_score=build_module(KPI_CONFIG,k1,k2)
            m2_df,m2_score=build_module(M2_CONFIG,k1,k2)

            st.markdown("---")
            a,b,c,d,e=st.columns(5)
            a.metric("Doanh thu",f"{d2['net_revenue']:,.0f} ty",f"{(d2['net_revenue']-d1['net_revenue'])/d1['net_revenue']*100:+.1f}%")
            b.metric("EBITDA",f"{d2['ebitda']:,.0f} ty",f"{(d2['ebitda']-d1['ebitda'])/d1['ebitda']*100:+.1f}%" if d1['ebitda'] else "")
            c.metric("LNST",f"{d2['lnst']:,.0f} ty",f"{(d2['lnst']-d1['lnst'])/d1['lnst']*100:+.1f}%" if d1['lnst'] else "")
            d.metric("M1 Score",f"{m1_score*100:.0f}%")
            e.metric("M2 Score",f"{m2_score*100:.0f}%")

            st.markdown(f"### {ticker} - {y1} vs {y2} (Quarterly TTM)")

            # P&L
            render_pl(result["pl_table"],y1,y2)

            # M1
            render_table(m1_df,"MODULE 1 - CORE HEALTH | 13 KPIs",m1_score,y1,y2)

            # M2
            render_table(m2_df,"MODULE 2 - BANK READINESS | 3 KPIs",m2_score,y1,y2)

            st.caption("Fortune Advisory | Confidential | FFM v6")
        except Exception as ex:
            st.error(f"Loi: {ex}")
