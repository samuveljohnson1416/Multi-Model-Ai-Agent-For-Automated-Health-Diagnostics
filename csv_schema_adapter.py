"""
CSV Schema Adapter for Phase-2 Integration
Handles schema validation and normalization with safety guarantees
"""

import pandas as pd
import io
from typing import Dict, List, Optional, Tuple


class CSVSchemaAdapter:
    """Adapter layer for CSV schema validation and normalization"""
    
    def __init__(self):
        # Define possible column name mappings
        self.column_mappings = {
            "test_name": ["test_name", "name", "parameter", "test", "parameter_name"],
            "value": ["value", "result", "measurement", "val"],
            "unit": ["unit", "units", "measure_unit", "uom"],
            "reference_range": ["reference_range", "ref_range", "normal_range", "range", "reference"]
        }
        
        # Required columns for Phase-2 processing
        self.required_columns = ["test_name", "value", "unit", "reference_range"]
    
    def validate_and_adapt_csv(self, csv_content: str) -> Dict:
        """
        Validate CSV schema and adapt to Phase-2 requirements
        Returns: {success: bool, data: DataFrame, error: str, schema_info: dict}
        """
        try:
            # Step 1: Parse CSV safely
            df = pd.read_csv(io.StringIO(csv_content))
            
            if df.empty:
                return {
                    "success": False,
                    "data": None,
                    "error": "CSV contains no data rows",
                    "schema_info": {"original_columns": [], "row_count": 0}
                }
            
            original_columns = list(df.columns)
            
            # Step 2: Detect and map columns
            column_mapping_result = self._detect_column_mapping(df.columns)
            
            if not column_mapping_result["success"]:
                return {
                    "success": False,
                    "data": None,
                    "error": column_mapping_result["error"],
                    "schema_info": {
                        "original_columns": original_columns,
                        "row_count": len(df),
                        "missing_columns": column_mapping_result["missing_columns"],
                        "detected_mappings": column_mapping_result["detected_mappings"]
                    }
                }
            
            # Step 3: Apply column mapping
            adapted_df = self._apply_column_mapping(df, column_mapping_result["mappings"])
            
            # Step 4: Validate data quality
            validation_result = self._validate_data_quality(adapted_df)
            
            return {
                "success": True,
                "data": adapted_df,
                "error": None,
                "schema_info": {
                    "original_columns": original_columns,
                    "mapped_columns": list(adapted_df.columns),
                    "row_count": len(adapted_df),
                    "valid_rows": validation_result["valid_rows"],
                    "column_mappings": column_mapping_result["mappings"],
                    "data_quality": validation_result
                }
            }
            
        except pd.errors.EmptyDataError:
            return {
                "success": False,
                "data": None,
                "error": "CSV file is empty or contains no valid data",
                "schema_info": {"original_columns": [], "row_count": 0}
            }
        except pd.errors.ParserError as e:
            return {
                "success": False,
                "data": None,
                "error": f"CSV parsing failed: {str(e)}",
                "schema_info": {"original_columns": [], "row_count": 0}
            }
        except Exception as e:
            return {
                "success": False,
                "data": None,
                "error": f"Unexpected error during CSV adaptation: {str(e)}",
                "schema_info": {"original_columns": [], "row_count": 0}
            }
    
    def _detect_column_mapping(self, csv_columns: List[str]) -> Dict:
        """Detect which CSV columns map to required Phase-2 columns"""
        
        csv_columns_lower = [col.lower().strip() for col in csv_columns]
        detected_mappings = {}
        missing_columns = []
        
        for required_col in self.required_columns:
            possible_names = [name.lower() for name in self.column_mappings[required_col]]
            
            # Find first matching column
            matched_column = None
            for i, csv_col in enumerate(csv_columns_lower):
                if csv_col in possible_names:
                    matched_column = csv_columns[i]  # Use original case
                    break
            
            if matched_column:
                detected_mappings[required_col] = matched_column
            else:
                missing_columns.append(required_col)
        
        if missing_columns:
            return {
                "success": False,
                "error": f"Required columns not found: {missing_columns}. Available columns: {list(csv_columns)}",
                "missing_columns": missing_columns,
                "detected_mappings": detected_mappings,
                "mappings": {}
            }
        
        return {
            "success": True,
            "error": None,
            "missing_columns": [],
            "detected_mappings": detected_mappings,
            "mappings": detected_mappings
        }
    
    def _apply_column_mapping(self, df: pd.DataFrame, mappings: Dict[str, str]) -> pd.DataFrame:
        """Apply column name mappings to create standardized DataFrame"""
        
        # Create new DataFrame with standardized column names
        adapted_df = pd.DataFrame()
        
        for standard_col, original_col in mappings.items():
            adapted_df[standard_col] = df[original_col]
        
        # Add any additional columns that might be useful
        additional_cols = ["raw_text", "confidence", "method"]
        for col in additional_cols:
            if col in df.columns and col not in adapted_df.columns:
                adapted_df[col] = df[col]
        
        return adapted_df
    
    def _validate_data_quality(self, df: pd.DataFrame) -> Dict:
        """Validate data quality for Phase-2 processing"""
        
        total_rows = len(df)
        valid_rows = 0
        issues = []
        
        for index, row in df.iterrows():
            row_valid = True
            
            # Check test_name
            if pd.isna(row["test_name"]) or str(row["test_name"]).strip() == "":
                row_valid = False
                issues.append(f"Row {index}: Missing test name")
            
            # Check value (allow string values like "Present/Absent")
            if pd.isna(row["value"]) or str(row["value"]).strip() == "":
                row_valid = False
                issues.append(f"Row {index}: Missing value")
            
            # Unit and reference_range can be empty (will be filled with "NA")
            
            if row_valid:
                valid_rows += 1
        
        return {
            "total_rows": total_rows,
            "valid_rows": valid_rows,
            "invalid_rows": total_rows - valid_rows,
            "data_quality_score": (valid_rows / total_rows) if total_rows > 0 else 0,
            "issues": issues[:10]  # Limit to first 10 issues
        }
    
    def get_schema_summary(self, schema_info: Dict) -> str:
        """Generate human-readable schema summary"""
        
        if not schema_info:
            return "No schema information available"
        
        summary = f"""CSV Schema Analysis:
- Original columns: {len(schema_info.get('original_columns', []))}
- Rows processed: {schema_info.get('row_count', 0)}
- Valid rows: {schema_info.get('valid_rows', 0)}
"""
        
        if "column_mappings" in schema_info:
            summary += "\nColumn Mappings:\n"
            for standard, original in schema_info["column_mappings"].items():
                summary += f"  {standard} ← {original}\n"
        
        if "data_quality" in schema_info:
            quality = schema_info["data_quality"]
            score = quality.get("data_quality_score", 0)
            summary += f"\nData Quality Score: {score:.1%}"
            
            if quality.get("issues"):
                summary += f"\nIssues found: {len(quality['issues'])}"
        
        return summary


