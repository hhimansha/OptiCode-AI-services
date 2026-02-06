# train_weakness_model.py

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.multioutput import MultiOutputClassifier
from sklearn.metrics import classification_report
import joblib
from sklearn.metrics import accuracy_score

print(" Loading dataset...")

# Load dataset
df = pd.read_csv("weakness_dataset.csv")
print("Dataset shape:", df.shape)

# ----------------------------
# Feature columns (INPUT)
# ----------------------------
feature_cols = [
    "num_functions",
    "num_loops",
    "has_if",
    "has_return",
    "has_recursion",
    "while_true",
    "syntax_error",
    "lines_of_code",
    "avg_line_length",
    "time_idle",
    "edits_last_30s"
]

# ----------------------------
# Label columns (OUTPUT)
# ----------------------------
label_cols = [
    "label_syntax_error",
    "label_missing_base_case",
    "label_infinite_loop",
    "label_logic_error",
    "label_idle_stuck"
]

X = df[feature_cols]
y = df[label_cols]

print("Features shape:", X.shape)
print("Labels shape:", y.shape)

# ----------------------------
# Train / Test split
# ----------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print("Training samples:", X_train.shape[0])
print("Testing samples:", X_test.shape[0])

# ----------------------------
# Model definition
# ----------------------------
print(" Training Weakness Model...")

base_model = RandomForestClassifier(
    n_estimators=200,
    max_depth=10,
    random_state=42,
    class_weight="balanced"
)

model = MultiOutputClassifier(base_model)

model.fit(X_train, y_train)

print(" Training complete!")

# ----------------------------
# Evaluation
# ----------------------------
print("\n Evaluation Report:\n")

y_pred = model.predict(X_test)

exact_accuracy = accuracy_score(y_test, y_pred) * 100
print(f"Exact Match Accuracy: {exact_accuracy:.2f}%")

print(classification_report(
    y_test,
    y_pred,
    target_names=label_cols
))

# ----------------------------
# Save model
# ----------------------------
joblib.dump(model, "weakness_model.pkl")

print("\n Model saved as weakness_model.pkl")
print(" Weakness model training finished successfully!")
