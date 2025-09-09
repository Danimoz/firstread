import pytest
from uuid import uuid4
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from src.contract.models import Contract, ContractStatus
from src.contract.utils import (
    sse_format,
    create_contract,
    update_contract_content,
    complete_contract,
    cancel_contract,
    get_contract_by_id,
    get_user_contracts,
    update_contract,
    create_contract_version
)
from src.contract.schema import ContractUpdate
from src.users.models import User


class TestSSEFormat:
    """Test SSE formatting utility."""
    
    def test_sse_format_simple_data(self):
        """Test formatting simple data."""
        result = sse_format("Hello World")
        expected = b"data: Hello World\n\n"
        assert result == expected
    
    def test_sse_format_with_event(self):
        """Test formatting data with event type."""
        result = sse_format("Hello World", event="test")
        expected = b"event: test\ndata: Hello World\n\n"
        assert result == expected
    
    def test_sse_format_multiline_data(self):
        """Test formatting multiline data."""
        result = sse_format("Line 1\nLine 2\nLine 3")
        expected = b"data: Line 1\ndata: Line 2\ndata: Line 3\n\n"
        assert result == expected
    
    def test_sse_format_empty_data(self):
        """Test formatting empty data."""
        result = sse_format("")
        expected = b"data: \n\n"
        assert result == expected


