"""يشغّل كل خطوات المشروع بالترتيب: python run_pipeline.py"""
import subprocess
import sys

STEPS = [
    ("preprocess.py", "1/3 تنظيف البيانات"),
    ("model_training.py", "2/3 حساب RFM"),
    ("cluster_model.py", "3/3 تدريب النموذج"),
]

for script, title in STEPS:
    print(f"\n=== {title} ===")
    if subprocess.run([sys.executable, script]).returncode != 0:
        sys.exit(f"توقف التنفيذ عند {script}. راجع الخطأ أعلاه.")
print("\n✅ انتهى كل شيء. شغّل التطبيق: streamlit run app.py")