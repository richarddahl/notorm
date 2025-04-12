#!/bin/bash

# Script to convert unittest-style tests to pytest style
# This script should be run from the project root directory

# Create destination directory if it doesn't exist
mkdir -p tests/unit/database

# Create a conftest.py file if it doesn't exist (we already did this)
if [ ! -f tests/unit/database/conftest.py ]; then
  echo "Error: conftest.py not found. Create it first."
  exit 1
fi

# Copy the example test file we created
if [ -f tests/unit/database/test_db_merge.py ]; then
  echo "File test_db_merge.py already exists in target directory. Skipping."
else
  cp tests/unit_unittest/database/test_db_merge.py.new tests/unit/database/test_db_merge.py
  echo "Copied test_db_merge.py to target directory."
fi

# List all unittest-style test files to convert
UNITTEST_FILES=(
  "test_db_basic.py"
  "test_db_create.py"
  "test_db_filter.py"
  "test_db_get.py"
  "test_session_async.py"
  "test_session_mock.py"
)

# Echo conversion instructions for each file
echo ""
echo "To complete the conversion, follow these steps for each file:"
echo ""
for file in "${UNITTEST_FILES[@]}"; do
  if [ "$file" == "test_db_merge.py" ]; then
    continue  # Skip the file we've already converted
  fi
  
  echo "1. Convert $file from unittest to pytest style:"
  echo "   - Replace 'unittest.IsolatedAsyncioTestCase' with '@pytest.mark.asyncio' decorator"
  echo "   - Convert 'setUp' method to pytest fixtures"
  echo "   - Replace assertion methods with pytest assertions"
  echo "   - Change class-based tests to function-based tests"
  echo "   - Use fixtures instead of self attributes"
  echo ""
  echo "2. Copy the converted file to tests/unit/database/$file"
  echo ""
  echo "3. Run tests to verify conversion:"
  echo "   python -m pytest tests/unit/database/$file -v"
  echo ""
  echo "--------------------------------------------------------"
  echo ""
done

echo "Once all files are converted, run the full test suite:"
echo "python -m pytest tests/unit/database/"
echo ""
echo "If all tests pass, you can delete the unittest-style files:"
echo "rm -rf tests/unit_unittest"