def adapt_csv_for_phase2(csv_content: str) -> Dict:
    """
    Main function to adapt CSV for Phase-2 processing
    Returns standardized result format
    """
    adapter = CSVSchemaAdapter()
    result = adapter.validate_and_adapt_csv(csv_content)
    
    if result["success"]:
        # Convert back to CSV string for Phase-2
        adapted_csv = result["data"].to_csv(index=False)
        
        return {
            "success": True,
            "adapted_csv": adapted_csv,
            "original_csv": csv_content,
            "schema_info": result["schema_info"],
            "schema_summary": adapter.get_schema_summary(result["schema_info"]),
            "error": None
        }
    else:
        return {
            "success": False,
            "adapted_csv": None,
            "original_csv": csv_content,
            "schema_info": result["schema_info"],
            "schema_summary": adapter.get_schema_summary(result["schema_info"]),
            "error": result["error"]
        }


# Safety validation functions
def validate_numeric_formatting(value, default=0):
    """Safely format numeric values for f-strings"""
    try:
        if pd.isna(value) or value is None:
            return default
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_percentage(numerator, denominator, decimal_places=1):
    """Safely calculate percentage with proper formatting"""
    try:
        if denominator == 0:
            return 0.0
        result = (numerator / denominator) * 100
        return round(result, decimal_places)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0.0