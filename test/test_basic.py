"""شغّلها من مجلد المشروع:  pytest"""
import os
import numpy as np
import pandas as pd
import joblib
import pytest

need = pytest.mark.skipif(not os.path.exists("models/kmeans_model.pkl"), reason="شغّل cluster_model.py أولاً")


@need
def test_scaler_trained_on_log():
    scaler = joblib.load("models/scaler.pkl")
    assert scaler.mean_[2] < 20, "النموذج قديم: مُدرَّب بدون log"


@need
def test_prediction_is_valid_cluster():
    kmeans = joblib.load("models/kmeans_model.pkl")
    scaler = joblib.load("models/scaler.pkl")
    c = kmeans.predict(scaler.transform(np.log1p([[10, 15, 2000]])))[0]
    assert c in range(kmeans.n_clusters)


@need
def test_clustered_file_is_sane():
    df = pd.read_csv("data/rfm_clustered.csv")
    assert {"CustomerID", "Recency", "Frequency", "Monetary", "Cluster"} <= set(df.columns)
    assert (df["Frequency"] >= 1).all() and (df["Monetary"] > 0).all()
    assert df["Cluster"].nunique() == 4


@pytest.mark.skipif(not os.path.exists("data/cleaned_data.csv"), reason="cleaned_data.csv غير موجود")
def test_frequency_counts_invoices_not_lines():
    raw = pd.read_csv("data/cleaned_data.csv", usecols=["CustomerID", "InvoiceNo"])
    expected = raw.groupby("CustomerID")["InvoiceNo"].nunique()
    rfm = pd.read_csv("data/rfm_data.csv").set_index("CustomerID")
    assert (rfm["Frequency"] == expected.reindex(rfm.index)).all()