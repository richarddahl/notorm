# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Tests for the CLI module.

These tests verify the functionality of the command-line interface.
"""

import pytest
from unittest.mock import patch, MagicMock
import os
import sys
import tempfile

from uno.devtools.cli.main import (
    main,
    CliCommands,
    handle_debug_command,
    handle_profile_command,
    handle_codegen_command,
    handle_docs_command
)


class TestCliMain:
    """Tests for the CLI main entry point."""
    
    @patch("uno.devtools.cli.main.typer")
    def test_main_with_typer(self, mock_typer):
        """Test the main entry point using Typer."""
        # Configure the mock
        mock_typer.Typer.return_value = mock_typer
        mock_typer.run.return_value = None
        
        # Call the main function
        main()
        
        # Check that Typer was used
        mock_typer.Typer.assert_called_once()
        mock_typer.run.assert_called_once()
    
    @patch("uno.devtools.cli.main.typer")
    @patch("uno.devtools.cli.main.argparse")
    def test_main_with_argparse_fallback(self, mock_argparse, mock_typer):
        """Test the main entry point with argparse fallback."""
        # Configure the typer mock to raise an ImportError
        mock_typer.Typer.side_effect = ImportError("Typer not found")
        
        # Configure the argparse mock
        mock_parser = MagicMock()
        mock_argparse.ArgumentParser.return_value = mock_parser
        mock_parser.parse_args.return_value = MagicMock(
            command="debug",
            subcommand="trace",
            target="example.py",
            options=[]
        )
        
        # Call the main function
        with patch("uno.devtools.cli.main.handle_debug_command") as mock_handle_debug:
            main()
            
            # Check that argparse was used
            mock_argparse.ArgumentParser.assert_called_once()
            mock_parser.parse_args.assert_called_once()
            
            # Check that the command handler was called
            mock_handle_debug.assert_called_once()


class TestDebugCommands:
    """Tests for the debug commands."""
    
    @patch("uno.devtools.cli.main.DebugMiddleware")
    def test_handle_debug_middleware(self, mock_middleware):
        """Test handling the debug middleware command."""
        # Configure the mock
        mock_middleware.return_value = mock_middleware
        
        # Handle the middleware command
        handle_debug_command(
            subcommand="middleware",
            target="example.py",
            options=["--log-requests", "--log-responses"]
        )
        
        # Check that the middleware was created with the right options
        mock_middleware.assert_called_once_with(
            enabled=True,
            log_requests=True,
            log_responses=True,
            log_sql=False,
            log_errors=False
        )
    
    @patch("uno.devtools.cli.main.trace_function")
    @patch("uno.devtools.cli.main.importlib")
    def test_handle_debug_trace(self, mock_importlib, mock_trace):
        """Test handling the debug trace command."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".py") as temp_file:
            # Write a sample function to the file
            temp_file.write(b"def sample_function():\n    return 'test'\n")
            temp_file.flush()
            
            # Configure the import_module mock
            mock_module = MagicMock()
            mock_module.sample_function = MagicMock(return_value="test")
            mock_importlib.import_module.return_value = mock_module
            
            # Configure the trace_function mock
            mock_trace.return_value = MagicMock(return_value="traced_test")
            
            # Handle the trace command
            handle_debug_command(
                subcommand="trace",
                target=temp_file.name,
                options=["--function=sample_function"]
            )
            
            # Check that the function was imported and traced
            mock_importlib.import_module.assert_called()
            mock_trace.assert_called_with(mock_module.sample_function)
    
    @patch("uno.devtools.cli.main.SqlQueryAnalyzer")
    def test_handle_debug_sql(self, mock_analyzer):
        """Test handling the debug SQL command."""
        # Configure the mock
        mock_analyzer_instance = MagicMock()
        mock_analyzer.return_value = mock_analyzer_instance
        
        # Handle the SQL command
        handle_debug_command(
            subcommand="sql",
            target="example.py",
            options=["--watch", "--threshold=100"]
        )
        
        # Check that the analyzer was created with the right options
        mock_analyzer.assert_called_once_with(
            threshold_ms=100,
            detect_n_plus_1=True,
            log_queries=True
        )
        mock_analyzer_instance.start_monitoring.assert_called_once()


class TestProfileCommands:
    """Tests for the profile commands."""
    
    @patch("uno.devtools.cli.main.profile")
    @patch("uno.devtools.cli.main.importlib")
    def test_handle_profile_function(self, mock_importlib, mock_profile):
        """Test handling the profile function command."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".py") as temp_file:
            # Write a sample function to the file
            temp_file.write(b"def sample_function():\n    return 'test'\n")
            temp_file.flush()
            
            # Configure the import_module mock
            mock_module = MagicMock()
            mock_module.sample_function = MagicMock(return_value="test")
            mock_importlib.import_module.return_value = mock_module
            
            # Configure the profile mock
            mock_profile.return_value = MagicMock(return_value="profiled_test")
            
            # Handle the profile command
            handle_profile_command(
                subcommand="function",
                target=temp_file.name,
                options=["--function=sample_function"]
            )
            
            # Check that the function was imported and profiled
            mock_importlib.import_module.assert_called()
            mock_profile.assert_called_with(
                mock_module.sample_function,
                use_cprofile=False,
                output=None
            )
    
    @patch("uno.devtools.cli.main.MemoryTracker")
    @patch("uno.devtools.cli.main.importlib")
    def test_handle_profile_memory(self, mock_importlib, mock_tracker):
        """Test handling the profile memory command."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".py") as temp_file:
            # Write a sample function to the file
            temp_file.write(b"def sample_function():\n    return 'test'\n")
            temp_file.flush()
            
            # Configure the import_module mock
            mock_module = MagicMock()
            mock_module.sample_function = MagicMock(return_value="test")
            mock_importlib.import_module.return_value = mock_module
            
            # Configure the tracker mock
            mock_tracker_instance = MagicMock()
            mock_tracker.return_value = mock_tracker_instance
            
            # Handle the memory command
            handle_profile_command(
                subcommand="memory",
                target=temp_file.name,
                options=["--function=sample_function"]
            )
            
            # Check that the function was imported and memory was tracked
            mock_importlib.import_module.assert_called()
            mock_tracker.assert_called_with(
                "sample_function",
                config=pytest.helpers.any_instance_of_object
            )


