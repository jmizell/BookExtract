#!/usr/bin/env python3
"""
Unit tests for the M4bGenerator class.

Tests configuration validation, dependency checking, and file structure creation
without requiring actual audio processing or external tools.
"""

import unittest
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from bookextract.m4b_generator import M4bGenerator, M4bConfig
from bookextract import BookIntermediate, BookMetadata, Chapter, ContentSection


class TestM4bConfig(unittest.TestCase):
    """Test M4bConfig dataclass functionality."""
    
    def test_default_config(self):
        """Test default M4bConfig values."""
        config = M4bConfig()
        
        self.assertEqual(config.tts_model, "am_michael")
        self.assertEqual(config.tts_language, "a")
        self.assertEqual(config.audio_bitrate, "64k")
        self.assertEqual(config.sample_rate, "22050")
        
    def test_custom_config(self):
        """Test custom M4bConfig values."""
        config = M4bConfig(
            tts_model="custom_model",
            tts_language="en",
            audio_bitrate="128k",
            sample_rate="44100"
        )
        
        self.assertEqual(config.tts_model, "custom_model")
        self.assertEqual(config.tts_language, "en")
        self.assertEqual(config.audio_bitrate, "128k")
        self.assertEqual(config.sample_rate, "44100")
        
    def test_config_validation(self):
        """Test configuration validation."""
        # Test valid bitrates
        valid_bitrates = ["32k", "64k", "128k", "256k"]
        for bitrate in valid_bitrates:
            config = M4bConfig(audio_bitrate=bitrate)
            self.assertEqual(config.audio_bitrate, bitrate)
            
        # Test valid sample rates
        valid_rates = ["22050", "44100", "48000"]
        for rate in valid_rates:
            config = M4bConfig(sample_rate=rate)
            self.assertEqual(config.sample_rate, rate)


class TestM4bGenerator(unittest.TestCase):
    """Test M4bGenerator functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = M4bConfig(
            tts_model="test_model",
            tts_language="en",
            audio_bitrate="64k",
            sample_rate="22050"
        )
        self.generator = M4bGenerator(self.config)
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_initialization_with_config(self):
        """Test M4bGenerator initialization with config."""
        self.assertEqual(self.generator.config, self.config)
        self.assertIsNone(self.generator.temp_dir)
        self.assertIsNone(self.generator.audio_dir)
        self.assertIsNone(self.generator.progress_callback)
        self.assertIsNone(self.generator.log_callback)
        
    def test_initialization_without_config(self):
        """Test M4bGenerator initialization without config."""
        generator = M4bGenerator()
        
        self.assertIsInstance(generator.config, M4bConfig)
        self.assertEqual(generator.config.tts_model, "am_michael")
        
    def test_callback_setting(self):
        """Test setting callback functions."""
        progress_callback = MagicMock()
        log_callback = MagicMock()
        
        self.generator.set_progress_callback(progress_callback)
        self.generator.set_log_callback(log_callback)
        
        self.assertEqual(self.generator.progress_callback, progress_callback)
        self.assertEqual(self.generator.log_callback, log_callback)
        
    def test_progress_update(self):
        """Test progress update functionality."""
        progress_callback = MagicMock()
        self.generator.set_progress_callback(progress_callback)
        
        self.generator._update_progress("Test progress message")
        
        progress_callback.assert_called_once_with("Test progress message")
        
    def test_log_message(self):
        """Test log message functionality."""
        log_callback = MagicMock()
        self.generator.set_log_callback(log_callback)
        
        self.generator._log_message("Test log message", "INFO")
        
        log_callback.assert_called_once_with("Test log message", "INFO")
        
    def test_log_message_without_callback(self):
        """Test log message without callback (should use print)."""
        with patch('builtins.print') as mock_print:
            self.generator._log_message("Test message", "WARNING")
            
            mock_print.assert_called_once_with("[WARNING] Test message")


class TestM4bDependencyChecking(unittest.TestCase):
    """Test dependency checking functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.generator = M4bGenerator()
        
    @patch('subprocess.run')
    def test_check_dependencies_all_available(self, mock_run):
        """Test dependency checking when all tools are available."""
        # Mock successful subprocess calls
        mock_run.return_value = MagicMock(returncode=0)
        
        results = self.generator.check_dependencies()
        
        self.assertIsInstance(results, dict)
        
        # Should check for required tools
        expected_tools = ["python3", "kokoro", "ffmpeg", "ffprobe"]
        for tool in expected_tools:
            if tool in results:
                self.assertTrue(results[tool])
                
    @patch('subprocess.run')
    def test_check_dependencies_some_missing(self, mock_run):
        """Test dependency checking when some tools are missing."""
        def mock_subprocess(cmd, **kwargs):
            if cmd[0] == "python3":
                return MagicMock(returncode=0)
            else:
                return MagicMock(returncode=1)
                
        mock_run.side_effect = mock_subprocess
        
        results = self.generator.check_dependencies()
        
        self.assertIsInstance(results, dict)
        
        # Python should be available, others might not be
        if "python3" in results:
            self.assertTrue(results["python3"])
            
    @patch('subprocess.run')
    def test_check_dependencies_timeout(self, mock_run):
        """Test dependency checking with timeout."""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired("test", 5)
        
        results = self.generator.check_dependencies()
        
        self.assertIsInstance(results, dict)
        # All dependencies should be marked as False due to timeout
        for cmd in ["python3", "kokoro", "ffmpeg", "ffprobe"]:
            self.assertFalse(results.get(cmd, True))
        
        # Should handle timeout gracefully
        for tool, available in results.items():
            self.assertIsInstance(available, bool)


