# User Guide: Email Priority Classification System

## 📋 Table of Contents
1. [Quick Start](#quick-start)
2. [Installation](#installation)
3. [Basic Usage](#basic-usage)
4. [Advanced Features](#advanced-features)
5. [Configuration](#configuration)
6. [Troubleshooting](#troubleshooting)
7. [API Reference](#api-reference)

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- 2GB free disk space
- Command line access (Terminal/Git Bash)

### 5-Minute Setup
```bash
# 1. Navigate to the system
cd 03_Source_Code/final_system

# 2. Install dependencies
pip install -r requirements.txt

# 3. Test the system
python scripts/predict.py --mode batch
```

That's it! The system will show predictions for sample emails.

## 💻 Installation

### Option 1: Direct Installation
```bash
cd 03_Source_Code/final_system
pip install -r requirements.txt
```

### Option 2: Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv email_classifier_env

# Activate (Windows)
email_classifier_env\Scripts\activate

# Activate (macOS/Linux)
source email_classifier_env/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Option 3: Package Installation
```bash
cd 03_Source_Code/final_system
pip install -e .

# Now you can use anywhere:
email-priority-predict --mode batch
```

## 📧 Basic Usage

### 1. Predict Email Priorities

#### Interactive Mode
```bash
python scripts/predict.py --mode interactive
```
- Enter email details when prompted
- Type '.' on a new line to finish body input
- Get instant priority prediction with confidence

#### Batch Mode (Sample Emails)
```bash
python scripts/predict.py --mode batch
```
- Processes 8 predefined sample emails
- Shows priority, confidence, and analysis
- Great for testing system functionality

#### Single Email Prediction
```bash
python scripts/predict.py \
  --subject "URGENT: Server maintenance required" \
  --body "The production server needs immediate attention."
```

#### File-Based Prediction
```bash
python scripts/predict.py --mode file --input my_emails.json
```

### 2. Train New Models

#### Use Existing Data
```bash
python scripts/train_model.py --data ../../02_Data/processed/enron_sample_data.csv
```

#### Extract Fresh Data from Enron Dataset
```bash
# Extract 1000 emails and train
python scripts/train_model.py --extract 1000

# Extract with balanced classes
python scripts/train_model.py --extract 2000 --balance

# Use different model
python scripts/train_model.py --extract 1000 --model logistic_regression
```

## 🔧 Advanced Features

### Configuration Files
Create custom training configurations:

```json
{
  "model": {
    "type": "random_forest",
    "max_features": 3000,
    "test_size": 0.3
  },
  "training": {
    "num_emails": 1500,
    "balance_dataset": true
  }
}
```

Use with:
```bash
python scripts/train_model.py --config my_config.json
```

### Logging and Debug
```bash
# Enable debug logging
python scripts/predict.py --log-level DEBUG

# Save logs to file
python scripts/train_model.py --log-file training.log

# Verbose output
python scripts/predict.py --verbose
```

### Model Management
```bash
# Save model to specific location
python scripts/train_model.py --output my_model.pkl

# Use custom model for prediction
python scripts/predict.py --model my_model.pkl

# Save feature importance
python scripts/train_model.py --save-features
```

## 🐍 Python API Usage

### Basic API Example
```python
from email_classifier import EmailPriorityClassifier

# Initialize and load model
classifier = EmailPriorityClassifier()
classifier.load_model('../../02_Data/models/email_priority_model.pkl')

# Single prediction
email = {
    'subject': 'Team meeting tomorrow',
    'body': 'Please join us for the quarterly review meeting.',
    'to': 'team@company.com'
}

priority, confidence = classifier.predict(email)
print(f"Priority: {priority}, Confidence: {confidence:.1%}")
```

### Batch Processing
```python
emails = [
    {'subject': 'URGENT: Help needed', 'body': 'Server is down'},
    {'subject': 'FYI: Newsletter', 'body': 'Monthly company updates'},
    {'subject': 'Meeting notes', 'body': 'Summary from yesterday'}
]

# Predict all at once
results = classifier.predict(emails)
for i, (priority, confidence) in enumerate(results):
    print(f"Email {i+1}: {priority} ({confidence:.1%})")
```

### Training Custom Models
```python
import pandas as pd
from email_classifier import EmailPriorityClassifier, CSVDataProcessor

# Load and process data
processor = CSVDataProcessor()
df = processor.load_and_process('my_emails.csv')

# Train classifier
classifier = EmailPriorityClassifier(max_features=3000)
metrics = classifier.train(df, model_type='random_forest')

# Save trained model
classifier.save_model('my_custom_model.pkl')

# View performance
print(f"Accuracy: {metrics['cv_mean']:.3f}")
```

## ⚙️ Configuration

### Default Configuration Location
- `config/default_config.json` - Main configuration
- Command line arguments override config file settings

### Key Configuration Options

#### Model Settings
```json
{
  "model": {
    "type": "random_forest",        // or "logistic_regression"
    "max_features": 5000,           // TF-IDF feature limit
    "ngram_range": [1, 2],          // Unigrams and bigrams
    "test_size": 0.2,               // Train/test split
    "cv_folds": 5                   // Cross-validation folds
  }
}
```

#### Training Options
```json
{
  "training": {
    "num_emails": 1000,             // Emails to extract
    "balance_dataset": false,       // Balance priority classes
    "save_extracted_data": true     // Save processed data
  }
}
```

#### File Paths
```json
{
  "data": {
    "enron_path": "../../02_Data/raw/enron_mail_20150507/maildir",
    "processed_path": "../../02_Data/processed",
    "models_path": "../../02_Data/models"
  }
}
```

## 🔍 Input Formats

### Email Dictionary Format
```python
email = {
    'subject': 'Required - Email subject line',
    'body': 'Required - Email body content',
    'to': 'Optional - recipient@example.com, multiple@example.com',
    'from': 'Optional - sender@example.com',
    'cc': 'Optional - cc@example.com'
}
```

### CSV File Format
```csv
subject,body,to,from,priority
"Meeting tomorrow","Please attend the meeting","team@company.com","manager@company.com","MEDIUM"
"URGENT: Server down","Production server crashed","it@company.com","ops@company.com","HIGH"
```

### JSON File Format
```json
[
  {
    "subject": "Meeting tomorrow",
    "body": "Please attend the meeting",
    "to": "team@company.com",
    "from": "manager@company.com"
  }
]
```

## 🛠 Troubleshooting

### Common Issues

#### "Module not found" Error
```bash
# Solution 1: Install dependencies
pip install -r requirements.txt

# Solution 2: Install package
pip install -e .

# Solution 3: Set Python path
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
```

#### "Model not found" Error
```bash
# Check model path
ls ../../02_Data/models/

# Use absolute path
python scripts/predict.py --model /full/path/to/model.pkl

# Retrain model
python scripts/train_model.py --data ../../02_Data/processed/enron_sample_data.csv
```

#### Low Prediction Accuracy
```bash
# Use more training data
python scripts/train_model.py --extract 2000 --balance

# Try different model
python scripts/train_model.py --model logistic_regression

# Check data quality
python scripts/train_model.py --log-level DEBUG
```

#### Performance Issues
```bash
# Reduce feature count
python scripts/train_model.py --max-features 3000

# Use faster model
python scripts/train_model.py --model logistic_regression

# Process smaller batches
python scripts/predict.py --mode file --input small_batch.json
```

### Debug Mode
```bash
# Enable detailed logging
python scripts/predict.py --log-level DEBUG --verbose

# Check system info
python -c "import sys; print(sys.version)"
python -c "import sklearn; print(sklearn.__version__)"
```

### Getting Help
1. Check error messages carefully
2. Review log files for details
3. Verify input data format
4. Test with sample data first
5. Consult technical documentation

## 📊 Output Interpretation

### Priority Levels
- **HIGH**: Urgent, time-sensitive, requires immediate attention
- **MEDIUM**: Standard business communications, normal priority
- **LOW**: Informational, optional, no immediate action needed

### Confidence Scores
- **>80%**: Very confident prediction
- **60-80%**: High confidence prediction  
- **40-60%**: Moderate confidence prediction
- **<40%**: Low confidence, manual review recommended

### Feature Importance
When training models, the system shows which features are most important:
- **Text Features**: Specific words and phrases
- **Metadata Features**: Email length, recipient count, etc.
- **Linguistic Features**: Tone, urgency indicators, etc.

## 🎯 Best Practices

### Data Preparation
1. Ensure emails have both subject and body
2. Remove personal/sensitive information
3. Use consistent date formats
4. Validate recipient email formats

### Model Training
1. Use balanced datasets when possible
2. Start with 1000+ emails for training
3. Validate results with cross-validation
4. Save feature importance for analysis

### Production Use
1. Monitor prediction confidence
2. Collect user feedback for improvement
3. Retrain models periodically
4. Test with new data regularly

---

**Need more help?** Check the `01_Documentation/Technical_Report.md` for detailed technical information or the `01_Documentation/API_Documentation.md` for complete API reference.