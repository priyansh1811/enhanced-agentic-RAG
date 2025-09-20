"""Basic tests for Archon."""

import sys
import os
import unittest
from unittest.mock import Mock, patch

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import Archon
from config.settings import Settings


class TestArchon(unittest.TestCase):
    """Test cases for Archon."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.archon = Archon()
    
    def test_archon_initialization(self):
        """Test Archon initialization."""
        self.assertIsNotNone(self.archon)
        self.assertIsNotNone(self.archon.settings)
    
    @patch('src.main.VectorStore')
    @patch('src.main.MemoryStore')
    @patch('src.main.SpecialistAgents')
    def test_setup(self, mock_specialist, mock_memory, mock_vector):
        """Test Archon setup."""
        # Mock the dependencies
        mock_vector.return_value = Mock()
        mock_memory.return_value = Mock()
        mock_specialist.return_value = Mock()
        
        # Mock file operations
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open()):
                self.archon.setup()
        
        # Verify setup was called
        mock_vector.assert_called_once()
        mock_memory.assert_called_once()
    
    def test_analyze_without_setup(self):
        """Test analyze method without setup."""
        with self.assertRaises(RuntimeError):
            self.archon.analyze("Test question")
    
    @patch('src.main.SpecialistAgents')
    def test_analyze_with_setup(self, mock_specialist):
        """Test analyze method with setup."""
        # Mock specialist agents
        mock_agent = Mock()
        mock_agent.analyze_request.return_value = {
            'response': 'Test response',
            'execution_steps': [],
            'verification_history': []
        }
        mock_specialist.return_value = mock_agent
        self.archon.specialist_agents = mock_agent
        
        result = self.archon.analyze("Test question")
        
        self.assertEqual(result['response'], 'Test response')
        mock_agent.analyze_request.assert_called_once_with("Test question")


class TestSettings(unittest.TestCase):
    """Test cases for Settings."""
    
    def test_settings_initialization(self):
        """Test Settings initialization."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            settings = Settings()
            self.assertEqual(settings.openai_api_key, 'test_key')
            self.assertEqual(settings.company_ticker, 'MSFT')
            self.assertEqual(settings.company_name, 'Microsoft')


def mock_open():
    """Mock open function for file operations."""
    from unittest.mock import mock_open as original_mock_open
    return original_mock_open(read_data='{"test": "data"}')


if __name__ == '__main__':
    unittest.main()
