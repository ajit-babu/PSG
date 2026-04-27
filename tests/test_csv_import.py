"""
PSG - Professional Safety Guardian
Test CSV Import and Validation Module

This module tests the CSV import and validation functionality.
"""

from pathlib import Path

from app.services.csv_importer import CSVImporter, ImportConfig, create_importer
from app.services.csv_validator import CSVValidator, ValidationResult, create_validator


def test_csv_validator():
    """Test the CSV validator with sample data."""
    print("=" * 60)
    print("Testing CSV Validator")
    print("=" * 60)
    
    validator = CSVValidator()
    
    # Test valid row
    valid_row = {
        "incident_id": "INC-001",
        "date": "2026-01-15",
        "time": "08:30",
        "location": "Site A - Floor 3",
        "severity": "near_miss",
        "description": "Worker nearly slipped on wet floor",
        "reported_by": "John Smith",
        "email": "john.smith@example.com",
        "phone": "+971-50-123-4567",
    }
    
    result = validator.validate_row(valid_row)
    print(f"\nValid row test: {'PASSED' if result.is_valid else 'FAILED'}")
    if not result.is_valid:
        print(f"  Errors: {result.error_message}")
    
    # Test invalid row - missing required field
    invalid_row_missing = {
        "incident_id": "",
        "date": "2026-01-15",
        "location": "Site A",
        "severity": "invalid_severity",
        "description": "Test",
        "reported_by": "Test User",
    }
    
    result = validator.validate_row(invalid_row_missing)
    print(f"\nInvalid row (missing required) test: {'PASSED' if not result.is_valid else 'FAILED'}")
    if not result.is_valid:
        print(f"  Errors: {result.error_message}")
    
    # Test invalid email
    invalid_email_row = {
        "incident_id": "INC-002",
        "date": "2026-01-15",
        "location": "Site A",
        "severity": "minor",
        "description": "Test",
        "reported_by": "Test User",
        "email": "not-an-email",
    }
    
    result = validator.validate_row(invalid_email_row)
    print(f"\nInvalid email test: {'PASSED' if not result.is_valid else 'FAILED'}")
    if not result.is_valid:
        print(f"  Errors: {result.error_message}")
    
    # Test batch validation
    test_rows = [valid_row, invalid_row_missing, invalid_email_row]
    summary = validator.get_validation_summary(test_rows)
    print(f"\nBatch validation summary:")
    print(f"  Total: {summary['total_rows']}")
    print(f"  Valid: {summary['valid_rows']}")
    print(f"  Invalid: {summary['invalid_rows']}")
    print(f"  Success rate: {summary['success_rate']:.1f}%")


def test_csv_importer():
    """Test the CSV importer with sample file."""
    print("\n" + "=" * 60)
    print("Testing CSV Importer")
    print("=" * 60)
    
    # Create importer with default config
    importer = create_importer(
        encoding="utf-8",
        validate_on_import=True,
        skip_invalid_rows=False,
    )
    
    # Test with sample file
    sample_file = Path(__file__).parent.parent / "samples" / "incidents_sample.csv"
    
    if sample_file.exists():
        # Preview the file
        columns, preview = importer.preview_file(sample_file, max_rows=3)
        print(f"\nFile preview:")
        print(f"  Columns: {columns}")
        print(f"  Preview rows: {len(preview)}")
        
        # Import the file
        result = importer.import_file(sample_file)
        
        print(f"\nImport results:")
        print(f"  Total rows: {result.total_rows}")
        print(f"  Successful: {result.successful_rows}")
        print(f"  Failed: {result.failed_rows}")
        print(f"  Success rate: {result.success_rate:.1f}%")
        
        if result.errors:
            print(f"\n  Errors:")
            for error in result.errors:
                print(f"    - {error}")
        
        if result.warnings:
            print(f"\n  Warnings:")
            for warning in result.warnings:
                print(f"    - {warning}")
    else:
        print(f"\nSample file not found: {sample_file}")


def test_custom_field_mapping():
    """Test CSV import with custom field mapping."""
    print("\n" + "=" * 60)
    print("Testing Custom Field Mapping")
    print("=" * 60)
    
    importer = create_importer()
    
    # Define field mapping
    field_mapping = {
        "incident_id": "id",
        "date": "incident_date",
        "severity": "severity_level",
    }
    
    sample_file = Path(__file__).parent.parent / "samples" / "incidents_sample.csv"
    
    if sample_file.exists():
        result = importer.import_file(sample_file, field_mapping=field_mapping)
        print(f"\nMapped import results:")
        print(f"  Total rows: {result.total_rows}")
        print(f"  Successful: {result.successful_rows}")
        
        if result.imported_data:
            print(f"\n  First row (mapped):")
            for key, value in result.imported_data[0].items():
                print(f"    {key}: {value}")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("PSG CSV Import and Validation Tests")
    print("=" * 60)
    
    test_csv_validator()
    test_csv_importer()
    test_custom_field_mapping()
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()