import pytest
from pydantic import ValidationError
from datetime import datetime
from uuid import uuid4

from src.contract.schema import (
    ContractCreate,
    ContractUpdate,
    ContractResponse,
    ContractVersionCreate,
    EditSuggestionsResponse,
    ContractEditRequest
)
from src.contract.models import ContractStatus


class TestContractCreate:
    """Test ContractCreate schema."""
    
    def test_contract_create_valid(self):
        """Test valid ContractCreate data."""
        data = {
            "prompt": "Create a service agreement for web development"
        }
        
        contract_create = ContractCreate(**data)
        
        assert contract_create.prompt == "Create a service agreement for web development"
    
    def test_contract_create_empty_prompt(self):
        """Test ContractCreate with empty prompt."""
        with pytest.raises(ValidationError) as exc_info:
            ContractCreate(prompt="")
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "string_too_short"
    
    def test_contract_create_whitespace_prompt(self):
        """Test ContractCreate with whitespace-only prompt."""
        with pytest.raises(ValidationError) as exc_info:
            ContractCreate(prompt="   ")
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "string_too_short"
    
    def test_contract_create_missing_prompt(self):
        """Test ContractCreate without prompt."""
        with pytest.raises(ValidationError) as exc_info:
            ContractCreate()
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "missing"
        assert errors[0]["loc"] == ("prompt",)
    
    def test_contract_create_long_prompt(self):
        """Test ContractCreate with very long prompt."""
        long_prompt = "a" * 10000
        contract_create = ContractCreate(prompt=long_prompt)
        
        assert len(contract_create.prompt) == 10000
    
    def test_contract_create_unicode_prompt(self):
        """Test ContractCreate with unicode characters."""
        unicode_prompt = "Create a contract with émojis 🚀 and special chars: αβγ"
        contract_create = ContractCreate(prompt=unicode_prompt)
        
        assert contract_create.prompt == unicode_prompt


class TestContractUpdate:
    """Test ContractUpdate schema."""
    
    def test_contract_update_all_fields(self):
        """Test ContractUpdate with all fields."""
        data = {
            "title": "Updated Title",
            "content": "<h1>Updated Content</h1>",
            "status": "completed"
        }
        
        contract_update = ContractUpdate(**data)
        
        assert contract_update.title == "Updated Title"
        assert contract_update.content == "<h1>Updated Content</h1>"
        assert contract_update.status == ContractStatus.COMPLETED
    
    def test_contract_update_partial_fields(self):
        """Test ContractUpdate with partial fields."""
        data = {"title": "New Title"}
        
        contract_update = ContractUpdate(**data)
        
        assert contract_update.title == "New Title"
        assert contract_update.content is None
        assert contract_update.status is None
    
    def test_contract_update_empty_data(self):
        """Test ContractUpdate with no fields."""
        contract_update = ContractUpdate()
        
        assert contract_update.title is None
        assert contract_update.content is None
        assert contract_update.status is None
    
    def test_contract_update_invalid_status(self):
        """Test ContractUpdate with invalid status."""
        with pytest.raises(ValidationError) as exc_info:
            ContractUpdate(status="invalid_status")
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "invalid_status" in str(errors[0])
    
    def test_contract_update_valid_statuses(self):
        """Test ContractUpdate with all valid statuses."""
        for status_value in ["generating", "completed", "failed"]:
            contract_update = ContractUpdate(status=status_value)
            assert contract_update.status.value == status_value
    
    def test_contract_update_empty_strings(self):
        """Test ContractUpdate with empty strings."""
        data = {
            "title": "",
            "content": ""
        }
        
        contract_update = ContractUpdate(**data)
        
        assert contract_update.title == ""
        assert contract_update.content == ""


