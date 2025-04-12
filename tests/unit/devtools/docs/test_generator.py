# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Tests for the documentation generator module.

These tests verify the functionality of the documentation generation tools.
"""

import pytest
from unittest.mock import patch, MagicMock
import os
import tempfile
import shutil
import inspect

from uno.devtools.docs.generator import (
    DocGenerator,
    DocItem,
    DocItemType,
    ModuleDoc,
    ClassDoc,
    FunctionDoc,
    DocGeneratorConfig
)


# Create a sample module, class, and function for testing
def sample_function(param1: str, param2: int = 0) -> str:
    """
    A sample function for testing documentation.
    
    Args:
        param1: The first parameter
        param2: The second parameter
    
    Returns:
        A string result
    
    Raises:
        ValueError: If param1 is empty
    """
    if not param1:
        raise ValueError("param1 cannot be empty")
    return f"{param1}_{param2}"


class SampleClass:
    """
    A sample class for testing documentation.
    
    Attributes:
        attr1: The first attribute
        attr2: The second attribute
    """
    
    def __init__(self, attr1: str, attr2: int = 0):
        """
        Initialize the sample class.
        
        Args:
            attr1: The first attribute
            attr2: The second attribute
        """
        self.attr1 = attr1
        self.attr2 = attr2
    
    def sample_method(self, param: str) -> str:
        """
        A sample method for testing.
        
        Args:
            param: The parameter
        
        Returns:
            A string result
        """
        return f"{self.attr1}_{param}"


class TestDocGenerator:
    """Tests for the DocGenerator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a temporary directory for doc outputs
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        # Remove the temporary directory
        shutil.rmtree(self.temp_dir)
    
    def test_extract_function_doc(self):
        """Test extracting documentation from a function."""
        # Create a doc generator
        generator = DocGenerator()
        
        # Extract documentation from the sample function
        func_doc = generator.extract_function_doc(sample_function)
        
        # Check the extracted documentation
        assert func_doc.name == "sample_function"
        assert func_doc.doc_type == DocItemType.FUNCTION
        assert func_doc.signature is not None
        assert "param1: str" in func_doc.signature
        assert "param2: int = 0" in func_doc.signature
        assert "-> str" in func_doc.signature
        assert func_doc.docstring is not None
        assert "A sample function for testing documentation" in func_doc.docstring
        assert len(func_doc.args) == 2
        assert func_doc.args[0].name == "param1"
        assert func_doc.args[0].type == "str"
        assert func_doc.args[0].description == "The first parameter"
        assert func_doc.args[1].name == "param2"
        assert func_doc.args[1].type == "int"
        assert func_doc.args[1].description == "The second parameter"
        assert func_doc.returns is not None
        assert func_doc.returns.type == "str"
        assert func_doc.returns.description == "A string result"
        assert len(func_doc.raises) == 1
        assert func_doc.raises[0].exception_type == "ValueError"
        assert func_doc.raises[0].description == "If param1 is empty"
    
    def test_extract_class_doc(self):
        """Test extracting documentation from a class."""
        # Create a doc generator
        generator = DocGenerator()
        
        # Extract documentation from the sample class
        class_doc = generator.extract_class_doc(SampleClass)
        
        # Check the extracted documentation
        assert class_doc.name == "SampleClass"
        assert class_doc.doc_type == DocItemType.CLASS
        assert class_doc.docstring is not None
        assert "A sample class for testing documentation" in class_doc.docstring
        assert len(class_doc.methods) == 2  # __init__ and sample_method
        assert class_doc.methods[0].name == "__init__"
        assert class_doc.methods[1].name == "sample_method"
        assert len(class_doc.methods[0].args) == 3  # self, attr1, attr2
        assert class_doc.methods[0].args[1].name == "attr1"
        assert class_doc.methods[0].args[1].type == "str"
        assert class_doc.methods[1].returns is not None
        assert class_doc.methods[1].returns.type == "str"
        assert class_doc.methods[1].returns.description == "A string result"
    
    def test_extract_module_doc(self):
        """Test extracting documentation from a module."""
        # Create a mock module
        mock_module = MagicMock()
        mock_module.__name__ = "sample_module"
        mock_module.__doc__ = "A sample module for testing."
        mock_module.__path__ = ["/path/to/module"]
        mock_module.__file__ = "/path/to/module/__init__.py"
        
        # Add the sample function and class to the module
        mock_module.sample_function = sample_function
        mock_module.SampleClass = SampleClass
        
        # Create a doc generator
        generator = DocGenerator()
        
        # Mock the inspect.getmembers function
        with patch("uno.devtools.docs.generator.inspect.getmembers") as mock_getmembers:
            # Configure the mock to return our sample items
            mock_getmembers.return_value = [
                ("sample_function", sample_function),
                ("SampleClass", SampleClass)
            ]
            
            # Extract documentation from the mock module
            module_doc = generator.extract_module_doc(mock_module)
            
            # Check the extracted documentation
            assert module_doc.name == "sample_module"
            assert module_doc.doc_type == DocItemType.MODULE
            assert module_doc.docstring == "A sample module for testing."
            assert len(module_doc.functions) == 1
            assert module_doc.functions[0].name == "sample_function"
            assert len(module_doc.classes) == 1
            assert module_doc.classes[0].name == "SampleClass"
    
    def test_generate_markdown(self):
        """Test generating markdown documentation."""
        # Create a doc generator
        generator = DocGenerator()
        
        # Create a sample module doc
        module_doc = ModuleDoc(
            name="sample_module",
            doc_type=DocItemType.MODULE,
            docstring="A sample module for testing.",
            filepath="/path/to/module/__init__.py",
            functions=[
                generator.extract_function_doc(sample_function)
            ],
            classes=[
                generator.extract_class_doc(SampleClass)
            ]
        )
        
        # Generate markdown
        markdown = generator.generate_markdown(module_doc)
        
        # Check the generated markdown
        assert "# sample_module" in markdown
        assert "A sample module for testing." in markdown
        assert "## Functions" in markdown
        assert "### sample_function" in markdown
        assert "A sample function for testing documentation" in markdown
        assert "## Classes" in markdown
        assert "### SampleClass" in markdown
        assert "A sample class for testing documentation" in markdown
        assert "#### Methods" in markdown
        assert "##### __init__" in markdown
        assert "##### sample_method" in markdown
    
    def test_generate_docs_for_package(self):
        """Test generating documentation for a package."""
        # Create a mock package structure
        mock_package = MagicMock()
        mock_package.__name__ = "sample_package"
        mock_package.__doc__ = "A sample package for testing."
        mock_package.__path__ = ["/path/to/package"]
        mock_package.__file__ = "/path/to/package/__init__.py"
        
        # Add the sample function and class to the package
        mock_package.sample_function = sample_function
        mock_package.SampleClass = SampleClass
        
        # Create a doc generator
        generator = DocGenerator()
        
        # Mock the necessary functions
        with patch("uno.devtools.docs.generator.pkgutil.iter_modules") as mock_iter_modules, \
             patch("uno.devtools.docs.generator.importlib.import_module") as mock_import_module, \
             patch("uno.devtools.docs.generator.inspect.getmembers") as mock_getmembers, \
             patch("uno.devtools.docs.generator.os.path.exists") as mock_exists, \
             patch("uno.devtools.docs.generator.os.makedirs") as mock_makedirs, \
             patch("builtins.open", create=True) as mock_open:
            
            # Configure the mocks
            mock_iter_modules.return_value = [
                (None, "submodule", False)
            ]
            mock_import_module.return_value = mock_package
            mock_getmembers.return_value = [
                ("sample_function", sample_function),
                ("SampleClass", SampleClass)
            ]
            mock_exists.return_value = False
            mock_open.return_value.__enter__.return_value = MagicMock()
            
            # Generate documentation
            generator.generate_docs_for_package(
                "sample_package", 
                output_dir=self.temp_dir
            )
            
            # Check that import_module was called
            mock_import_module.assert_any_call("sample_package")
            mock_import_module.assert_any_call("sample_package.submodule")
            
            # Check that files were written
            mock_makedirs.assert_called()
            mock_open.assert_called()
    
    def test_generate_with_config(self):
        """Test generating documentation with custom configuration."""
        # Create a doc generator with custom config
        config = DocGeneratorConfig(
            include_private=False,
            include_source=True,
            include_toc=True,
            output_format="markdown"
        )
        generator = DocGenerator(config=config)
        
        # Extract documentation from the sample function
        func_doc = generator.extract_function_doc(sample_function)
        
        # Check that the configuration was applied
        assert func_doc.source_code is not None
        assert "def sample_function" in func_doc.source_code
        
        # Generate markdown with custom config
        markdown = generator.generate_markdown(func_doc)
        
        # Check that the configuration was applied
        assert "Source Code" in markdown
        assert "```python" in markdown