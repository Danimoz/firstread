import pytest
from datetime import datetime
from uuid import uuid4
from sqlalchemy.exc import IntegrityError

from src.contract.models import Contract, ContractStatus
from src.users.models import User


@pytest.mark.asyncio
class TestContractModel:
    """Test the Contract SQLAlchemy model."""
    
    async def test_create_contract(self, db_session, test_user: User):
        """Test creating a new contract."""
        contract = Contract(
            user_id=test_user.id,
            title="Test Contract",
            content="<h1>Test Content</h1>",
            prompt="Create a test contract",
            status=ContractStatus.COMPLETED
        )
        
        db_session.add(contract)
        await db_session.commit()
        await db_session.refresh(contract)
        
        assert contract.id is not None
        assert contract.user_id == test_user.id
        assert contract.title == "Test Contract"
        assert contract.content == "<h1>Test Content</h1>"
        assert contract.prompt == "Create a test contract"
        assert contract.status == ContractStatus.COMPLETED
        assert contract.created_at is not None
        assert contract.updated_at is not None
        assert isinstance(contract.created_at, datetime)
        assert isinstance(contract.updated_at, datetime)
    
    async def test_contract_default_status(self, db_session, test_user: User):
        """Test that contract defaults to GENERATING status."""
        contract = Contract(
            user_id=test_user.id,
            title="Test Contract",
            prompt="Create a test contract"
        )
        
        db_session.add(contract)
        await db_session.commit()
        await db_session.refresh(contract)
        
        assert contract.status == ContractStatus.GENERATING
    
    async def test_contract_without_user_id_fails(self, db_session):
        """Test that creating a contract without user_id fails."""
        contract = Contract(
            title="Test Contract",
            prompt="Create a test contract"
        )
        
        db_session.add(contract)
        
        with pytest.raises(IntegrityError):
            await db_session.commit()
    
    async def test_contract_without_title_fails(self, db_session, test_user: User):
        """Test that creating a contract without title fails."""
        contract = Contract(
            user_id=test_user.id,
            prompt="Create a test contract"
        )
        
        db_session.add(contract)
        
        with pytest.raises(IntegrityError):
            await db_session.commit()
    
    async def test_contract_without_prompt_fails(self, db_session, test_user: User):
        """Test that creating a contract without prompt fails."""
        contract = Contract(
            user_id=test_user.id,
            title="Test Contract"
        )
        
        db_session.add(contract)
        
        with pytest.raises(IntegrityError):
            await db_session.commit()
    
    async def test_contract_with_invalid_user_id_fails(self, db_session):
        """Test that creating a contract with invalid user_id fails."""
        fake_user_id = uuid4()
        contract = Contract(
            user_id=fake_user_id,
            title="Test Contract",
            prompt="Create a test contract"
        )
        
        db_session.add(contract)
        
        with pytest.raises(IntegrityError):
            await db_session.commit()
    
    async def test_contract_timestamps_auto_populate(self, db_session, test_user: User):
        """Test that created_at and updated_at are automatically populated."""
        contract = Contract(
            user_id=test_user.id,
            title="Test Contract",
            prompt="Create a test contract"
        )
        
        # Timestamps should be None before saving
        assert contract.created_at is None
        assert contract.updated_at is None
        
        db_session.add(contract)
        await db_session.commit()
        await db_session.refresh(contract)
        
        # Timestamps should be populated after saving
        assert contract.created_at is not None
        assert contract.updated_at is not None
        assert contract.created_at == contract.updated_at
    
    async def test_contract_updated_at_changes(self, db_session, test_user: User):
        """Test that updated_at changes when contract is modified."""
        contract = Contract(
            user_id=test_user.id,
            title="Test Contract",
            prompt="Create a test contract"
        )
        
        db_session.add(contract)
        await db_session.commit()
        await db_session.refresh(contract)
        
        original_updated_at = contract.updated_at
        
        # Make a small delay to ensure timestamp difference
        import asyncio
        await asyncio.sleep(0.01)
        
        # Update the contract
        contract.title = "Updated Contract"
        await db_session.commit()
        await db_session.refresh(contract)
        
        # updated_at should have changed
        assert contract.updated_at > original_updated_at
    
    async def test_contract_relationship_with_user(self, db_session, test_user: User):
        """Test the relationship between Contract and User."""
        contract = Contract(
            user_id=test_user.id,
            title="Test Contract",
            prompt="Create a test contract"
        )
        
        db_session.add(contract)
        await db_session.commit()
        await db_session.refresh(contract)
        
        # Test that we can access the user through the relationship
        await db_session.refresh(contract, ["user"])
        assert contract.user is not None
        assert contract.user.id == test_user.id
        assert contract.user.email == test_user.email
    
    async def test_contract_can_have_null_content(self, db_session, test_user: User):
        """Test that content can be null (for contracts being generated)."""
        contract = Contract(
            user_id=test_user.id,
            title="Test Contract",
            prompt="Create a test contract",
            content=None
        )
        
        db_session.add(contract)
        await db_session.commit()
        await db_session.refresh(contract)
        
        assert contract.content is None
    
    async def test_contract_can_have_empty_content(self, db_session, test_user: User):
        """Test that content can be empty string."""
        contract = Contract(
            user_id=test_user.id,
            title="Test Contract",
            prompt="Create a test contract",
            content=""
        )
        
        db_session.add(contract)
        await db_session.commit()
        await db_session.refresh(contract)
        
        assert contract.content == ""
    
    async def test_contract_long_content(self, db_session, test_user: User):
        """Test that contract can handle long content."""
        long_content = "<h1>Very Long Contract</h1>" + "<p>Content</p>" * 1000
        
        contract = Contract(
            user_id=test_user.id,
            title="Long Contract",
            prompt="Create a very long contract",
            content=long_content
        )
        
        db_session.add(contract)
        await db_session.commit()
        await db_session.refresh(contract)
        
        assert len(contract.content) > 10000
        assert contract.content == long_content
    
    async def test_contract_unicode_content(self, db_session, test_user: User):
        """Test that contract can handle unicode content."""
        unicode_content = """
        <h1>Contrat de Service 🚀</h1>
        <p>Términos y condiciones en español</p>
        <p>中文内容测试</p>
        <p>العربية محتوى</p>
        """
        
        contract = Contract(
            user_id=test_user.id,
            title="Unicode Contract",
            prompt="Create a multilingual contract",
            content=unicode_content
        )
        
        db_session.add(contract)
        await db_session.commit()
        await db_session.refresh(contract)
        
        assert contract.content == unicode_content
        assert "🚀" in contract.content
        assert "español" in contract.content
        assert "中文" in contract.content
    
    @pytest.mark.parametrize("status", [
        ContractStatus.GENERATING,
        ContractStatus.COMPLETED,
        ContractStatus.FAILED
    ])
    async def test_contract_status_values(self, db_session, test_user: User, status):
        """Test all possible contract status values."""
        contract = Contract(
            user_id=test_user.id,
            title="Test Contract",
            prompt="Create a test contract",
            status=status
        )
        
        db_session.add(contract)
        await db_session.commit()
        await db_session.refresh(contract)
        
        assert contract.status == status
    
    async def test_multiple_contracts_per_user(self, db_session, test_user: User):
        """Test that a user can have multiple contracts."""
        contracts = []
        for i in range(3):
            contract = Contract(
                user_id=test_user.id,
                title=f"Contract {i+1}",
                prompt=f"Create contract {i+1}"
            )
            contracts.append(contract)
            db_session.add(contract)
        
        await db_session.commit()
        
        # Refresh all contracts
        for contract in contracts:
            await db_session.refresh(contract)
        
        # All contracts should have different IDs
        contract_ids = [c.id for c in contracts]
        assert len(set(contract_ids)) == 3
        
        # All should belong to the same user
        for contract in contracts:
            assert contract.user_id == test_user.id


@pytest.mark.asyncio
class TestContractStatus:
    """Test the ContractStatus enum."""
    
    def test_contract_status_values(self):
        """Test that ContractStatus has the expected values."""
        assert ContractStatus.GENERATING.value == "generating"
        assert ContractStatus.COMPLETED.value == "completed"
        assert ContractStatus.FAILED.value == "failed"
    
    def test_contract_status_count(self):
        """Test that we have the expected number of status values."""
        status_values = list(ContractStatus)
        assert len(status_values) == 3
    
    def test_contract_status_string_representation(self):
        """Test string representation of status values."""
        assert str(ContractStatus.GENERATING) == "ContractStatus.GENERATING"
        assert str(ContractStatus.COMPLETED) == "ContractStatus.COMPLETED"
        assert str(ContractStatus.FAILED) == "ContractStatus.FAILED"
