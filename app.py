import os
import json
import time
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import altair as alt
import joblib

st.set_page_config(
    page_title="ذكاء العملاء",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ───────────────────────── الشرائح (من الأفضل إلى الأضعف) ─────────────────────────
SEGMENTS = [
    dict(name="كبار العملاء (VIP)", color="#0B7A75",
         about="يشترون كثيراً، بمبالغ كبيرة، وبشكل حديث.",
         advice="خصّص مدير حساب شخصي وعروضاً حصرية للحفاظ على ولائهم."),
    dict(name="العملاء الأوفياء", color="#3B6FB6",
         about="إنفاقهم جيد وتكرار شرائهم ثابت.",
         advice="أدرجهم في برنامج نقاط تصاعدي واعرض عليهم منتجات مكمّلة."),
    dict(name="عملاء واعدون", color="#D9A441",
         about="اشتروا مؤخراً لكن إنفاقهم ما زال متواضعاً.",
         advice="قدّم حوافز على الطلب التالي لرفع التكرار والإنفاق."),
    dict(name="عملاء معرّضون للخسارة", color="#C2503F",
         about="لم يشتروا منذ فترة طويلة وإنفاقهم قليل.",
         advice="أطلق حملة استعادة مباشرة (رسالة أو خصم محدود المدة)."),
]

# ───────────────────────── التصميم ─────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&display=swap');

:root {
  --ink: #1B2430;
  --muted: #5B6B7A;
  --line: #E3E7EC;
  --surface: #FFFFFF;
  --canvas: #F6F7F9;
  --accent: #0B7A75;
  --ease: cubic-bezier(.2, .8, .2, 1);
}

html, body, .stApp, [data-testid="stSidebar"], button, input, textarea, label, p, span, div {
  font-family: 'IBM Plex Sans Arabic', 'Segoe UI', Tahoma, sans-serif;
}
.stApp { background: var(--canvas); color: var(--ink); direction: rtl; }
[data-testid="stSidebar"] { direction: rtl; border-left: 1px solid var(--line); }
[data-testid="stToolbar"], [data-testid="stDecoration"], footer, #MainMenu { display: none !important; }
[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1240px; }

/* عناصر لازم تبقى يسار→يمين حتى ما تنكسر (السلايدر، الأرقام، الرسوم) */
[data-testid="stSlider"], [data-testid="stSelectSlider"],
[data-testid="stNumberInput"] input, .stVegaLiteChart, [data-testid="stDataFrame"] { direction: ltr; }
[data-testid="stSelectSlider"] label, [data-testid="stSlider"] label { direction: rtl; text-align: right; width: 100%; }

/* البطاقات (الحاويات ذات الإطار) */
[data-testid="stVerticalBlockBorderWrapper"] {
  background: var(--surface);
  border-color: var(--line) !important;
  border-radius: 14px !important;
}

/* ── العنوان ── */
.page-title { font-size: 2rem; font-weight: 700; margin: 0; line-height: 1.3; }
.page-sub { color: var(--muted); margin: .35rem 0 0 0; font-size: 1.02rem; }
.page-head { animation: rise .6s var(--ease) both; }

.section-title { font-weight: 700; font-size: 1.08rem; margin: 2px 0 2px 0; }
.section-note { color: var(--muted); font-size: .92rem; margin-bottom: 6px; }

/* ── شريط توزيع العملاء ── */
.strip-wrap { background: var(--surface); border: 1px solid var(--line); border-radius: 14px; padding: 20px 22px; animation: rise .6s var(--ease) .25s both; }
.strip { display: flex; gap: 4px; height: 38px; }
.strip .part { border-radius: 8px; transform-origin: right center; animation: reveal .9s var(--ease) both; min-width: 6px; }
.legend { display: flex; flex-wrap: wrap; gap: 8px 26px; margin-top: 14px; }
.legend .lg { display: flex; align-items: center; gap: 8px; font-size: .94rem; }
.legend .dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
.legend b { direction: ltr; color: var(--muted); font-weight: 600; }

/* ── أعمدة أفقية متحركة ── */
.brow { display: grid; grid-template-columns: 170px 1fr 112px; align-items: center; gap: 12px; margin: 16px 0; }
.bl { font-size: .94rem; line-height: 1.35; }
.bt { background: #EDF0F3; border-radius: 8px; height: 22px; overflow: hidden; }
.bf { height: 100%; width: var(--w); border-radius: 8px;
      animation: grow .95s var(--ease) both; animation-delay: var(--d); transition: width .5s var(--ease); }
.bv { white-space: nowrap; direction: ltr; text-align: left; font-weight: 600; font-variant-numeric: tabular-nums; }

/* ── بطاقات معنى الشرائح ── */
.seg-card { background: var(--surface); border: 1px solid var(--line); border-right: 4px solid var(--c);
            border-radius: 12px; padding: 14px 16px; height: 100%;
            animation: rise .6s var(--ease) both; animation-delay: var(--d); }
.seg-card .t { color: var(--c); font-weight: 700; margin-bottom: 4px; }
.seg-card .d { font-size: .92rem; color: var(--ink); line-height: 1.6; }

.prof { display:flex; flex-wrap:wrap; gap:10px 28px; margin-top:6px; color:var(--muted); font-size:.95rem; }
.prof b { color:var(--ink); }
.big { font-size:1.6rem; font-weight:700; color:var(--c); direction:ltr; text-align:right; font-variant-numeric:tabular-nums; }
/* ── نتيجة التصنيف ── */
.result { background: var(--surface); border: 1px solid var(--line); border-right: 8px solid var(--seg);
          border-radius: 14px; padding: 22px 26px; margin-top: 16px; animation: slidein .6s var(--ease) both; }
.result .tag { color: var(--muted); font-size: .92rem; }
.result .seg { font-size: 1.7rem; font-weight: 700; color: var(--seg); margin: 2px 0 10px 0; }
.result p { margin: .25rem 0; line-height: 1.7; }

.cmp-title { font-weight: 600; margin-bottom: 6px; }
.cmp-row { margin-bottom: 18px; }
.cmp-line { display: grid; grid-template-columns: 110px 1fr 80px; align-items: center; gap: 10px; margin: 5px 0; font-size: .9rem; }
.cmp-line .who { color: var(--muted); }

/* ── الأزرار والمدخلات ── */
.stButton > button[kind="primary"] {
  background: var(--accent); border: none; border-radius: 10px; padding: .6rem 1.6rem; font-weight: 600;
  transition: transform .2s var(--ease), filter .2s var(--ease);
}
.stButton > button[kind="primary"]:hover { transform: translateY(-2px); filter: brightness(1.08); }
.stButton > button[kind="primary"]:active { transform: translateY(0); }
.stDownloadButton > button { border-radius: 10px; transition: transform .2s var(--ease), border-color .2s; }
.stDownloadButton > button:hover { transform: translateY(-2px); border-color: var(--accent); color: var(--accent); }
[data-testid="stNumberInput"] input { transition: box-shadow .2s; }

/* ── التبويبات ── */
.stTabs [data-baseweb="tab-list"] { gap: 6px; border-bottom: 1px solid var(--line); }
.stTabs [data-baseweb="tab"] { padding: 10px 18px; font-weight: 600; color: var(--muted); background: transparent; transition: color .2s; }
.stTabs [data-baseweb="tab"]:hover { color: var(--ink); }
.stTabs [aria-selected="true"] { color: var(--ink) !important; }
.stTabs [data-baseweb="tab-highlight"] { background-color: var(--accent); height: 3px; transition: all .35s var(--ease); }
.stTabs [data-baseweb="tab-panel"] { padding-top: 1.4rem; animation: fade .45s var(--ease) both; }

/* ── الحركات ── */
@keyframes rise    { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: none; } }
@keyframes slidein { from { opacity: 0; transform: translateX(24px); } to { opacity: 1; transform: none; } }
@keyframes fade    { from { opacity: 0; } to { opacity: 1; } }
@keyframes grow    { from { width: 0; } }
@keyframes reveal  { from { transform: scaleX(0); } to { transform: scaleX(1); } }

@media (prefers-reduced-motion: reduce) {
  * { animation: none !important; transition: none !important; }
}
@media (max-width: 760px) {
  .brow { grid-template-columns: 110px 1fr 70px; }
  .page-title { font-size: 1.5rem; }
}
</style>
""", unsafe_allow_html=True)


# ───────────────────────── مكوّنات HTML ─────────────────────────
KPI_TEMPLATE = """
<html><head><meta charset="utf-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;600;700&display=swap');
html, body { margin: 0; background: transparent; font-family: 'IBM Plex Sans Arabic', Tahoma, sans-serif; direction: rtl; }
.row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; padding: 2px; }
.k { background: #fff; border: 1px solid #E3E7EC; border-right: 4px solid #0B7A75; border-radius: 12px;
     padding: 16px 18px; opacity: 0; transform: translateY(12px);
     animation: in .6s cubic-bezier(.2,.8,.2,1) forwards; }
