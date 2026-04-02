import pandas as pd
import numpy as np
from catboost import CatBoostClassifier
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, precision_recall_curve

# ==========================================
# 1. LOAD DATA
# ==========================================

df = pd.read_csv("geomagnetic_forecasting_master_dataset.csv", parse_dates=['datetime'])
df = df.sort_values("datetime")
df = df.set_index("datetime")

print("Total rows:", len(df))

# ==========================================
# 2. SELECT TARGET (3-HOUR)
# ==========================================

y = df["target_3h"]

remove_cols = ["target_1h", "target_3h", "target_6h", "Kp"]
X = df.drop(columns=[c for c in remove_cols if c in df.columns], errors="ignore")

print("Total features used:", X.shape[1])
print("Total storms:", y.sum())
print("Storm rate:", round(y.mean(), 4))

# ==========================================
# 3. TIME-BASED SPLIT (80/20)
# ==========================================

split = int(len(df) * 0.8)

X_train = X.iloc[:split]
X_test  = X.iloc[split:]
y_train = y.iloc[:split]
y_test  = y.iloc[split:]

print("\nTrain size:", len(X_train))
print("Test size:", len(X_test))
print("Storms in train:", y_train.sum())
print("Storms in test:", y_test.sum())

# ==========================================
# 4. MODEL (CATBOOST)
# ==========================================

model = CatBoostClassifier(
    iterations=500,
    learning_rate=0.05,
    depth=6,
    l2_leaf_reg=3,
    loss_function='Logloss',
    auto_class_weights='Balanced',
    early_stopping_rounds=50,
    verbose=100,
    random_seed=42,
    allow_writing_files=False
)

print("\nTraining CatBoost...")

model.fit(
    X_train, y_train,
    eval_set=(X_test, y_test),
    use_best_model=True
)

# Save model
import pickle
with open("model.pkl", "wb") as f:
    pickle.dump(model, f)


# ==========================================
# 5. PREDICT
# ==========================================

y_prob = model.predict_proba(X_test)[:, 1]

threshold = 0.3
y_pred = (y_prob >= threshold).astype(int)

# ==========================================
# 6. EVALUATION
# ==========================================

print("\n=== Evaluation at Threshold =", threshold, "===")

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))

print("\nClassification Report:")
print(classification_report(y_test, y_pred))

roc = roc_auc_score(y_test, y_prob)
print("ROC-AUC:", round(roc, 4))

# ==========================================
# 7. THRESHOLD SWEEP
# ==========================================

print("\n=== Threshold Sensitivity ===")

for t in [0.2, 0.25, 0.3, 0.35, 0.4]:
    preds = (y_prob >= t).astype(int)
    cm = confusion_matrix(y_test, preds)
    tp = cm[1, 1]
    fn = cm[1, 0]
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    print(f"Threshold {t} | Recall: {recall:.2f}")
    print(cm)

# ==========================================
# 8. FEATURE IMPORTANCE
# ==========================================

print("\n=== Top 10 Drivers of Storms ===")
feature_importance = model.get_feature_importance()
sorted_idx = np.argsort(feature_importance)[::-1]

for i in sorted_idx[:10]:
    print(f"{X.columns[i]}: {feature_importance[i]:.2f}")

# ==========================================
# 9. AUTO-TUNE THRESHOLD
# ==========================================

print("\n=== Auto-Tuning Threshold ===")

precisions, recalls, thresholds = precision_recall_curve(y_test, y_prob)
target_recall = 0.90

valid_indices = np.where(recalls >= target_recall)[0]

if len(valid_indices) > 0:
    best_idx = valid_indices[np.argmax(precisions[valid_indices])]
    best_threshold = thresholds[best_idx]
    best_recall = recalls[best_idx]

    y_tuned = (y_prob >= best_threshold).astype(int)
    cm = confusion_matrix(y_test, y_tuned)
    false_alarms = cm[0, 1]

    print(f"Optimal Threshold: {best_threshold:.4f}")
    print(f"Actual Recall: {best_recall:.4f}")
    print(f"False Alarms: {false_alarms}")
    print("\nConfusion Matrix at Optimized Threshold:")
    print(cm)
else:
    print("Could not achieve target recall.")
