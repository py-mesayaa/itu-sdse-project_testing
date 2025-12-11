# ITU BDS MLOPS'25 - Project

## Project Description

This project implements an end-to-end MLOps pipeline for training and deploying a machine learning model. The solution follows MLOps best practices with a modular structure, containerized execution via Dagger, and automated CI/CD workflows on GitHub Actions.

The project structure adheres to standard data science MLOps conventions:
- **Data processing**: Raw data ingestion, cleaning, and feature engineering
- **Model training**: Training multiple models and selecting the best performer
- **Model deployment**: Packaging and exporting the selected model
- **Automation**: Dagger workflow for containerized execution and GitHub Actions for CI/CD


## Project Structure

```
.
├── ci/                    # Dagger workflow (Go)
│   └── main.go            # Main Dagger pipeline definition
├── src/                   # Source code
│   ├── data/              # Data processing modules
│   │   └── make_dataset.py
│   ├── features/          # Feature engineering
│   │   └── build_features.py
│   ├── models/            # Model training and deployment
│   │   ├── train_model.py
│   │   ├── model_selection.py
│   │   ├── model_deploy.py
│   │   └── model_inference.py
│   └── visualization/    # Visualization utilities
│       └── visualize.py
├── data/                  # Data directory
│   └── raw/              # Raw input data (DVC managed)
├── artifacts/             # Model artifacts and outputs
├── .github/workflows/     # GitHub Actions workflows
│   └── train.yml         # Training and validation workflow
├── Dockerfile            # Container image definition
├── requirements.txt      # Python dependencies
├── setup.py             # Python package setup
└── go.mod               # Go module dependencies
```

## Prerequisites

Before running the project, ensure you have the following installed:

- **Python 3.11+** (check with `python3 --version`)
- **Go 1.24+** (check with `go version`)
- **Dagger CLI** (see installation instructions below)
- **Git** (for version control)
- **Docker** (required by Dagger for containerization)
- **DVC** (used for data versioning)

### Installing Dagger CLI

To install Dagger CLI locally:

```bash
curl -fsSL https://dl.dagger.io/dagger/install.sh | BIN_DIR=$HOME/.local/bin sh
export PATH="$HOME/.local/bin:$PATH"
```

Verify installation:
```bash
dagger version
```

## Running the Project Locally

### 1. Clone the Repository

```bash
git clone <repository-url>
cd itu-sdse-project_testing
```

### 2. Set Up Python Environment

Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This will install all required packages including:
- Data science libraries (pandas, numpy, scikit-learn)
- Machine learning libraries (xgboost)
- MLOps tools (mlflow, dvc)

### 4. Verify Environment

Test that your environment is set up correctly:

```bash
python test_environment.py
```

You should see: `>>> Development environment passes all tests!`

### 5. Download Raw Data

**Important Note on Data Management**: The project uses DVC (Data Version Control) for managing the raw data file. However, if DVC remote is not configured or accessible, the pipeline includes a fallback mechanism using `curl` to download the data directly from GitHub.

The raw data file (`raw_data.csv`) is stored in `data/raw/`. You can obtain it in two ways:

#### Option A: Using DVC (if configured)

```bash
dvc pull data/raw/raw_data.csv.dvc
```

#### Option B: Direct Download (Fallback Method)

If DVC is not working or the remote is not configured, download the data directly:

```bash
mkdir -p data/raw
curl -fsSL https://raw.githubusercontent.com/Jeppe-T-K/itu-sdse-project-data/refs/heads/main/raw_data.csv -o data/raw/raw_data.csv
```

**Note**: The Dagger workflow automatically uses this curl fallback method if DVC pull fails. This ensures the pipeline works even when DVC remote configuration is not available (e.g., in CI/CD environments).

### 6. Run the Dagger Pipeline Locally

The Dagger workflow orchestrates the entire ML pipeline in a containerized environment:

```bash
# Ensure you're in the project root directory
go run ci/main.go
```

This will:
1. Build a Docker image from the `Dockerfile`
2. Pull/download the raw data (with DVC fallback to curl)
3. Process the data (`src.data.make_dataset`)
4. Train models (`src.models.train_model`)
5. Select the best model (`src.models.model_selection`)
6. Deploy the model (`src.models.model_deploy`)
7. Export the model artifact to `./model/` directory

The final model artifact will be available in the `./model/` directory containing:
- `model.pkl` - The trained model
- `columns_list.json` - Feature column names
- `scaler.pkl` - Data scaler for preprocessing

### 7. Run Individual Components (Optional)

You can also run individual pipeline steps manually:

```bash
# Set Python path
export PYTHONPATH=$(pwd)

# Data processing
python -m src.data.make_dataset data/raw/raw_data.csv artifacts/train_data_gold.csv

# Model training
python -m src.models.train_model

# Model selection
python -m src.models.model_selection

# Model deployment
python -m src.models.model_deploy
```

## GitHub Workflows

### Triggering the Workflow

The GitHub workflow (`.github/workflows/train.yml`) is automatically triggered on:

1. **Push to any branch**: Any push to the repository will trigger the workflow
2. **Pull requests to main**: Opening or updating a PR targeting the `main` branch

To manually trigger the workflow:

1. Go to your GitHub repository
2. Navigate to **Actions** tab
3. Select **Train Model** workflow
4. Click **Run workflow** button
5. Choose the branch and click **Run workflow**

### Workflow Steps

The GitHub workflow consists of two jobs:

#### Job 1: `train`
1. Checks out the code
2. Sets up Go 1.24
3. Installs Dagger CLI
4. Runs the Dagger pipeline (`go run ci/main.go`)
5. Uploads the model artifact named `model` to GitHub Actions artifacts

#### Job 2: `validate-model`
1. Downloads the trained model artifact
2. Runs the model validator action to test model inference

### Workflow Outputs

After successful completion:
- The model artifact is stored in GitHub Actions artifacts (retention: 7 days)
- The artifact can be downloaded from the workflow run page
- The model validator ensures the model works correctly for inference

## Data Management and DVC Workaround

### The Problem

DVC (Data Version Control) is used for managing large data files. However, in CI/CD environments or when DVC remote is not properly configured, `dvc pull` may fail.

### The Solution

The Dagger workflow (`ci/main.go`) implements a robust fallback mechanism:

```go
// Try DVC first, but if it fails, download directly using curl
"(dvc update data/raw/raw_data.csv.dvc && dvc pull data/raw/raw_data.csv || " +
"curl -fsSL https://raw.githubusercontent.com/Jeppe-T-K/itu-sdse-project-data/refs/heads/main/raw_data.csv -o data/raw/raw_data.csv) && " +
"ls -lh data/raw/raw_data.csv"
```

This approach:
1. **First attempts DVC**: Tries to use DVC to pull the data file
2. **Falls back to curl**: If DVC fails, downloads the file directly from the GitHub repository
3. **Always succeeds**: Ensures the pipeline continues even if DVC is not configured

### Why This Was Necessary

- DVC requires remote storage configuration (S3, GCS, etc.) which may not be available in all environments
- GitHub Actions runners may not have DVC remotes configured
- Direct download ensures the pipeline is self-contained and works out-of-the-box

The `Dockerfile` includes `curl` as a system dependency specifically to support this fallback mechanism.

## Generating the Model Artifact

The model artifact is automatically generated by the Dagger pipeline and contains:

- `model.pkl`: The trained logistic regression model (selected as best performer)
- `columns_list.json`: List of feature columns used during training
- `scaler.pkl`: MinMaxScaler used for data normalization

The artifact is created in the `./model/` directory and can be:
- Used locally for inference
- Uploaded to GitHub Actions artifacts (in CI/CD)
- Deployed to production environments