.l { color: #5B6B7A; font-size: 14px; }
.v { color: #1B2430; font-size: 28px; font-weight: 700; margin-top: 6px; direction: ltr; text-align: right;
     font-variant-numeric: tabular-nums; }
@keyframes in { to { opacity: 1; transform: none; } }
@media (max-width: 640px) { .row { grid-template-columns: repeat(2, 1fr); } }
@media (prefers-reduced-motion: reduce) { .k { animation: none; opacity: 1; transform: none; } }
</style></head>
<body><div class="row">__CARDS__</div>
<script>
const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
document.querySelectorAll('.v').forEach(el => {
  const end = parseFloat(el.dataset.v), dec = parseInt(el.dataset.d), pre = el.dataset.p || '';
  const fmt = n => pre + n.toLocaleString('en-US', {minimumFractionDigits: dec, maximumFractionDigits: dec});
  if (reduce) { el.textContent = fmt(end); return; }
  const delay = parseInt(el.dataset.delay), dur = 1100;
  setTimeout(() => {
    const t0 = performance.now();
    (function step(t) {
      const p = Math.min((t - t0) / dur, 1), e = 1 - Math.pow(1 - p, 3);
      el.textContent = fmt(end * e);
      if (p < 1) requestAnimationFrame(step);
    })(t0);
  }, delay);
});
</script></body></html>
"""


def kpi_row(items):
    cards = ""
    for i, (label, val, pre, dec) in enumerate(items):
        cards += (
            f'<div class="k" style="animation-delay:{i * 100}ms">'
            f'<div class="l">{label}</div>'
            f'<div class="v" data-v="{val}" data-d="{dec}" data-p="{pre}" data-delay="{i * 100}">{pre}0</div></div>'
        )
    components.html(KPI_TEMPLATE.replace("__CARDS__", cards), height=118)


def share_strip(df):
    counts = df.groupby("Segment").size()
    total = int(counts.sum())
    parts, legend = "", ""
    for i, s in enumerate(SEGMENTS):
        n = int(counts.get(s["name"], 0))
        if n == 0:
            continue
        pct = n / total * 100
        parts += (f'<div class="part" title="{s["name"]}: {n:,}" '
                  f'style="flex:{n};background:{s["color"]};animation-delay:{i * 130}ms"></div>')
        legend += (f'<div class="lg"><span class="dot" style="background:{s["color"]}"></span>'
                   f'{s["name"]} <b>{pct:.0f}%</b></div>')
    return (f'<div class="strip-wrap"><div class="section-title">من هم عملاؤك؟</div>'
            f'<div class="section-note">نسبة كل شريحة من إجمالي العملاء.</div>'
            f'<div class="strip">{parts}</div><div class="legend">{legend}</div></div>')


def bars(values, fmt):
    mx = max(values.values()) or 1
    rows = ""
    for i, s in enumerate(SEGMENTS):
        if s["name"] not in values:
            continue
        v = values[s["name"]]
        w = max(v / mx * 100, 1.5)
        rows += (f'<div class="brow"><div class="bl">{s["name"]}</div>'
                 f'<div class="bt"><div class="bf" style="--w:{w:.1f}%;--d:{i * 120}ms;background:{s["color"]}"></div></div>'
                 f'<div class="bv">{fmt(v)}</div></div>')
    return rows


def compare_block(rows, color):
    out = ""
    for i, (label, mine, avg, fmt) in enumerate(rows):
        mx = max(mine, avg, 1)
        out += (
            f'<div class="cmp-row"><div class="cmp-title">{label}</div>'
            f'<div class="cmp-line"><span class="who">هذا العميل</span>'
            f'<div class="bt"><div class="bf" style="--w:{max(mine / mx * 100, 1.5):.1f}%;--d:{i * 150}ms;background:{color}"></div></div>'
            f'<span class="bv">{fmt(mine)}</span></div>'
            f'<div class="cmp-line"><span class="who">متوسط الشريحة</span>'
            f'<div class="bt"><div class="bf" style="--w:{max(avg / mx * 100, 1.5):.1f}%;--d:{i * 150 + 80}ms;background:#B8C2CC"></div></div>'
            f'<span class="bv">{fmt(avg)}</span></div></div>'
        )
    return out


def style_chart(ch):
    return (ch.configure(background="#FFFFFF", font="IBM Plex Sans Arabic")
              .configure_view(strokeWidth=0)
              .configure_axis(gridColor="#EDF0F3", domainColor="#D5DBE1", labelColor="#5B6B7A",
                              titleColor="#5B6B7A", labelFontSize=12, titleFontSize=12, titleFontWeight=500)
              .configure_legend(labelColor="#1B2430", labelFontSize=13, symbolSize=120))


def build_report(df):
    g = df.groupby("Segment").agg(n=("CustomerID", "count"), rev=("Monetary", "sum"), r=("Recency", "mean"),
                                  f=("Frequency", "mean"), m=("Monetary", "mean"))
    rows = ""
    for sg in SEGMENTS:
        if sg["name"] in g.index:
            x = g.loc[sg["name"]]
            rows += (f'<tr><td style="color:{sg["color"]};font-weight:700">{sg["name"]}</td><td>{int(x.n):,}</td>'
                     f'<td>${x.rev:,.0f}</td><td>{x.r:.0f}</td><td>{x.f:.1f}</td><td>${x.m:,.0f}</td><td>{sg["advice"]}</td></tr>')
    ins = "".join(f"<li><b>{t}:</b> {d}</li>" for _, t, d in smart_insights(df))
    return f"""<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><title>تقرير العملاء</title>
<style>
body{{font-family:'Segoe UI',Tahoma,sans-serif;max-width:960px;margin:30px auto;padding:0 20px;color:#1B2430;line-height:1.7}}
h1{{margin-bottom:0}} .sub{{color:#5B6B7A;margin-top:4px}}
.kpis{{display:flex;gap:14px;margin:22px 0}} .kpis div{{flex:1;border:1px solid #E3E7EC;border-right:4px solid #0B7A75;border-radius:10px;padding:12px 16px}}
.kpis b{{display:block;font-size:1.5rem;direction:ltr;text-align:right}}
table{{width:100%;border-collapse:collapse;font-size:.92rem}} th,td{{border-bottom:1px solid #E3E7EC;padding:9px 8px;text-align:right}}
th{{color:#5B6B7A;font-weight:600}} button{{padding:8px 18px;border-radius:8px;border:0;background:#0B7A75;color:#fff;font-size:1rem;cursor:pointer}}
@media print{{button{{display:none}}}}
</style></head><body>
<h1>تقرير تحليل العملاء</h1><p class="sub">تقسيم العملاء حسب آخر شراء وتكرار الشراء وحجم الإنفاق</p>
<button onclick="window.print()">طباعة / حفظ PDF</button>
<div class="kpis"><div>عدد العملاء<b>{len(df):,}</b></div><div>إجمالي الإيرادات<b>${df['Monetary'].sum():,.0f}</b></div>
<div>متوسط إنفاق العميل<b>${df['Monetary'].mean():,.0f}</b></div></div>
<h3>أهم الرؤى</h3><ul>{ins}</ul>
<h3>ملخص الشرائح</h3>
<table><tr><th>الشريحة</th><th>العملاء</th><th>الإيرادات</th><th>أيام منذ آخر شراء</th><th>متوسط الطلبات</th><th>متوسط الإنفاق</th><th>الإجراء المقترح</th></tr>{rows}</table>
</body></html>"""


# ───────────────────────── تحميل البيانات والنموذج ─────────────────────────
@st.cache_data
def load_data():
    return pd.read_csv("data/rfm_clustered.csv")


@st.cache_resource
def load_models():
    return joblib.load("models/kmeans_model.pkl"), joblib.load("models/scaler.pkl")


try:
    rfm_df = load_data().copy()
    kmeans, scaler = load_models()
except Exception as e:
    st.error(f"تعذّر تحميل الملفات: {e}\n\nتأكد أن مجلدي data و models موجودان بجانب app.py.")
    st.stop()

if scaler.mean_[2] > 20:
    st.error("النموذج المحفوظ قديم (مُدرَّب بدون تحويل log). شغّل `python cluster_model.py` مرة واحدة ثم أعد تشغيل التطبيق.")
    st.stop()

@st.cache_data
def load_extra(name):
    path = f"data/{name}.csv"
    return pd.read_csv(path) if os.path.exists(path) else None


@st.cache_data
def load_metrics():
    path = "data/model_metrics.json"
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ترتيب الشرائح تلقائياً: (تكرار + إنفاق) − حداثة
centers = kmeans.cluster_centers_
score = -centers[:, 0] + centers[:, 1] + centers[:, 2]
order = np.argsort(-score)
cluster_to_seg = {int(c): SEGMENTS[i] for i, c in enumerate(order)}

rfm_df["Segment"] = rfm_df["Cluster"].map(lambda c: cluster_to_seg[int(c)]["name"])
color_scale = alt.Scale(domain=[s["name"] for s in SEGMENTS], range=[s["color"] for s in SEGMENTS])

# ───────────────────────── الشريط الجانبي ─────────────────────────
st.sidebar.markdown("### تصفية العملاء")
selected = st.sidebar.multiselect(
    "الشرائح",
    options=[s["name"] for s in SEGMENTS],
    default=[s["name"] for s in SEGMENTS],
)

max_int = int(np.ceil(rfm_df["Monetary"].max()))
RANGES = {
    "كل العملاء": (0, max_int),
    "أقل من $500": (0, 500),
    "من $500 إلى $2,000": (500, 2000),
    "من $2,000 إلى $10,000": (2000, 10000),
    "أكثر من $10,000": (10000, max_int),
}
choice = st.sidebar.radio("نطاق الإنفاق", list(RANGES))
lo, hi = RANGES[choice]

filtered = rfm_df[
    rfm_df["Segment"].isin(selected) & rfm_df["Monetary"].between(lo, hi)
]

# ───────────────────────── العنوان ─────────────────────────
st.markdown(
    '<div class="page-head"><p class="page-title">لوحة تحليل العملاء</p>'
    '<p class="page-sub">تقسيم العملاء حسب آخر شراء، وتكرار الشراء، وحجم الإنفاق.</p></div>',
    unsafe_allow_html=True,
)
st.write("")

if filtered.empty:
    st.warning("لا يوجد عملاء ضمن هذه التصفية. وسّع نطاق الإنفاق أو اختر شرائح أخرى من الشريط الجانبي.")
    st.stop()

kpi_row([
    ("عدد العملاء", len(filtered), "", 0),
    ("إجمالي الإيرادات", round(filtered["Monetary"].sum(), 0), "$", 0),
    ("متوسط إنفاق العميل", round(filtered["Monetary"].mean(), 0), "$", 0),
    ("متوسط عدد الطلبات", round(filtered["Frequency"].mean(), 1), "", 1),
])
st.markdown(share_strip(filtered), unsafe_allow_html=True)
st.write("")


def smart_insights(df):
    out = []
    ranked = df.sort_values("Monetary", ascending=False)
    top_n = max(1, int(len(ranked) * 0.2))
    share = ranked.head(top_n)["Monetary"].sum() / ranked["Monetary"].sum() * 100
    out.append((SEGMENTS[1]["color"], "تركّز الإيرادات", f"أعلى 20% من العملاء ({top_n:,} عميل) يحققون {share:.0f}% من الإيرادات."))
    vip = df[df["Segment"] == SEGMENTS[0]["name"]]
    if len(vip):
        out.append((SEGMENTS[0]["color"], "كبار العملاء",
                    f"يمثلون {len(vip) / len(df) * 100:.0f}% من العملاء ويحققون {vip['Monetary'].sum() / df['Monetary'].sum() * 100:.0f}% من الإيرادات."))
    risk = df[df["Segment"] == SEGMENTS[3]["name"]]
    if len(risk):
        out.append((SEGMENTS[3]["color"], "إيرادات في خطر",
                    f"{len(risk):,} عميل معرّض للخسارة أنفقوا سابقاً ${risk['Monetary'].sum():,.0f}. ابدأ بحملة استعادة."))
    return out


ins = smart_insights(filtered)
for i, (col, (c, t, d)) in enumerate(zip(st.columns(len(ins)), ins)):
    col.markdown(f'<div class="seg-card" style="--c:{c};--d:{i * 120}ms"><div class="t">{t}</div><div class="d">{d}</div></div>',
                 unsafe_allow_html=True)
st.write("")

tab1, tab_trend, tab2, tab_find, tab_camp, tab_q, tab3 = st.tabs(
    ["نظرة على الشرائح", "الاتجاهات", "تصنيف عميل جديد", "بحث عن عميل", "حملة تسويقية", "جودة النموذج", "سجل العملاء"])

# ───────────────────────── التبويب 1 ─────────────────────────
with tab1:
    g = filtered.groupby("Segment")
    revenue = g["Monetary"].sum().to_dict()
    counts = g["CustomerID"].count().to_dict()

    a, b = st.columns(2)
    with a:
        with st.container(border=True):
            st.markdown('<div class="section-title">الإيرادات لكل شريحة</div>', unsafe_allow_html=True)
            st.markdown(bars(revenue, lambda v: f"${v:,.0f}"), unsafe_allow_html=True)
    with b:
        with st.container(border=True):
            st.markdown('<div class="section-title">عدد العملاء لكل شريحة</div>', unsafe_allow_html=True)
            st.markdown(bars(counts, lambda v: f"{v:,.0f}"), unsafe_allow_html=True)

    st.write("")
    with st.container(border=True):
        st.markdown('<div class="section-title">كل عميل على الخريطة</div>'
                    '<div class="section-note">كل نقطة عميل. كلما اتجهت النقطة لأعلى اليمين زاد تكرار شرائه وإنفاقه.</div>',
                    unsafe_allow_html=True)
        sample = filtered.sample(min(len(filtered), 1500), random_state=1)
        scatter = (
            alt.Chart(sample)
            .mark_circle(size=46, opacity=0.65)
            .encode(
                x=alt.X("Frequency:Q", scale=alt.Scale(type="log"), title="عدد الطلبات (مقياس لوغاريتمي)"),
                y=alt.Y("Monetary:Q", scale=alt.Scale(type="log"), title="إجمالي الإنفاق ($)"),
                color=alt.Color("Segment:N", scale=color_scale, legend=alt.Legend(title=None, orient="bottom")),
                tooltip=[
                    alt.Tooltip("CustomerID:N", title="العميل"),
                    alt.Tooltip("Segment:N", title="الشريحة"),
                    alt.Tooltip("Recency:Q", title="أيام منذ آخر شراء"),
                    alt.Tooltip("Frequency:Q", title="الطلبات"),
                    alt.Tooltip("Monetary:Q", title="الإنفاق", format=",.0f"),
                ],
            )
            .properties(height=380)
            .configure(background="#FFFFFF", font="IBM Plex Sans Arabic")
            .configure_view(strokeWidth=0)
            .configure_axis(gridColor="#EDF0F3", domainColor="#D5DBE1", labelColor="#5B6B7A",
                            titleColor="#5B6B7A", labelFontSize=12, titleFontSize=12, titleFontWeight=500)
            .configure_legend(labelColor="#1B2430", labelFontSize=13, symbolSize=120)
        )
        st.altair_chart(scatter, use_container_width=True, theme=None)

    st.write("")
    with st.container(border=True):
        st.markdown('<div class="section-title">منحنى توزيع الإيرادات (قاعدة 80/20)</div>'
                    '<div class="section-note">كم نسبة من العملاء تحقق معظم الإيرادات؟ كلما كان المنحنى أكثر انحناءً زاد التركّز.</div>',
                    unsafe_allow_html=True)
        ps = filtered["Monetary"].sort_values(ascending=False).reset_index(drop=True)
        par = pd.DataFrame({"cust": (np.arange(1, len(ps) + 1) / len(ps)) * 100, "rev": ps.cumsum() / ps.sum() * 100})
        pct80 = par.loc[(par["rev"] >= 80).idxmax(), "cust"]
        area = alt.Chart(par).mark_area(color="#0B7A75", opacity=0.22, line={"color": "#0B7A75", "strokeWidth": 2.5}).encode(
            x=alt.X("cust:Q", title="نسبة العملاء (%)", scale=alt.Scale(domain=[0, 100])),
            y=alt.Y("rev:Q", title="نسبة الإيرادات التراكمية (%)", scale=alt.Scale(domain=[0, 100])),
            tooltip=[alt.Tooltip("cust:Q", title="العملاء %", format=".0f"), alt.Tooltip("rev:Q", title="الإيرادات %", format=".0f")])
        rule = alt.Chart(pd.DataFrame({"y": [80]})).mark_rule(strokeDash=[5, 4], color="#C2503F").encode(y="y:Q")
        st.altair_chart(style_chart((area + rule).properties(height=300)), use_container_width=True, theme=None)
        st.caption(f"أعلى {pct80:.0f}% من العملاء يحققون 80% من الإيرادات.")

    st.write("")
    st.markdown('<div class="section-title">ملخص كل شريحة</div>', unsafe_allow_html=True)
    seg_order = [s["name"] for s in SEGMENTS if s["name"] in counts]
    table = g.agg(
        العملاء=("CustomerID", "count"),
        الإيرادات=("Monetary", "sum"),
        الحداثة=("Recency", "mean"),
        التكرار=("Frequency", "mean"),
        الإنفاق=("Monetary", "mean"),
    ).loc[seg_order]
    table.index.name = "الشريحة"
    st.dataframe(
        table,
        use_container_width=True,
        column_config={
            "العملاء": st.column_config.NumberColumn(format="%d"),
            "الإيرادات": st.column_config.NumberColumn(format="$%.0f"),
            "الحداثة": st.column_config.NumberColumn("أيام منذ آخر شراء", format="%.0f"),
            "التكرار": st.column_config.NumberColumn("متوسط الطلبات", format="%.1f"),
            "الإنفاق": st.column_config.NumberColumn("متوسط الإنفاق", format="$%.0f"),
        },
    )

    st.write("")
    st.markdown('<div class="section-title">ماذا يعني كل تصنيف؟</div>', unsafe_allow_html=True)
    cols = st.columns(4)
    for i, (col, s) in enumerate(zip(cols, SEGMENTS)):
        col.markdown(
            f'<div class="seg-card" style="--c:{s["color"]};--d:{i * 110}ms">'
            f'<div class="t">{s["name"]}</div><div class="d">{s["about"]}</div></div>',
            unsafe_allow_html=True,
        )

# ───────────────────────── التبويب 2 ─────────────────────────
with tab2:
    with st.container(border=True):
        st.markdown('<div class="section-title">أدخل بيانات العميل</div>', unsafe_allow_html=True)
        i1, i2, i3 = st.columns(3)
        r_val = i1.number_input("أيام منذ آخر شراء", 0, 2000, 10)
        f_val = i2.number_input("عدد الطلبات", 1, 10000, 15)
        m_val = i3.number_input("إجمالي الإنفاق ($)", 1.0, 1000000.0, 2000.0)
        go = st.button("صنّف العميل", type="primary")

    if go:
        with st.spinner("جاري تحليل العميل..."):
            time.sleep(0.5)
            x = np.log1p(np.array([[r_val, f_val, m_val]]))
            seg = cluster_to_seg[int(kmeans.predict(scaler.transform(x))[0])]

        st.markdown(
            f'<div class="result" style="--seg:{seg["color"]}">'
            f'<div class="tag">هذا العميل ينتمي إلى</div>'
            f'<div class="seg">{seg["name"]}</div>'
            f'<p>{seg["about"]}</p>'
            f'<p><b>الإجراء المقترح:</b> {seg["advice"]}</p></div>',
            unsafe_allow_html=True,
        )

        avg = rfm_df[rfm_df["Segment"] == seg["name"]][["Recency", "Frequency", "Monetary"]].mean()
        st.write("")
        with st.container(border=True):
            st.markdown('<div class="section-title">مقارنة مع متوسط الشريحة</div>', unsafe_allow_html=True)
            st.markdown(compare_block([
                ("أيام منذ آخر شراء", r_val, avg["Recency"], lambda v: f"{v:,.0f}"),
                ("عدد الطلبات", f_val, avg["Frequency"], lambda v: f"{v:,.0f}"),
                ("إجمالي الإنفاق", m_val, avg["Monetary"], lambda v: f"${v:,.0f}"),
            ], seg["color"]), unsafe_allow_html=True)

    st.write("")
    with st.container(border=True):
        st.markdown('<div class="section-title">تصنيف مجموعة عملاء دفعة واحدة</div>'
                    '<div class="section-note">ارفع ملف CSV فيه الأعمدة Recency و Frequency و Monetary وسنصنّف كل صف.</div>',
                    unsafe_allow_html=True)
        up = st.file_uploader("ملف العملاء", type="csv", label_visibility="collapsed")
        if up is not None:
            new = pd.read_csv(up)
            need = ["Recency", "Frequency", "Monetary"]
            if not set(need) <= set(new.columns):
                st.error("الملف لازم يحتوي الأعمدة: Recency, Frequency, Monetary.")
            else:
                Xn = np.log1p(new[need].clip(lower=0))
                new["Segment"] = [cluster_to_seg[int(c)]["name"] for c in kmeans.predict(scaler.transform(Xn))]
                st.dataframe(new, use_container_width=True, hide_index=True)
                st.download_button("تنزيل النتيجة (CSV)", new.to_csv(index=False).encode("utf-8-sig"),
                                   "classified_customers.csv", "text/csv")

# ───────────────────────── التبويب 3 ─────────────────────────
with tab3:
    st.markdown('<div class="section-title">سجل العملاء</div>'
                '<div class="section-note">مرتّب من الأعلى إنفاقاً، ويتأثر بالتصفية في الشريط الجانبي.</div>',
                unsafe_allow_html=True)
    log_df = filtered[["CustomerID", "Segment", "Recency", "Frequency", "Monetary"]].copy()
    log_df["CustomerID"] = log_df["CustomerID"].astype(int)
    log_df = log_df.sort_values("Monetary", ascending=False)
    st.dataframe(
        log_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "CustomerID": "رقم العميل",
            "Segment": "الشريحة",
            "Recency": st.column_config.NumberColumn("أيام منذ آخر شراء", format="%d"),
            "Frequency": st.column_config.NumberColumn("عدد الطلبات", format="%d"),
            "Monetary": st.column_config.NumberColumn("الإنفاق", format="$%.0f"),
        },
    )
    st.download_button(
        "تنزيل التقرير (CSV)",
        data=log_df.to_csv(index=False).encode("utf-8-sig"),
        file_name="customer_segments.csv",
        mime="text/csv",
    )
    st.download_button(
        "تنزيل تقرير للإدارة (HTML، افتحه واطبعه PDF)",
        data=build_report(filtered).encode("utf-8"),
        file_name="customer_report.html",
        mime="text/html",
    )


# ───────────────────────── بحث عن عميل ─────────────────────────
with tab_find:
    with st.container(border=True):
        st.markdown('<div class="section-title">ابحث برقم العميل</div>', unsafe_allow_html=True)
        cid_txt = st.text_input("رقم العميل", placeholder="مثال: 12347", label_visibility="collapsed")
    if cid_txt.strip():
        try:
            row = rfm_df[rfm_df["CustomerID"].astype(int) == int(cid_txt)]
        except ValueError:
            row = rfm_df.iloc[0:0]
            st.warning("اكتب رقم العميل بالأرقام فقط.")
        if row.empty:
            st.info("ما لقينا عميل بهذا الرقم.")
        else:
            r = row.iloc[0]
            seg = next(x for x in SEGMENTS if x["name"] == r["Segment"])
            st.markdown(
                f'<div class="result" style="--seg:{seg["color"]}"><div class="tag">العميل رقم {int(r["CustomerID"])}</div>'
                f'<div class="seg">{seg["name"]}</div>'
                f'<div class="prof"><span>آخر شراء قبل <b>{int(r["Recency"])}</b> يوم</span>'
                f'<span><b>{int(r["Frequency"])}</b> طلب</span><span>إنفاق <b>${r["Monetary"]:,.0f}</b></span></div>'
                f'<p><b>الإجراء المقترح:</b> {seg["advice"]}</p></div>', unsafe_allow_html=True)
            st.write("")
            with st.container(border=True):
                st.markdown('<div class="section-title">ترتيبه بين كل العملاء</div>', unsafe_allow_html=True)
                prow = [("حداثة الشراء", (rfm_df["Recency"] >= r["Recency"]).mean() * 100),
                        ("تكرار الشراء", (rfm_df["Frequency"] <= r["Frequency"]).mean() * 100),
                        ("حجم الإنفاق", (rfm_df["Monetary"] <= r["Monetary"]).mean() * 100)]
                html = ""
                for i, (lbl, v) in enumerate(prow):
                    html += (f'<div class="brow"><div class="bl">{lbl}</div><div class="bt"><div class="bf" '
                             f'style="--w:{max(v, 1.5):.1f}%;--d:{i * 130}ms;background:{seg["color"]}"></div></div>'
                             f'<div class="bv">أفضل من {v:.0f}%</div></div>')
                st.markdown(html, unsafe_allow_html=True)

# ───────────────────────── حملة تسويقية ─────────────────────────
with tab_camp:
    with st.container(border=True):
        st.markdown('<div class="section-title">خطّط حملة واحسب العائد المتوقع</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        target_name = c1.selectbox("الشريحة المستهدفة", [x["name"] for x in SEGMENTS], index=3)
        rate = c2.number_input("نسبة الاستجابة المتوقعة (%)", 1, 100, 10, step=1)
    seg = next(x for x in SEGMENTS if x["name"] == target_name)
    tgt = rfm_df[rfm_df["Segment"] == target_name]
    won = len(tgt) * rate / 100
    gain = won * tgt["Monetary"].mean()
    st.write("")
    cols = st.columns(3)
    for i, (col, (t, v)) in enumerate(zip(cols, [("عملاء مستهدفون", f"{len(tgt):,}"),
                                                  ("عملاء متوقع استجابتهم", f"{won:,.0f}"),
                                                  ("إيراد متوقع", f"${gain:,.0f}")])):
        col.markdown(f'<div class="seg-card" style="--c:{seg["color"]};--d:{i * 110}ms"><div class="t">{t}</div>'
                     f'<div class="big">{v}</div></div>', unsafe_allow_html=True)
    st.caption("تقدير تقريبي: نفترض أن كل عميل مستجيب ينفق بمتوسط إنفاق شريحته.")
    st.markdown(f'<p><b>الإجراء المقترح:</b> {seg["advice"]}</p>', unsafe_allow_html=True)
    lst = tgt[["CustomerID", "Segment", "Recency", "Frequency", "Monetary"]].copy()
    lst["CustomerID"] = lst["CustomerID"].astype(int)
    lst["Action"] = seg["advice"]
    st.download_button("تنزيل قائمة المستهدفين (CSV)", lst.sort_values("Monetary", ascending=False)
                       .to_csv(index=False).encode("utf-8-sig"), "campaign_targets.csv", "text/csv")


# ───────────────────────── الاتجاهات ─────────────────────────
with tab_trend:
    tm = load_extra("trends_monthly")
    if tm is None:
        st.info("لتفعيل هذا التبويب شغّل `python cluster_model.py` مرة واحدة لتوليد ملفات الاتجاهات.")
    else:
        tm["Segment"] = tm["Cluster"].map(lambda c: cluster_to_seg[int(c)]["name"])
        tm = tm[tm["Segment"].isin(selected)].copy()
        tm["Date"] = pd.to_datetime(tm["Month"] + "-01")
        with st.container(border=True):
            st.markdown('<div class="section-title">الإيرادات الشهرية حسب الشريحة</div>'
                        '<div class="section-note">يتأثر بالشرائح المختارة في الشريط الجانبي. الشهر الأخير قد يكون غير مكتمل.</div>',
                        unsafe_allow_html=True)
            area = alt.Chart(tm).mark_area(opacity=0.92).encode(
                x=alt.X("Date:T", title=None, axis=alt.Axis(format="%b %Y")),
                y=alt.Y("Revenue:Q", title="الإيرادات ($)", stack=True),
                color=alt.Color("Segment:N", scale=color_scale, legend=alt.Legend(title=None, orient="bottom")),
                tooltip=[alt.Tooltip("Month:N", title="الشهر"), alt.Tooltip("Segment:N", title="الشريحة"),
                         alt.Tooltip("Revenue:Q", title="الإيرادات", format=",.0f")])
            st.altair_chart(style_chart(area.properties(height=340)), use_container_width=True, theme=None)

        def hbar(df, field):
            return style_chart(alt.Chart(df).mark_bar(color="#0B7A75", cornerRadiusEnd=3).encode(
                x=alt.X("Revenue:Q", title=None),
                y=alt.Y(f"{field}:N", sort="-x", title=None, axis=alt.Axis(labelLimit=260)),
                tooltip=[alt.Tooltip(f"{field}:N", title="الاسم"), alt.Tooltip("Revenue:Q", title="الإيرادات", format=",.0f")],
            ).properties(height=330))

        st.write("")
        pa, pb = st.columns(2)
        prod, ctry = load_extra("top_products"), load_extra("top_countries")
        with pa:
            with st.container(border=True):
                st.markdown('<div class="section-title">أفضل 10 منتجات (بالإيرادات)</div>', unsafe_allow_html=True)
                if prod is not None:
                    st.altair_chart(hbar(prod, "Description"), use_container_width=True, theme=None)
        with pb:
            with st.container(border=True):
                st.markdown('<div class="section-title">أفضل 10 دول (بالإيرادات)</div>', unsafe_allow_html=True)
                if ctry is not None:
                    st.altair_chart(hbar(ctry, "Country"), use_container_width=True, theme=None)

# ───────────────────────── جودة النموذج ─────────────────────────
with tab_q:
    mt = load_metrics()
    if mt is None:
        st.info("لتفعيل هذا التبويب شغّل `python cluster_model.py` مرة واحدة.")
    else:
        mdf = pd.DataFrame(mt["metrics"])
        k0 = mt["chosen_k"]
        cur = mdf[mdf["k"] == k0].iloc[0]
        smallest = rfm_df["Cluster"].value_counts(normalize=True).min() * 100
        qc = st.columns(3)
        for i, (col, (t, v)) in enumerate(zip(qc, [("عدد الشرائح", str(k0)),
                                                    ("معامل Silhouette", f"{cur['silhouette']:.2f}"),
                                                    ("أصغر شريحة", f"{smallest:.0f}% من العملاء")])):
            col.markdown(f'<div class="seg-card" style="--c:#0B7A75;--d:{i * 110}ms"><div class="t">{t}</div>'
                         f'<div class="big">{v}</div></div>', unsafe_allow_html=True)
        st.write("")

        def curve(field, title):
            base = alt.Chart(mdf).encode(x=alt.X("k:O", title="عدد الشرائح (k)", axis=alt.Axis(labelAngle=0)))
            line = base.mark_line(color="#3B6FB6", strokeWidth=2.5).encode(y=alt.Y(f"{field}:Q", title=title, scale=alt.Scale(zero=False)))
            pts = base.mark_point(filled=True, size=90, color="#3B6FB6").encode(y=f"{field}:Q")
            chosen = alt.Chart(mdf[mdf["k"] == k0]).mark_point(filled=True, size=260, color="#0B7A75").encode(
                x="k:O", y=f"{field}:Q")
            return style_chart((line + pts + chosen).properties(height=280))

        qa, qb = st.columns(2)
        with qa:
            with st.container(border=True):
                st.markdown('<div class="section-title">منحنى Elbow (الكوع)</div>'
                            '<div class="section-note">كلما زادت الشرائح قلّ التشتت، لكن بعد نقطة الكوع تصير الفائدة صغيرة.</div>',
                            unsafe_allow_html=True)
                st.altair_chart(curve("inertia", "التشتت داخل الشرائح"), use_container_width=True, theme=None)
        with qb:
            with st.container(border=True):
                st.markdown('<div class="section-title">معامل Silhouette</div>'
                            '<div class="section-note">من 0 إلى 1: كلما زاد كان الفصل بين الشرائح أوضح.</div>',
                            unsafe_allow_html=True)
                st.altair_chart(curve("silhouette", "Silhouette"), use_container_width=True, theme=None)

        st.markdown(
            '<div class="seg-card" style="--c:#3B6FB6;--d:0ms"><div class="t">ليش اخترنا 4 شرائح؟</div>'
            '<div class="d">قد تلاحظ أن شريحتين تعطي Silhouette أعلى، لأن الفصل الثنائي أسهل رياضياً. لكن شريحتين لا تكفيان '
            'لقرارات تسويقية مختلفة. اخترنا 4 لأنها تعطي إجراءً واضحاً لكل شريحة: كبار العملاء، الأوفياء، الواعدون، '
            'والمعرّضون للخسارة، مع درجة فصل مقبولة في بيانات سلوك العملاء (قيم Silhouette بين 0.3 و 0.5 تُعد معقولة عادةً).</div></div>',
            unsafe_allow_html=True)