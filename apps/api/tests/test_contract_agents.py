import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import asyncio

from src.contract.agents import (
    generate_toc,
    get_title,
    edit_contract,
    suggest_edits
)


@pytest.mark.asyncio
class TestContractAgents:
    """Test contract AI agent functions."""
    
    @patch('src.contract.agents.genai')
    async def test_generate_toc_success(self, mock_genai):
        """Test successful TOC generation."""
        # Mock the model and response
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = """1. Introduction
2. Service Description
3. Terms and Conditions
4. Payment Terms
5. Termination"""
        
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        prompt = "Create a service agreement for web development"
        result = await generate_toc(prompt)
        
        assert isinstance(result, list)
        assert len(result) == 5
        assert "Introduction" in result[0]
        assert "Service Description" in result[1]
        assert "Payment Terms" in result[3]
        
        # Verify the model was called correctly
        mock_genai.GenerativeModel.assert_called_once_with("gemini-2.0-flash-exp")
        mock_model.generate_content.assert_called_once()
    
    @patch('src.contract.agents.genai')
    async def test_generate_toc_with_retries(self, mock_genai):
        """Test TOC generation with retries on failure."""
        mock_model = MagicMock()
        
        # First call fails, second succeeds
        mock_response_success = MagicMock()
        mock_response_success.text = "1. Introduction\n2. Terms"
        
        mock_model.generate_content.side_effect = [
            Exception("API Error"),
            mock_response_success
        ]
        mock_genai.GenerativeModel.return_value = mock_model
        
        result = await generate_toc("test prompt")
        
        assert len(result) == 2
        assert mock_model.generate_content.call_count == 2
    
    @patch('src.contract.agents.genai')
    async def test_generate_toc_empty_response(self, mock_genai):
        """Test TOC generation with empty response."""
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = ""
        
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        result = await generate_toc("test prompt")
        
        assert result == []
    
    @patch('src.contract.agents.genai')
    async def test_get_title_success(self, mock_genai):
        """Test successful title generation."""
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Web Development Service Agreement"
        
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        prompt = "Create a service agreement for web development"
        result = await get_title(prompt)
        
        assert result == "Web Development Service Agreement"
        
        # Verify the model was called with correct parameters
        mock_genai.GenerativeModel.assert_called_once_with("gemini-2.0-flash-exp")
        mock_model.generate_content.assert_called_once()
    
    @patch('src.contract.agents.genai')
    async def test_get_title_invalid_prompt(self, mock_genai):
        """Test title generation with invalid prompt."""
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "The prompt does not contain information to generate a contract title"
        
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        result = await get_title("invalid prompt")
        
        assert "does not contain information to generate" in result
    
    @patch('src.contract.agents.genai')
    async def test_get_title_with_retries(self, mock_genai):
        """Test title generation with retries on failure."""
        mock_model = MagicMock()
        
        # First call fails, second succeeds
        mock_response_success = MagicMock()
        mock_response_success.text = "Service Agreement"
        
        mock_model.generate_content.side_effect = [
            Exception("API Error"),
            mock_response_success
        ]
        mock_genai.GenerativeModel.return_value = mock_model
        
        result = await get_title("test prompt")
        
        assert result == "Service Agreement"
        assert mock_model.generate_content.call_count == 2
    
    @patch('src.contract.agents.genai')
    async def test_edit_contract_success(self, mock_genai):
        """Test successful contract editing."""
        mock_model = MagicMock()
        
        # Mock the streaming response
        class MockResponse:
            def __init__(self, chunks):
                self.chunks = chunks
                self.index = 0
            
            def __iter__(self):
                return self
            
            def __next__(self):
                if self.index >= len(self.chunks):
                    raise StopIteration
                chunk = self.chunks[self.index]
                self.index += 1
                return chunk
        
        class MockChunk:
            def __init__(self, text):
                self.text = text
        
        mock_chunks = [
            MockChunk("Updated "),
            MockChunk("contract "),
            MockChunk("content")
        ]
        mock_response = MockResponse(mock_chunks)
        
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        content = "<h1>Original Contract</h1>"
        edit_prompt = "Make payment terms more flexible"
        
        result_chunks = []
        async for chunk in edit_contract(content, edit_prompt):
            result_chunks.append(chunk)
        
        assert len(result_chunks) == 3
        assert result_chunks[0] == "Updated "
        assert result_chunks[1] == "contract "
        assert result_chunks[2] == "content"
        
        # Verify the model was called correctly
        mock_genai.GenerativeModel.assert_called_once_with("gemini-2.0-flash-exp")
        mock_model.generate_content.assert_called_once()
    
    @patch('src.contract.agents.genai')
    async def test_edit_contract_with_stream_option(self, mock_genai):
        """Test contract editing with stream=True parameter."""
        mock_model = MagicMock()
        mock_response = iter([MagicMock(text="chunk")])
        
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        content = "<h1>Test</h1>"
        edit_prompt = "Edit this"
        
        chunks = []
        async for chunk in edit_contract(content, edit_prompt):
            chunks.append(chunk)
        
        # Verify stream=True was passed
        call_args = mock_model.generate_content.call_args
        assert call_args[1]['stream'] == True
    
    @patch('src.contract.agents.genai')
    async def test_edit_contract_api_error(self, mock_genai):
        """Test contract editing with API error."""
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("API Error")
        mock_genai.GenerativeModel.return_value = mock_model
        
        content = "<h1>Test</h1>"
        edit_prompt = "Edit this"
        
        chunks = []
        async for chunk in edit_contract(content, edit_prompt):
            chunks.append(chunk)
        
        # Should yield error message
        assert len(chunks) > 0
        assert any("error" in chunk.lower() for chunk in chunks)
    
    @patch('src.contract.agents.genai')
    async def test_suggest_edits_success(self, mock_genai):
        """Test successful edit suggestions generation."""
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = """1. Make payment terms more flexible
2. Add termination clause
3. Include dispute resolution process
4. Clarify deliverables timeline
5. Add intellectual property rights"""
        
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        content = "<h1>Test Contract</h1><p>Basic terms</p>"
        result = await suggest_edits(content)
        
        assert isinstance(result, list)
        assert len(result) == 5
        assert "payment terms" in result[0].lower()
        assert "termination clause" in result[1].lower()
        assert "dispute resolution" in result[2].lower()
        
        # Verify the model was called correctly
        mock_genai.GenerativeModel.assert_called_once_with("gemini-2.0-flash-exp")
        mock_model.generate_content.assert_called_once()
    
    @patch('src.contract.agents.genai')
    async def test_suggest_edits_empty_content(self, mock_genai):
        """Test edit suggestions with empty content."""
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "No specific suggestions for empty content"
        
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        result = await suggest_edits("")
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert "empty content" in result[0].lower()
    
    @patch('src.contract.agents.genai')
    async def test_suggest_edits_with_retries(self, mock_genai):
        """Test edit suggestions with retries on failure."""
        mock_model = MagicMock()
        
        # First call fails, second succeeds
        mock_response_success = MagicMock()
        mock_response_success.text = "1. Add clear terms\n2. Include deadlines"
        
        mock_model.generate_content.side_effect = [
            Exception("API Error"),
            mock_response_success
        ]
        mock_genai.GenerativeModel.return_value = mock_model
        
        content = "<h1>Contract</h1>"
        result = await suggest_edits(content)
        
        assert len(result) == 2
        assert "clear terms" in result[0].lower()
        assert mock_model.generate_content.call_count == 2
    
    @patch('src.contract.agents.genai')
    async def test_suggest_edits_malformed_response(self, mock_genai):
        """Test edit suggestions with malformed response."""
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "This is not a proper numbered list format"
        
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        content = "<h1>Contract</h1>"
        result = await suggest_edits(content)
        
        # Should still return something, even if not properly formatted
        assert isinstance(result, list)
        assert len(result) >= 1
    
    @pytest.mark.parametrize("model_name", [
        "gemini-2.0-flash-exp",
        "gemini-1.5-pro"
    ])
    @patch('src.contract.agents.genai')
    async def test_agents_use_correct_model(self, mock_genai, model_name):
        """Test that agents use the correct Gemini model."""
        # Temporarily patch the model name if needed
        with patch('src.contract.agents.genai.GenerativeModel') as mock_gen_model:
            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.text = "test response"
            mock_model.generate_content.return_value = mock_response
            mock_gen_model.return_value = mock_model
            
            await get_title("test prompt")
            
            # Verify the correct model was used
            mock_gen_model.assert_called_with("gemini-2.0-flash-exp")
    
    @patch('src.contract.agents.genai')
    async def test_all_agents_handle_exceptions(self, mock_genai):
        """Test that all agent functions handle exceptions gracefully."""
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("API Error")
        mock_genai.GenerativeModel.return_value = mock_model
        
        # Test get_title
        title_result = await get_title("test")
        assert isinstance(title_result, str)
        
        # Test generate_toc
        toc_result = await generate_toc("test")
        assert isinstance(toc_result, list)
        
        # Test suggest_edits
        suggestions_result = await suggest_edits("test")
        assert isinstance(suggestions_result, list)
        
        # Test edit_contract
        edit_chunks = []
        async for chunk in edit_contract("test", "edit"):
            edit_chunks.append(chunk)
        assert len(edit_chunks) > 0
