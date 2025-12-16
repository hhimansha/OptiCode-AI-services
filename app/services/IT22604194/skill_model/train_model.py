# coding_skill_assessor/01_train_model.py
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
import os

print("Starting Coding Skill Model Training...")
print("=" * 50)

# Step 1: Load the Excel dataset
print("Step 1: Loading Excel dataset...")
try:
    # Read the Excel file
    df = pd.read_excel('student_coding_skill_dataset.xlsx')
    print(f"Excel dataset loaded successfully! Shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    
    # Display first few rows
    print(f"\nFirst 3 rows of the dataset:")
    print(df.head(3))
    
except FileNotFoundError:
    print("Error: student_coding_skill_dataset.xlsx not found!")
    print("Please make sure the Excel file exists in the same directory")
    exit()
except Exception as e:
    print(f"Error loading Excel file: {e}")
    exit()

# Step 2: Explore the data
print("\n Step 2: Exploring data...")
print(f"Dataset shape: {df.shape}")
print(f"\nColumn names:")
for col in df.columns:
    print(f"  - {col}")

print(f"\nSkill level distribution:")
skill_counts = df['skill_level'].value_counts()
print(skill_counts)

print(f"\nData types:")
print(df.dtypes)

# Step 3: Check for missing values
print("\n Step 3: Checking for missing values...")
missing_values = df.isnull().sum()
print("Missing values per column:")
print(missing_values)

if missing_values.sum() > 0:
    print("⚠️  Missing values detected. Handling them...")
    df = df.dropna()  # Remove rows with missing values
    print(f"Dataset shape after handling missing values: {df.shape}")

# Step 4: Prepare features and target
print("\n Step 4: Preparing features and target...")
feature_columns = ['foundational_coding', 'problem_solving', 'workflow', 
                   'tools', 'computational', 'confidence', 'average_score']

# Check if all feature columns exist
missing_features = [col for col in feature_columns if col not in df.columns]
if missing_features:
    print(f" Missing feature columns: {missing_features}")
    exit()

X = df[feature_columns]
y = df['skill_level']

print(f"Features: {feature_columns}")
print(f"Target variable: skill_level")
print(f"Feature matrix shape: {X.shape}")
print(f"Target vector shape: {y.shape}")

# Step 5: Encode target variable
print("\n Step 5: Encoding target variable...")
le = LabelEncoder()
y_encoded = le.fit_transform(y)
print(f"Encoded classes: {list(zip(le.classes_, range(len(le.classes_))))}")
print(f"Class distribution: {dict(zip(le.classes_, np.bincount(y_encoded)))}")

# Step 6: Split the data
print("\n Step 6: Splitting data into training and test sets...")
X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
)
print(f"Training set: {X_train.shape}")
print(f"Test set: {X_test.shape}")

# Show class distribution in splits
print(f"\nTraining set class distribution:")
train_counts = pd.Series(y_train).value_counts().sort_index()
for i, count in train_counts.items():
    print(f"  {le.classes_[i]}: {count} samples")

print(f"Test set class distribution:")  
test_counts = pd.Series(y_test).value_counts().sort_index()
for i, count in test_counts.items():
    print(f"  {le.classes_[i]}: {count} samples")

# Step 7: Train the model
print("\n Step 7: Training Random Forest model...")
rf_model = RandomForestClassifier(
    n_estimators=100,
    random_state=42,
    max_depth=10,
    min_samples_split=5,
    min_samples_leaf=2,
    class_weight='balanced'  # Handle class imbalance
)
rf_model.fit(X_train, y_train)
print(" Model training completed!")

# Step 8: Evaluate the model
print("\n Step 8: Evaluating model performance...")
y_pred = rf_model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

print(f" Model Accuracy: {accuracy:.3f}")
print(f"\n Detailed Classification Report:")
print(classification_report(y_test, y_pred, target_names=le.classes_))

# Step 9: Feature importance
print("\n Step 9: Analyzing feature importance...")
feature_importance = pd.DataFrame({
    'feature': feature_columns,
    'importance': rf_model.feature_importances_
}).sort_values('importance', ascending=False)

print("Feature Importance Ranking:")
for idx, row in feature_importance.iterrows():
    print(f"  {row['feature']}: {row['importance']:.4f}")

# Step 10: Save the model
print("\n Step 10: Saving model and encoder...")
joblib.dump(rf_model, 'coding_skill_classifier.pkl')
joblib.dump(le, 'label_encoder.pkl')
print(" Model saved as 'coding_skill_classifier.pkl'")
print(" Label encoder saved as 'label_encoder.pkl'")

# Step 11: Create visualization
print("\n Step 11: Creating visualizations...")
plt.figure(figsize=(12, 8))

# Plot 1: Feature Importance
plt.subplot(2, 2, 1)
sns.barplot(data=feature_importance, x='importance', y='feature', palette='viridis')
plt.title('Feature Importance in Coding Skill Classification')
plt.xlabel('Importance Score')

# Plot 2: Class Distribution
plt.subplot(2, 2, 2)
skill_counts.plot(kind='bar', color=['skyblue', 'lightcoral', 'lightgreen'])
plt.title('Skill Level Distribution')
plt.xlabel('Skill Level')
plt.ylabel('Count')
plt.xticks(rotation=45)

# Plot 3: Correlation Heatmap
plt.subplot(2, 2, 3)
correlation_matrix = X.corr()
sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0)
plt.title('Feature Correlation Heatmap')

# Plot 4: Average Scores by Skill Level
plt.subplot(2, 2, 4)
df_boxplot = df.copy()
df_boxplot['skill_level_encoded'] = le.transform(df_boxplot['skill_level'])
sns.boxplot(data=df_boxplot, x='skill_level', y='average_score', palette='Set2')
plt.title('Average Scores by Skill Level')
plt.xticks(rotation=45)

plt.tight_layout()
plt.savefig('model_analysis.png', dpi=300, bbox_inches='tight')
print("✅ Visualizations saved as 'model_analysis.png'")

# Step 12: Model validation with cross-validation
print("\n🔍 Step 12: Performing cross-validation...")
from sklearn.model_selection import cross_val_score

cv_scores = cross_val_score(rf_model, X, y_encoded, cv=5, scoring='accuracy')
print(f"📊 Cross-validation scores: {cv_scores}")
print(f"📊 Mean CV accuracy: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")

print("\n🎉 Model training completed successfully!")
print("📁 Files created:")
print("   - coding_skill_classifier.pkl (trained model)")
print("   - label_encoder.pkl (label encoder)") 
print("   - model_analysis.png (comprehensive visualizations)")

print(f"\n📊 Dataset Summary:")
print(f"   Total samples: {len(df)}")
print(f"   Beginner: {skill_counts.get('Beginner', 0)}")
print(f"   Intermediate: {skill_counts.get('Intermediate', 0)}")
print(f"   Advanced: {skill_counts.get('Advanced', 0)}")