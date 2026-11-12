import os
import json
import numpy as np
import pandas as pd
import joblib
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

K = 4
COLS = ['Recency', 'Frequency', 'Monetary']

print("⏳ جاري تحميل بيانات الـ RFM...")
rfm = pd.read_csv("data/rfm_data.csv")

# 1. log ثم توحيد المقياس (بدون log تسيطر قلة من العملاء الضخام على النموذج)
scaler = StandardScaler()
Z = scaler.fit_transform(np.log1p(rfm[COLS]))

# 2. مقاييس جودة النموذج لعدة قيم k (للمنحنى في تبويب "جودة النموذج")
print("📐 جاري حساب مقاييس الجودة...")
metrics = []
for k in range(2, 9):
    km = KMeans(n_clusters=k, random_state=42, n_init=10).fit(Z)
    metrics.append({"k": k, "inertia": float(km.inertia_), "silhouette": float(silhouette_score(Z, km.labels_))})

# 3. النموذج النهائي
print("🤖 جاري تدريب النموذج النهائي...")
kmeans = KMeans(n_clusters=K, random_state=42, n_init=10)
rfm['Cluster'] = kmeans.fit_predict(Z)
print(rfm['Cluster'].value_counts().sort_index())

os.makedirs("models", exist_ok=True)
joblib.dump(kmeans, "models/kmeans_model.pkl")
joblib.dump(scaler, "models/scaler.pkl")
rfm.to_csv("data/rfm_clustered.csv", index=False)
with open("data/model_metrics.json", "w", encoding="utf-8") as f:
    json.dump({"chosen_k": K, "metrics": metrics}, f, ensure_ascii=False, indent=2)

# 4. ملفات صغيرة للاتجاهات (حتى لا نحتاج رفع cleaned_data الكبير عند النشر)
if os.path.exists("data/cleaned_data.csv"):
    print("📈 جاري تجهيز ملفات الاتجاهات...")
    raw = pd.read_csv("data/cleaned_data.csv",
                      usecols=["CustomerID", "InvoiceDate", "Description", "Country", "TotalPrice"],
                      parse_dates=["InvoiceDate"])
    raw = raw.merge(rfm[["CustomerID", "Cluster"]], on="CustomerID")
    raw["Month"] = raw["InvoiceDate"].dt.to_period("M").astype(str)
    (raw.groupby(["Month", "Cluster"], as_index=False)["TotalPrice"].sum()
        .rename(columns={"TotalPrice": "Revenue"}).to_csv("data/trends_monthly.csv", index=False))
    (raw.groupby("Description")["TotalPrice"].sum().nlargest(10).reset_index()
        .rename(columns={"TotalPrice": "Revenue"}).to_csv("data/top_products.csv", index=False))
    (raw.groupby("Country")["TotalPrice"].sum().nlargest(10).reset_index()
        .rename(columns={"TotalPrice": "Revenue"}).to_csv("data/top_countries.csv", index=False))

print("💾 تم حفظ النموذج والشرائح والمقاييس بنجاح.")