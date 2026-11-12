import pandas as pd

def load_and_clean_data(file_path):
    print("⏳ جاري قراءة ملف البيانات وتفريغه...")
    # قراءة الملف مع تحديد الترميز المناسب للبيانات
    df = pd.read_csv(file_path, encoding='latin1')
    
    print(f"📊 حجم البيانات الأولي: {df.shape}")
    
    # 1. إزالة الصفوف التي لا تحتوي على CustomerID (لأننا نعمل على تحليلات وسلوك العملاء)
    df = df.dropna(subset=['CustomerID'])
    
    # 2. إزالة المرتجعات والكميات أو الأسعار السالبة (حيث تبدأ InvoiceNo بحرف C غالباً أو الكمية <= 0)
    df = df[df['Quantity'] > 0]
    df = df[df['UnitPrice'] > 0]
    
    # 3. تحويل عمود التاريخ إلى صيغة DateTime
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
    
    # 4. إنشاء عمود إجمالي السعر للمعاملة الواحدة (TotalPrice)
    df['TotalPrice'] = df['Quantity'] * df['UnitPrice']
    
    print(f"✅ حجم البيانات بعد التنظيف: {df.shape}")
    return df

if __name__ == "__main__":
    # مسار الملف داخل مجلد data
    file_path = "data/data.csv"
    cleaned_df = load_and_clean_data(file_path)
    
    # حفظ البيانات النظيفة في ملف جديد داخل مجلد data
    cleaned_df.to_csv("data/cleaned_data.csv", index=False)
    print("💾 تم حفظ البيانات النظيفة بنجاح في ملف: data/cleaned_data.csv")