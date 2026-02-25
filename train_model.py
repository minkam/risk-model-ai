import pandas as pd
import numpy as np
import xgboost as xgb
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score


print("Loading dataset...")
df = pd.read_csv("training_data.csv")

print("Preparing features...")

X = df[["ma20","ma50","rsi","atr"]]
y = df["target"]

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, shuffle=True, random_state=42
)

# Handle class imbalance
pos_weight = (len(y_train) - sum(y_train)) / sum(y_train)

print("Training model...")

model = xgb.XGBClassifier(
    n_estimators=400,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.9,
    colsample_bytree=0.9,
    scale_pos_weight=pos_weight,
    use_label_encoder=False,
    eval_metric="logloss"
)

model.fit(X_train, y_train)

print("\nEvaluating...\n")

y_pred = model.predict(X_test)
y_proba = model.predict_proba(X_test)[:,1]

print("Classification Report:\n")
print(classification_report(y_test, y_pred))

auc = roc_auc_score(y_test, y_proba)
print("ROC AUC:", round(auc, 4))

joblib.dump(model, "swing_model.pkl")

print("\nModel saved as swing_model.pkl")