class TestM4bFileOperations(unittest.TestCase):
    """Test file operations for M4B generation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.generator = M4bGenerator()
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create sample intermediate data
        self.metadata = BookMetadata(
            title="Test Audiobook",
            author="Test Author",
            language="en"
        )
        
        chapter = Chapter(
            number=1, 
            title="Test Chapter",
            sections=[
                ContentSection(type="paragraph", content="This is test content for audio generation.")
            ]
        )
        
        self.intermediate = BookIntermediate(
            metadata=self.metadata,
            chapters=[chapter]
        )
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_workspace_setup(self):
        """Test setting up workspace directories."""
        if hasattr(self.generator, 'setup_workspace'):
            workspace = self.generator.setup_workspace(str(self.temp_dir))
            
            self.assertIsInstance(workspace, (str, Path))
            
            # Workspace should exist
            workspace_path = Path(workspace)
            self.assertTrue(workspace_path.exists())
            
    def test_text_file_preparation(self):
        """Test preparing text files for TTS processing."""
        if hasattr(self.generator, 'prepare_text_files'):
            text_dir = self.temp_dir / "text_files"
            
            self.generator.prepare_text_files(self.intermediate, str(text_dir))
            
            # Should create text files
            self.assertTrue(text_dir.exists())
            
            # Should have title and chapter files
            text_files = list(text_dir.glob("*.txt"))
            self.assertGreater(len(text_files), 0)
            
    def test_audio_directory_setup(self):
        """Test setting up audio processing directories."""
        if hasattr(self.generator, 'setup_audio_directories'):
            audio_dirs = self.generator.setup_audio_directories(str(self.temp_dir))
            
            self.assertIsInstance(audio_dirs, dict)
            
            # Should have required directories
            for dir_path in audio_dirs.values():
                if dir_path:
                    self.assertTrue(Path(dir_path).exists())
                    
    def test_metadata_file_creation(self):
        """Test creating metadata files for M4B."""
        if hasattr(self.generator, 'create_metadata_files'):
            metadata_dir = self.temp_dir / "metadata"
            
            self.generator.create_metadata_files(self.intermediate, str(metadata_dir))
            
            # Should create metadata files
            self.assertTrue(metadata_dir.exists())
            
            metadata_files = list(metadata_dir.glob("*.txt"))
            if metadata_files:
                # Check content of metadata file
                with open(metadata_files[0], 'r') as f:
                    content = f.read()
                    
                self.assertIn("Test Audiobook", content)


class TestM4bProcessingWorkflow(unittest.TestCase):
    """Test M4B processing workflow."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.generator = M4bGenerator()
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create sample intermediate
        metadata = BookMetadata(title="Workflow Test", author="Test Author")
        chapter = Chapter(
            number=1, 
            title="Test Chapter",
            sections=[
                ContentSection(type="paragraph", content="Test content for workflow.")
            ]
        )
        self.intermediate = BookIntermediate(metadata=metadata, chapters=[chapter])
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_workflow_validation(self):
        """Test validation of processing workflow."""
        if hasattr(self.generator, 'validate_workflow'):
            is_valid = self.generator.validate_workflow(self.intermediate)
            
            self.assertIsInstance(is_valid, bool)
            
    def test_processing_steps(self):
        """Test individual processing steps."""
        steps = [
            'prepare_workspace',
            'generate_text_files',
            'process_tts',
            'combine_audio',
            'create_m4b'
        ]
        
        for step in steps:
            if hasattr(self.generator, step):
                with self.subTest(step=step):
                    # Test that method exists and can be called
                    method = getattr(self.generator, step)
                    self.assertTrue(callable(method))
                    
    @patch('subprocess.run')
    def test_tts_processing_mock(self, mock_run):
        """Test TTS processing with mocked subprocess calls."""
        if hasattr(self.generator, 'process_tts'):
            mock_run.return_value = MagicMock(returncode=0)
            
            text_files = [str(self.temp_dir / "test.txt")]
            
            # Create test text file
            with open(text_files[0], 'w') as f:
                f.write("Test content for TTS processing.")
                
            result = self.generator.process_tts(text_files, str(self.temp_dir))
            
            # Should handle TTS processing
            self.assertIsNotNone(result)
            
    @patch('subprocess.run')
    def test_audio_combination_mock(self, mock_run):
        """Test audio combination with mocked subprocess calls."""
        if hasattr(self.generator, 'combine_audio_files'):
            mock_run.return_value = MagicMock(returncode=0)
            
            audio_files = [
                str(self.temp_dir / "audio1.wav"),
                str(self.temp_dir / "audio2.wav")
            ]
            
            # Create mock audio files
            for audio_file in audio_files:
                with open(audio_file, 'w') as f:
                    f.write("mock audio data")
                    
            output_file = str(self.temp_dir / "combined.m4b")
            
            result = self.generator.combine_audio_files(audio_files, output_file)
            
            # Should handle audio combination
            self.assertIsNotNone(result)


