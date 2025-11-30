from db.rag import SemanticRouter
import pytest

def test_rag_retrieval(populated_db, mock_embeddings):
    router = SemanticRouter()
    
    # Test 1: Category Retrieval
    category = "locations"
    context = router.get_content_by_category(category)
    
    assert context is not None
    assert "Puebla" in context
    
    # Test 2: Invalid Category
    context = router.get_content_by_category("invalid_category")
    assert context is None
