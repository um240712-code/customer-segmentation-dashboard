import pandas as pd
import datetime as dt

print("⏳ جاري تحميل البيانات النظيفة...")
df = pd.read_csv("data/cleaned_data.csv")
df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])

# التاريخ المرجعي = يوم بعد آخر عملية في البيانات
snapshot_date = df['InvoiceDate'].max() + dt.timedelta(days=1)
print(f"📅 التاريخ المرجعي للتحليل: {snapshot_date}")

rfm_df = df.groupby('CustomerID').agg({
    'InvoiceDate': lambda x: (snapshot_date - x.max()).days,  # Recency: أيام منذ آخر شراء
    'InvoiceNo': 'nunique',   # Frequency: عدد الفواتير المختلفة (كان count وهذا يعدّ أسطر المنتجات!)
    'TotalPrice': 'sum'       # Monetary: إجمالي الإنفاق
})

rfm_df.rename(columns={'InvoiceDate': 'Recency', 'InvoiceNo': 'Frequency', 'TotalPrice': 'Monetary'}, inplace=True)

print("📊 عينة من تحليلات سلوك العملاء (RFM):")
print(rfm_df.head())

rfm_df.to_csv("data/rfm_data.csv")
print("💾 تم حفظ جدول RFM في: data/rfm_data.csv")