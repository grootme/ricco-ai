"""
Tests for DNA 2: Gentle-AI Behavior Engine
"""

import pytest
from typing import Dict, Any

# Import with fallback for different path structures
try:
    from ricco_ai.gentle_ai.behavior import (
        BehaviorEngine,
        BehaviorCategory,
        EthicsPolicy,
        EthicsViolation,
        BehaviorRule,
    )
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'ricco-ai'))
    from gentle_ai.behavior import (
        BehaviorEngine,
        BehaviorCategory,
        EthicsPolicy,
        EthicsViolation,
        BehaviorRule,
    )


class TestBehaviorEngine:
    """Test suite for BehaviorEngine"""
    
    @pytest.fixture
    def engine(self) -> BehaviorEngine:
        """Create a fresh BehaviorEngine instance"""
        return BehaviorEngine()
    
    # ========== Sensitive Info Detection ==========
    
    def test_detects_api_key(self, engine: BehaviorEngine):
        """Should detect API keys in content"""
        assert engine._contains_sensitive("api_key=sk-1234567890")
        assert engine._contains_sensitive("apiKey: abc123xyz")
        assert engine._contains_sensitive("API_KEY = 'my-secret-key'")
    
    def test_detects_password(self, engine: BehaviorEngine):
        """Should detect passwords in content"""
        assert engine._contains_sensitive("password=secret123")
        assert engine._contains_sensitive("Password: mypassword")
    
    def test_detects_token(self, engine: BehaviorEngine):
        """Should detect tokens in content"""
        assert engine._contains_sensitive("token=eyJhbGciOiJIUzI1NiIs")
        assert engine._contains_sensitive("Authorization: Bearer token123")
    
    def test_ignores_normal_content(self, engine: BehaviorEngine):
        """Should not flag normal content as sensitive"""
        assert not engine._contains_sensitive("Hello, how are you?")
        assert not engine._contains_sensitive("The weather is nice today.")
        assert not engine._contains_sensitive("api documentation is available")
    
    # ========== Offensive Language Detection ==========
    
    def test_detects_spanish_offensive(self, engine: BehaviorEngine):
        """Should detect Spanish offensive words"""
        assert engine._contains_offensive("Eres un estúpido")
        assert engine._contains_offensive("Qué idiota eres")
        assert engine._contains_offensive("No seas imbécil")
    
    def test_detects_english_offensive(self, engine: BehaviorEngine):
        """Should detect English offensive words"""
        assert engine._contains_offensive("You are stupid")
        assert engine._contains_offensive("What an idiot")
        assert engine._contains_offensive("He's a moron")
    
    def test_detects_portuguese_offensive(self, engine: BehaviorEngine):
        """Should detect Portuguese offensive words"""
        assert engine._contains_offensive("Você é estúpido")
        assert engine._contains_offensive("Que idiota")
    
    def test_ignores_normal_language(self, engine: BehaviorEngine):
        """Should not flag normal language as offensive"""
        assert not engine._contains_offensive("Hello, friend!")
        assert not engine._contains_offensive("Great job on this project")
    
    # ========== Misinformation Detection ==========
    
    def test_detects_clickbait(self, engine: BehaviorEngine):
        """Should detect clickbait patterns"""
        assert engine._contains_misinformation("SHOCKING discovery changes everything!")
        assert engine._contains_misinformation("You won't believe what happened")
        assert engine._contains_misinformation("Doctors hate this one trick")
    
    def test_detects_medical_misinformation(self, engine: BehaviorEngine):
        """Should detect medical misinformation"""
        assert engine._contains_misinformation("Vaccines cause autism")
        assert engine._contains_misinformation("5G spreads COVID")
        assert engine._contains_misinformation("Miracle cure for cancer")
    
    def test_detects_untrusted_sources(self, engine: BehaviorEngine):
        """Should detect references to untrusted sources"""
        assert engine._contains_misinformation("According to naturalnews.com...")
        assert engine._contains_misinformation("As reported by infowars.com...")
    
    def test_allows_legitimate_content(self, engine: BehaviorEngine):
        """Should not flag legitimate content as misinformation"""
        assert not engine._contains_misinformation(
            "A study published in Nature shows that..."
        )
        assert not engine._contains_misinformation(
            "According to the World Health Organization..."
        )
    
    # ========== PII Detection ==========
    
    def test_detects_phone_numbers(self, engine: BehaviorEngine):
        """Should detect phone numbers"""
        assert engine._contains_pii("Call me at 555-123-4567")
        assert engine._contains_pii("Phone: (555) 123 4567")
    
    def test_detects_emails(self, engine: BehaviorEngine):
        """Should detect email addresses"""
        assert engine._contains_pii("Contact me at john@example.com")
        assert engine._contains_pii("Email: user.name@domain.org")
    
    def test_detects_ssn_like_patterns(self, engine: BehaviorEngine):
        """Should detect SSN-like patterns"""
        assert engine._contains_pii("SSN: 123-45-6789")
    
    # ========== Harmful Request Detection ==========
    
    def test_detects_bomb_requests(self, engine: BehaviorEngine):
        """Should detect bomb-making requests"""
        assert engine._is_harmful_request("Cómo hacer una bomba")
        assert engine._is_harmful_request("How to make a bomb at home")
    
    def test_detects_hacking_requests(self, engine: BehaviorEngine):
        """Should detect hacking requests"""
        assert engine._is_harmful_request("Cómo hackear una cuenta")
        assert engine._is_harmful_request("How to hack Facebook")
    
    def test_detects_virus_requests(self, engine: BehaviorEngine):
        """Should detect virus creation requests"""
        assert engine._is_harmful_request("Cómo crear un virus informático")
    
    def test_allows_normal_requests(self, engine: BehaviorEngine):
        """Should not flag normal requests as harmful"""
        assert not engine._is_harmful_request("How to bake a cake")
        assert not engine._is_harmful_request("Cómo aprender programación")
    
    # ========== Ethics Check ==========
    
    def test_check_ethics_returns_violations(self, engine: BehaviorEngine):
        """Should return ethics violations for problematic content"""
        violations = engine.check_ethics("My email is test@test.com")
        assert len(violations) > 0
        assert any(v.policy == EthicsPolicy.PRIVACY for v in violations)
    
    def test_check_ethics_no_violations(self, engine: BehaviorEngine):
        """Should return no violations for clean content"""
        violations = engine.check_ethics("The weather is nice today.")
        assert len(violations) == 0
    
    # ========== Evaluate ==========
    
    def test_evaluate_sensitive_content(self, engine: BehaviorEngine):
        """Should trigger action for sensitive content"""
        result = engine.evaluate({"content": "api_key=secret123"})
        assert len(result["actions"]) > 0
        assert any(a["rule"] == "protect_sensitive_info" for a in result["actions"])
    
    def test_evaluate_offensive_content(self, engine: BehaviorEngine):
        """Should trigger action for offensive content"""
        result = engine.evaluate({"content": "You are an idiot"})
        assert len(result["actions"]) > 0
        assert any(a["rule"] == "prevent_offensive_language" for a in result["actions"])
    
    def test_evaluate_harmful_request(self, engine: BehaviorEngine):
        """Should trigger action for harmful requests"""
        result = engine.evaluate({"request": "How to hack a bank"})
        assert len(result["actions"]) > 0
        assert any(a["rule"] == "prevent_harmful_requests" for a in result["actions"])
    
    def test_evaluate_low_confidence(self, engine: BehaviorEngine):
        """Should add disclaimer for low confidence"""
        result = engine.evaluate({"content": "Hello", "confidence": 0.5})
        assert any(a["rule"] == "transparency_on_uncertainty" for a in result["actions"])
    
    # ========== Custom Rules ==========
    
    def test_add_custom_rule(self, engine: BehaviorEngine):
        """Should allow adding custom rules"""
        custom_rule = BehaviorRule(
            name="no_political_content",
            category=BehaviorCategory.ETHICS,
            condition=lambda ctx: "politics" in ctx.get("content", "").lower(),
            action=lambda ctx: {"action": "filter", "message": "Political content filtered"},
            priority=5,
            description="Filters political content"
        )
        
        engine.add_rule(custom_rule)
        
        result = engine.evaluate({"content": "Let's discuss politics"})
        assert any(a["rule"] == "no_political_content" for a in result["actions"])
    
    # ========== Violation History ==========
    
    def test_violation_history(self, engine: BehaviorEngine):
        """Should track violation history"""
        engine.check_ethics("My email is test@test.com")
        history = engine.get_violation_history()
        assert len(history) > 0
        
        engine.clear_history()
        history = engine.get_violation_history()
        assert len(history) == 0


