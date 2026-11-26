import pickle
import os
import pandas as pd
import sys
from sklearn.cluster import AgglomerativeClustering

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "logistic_regression_model.pkl")

# Loads trained Logistic Regression model & Scaler
# Called By: run_prediction()
# Returns: Tuple (classifier, scaler) or (None, None)
def load_ml_model():
    if not os.path.exists(MODEL_PATH):
        print(f"ML Service Error: Model not found at {MODEL_PATH}")
        return None, None

    try:
        with open(MODEL_PATH, 'rb') as file:
            data = pickle.load(file)
            return data['classifier'], data.get('scaler', None)
    except Exception as e:
        print(f"ML Service Error: Failed to load model. {e}")
        return None, None

# Predicts Pass/Fail for a list of students
# Logic: Normalizes data -> Feeds to Classifier -> Maps 1=Pass, 0=Fail
# Called By: HOD Prediction Page, What-If Analysis Page
# Returns: Dict {Student_ID: 'Pass'/'Fail'}
def run_prediction(student_data: list, ml_features: list) -> dict:
    classifier, scaler = load_ml_model()
    if not classifier:
        return {}

    df = pd.DataFrame(student_data)

    if df.empty:
        return {}

    try:
        X = df[ml_features].fillna(0).values
    except KeyError as e:
        print(f"ML Service Error: Missing columns in data - {e}")
        return {}

    if scaler:
        X = scaler.transform(X)

    try:
        y_pred = classifier.predict(X)
    except Exception as e:
        print(f"ML Prediction Runtime Error: {e}")
        return {}

    results = {}
    for idx, row in df.iterrows():
        student_id = row.get('Student_ID')
        prediction = "Pass" if y_pred[idx] == 1 else "Fail"
        if student_id:
            results[student_id] = prediction

    return results

# Groups students into High/Avg/Low using Unsupervised Learning
# Logic: Agglomerative Clustering -> Calculate Mean Scores -> Label Clusters
# Called By: Teacher Analysis Page, HOD Groups Page
# Returns: DataFrame (Input data + 'Performance_Group' column)
def perform_clustering(student_data: list, feature_cols: list, n_clusters=3):
    if len(student_data) < n_clusters:
        print("ML Service: Not enough data points to form clusters.")
        return None

    df = pd.DataFrame(student_data)
    X = df[feature_cols].fillna(0).values

    try:
        clustering = AgglomerativeClustering(n_clusters=n_clusters, linkage='ward')
        df['Assigned_Cluster'] = clustering.fit_predict(X)

        # Dynamic Labeling: Rank clusters by average score
        cluster_means = df.groupby('Assigned_Cluster')[feature_cols].mean()
        cluster_means['Overall_Score'] = cluster_means.mean(axis=1)

        sorted_clusters = cluster_means['Overall_Score'].sort_values().index

        label_map = {
            sorted_clusters[0]: 'Low Performer',
            sorted_clusters[1]: 'Average Performer',
            sorted_clusters[2]: 'High Performer'
        }
        df['Performance_Group'] = df['Assigned_Cluster'].map(label_map)

        return df

    except Exception as e:
        print(f"Clustering Error: {e}")
        return None