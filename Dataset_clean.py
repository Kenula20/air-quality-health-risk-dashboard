import pandas as pd
import re
from pathlib import Path

# =========================================
# File paths
# =========================================
project_folder = Path(__file__).resolve().parent
input_file = project_folder / "DataExtract.csv"
output_file = project_folder / "air_quality_health_risk_assessment_cleaned.csv"
data_dict_file = project_folder / "air_quality_health_risk_assessment_data_dictionary.csv"

# =========================================
# Load raw dataset
# =========================================
df = pd.read_csv(input_file)

# Keep original column names for data dictionary
original_columns = df.columns.tolist()

# =========================================
# Step 1: Standardize raw column names safely
# This avoids errors caused by spaces, symbols,
# brackets, slashes, and inconsistent formatting.
# =========================================
df.columns = [
    re.sub(r"[^a-z0-9]+", "_", str(col).strip().lower()).strip("_")
    for col in df.columns
]

# Save intermediate standardized column names
standardized_columns = df.columns.tolist()

# =========================================
# Step 2: Rename columns to cleaner final names
# =========================================
final_rename_map = {
    "city_boundary_specification_lau_grid": "city_boundary_specification",
    "country_or_territory": "country",
    "city_or_territory": "city",
    "city_code": "city_code",
    "year": "year",
    "air_pollutant": "pollutant",
    "data_aggregation_id": "data_aggregation_id",
    "scenario": "scenario",
    "category": "category",
    "outcome": "outcome",
    "health_indicator": "health_indicator",
    "sex": "sex",
    "description_of_age_group": "age_group",
    "affected_population": "affected_population",
    "air_pollution_average_ug_m3": "air_pollution_avg_ug_m3",
    "air_pollution_population_weighted_average_ug_m3": "air_pollution_pop_weighted_avg_ug_m3",
    "value": "value",
    "value_lower_ci": "value_lower_ci",
    "value_upper_ci": "value_upper_ci",
    "value_for_100k_of_affected_population": "value_per_100k",
    "value_for_100k_of_affected_population_lower_ci": "value_per_100k_lower_ci",
    "value_for_100k_of_affected_population_upper_ci": "value_per_100k_upper_ci",
}

df = df.rename(columns=final_rename_map)

# =========================================
# Step 3: Clean text fields
# Trim spaces and preserve missing values
# =========================================
for col in df.select_dtypes(include="object").columns:
    df[col] = df[col].where(df[col].isna(), df[col].astype(str).str.strip())
    df[col] = df[col].replace({
        "nan": pd.NA,
        "None": pd.NA,
        "NaT": pd.NA,
        "": pd.NA
    })

# =========================================
# Step 4: Convert analytical columns to numeric
# Only convert columns that actually exist
# =========================================
numeric_cols = [
    "year",
    "affected_population",
    "air_pollution_avg_ug_m3",
    "air_pollution_pop_weighted_avg_ug_m3",
    "value",
    "value_lower_ci",
    "value_upper_ci",
    "value_per_100k",
    "value_per_100k_lower_ci",
    "value_per_100k_upper_ci",
]

existing_numeric_cols = [col for col in numeric_cols if col in df.columns]

for col in existing_numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Convert year to nullable integer if present
if "year" in df.columns:
    df["year"] = df["year"].astype("Int64")

# =========================================
# Step 5: Sort rows for easier inspection
# Only sort by columns that exist
# =========================================
sort_cols = [
    "country",
    "city",
    "pollutant",
    "category",
    "outcome",
    "health_indicator",
    "age_group",
]

existing_sort_cols = [col for col in sort_cols if col in df.columns]

if existing_sort_cols:
    df = df.sort_values(existing_sort_cols, kind="stable").reset_index(drop=True)

# =========================================
# Step 6: Save cleaned dataset
# =========================================
df.to_csv(output_file, index=False)

# =========================================
# Step 7: Save data dictionary
# original -> standardized -> final
# =========================================
data_dict = pd.DataFrame({
    "original_column_name": original_columns,
    "standardized_column_name": standardized_columns,
    "final_column_name": df.columns.tolist()
})

data_dict.to_csv(data_dict_file, index=False)

# =========================================
# Step 8: Print summary
# =========================================
print("Cleaning complete.")
print(f"Input file: {input_file}")
print(f"Cleaned dataset saved to: {output_file}")
print(f"Data dictionary saved to: {data_dict_file}")
print(f"Rows: {len(df):,}")
print(f"Columns: {len(df.columns)}")
print("Final columns:")
print(df.columns.tolist())