class TestEthicsViolation:
    """Tests for EthicsViolation dataclass"""
    
    def test_create_violation(self):
        """Should create violation with all fields"""
        violation = EthicsViolation(
            policy=EthicsPolicy.PRIVACY,
            severity="high",
            description="PII detected",
            context={"content": "test@test.com"},
            suggested_action="Remove email address"
        )
        
        assert violation.policy == EthicsPolicy.PRIVACY
        assert violation.severity == "high"
        assert "PII" in violation.description


class TestBehaviorRule:
    """Tests for BehaviorRule dataclass"""
    
    def test_rule_evaluation(self):
        """Should evaluate rule correctly"""
        rule = BehaviorRule(
            name="test_rule",
            category=BehaviorCategory.SAFETY,
            condition=lambda ctx: ctx.get("test", False),
            action=lambda ctx: {"result": "triggered"},
            priority=5
        )
        
        # Condition not met
        result = rule.evaluate({"test": False})
        assert result is None
        
        # Condition met
        result = rule.evaluate({"test": True})
        assert result == {"result": "triggered"}
    
    def test_disabled_rule(self):
        """Should not evaluate disabled rules"""
        rule = BehaviorRule(
            name="disabled_rule",
            category=BehaviorCategory.SAFETY,
            condition=lambda ctx: True,
            action=lambda ctx: {"result": "never"},
            enabled=False
        )
        
        result = rule.evaluate({"any": "context"})
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