class TestCodegenCommands:
    """Tests for the codegen commands."""
    
    @patch("uno.devtools.cli.main.ModelGenerator")
    def test_handle_codegen_model(self, mock_generator):
        """Test handling the codegen model command."""
        # Configure the mock
        mock_generator_instance = MagicMock()
        mock_generator.return_value = mock_generator_instance
        mock_generator_instance.generate_model.return_value = "# Generated model code"
        
        # Create a temporary file to write the output
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_file:
            temp_path = temp_file.name
            
            try:
                # Handle the model command
                handle_codegen_command(
                    subcommand="model",
                    target="User",
                    options=[
                        "--table=users",
                        "--fields=id:int:pk,name:str,email:str:unique",
                        "--output=" + temp_path
                    ]
                )
                
                # Check that the generator was called with the right options
                mock_generator.assert_called_once()
                mock_generator_instance.generate_model.assert_called_once()
                
                # Check that the output was written to the file
                with open(temp_path, "r") as f:
                    content = f.read()
                    assert "# Generated model code" in content
            finally:
                # Clean up the temporary file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
    
    @patch("uno.devtools.cli.main.RepositoryGenerator")
    def test_handle_codegen_repository(self, mock_generator):
        """Test handling the codegen repository command."""
        # Configure the mock
        mock_generator_instance = MagicMock()
        mock_generator.return_value = mock_generator_instance
        mock_generator_instance.generate_repository.return_value = "# Generated repository code"
        
        # Create a temporary file to write the output
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_file:
            temp_path = temp_file.name
            
            try:
                # Handle the repository command
                handle_codegen_command(
                    subcommand="repository",
                    target="User",
                    options=[
                        "--table=users",
                        "--output=" + temp_path
                    ]
                )
                
                # Check that the generator was called with the right options
                mock_generator.assert_called_once()
                mock_generator_instance.generate_repository.assert_called_once()
                
                # Check that the output was written to the file
                with open(temp_path, "r") as f:
                    content = f.read()
                    assert "# Generated repository code" in content
            finally:
                # Clean up the temporary file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
    
    @patch("uno.devtools.cli.main.ApiGenerator")
    def test_handle_codegen_api(self, mock_generator):
        """Test handling the codegen API command."""
        # Configure the mock
        mock_generator_instance = MagicMock()
        mock_generator.return_value = mock_generator_instance
        mock_generator_instance.generate_api.return_value = "# Generated API code"
        
        # Create a temporary file to write the output
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_file:
            temp_path = temp_file.name
            
            try:
                # Handle the API command
                handle_codegen_command(
                    subcommand="api",
                    target="User",
                    options=[
                        "--route=/users",
                        "--schema=UserSchema",
                        "--repository=UserRepository",
                        "--endpoints=get,post,put,delete",
                        "--output=" + temp_path
                    ]
                )
                
                # Check that the generator was called with the right options
                mock_generator.assert_called_once()
                mock_generator_instance.generate_api.assert_called_once()
                
                # Check that the output was written to the file
                with open(temp_path, "r") as f:
                    content = f.read()
                    assert "# Generated API code" in content
            finally:
                # Clean up the temporary file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)


class TestDocsCommands:
    """Tests for the docs commands."""
    
    @patch("uno.devtools.cli.main.DocGenerator")
    def test_handle_docs_generate(self, mock_generator):
        """Test handling the docs generate command."""
        # Configure the mock
        mock_generator_instance = MagicMock()
        mock_generator.return_value = mock_generator_instance
        
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Handle the generate command
            handle_docs_command(
                subcommand="generate",
                target="uno",
                options=[
                    "--output=" + temp_dir,
                    "--format=markdown"
                ]
            )
            
            # Check that the generator was called with the right options
            mock_generator.assert_called_once()
            mock_generator_instance.generate_docs_for_package.assert_called_with(
                "uno",
                output_dir=temp_dir,
                include_private=False
            )
    
    @patch("uno.devtools.cli.main.os.path.exists")
    @patch("uno.devtools.cli.main.shutil.copytree")
    @patch("uno.devtools.cli.main.subprocess.run")
    def test_handle_docs_serve(self, mock_run, mock_copytree, mock_exists):
        """Test handling the docs serve command."""
        # Configure the mocks
        mock_exists.return_value = True
        
        # Handle the serve command
        handle_docs_command(
            subcommand="serve",
            target="/path/to/docs",
            options=["--port=8000"]
        )
        
        # Check that the server was started
        mock_run.assert_called_with(
            ["python", "-m", "http.server", "8000", "-d", "/path/to/docs"],
            check=True
        )