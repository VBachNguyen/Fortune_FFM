import warnings
warnings.filterwarnings("ignore")

from typing import Dict, Any, Tuple
import pandas as pd


BILLION = 1e9


def ttm(df: pd.DataFrame, year: int) -> pd.Series:
    """Cộng 4 quý của 1 năm"""
    num = df[df["yearReport"] == year].select_dtypes(include="number")
    return num.sum()


def latest_q(df: pd.DataFrame, year: int) -> pd.Series:
    """Lấy kỳ mới nhất của năm cho balance sheet"""
    yr_data = df[df["yearReport"] == year].copy()
    if yr_data.empty:
        raise ValueError(f"Không có dữ liệu balance sheet cho năm {year}")
    return yr_data.iloc[0]


def fetch_financial_data(ticker: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    from vnstock import Vnstock

    stock = Vnstock().stock(symbol=ticker.upper().strip(), source="TCBS")
    iq = stock.finance.income_statement(period="quarter", lang="en")
    bq = stock.finance.balance_sheet(period="quarter", lang="en")
    cq = stock.finance.cash_flow(period="quarter", lang="en")

    if iq.empty or bq.empty or cq.empty:
        raise ValueError(f"Không kéo được dữ liệu cho mã {ticker}")

    return iq, bq, cq


def extract_year_data(iq: pd.DataFrame, bq: pd.DataFrame, cq: pd.DataFrame, year: int) -> Dict[str, float]:
    li = ttm(iq, year)
    lb = latest_q(bq, year)
    lc = ttm(cq, year)

    nr = li.get("Net Sales", 0) / BILLION
    gp = li.get("Gross Profit", 0) / BILLION
    cos = abs(li.get("Cost of Sales", 0)) / BILLION
    se = abs(li.get("Selling Expenses", 0)) / BILLION
    ae = abs(li.get("General & Admin Expenses", 0)) / BILLION
    ebit = li.get("Operating Profit/Loss", 0) / BILLION
    ie = abs(li.get("Interest Expenses", 0)) / BILLION
    lnst = li.get("Net Profit For the Year", 0) / BILLION

    dep = lc.get("Depreciation and Amortisation", 0) / BILLION
    ebitda = ebit + dep
    cfo = lc.get("Net cash inflows/outflows from operating activities", 0) / BILLION
    capex = abs(lc.get("Purchase of fixed assets", 0)) / BILLION

    ta = lb.get("TOTAL ASSETS (Bn. VND)", 0) / BILLION
    ca = lb.get("CURRENT ASSETS (Bn. VND)", 0) / BILLION
    cash = lb.get("Cash and cash equivalents (Bn. VND)", 0) / BILLION
    si = lb.get("Short-term investments (Bn. VND)", 0) / BILLION
    cl = lb.get("Current liabilities (Bn. VND)", 0) / BILLION
    eq = lb.get("OWNER'S EQUITY(Bn.VND)", 0) / BILLION
    stb = lb.get("Short-term borrowings (Bn. VND)", 0) / BILLION
    ltb = lb.get("Long-term borrowings (Bn. VND)", 0) / BILLION
    td = stb + ltb
    rec = lb.get("Accounts receivable (Bn. VND)", 0) / BILLION
    inv = lb.get("Net Inventories", 0) / BILLION
    pay = cl - stb

    dso = (rec / nr) * 365 if nr else 0
    dio = (inv / cos) * 365 if cos else 0
    dpo = (pay / cos) * 365 if cos else 0

    return {
        "year": year,
        "net_revenue": nr,
        "gross_profit": gp,
        "cost_of_sales": cos,
        "selling_exp": se,
        "admin_exp": ae,
        "ebit": ebit,
        "ebitda": ebitda,
        "nopat": ebit * 0.8,
        "lnst": lnst,
        "cfo": cfo,
        "capex": capex,
        "total_assets": ta,
        "current_assets": ca,
        "total_cash": cash + si,
        "current_liab": cl,
        "equity": eq,
        "total_debt": td,
        "st_borrowings": stb,
        "invested_capital": eq + td,
        "interest_exp": ie,
        "total_fixed_cost": se + ae,
        "total_variable_cost": cos,
        "dso": dso,
        "dio": dio,
        "dpo": dpo,
        "depreciation": dep,
    }


def calc_kpis(d: Dict[str, float], dp: Dict[str, float]) -> Dict[str, float]:
    nr = d["net_revenue"]
    nrp = dp["net_revenue"] if dp else 0
    fc = d["total_fixed_cost"]
    vc = d["total_variable_cost"]
    cm = nr - vc

    return {
        "ROIC": d["nopat"] / d["invested_capital"] if d["invested_capital"] else 0,
        "Gross Margin": d["gross_profit"] / nr if nr else 0,
        "CCQ": d["cfo"] / d["ebitda"] if d["ebitda"] else 0,
        "CCC": d["dso"] + d["dio"] - d["dpo"],
        "Rev Growth": (nr - nrp) / nrp if nrp else 0,
        "EBITDA Margin": d["ebitda"] / nr if nr else 0,
        "Net Debt/EBITDA": (d["total_debt"] - d["total_cash"]) / d["ebitda"] if d["ebitda"] else 0,
        "Fixed Cost Cov": d["ebit"] / fc if fc else 0,
        "Reinvest Rate": d["capex"] / d["nopat"] if d["nopat"] else 0,
        "Op Leverage": fc / (fc + vc) if (fc + vc) else 0,
        "Margin Safety": 1 - (fc / cm) if cm > 0 else 0,
        "CMR": cm / nr if nr else 0,
        "DSCR": d["ebitda"] / (d["interest_exp"] + d["st_borrowings"]) if (d["interest_exp"] + d["st_borrowings"]) else 0,
        "Current Ratio": d["current_assets"] / d["current_liab"] if d["current_liab"] else 0,
        "Collateral Cov": d["total_assets"] / d["total_debt"] if d["total_debt"] else 0,
    }


def build_pl_table(d1: Dict[str, float], d2: Dict[str, float], y1: int, y2: int) -> pd.DataFrame:
    rows = []
    items = [
        ("Doanh thu thuần", "net_revenue"),
        ("Lợi nhuận gộp", "gross_profit"),
        ("EBIT", "ebit"),
        ("EBITDA", "ebitda"),
        ("LNST", "lnst"),
        ("CFO", "cfo"),
        ("Tổng tài sản", "total_assets"),
        ("VCSH", "equity"),
        ("Tổng nợ vay", "total_debt"),
        ("Tiền & ĐT ngắn hạn", "total_cash"),
    ]

    for label, key in items:
        v1 = d1.get(key, 0)
        v2 = d2.get(key, 0)
        yoy = (v2 - v1) / abs(v1) if v1 else None
        rows.append({
            "Khoản mục": label,
            str(y1): v1,
            str(y2): v2,
            "YoY": yoy
        })

    return pd.DataFrame(rows)


def run_analysis(ticker: str) -> Dict[str, Any]:
    iq, bq, cq = fetch_financial_data(ticker)

    latest_years = sorted(iq["yearReport"].dropna().unique())[-2:]
    if len(latest_years) < 2:
        raise ValueError(f"Không đủ 2 năm dữ liệu cho mã {ticker}")

    y1, y2 = int(latest_years[0]), int(latest_years[1])

    d1 = extract_year_data(iq, bq, cq, y1)
    d2 = extract_year_data(iq, bq, cq, y2)

    k1 = calc_kpis(d1, d1)
    k2 = calc_kpis(d2, d1)

    pl_df = build_pl_table(d1, d2, y1, y2)

    return {
        "ticker": ticker.upper().strip(),
        "years": (y1, y2),
        "raw": {"income_q": iq, "balance_q": bq, "cashflow_q": cq},
        "year_data": {y1: d1, y2: d2},
        "kpis": {y1: k1, y2: k2},
        "pl_table": pl_df,
    }
