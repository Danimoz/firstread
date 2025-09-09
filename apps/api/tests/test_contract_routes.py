import pytest
from unittest.mock import Mock, AsyncMock, patch
from httpx import AsyncClient
from uuid import uuid4
import json

from src.contract.models import Contract, ContractStatus
from src.users.models import User


@pytest.mark.asyncio
class TestContractRoutes:
    """Test contract API routes."""
    
    @patch('src.contract.routes.generate_toc')
    @patch('src.contract.routes.get_title')
    async def test_create_contract_success(
        self, 
        mock_get_title: AsyncMock,
        mock_generate_toc: AsyncMock,
        async_client: AsyncClient, 
        auth_headers: dict
    ):
        """Test successful contract creation."""
        mock_get_title.return_value = "Test Service Agreement"
        mock_generate_toc.return_value = [
            "1. Introduction",
            "2. Terms and Conditions",
            "3. Payment"
        ]
        
        response = await async_client.post(
            "/contracts/",
            json={"prompt": "Create a service agreement"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        
        # Verify mocks were called
        mock_get_title.assert_called_once_with("Create a service agreement")
        mock_generate_toc.assert_called_once_with("Create a service agreement")
    
    async def test_create_contract_unauthorized(self, async_client: AsyncClient):
        """Test contract creation without authentication."""
        response = await async_client.post(
            "/contracts/",
            json={"prompt": "Create a service agreement"}
        )
        
        assert response.status_code == 401
    
    @patch('src.contract.routes.get_title')
    async def test_create_contract_invalid_prompt(
        self,
        mock_get_title: AsyncMock,
        async_client: AsyncClient,
        auth_headers: dict
    ):
        """Test contract creation with invalid prompt."""
        mock_get_title.return_value = "does not contain information to generate a contract title"
        
        response = await async_client.post(
            "/contracts/",
            json={"prompt": "invalid prompt"},
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "does not contain sufficient information" in data["detail"]
    
    async def test_get_user_contracts(
        self, 
        async_client: AsyncClient, 
        auth_headers: dict,
        test_contract: Contract
    ):
        """Test getting user contracts."""
        response = await async_client.get("/contracts/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        contract_data = data[0]
        assert contract_data["id"] == str(test_contract.id)
        assert contract_data["title"] == test_contract.title
        assert contract_data["status"] == test_contract.status.value
    
    async def test_get_user_contracts_with_pagination(
        self,
        async_client: AsyncClient,
        auth_headers: dict
    ):
        """Test getting user contracts with pagination."""
        response = await async_client.get(
            "/contracts/?limit=10&offset=0",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    async def test_get_contract_by_id(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_contract: Contract
    ):
        """Test getting a specific contract by ID."""
        response = await async_client.get(
            f"/contracts/{test_contract.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_contract.id)
        assert data["title"] == test_contract.title
        assert data["content"] == test_contract.content
        assert data["status"] == test_contract.status.value
    
    async def test_get_contract_by_id_not_found(
        self,
        async_client: AsyncClient,
        auth_headers: dict
    ):
        """Test getting a non-existent contract."""
        fake_id = uuid4()
        response = await async_client.get(
            f"/contracts/{fake_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Contract not found"
    
    async def test_get_contract_unauthorized(
        self,
        async_client: AsyncClient,
        test_contract: Contract
    ):
        """Test getting a contract without authentication."""
        response = await async_client.get(f"/contracts/{test_contract.id}")
        
        assert response.status_code == 401
    
    async def test_update_contract(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_contract: Contract
    ):
        """Test updating a contract."""
        update_data = {
            "title": "Updated Title",
            "content": "<h1>Updated Content</h1>"
        }
        
        response = await async_client.put(
            f"/contracts/{test_contract.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["content"] == "<h1>Updated Content</h1>"
    
    async def test_update_contract_not_found(
        self,
        async_client: AsyncClient,
        auth_headers: dict
    ):
        """Test updating a non-existent contract."""
        fake_id = uuid4()
        response = await async_client.put(
            f"/contracts/{fake_id}",
            json={"title": "Updated"},
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    async def test_create_contract_version(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_contract: Contract
    ):
        """Test creating a new version of a contract."""
        version_data = {
            "content": "<h1>New Version Content</h1>"
        }
        
        response = await async_client.post(
            f"/contracts/{test_contract.id}/versions",
            json=version_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == f"{test_contract.title} (Edited)"
        assert data["content"] == "<h1>New Version Content</h1>"
        assert data["status"] == ContractStatus.COMPLETED.value
        assert data["id"] != str(test_contract.id)  # Should be a new contract
    
    async def test_create_contract_version_missing_content(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_contract: Contract
    ):
        """Test creating a version without content."""
        response = await async_client.post(
            f"/contracts/{test_contract.id}/versions",
            json={},
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "Content is required" in data["detail"]
    
    async def test_stop_contract_generation(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_contract: Contract
    ):
        """Test stopping contract generation."""
        # First, we need to simulate an active generation
        from src.contract.routes import active_contracts
        import asyncio
        
        contract_id = str(test_contract.id)
        active_contracts[contract_id] = asyncio.Event()
        
        response = await async_client.delete(
            f"/contracts/{contract_id}/stop",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "stopped successfully" in data["message"]
        
        # Verify the event was set
        assert active_contracts[contract_id].is_set()
    
    async def test_stop_contract_generation_not_active(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_contract: Contract
    ):
        """Test stopping a contract that's not actively generating."""
        response = await async_client.delete(
            f"/contracts/{test_contract.id}/stop",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "not found or already completed" in data["detail"]
    
    @patch('src.contract.routes.suggest_edits')
    async def test_get_edit_suggestions(
        self,
        mock_suggest_edits: AsyncMock,
        async_client: AsyncClient,
        auth_headers: dict,
        test_contract: Contract
    ):
        """Test getting edit suggestions for a contract."""
        mock_suggest_edits.return_value = [
            "Make payment terms more flexible",
            "Add termination clause",
            "Include dispute resolution"
        ]
        
        response = await async_client.get(
            f"/contracts/{test_contract.id}/suggestions",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        assert len(data["suggestions"]) == 3
        assert "Make payment terms more flexible" in data["suggestions"]
        
        mock_suggest_edits.assert_called_once_with(test_contract.content)
    
    async def test_get_edit_suggestions_no_content(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        db_session,
        test_user: User
    ):
        """Test getting suggestions for a contract with no content."""
        # Create a contract without content
        from src.contract.utils import create_contract
        contract = await create_contract(
            db_session, test_user.id, "Empty Contract", "test prompt"
        )
        await db_session.commit()
        
        response = await async_client.get(
            f"/contracts/{contract.id}/suggestions",
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "no content to analyze" in data["detail"]
    
    @patch('src.contract.routes.edit_contract')
    async def test_edit_contract_with_llm(
        self,
        mock_edit_contract: AsyncMock,
        async_client: AsyncClient,
        auth_headers: dict,
        test_contract: Contract
    ):
        """Test editing a contract using LLM."""
        # Mock the async generator
        async def mock_generator():
            yield "Edited "
            yield "contract "
            yield "content"
        
        mock_edit_contract.return_value = mock_generator()
        
        response = await async_client.post(
            f"/contracts/{test_contract.id}/edit",
            json={"edit_prompt": "Make the payment terms more flexible"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        
        mock_edit_contract.assert_called_once_with(
            test_contract.content,
            "Make the payment terms more flexible"
        )
    
    async def test_edit_contract_missing_prompt(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_contract: Contract
    ):
        """Test editing a contract without providing an edit prompt."""
        response = await async_client.post(
            f"/contracts/{test_contract.id}/edit",
            json={},
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "Edit prompt is required" in data["detail"]
    
    async def test_edit_contract_no_content(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        db_session,
        test_user: User
    ):
        """Test editing a contract that has no content."""
        # Create a contract without content
        from src.contract.utils import create_contract
        contract = await create_contract(
            db_session, test_user.id, "Empty Contract", "test prompt"
        )
        await db_session.commit()
        
        response = await async_client.post(
            f"/contracts/{contract.id}/edit",
            json={"edit_prompt": "Add some content"},
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "no content to edit" in data["detail"]