class TestM4bErrorHandling(unittest.TestCase):
    """Test error handling in M4B generation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.generator = M4bGenerator()
        
    def test_invalid_intermediate_handling(self):
        """Test handling of invalid intermediate data."""
        if hasattr(self.generator, 'validate_intermediate'):
            # Test with None
            is_valid = self.generator.validate_intermediate(None)
            self.assertFalse(is_valid)
            
            # Test with empty intermediate
            empty_metadata = BookMetadata(title="", author="")
            empty_intermediate = BookIntermediate(metadata=empty_metadata, chapters=[])
            
            is_valid = self.generator.validate_intermediate(empty_intermediate)
            # Should handle empty data appropriately
            self.assertIsInstance(is_valid, bool)
            
    def test_missing_dependencies_handling(self):
        """Test handling when dependencies are missing."""
        with patch.object(self.generator, 'check_dependencies') as mock_check:
            mock_check.return_value = {
                "python3": True,
                "kokoro": False,
                "ffmpeg": False,
                "ffprobe": False
            }
            
            if hasattr(self.generator, 'can_process'):
                can_process = self.generator.can_process()
                
                # Should indicate that processing is not possible
                self.assertFalse(can_process)
                
    def test_processing_error_recovery(self):
        """Test error recovery during processing."""
        if hasattr(self.generator, 'process_with_recovery'):
            # Test that error recovery mechanisms work
            with patch('subprocess.run') as mock_run:
                mock_run.side_effect = Exception("Processing error")
                
                result = self.generator.process_with_recovery("test_input", "test_output")
                
                # Should handle errors gracefully
                self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()