@pytest.mark.asyncio
class TestContractUtils:
    """Test contract utility functions."""
    
    async def test_create_contract(self, db_session: AsyncSession, test_user: User):
        """Test creating a new contract."""
        title = "Test Contract"
        prompt = "Create a test contract"
        
        contract = await create_contract(db_session, test_user.id, title, prompt)
        
        assert contract is not None
        assert contract.title == title
        assert contract.prompt == prompt
        assert contract.user_id == test_user.id
        assert contract.status == ContractStatus.GENERATING
        assert contract.content is None
        assert contract.created_at is not None
    
    async def test_update_contract_content(self, db_session: AsyncSession, test_contract: Contract):
        """Test updating contract content."""
        new_content = "<h1>Updated Content</h1>"
        
        updated_contract = await update_contract_content(db_session, test_contract.id, new_content)
        
        assert updated_contract is not None
        assert updated_contract.content == new_content
        assert updated_contract.updated_at > test_contract.updated_at
    
    async def test_update_contract_content_nonexistent(self, db_session: AsyncSession):
        """Test updating content for non-existent contract."""
        fake_id = uuid4()
        
        result = await update_contract_content(db_session, fake_id, "content")
        
        assert result is None
    
    async def test_complete_contract(self, db_session: AsyncSession, test_user: User):
        """Test completing a contract."""
        # Create a generating contract
        contract = await create_contract(
            db_session, test_user.id, "Test", "test prompt"
        )
        await db_session.commit()
        
        final_content = "<h1>Final Contract</h1><p>Complete content</p>"
        
        completed_contract = await complete_contract(db_session, contract.id, final_content)
        
        assert completed_contract is not None
        assert completed_contract.status == ContractStatus.COMPLETED
        assert completed_contract.content == final_content
        assert completed_contract.completed_at is not None
        assert completed_contract.updated_at is not None
    
    async def test_cancel_contract(self, db_session: AsyncSession, test_user: User):
        """Test cancelling a contract."""
        # Create a generating contract
        contract = await create_contract(
            db_session, test_user.id, "Test", "test prompt"
        )
        await db_session.commit()
        
        partial_content = "<h1>Partial Content</h1>"
        
        cancelled_contract = await cancel_contract(db_session, contract.id, partial_content)
        
        assert cancelled_contract is not None
        assert cancelled_contract.status == ContractStatus.CANCELLED
        assert cancelled_contract.content == partial_content
        assert cancelled_contract.updated_at is not None
    
    async def test_cancel_contract_without_content(self, db_session: AsyncSession, test_user: User):
        """Test cancelling a contract without providing partial content."""
        # Create a generating contract
        contract = await create_contract(
            db_session, test_user.id, "Test", "test prompt"
        )
        await db_session.commit()
        
        cancelled_contract = await cancel_contract(db_session, contract.id)
        
        assert cancelled_contract is not None
        assert cancelled_contract.status == ContractStatus.CANCELLED
        assert cancelled_contract.content is None
    
    async def test_get_contract_by_id(self, db_session: AsyncSession, test_contract: Contract):
        """Test getting a contract by ID."""
        contract = await get_contract_by_id(db_session, test_contract.id)
        
        assert contract is not None
        assert contract.id == test_contract.id
        assert contract.title == test_contract.title
        assert contract.user is not None  # Should be loaded via selectinload
    
    async def test_get_contract_by_id_nonexistent(self, db_session: AsyncSession):
        """Test getting a non-existent contract."""
        fake_id = uuid4()
        
        contract = await get_contract_by_id(db_session, fake_id)
        
        assert contract is None
    
    async def test_get_user_contracts(self, db_session: AsyncSession, test_user: User):
        """Test getting contracts for a user."""
        # Create multiple contracts
        contracts = []
        for i in range(3):
            contract = Contract(
                title=f"Contract {i}",
                prompt=f"Prompt {i}",
                content=f"Content {i}",
                status=ContractStatus.COMPLETED,
                user_id=test_user.id
            )
            db_session.add(contract)
            contracts.append(contract)
        
        await db_session.commit()
        
        user_contracts = await get_user_contracts(db_session, test_user.id)
        
        assert len(user_contracts) == 3
        # Should be ordered by created_at desc
        assert user_contracts[0].title == "Contract 2"
    
    async def test_get_user_contracts_with_pagination(self, db_session: AsyncSession, test_user: User):
        """Test getting user contracts with pagination."""
        # Create 5 contracts
        for i in range(5):
            contract = Contract(
                title=f"Contract {i}",
                prompt=f"Prompt {i}",
                status=ContractStatus.COMPLETED,
                user_id=test_user.id
            )
            db_session.add(contract)
        
        await db_session.commit()
        
        # Get first 2 contracts
        contracts_page1 = await get_user_contracts(db_session, test_user.id, limit=2, offset=0)
        assert len(contracts_page1) == 2
        
        # Get next 2 contracts
        contracts_page2 = await get_user_contracts(db_session, test_user.id, limit=2, offset=2)
        assert len(contracts_page2) == 2
        
        # Should be different contracts
        assert contracts_page1[0].id != contracts_page2[0].id
    
    async def test_update_contract(self, db_session: AsyncSession, test_contract: Contract):
        """Test updating a contract with ContractUpdate schema."""
        updates = ContractUpdate(
            title="Updated Title",
            content="<h1>Updated Content</h1>",
            status=ContractStatus.COMPLETED
        )
        
        updated_contract = await update_contract(db_session, test_contract.id, updates)
        
        assert updated_contract is not None
        assert updated_contract.title == "Updated Title"
        assert updated_contract.content == "<h1>Updated Content</h1>"
        assert updated_contract.status == ContractStatus.COMPLETED
        assert updated_contract.updated_at > test_contract.updated_at
    
    async def test_update_contract_partial(self, db_session: AsyncSession, test_contract: Contract):
        """Test partially updating a contract."""
        original_title = test_contract.title
        updates = ContractUpdate(content="<h1>Only Content Updated</h1>")
        
        updated_contract = await update_contract(db_session, test_contract.id, updates)
        
        assert updated_contract is not None
        assert updated_contract.title == original_title  # Should remain unchanged
        assert updated_contract.content == "<h1>Only Content Updated</h1>"
    
    async def test_update_contract_nonexistent(self, db_session: AsyncSession):
        """Test updating a non-existent contract."""
        fake_id = uuid4()
        updates = ContractUpdate(title="New Title")
        
        result = await update_contract(db_session, fake_id, updates)
        
        assert result is None
    
    async def test_create_contract_version(self, db_session: AsyncSession, test_contract: Contract, test_user: User):
        """Test creating a new version of a contract."""
        new_content = "<h1>Edited Version</h1><p>This is an edited version</p>"
        
        new_version = await create_contract_version(
            db_session, test_contract.id, new_content, test_user.id
        )
        
        assert new_version is not None
        assert new_version.title == f"{test_contract.title} (Edited)"
        assert new_version.prompt == test_contract.prompt
        assert new_version.content == new_content
        assert new_version.status == ContractStatus.COMPLETED
        assert new_version.user_id == test_user.id
        assert new_version.completed_at is not None
        assert new_version.id != test_contract.id  # Should be a new contract
    
    async def test_create_contract_version_nonexistent_original(self, db_session: AsyncSession, test_user: User):
        """Test creating a version from a non-existent original contract."""
        fake_id = uuid4()
        
        result = await create_contract_version(
            db_session, fake_id, "content", test_user.id
        )
        
        assert result is None
