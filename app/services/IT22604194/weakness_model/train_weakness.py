import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.multioutput import MultiOutputClassifier
import joblib

df = pd.read_parquet("data/combined_features.parquet")

label_cols = ["syntax_error","logic_error","infinite_loop","missing_base_case","stuck_idle"]
feature_cols = [c for c in df.columns if c not in label_cols + ["code_text","exception","runtime_status","id"]]

X = df[feature_cols]
y = df[label_cols]

Xtrain, Xtest, ytrain, ytest = train_test_split(X, y, test_size=0.2)

model = MultiOutputClassifier(RandomForestClassifier())
model.fit(Xtrain, ytrain)

joblib.dump({
    "model": model,
    "feat_cols": feature_cols,
    "labels": label_cols
}, "weakness_model.pkl")

print("Model saved!")