class TestContractResponse:
    """Test ContractResponse schema."""
    
    def test_contract_response_valid(self):
        """Test valid ContractResponse data."""
        data = {
            "id": str(uuid4()),
            "user_id": str(uuid4()),
            "title": "Test Contract",
            "content": "<h1>Test Content</h1>",
            "prompt": "Create a test contract",
            "status": "completed",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        contract_response = ContractResponse(**data)
        
        assert contract_response.title == "Test Contract"
        assert contract_response.content == "<h1>Test Content</h1>"
        assert contract_response.status == ContractStatus.COMPLETED
    
    def test_contract_response_with_none_content(self):
        """Test ContractResponse with None content."""
        data = {
            "id": str(uuid4()),
            "user_id": str(uuid4()),
            "title": "Test Contract",
            "content": None,
            "prompt": "Create a test contract",
            "status": "generating",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        contract_response = ContractResponse(**data)
        
        assert contract_response.content is None
        assert contract_response.status == ContractStatus.GENERATING
    
    def test_contract_response_missing_required_fields(self):
        """Test ContractResponse with missing required fields."""
        with pytest.raises(ValidationError) as exc_info:
            ContractResponse(title="Test")
        
        errors = exc_info.value.errors()
        assert len(errors) > 1  # Multiple missing fields
        
        missing_fields = [error["loc"][0] for error in errors]
        assert "id" in missing_fields
        assert "user_id" in missing_fields
    
    def test_contract_response_invalid_uuid(self):
        """Test ContractResponse with invalid UUID."""
        data = {
            "id": "not-a-uuid",
            "user_id": str(uuid4()),
            "title": "Test Contract",
            "prompt": "Create a test contract",
            "status": "completed",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ContractResponse(**data)
        
        errors = exc_info.value.errors()
        assert any("uuid" in str(error).lower() for error in errors)


class TestContractVersionCreate:
    """Test ContractVersionCreate schema."""
    
    def test_contract_version_create_valid(self):
        """Test valid ContractVersionCreate data."""
        data = {
            "content": "<h1>New Version Content</h1>"
        }
        
        version_create = ContractVersionCreate(**data)
        
        assert version_create.content == "<h1>New Version Content</h1>"
    
    def test_contract_version_create_empty_content(self):
        """Test ContractVersionCreate with empty content."""
        with pytest.raises(ValidationError) as exc_info:
            ContractVersionCreate(content="")
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "string_too_short"
    
    def test_contract_version_create_whitespace_content(self):
        """Test ContractVersionCreate with whitespace-only content."""
        with pytest.raises(ValidationError) as exc_info:
            ContractVersionCreate(content="   ")
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "string_too_short"
    
    def test_contract_version_create_missing_content(self):
        """Test ContractVersionCreate without content."""
        with pytest.raises(ValidationError) as exc_info:
            ContractVersionCreate()
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "missing"
        assert errors[0]["loc"] == ("content",)


class TestEditSuggestionsResponse:
    """Test EditSuggestionsResponse schema."""
    
    def test_edit_suggestions_response_valid(self):
        """Test valid EditSuggestionsResponse data."""
        data = {
            "suggestions": [
                "Make payment terms more flexible",
                "Add termination clause",
                "Include dispute resolution"
            ]
        }
        
        suggestions_response = EditSuggestionsResponse(**data)
        
        assert len(suggestions_response.suggestions) == 3
        assert "payment terms" in suggestions_response.suggestions[0]
    
    def test_edit_suggestions_response_empty_list(self):
        """Test EditSuggestionsResponse with empty suggestions list."""
        data = {"suggestions": []}
        
        suggestions_response = EditSuggestionsResponse(**data)
        
        assert suggestions_response.suggestions == []
    
    def test_edit_suggestions_response_single_suggestion(self):
        """Test EditSuggestionsResponse with single suggestion."""
        data = {"suggestions": ["Add clear payment terms"]}
        
        suggestions_response = EditSuggestionsResponse(**data)
        
        assert len(suggestions_response.suggestions) == 1
        assert suggestions_response.suggestions[0] == "Add clear payment terms"
    
    def test_edit_suggestions_response_missing_suggestions(self):
        """Test EditSuggestionsResponse without suggestions field."""
        with pytest.raises(ValidationError) as exc_info:
            EditSuggestionsResponse()
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "missing"
        assert errors[0]["loc"] == ("suggestions",)


class TestContractEditRequest:
    """Test ContractEditRequest schema."""
    
    def test_contract_edit_request_valid(self):
        """Test valid ContractEditRequest data."""
        data = {
            "edit_prompt": "Make the payment terms more flexible"
        }
        
        edit_request = ContractEditRequest(**data)
        
        assert edit_request.edit_prompt == "Make the payment terms more flexible"
    
    def test_contract_edit_request_empty_prompt(self):
        """Test ContractEditRequest with empty prompt."""
        with pytest.raises(ValidationError) as exc_info:
            ContractEditRequest(edit_prompt="")
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "string_too_short"
    
    def test_contract_edit_request_whitespace_prompt(self):
        """Test ContractEditRequest with whitespace-only prompt."""
        with pytest.raises(ValidationError) as exc_info:
            ContractEditRequest(edit_prompt="   ")
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "string_too_short"
    
    def test_contract_edit_request_missing_prompt(self):
        """Test ContractEditRequest without edit_prompt."""
        with pytest.raises(ValidationError) as exc_info:
            ContractEditRequest()
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "missing"
        assert errors[0]["loc"] == ("edit_prompt",)
    
    def test_contract_edit_request_long_prompt(self):
        """Test ContractEditRequest with very long prompt."""
        long_prompt = "Make changes: " + "a" * 5000
        edit_request = ContractEditRequest(edit_prompt=long_prompt)
        
        assert len(edit_request.edit_prompt) > 5000
    
    def test_contract_edit_request_unicode_prompt(self):
        """Test ContractEditRequest with unicode characters."""
        unicode_prompt = "Modifier les termes de paiement 💰 中文编辑"
        edit_request = ContractEditRequest(edit_prompt=unicode_prompt)
        
        assert edit_request.edit_prompt == unicode_prompt


class TestSchemaIntegration:
    """Test schema integration and edge cases."""
    
    def test_contract_status_serialization(self):
        """Test that ContractStatus enum serializes correctly."""
        response_data = {
            "id": str(uuid4()),
            "user_id": str(uuid4()),
            "title": "Test",
            "content": "Content",
            "prompt": "Prompt",
            "status": ContractStatus.COMPLETED,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        contract_response = ContractResponse(**response_data)
        
        # Test that we can serialize to dict
        response_dict = contract_response.model_dump()
        assert response_dict["status"] == "completed"
    
    def test_schema_with_actual_datetime_objects(self):
        """Test schemas with actual datetime objects."""
        now = datetime.now()
        
        response_data = {
            "id": str(uuid4()),
            "user_id": str(uuid4()),
            "title": "Test",
            "content": "Content",
            "prompt": "Prompt",
            "status": "completed",
            "created_at": now,
            "updated_at": now
        }
        
        contract_response = ContractResponse(**response_data)
        
        assert contract_response.created_at == now
        assert contract_response.updated_at == now
    
    def test_schema_field_validation_independence(self):
        """Test that field validation works independently."""
        # Valid title, invalid status
        with pytest.raises(ValidationError) as exc_info:
            ContractUpdate(title="Valid Title", status="invalid")
        
        errors = exc_info.value.errors()
        # Should only have one error for the invalid status
        assert len(errors) == 1
        assert errors[0]["loc"] == ("status",)
