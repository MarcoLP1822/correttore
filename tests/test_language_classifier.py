"""
Test suite for LanguageClassifier and ForeignWordFilter
Tests detection of Latin, English, proper nouns, and technical terms
"""

from src.correttore.core.language_classifier import (
    LanguageClassifier, ForeignWordFilter, Language
)


def test_latin_detection():
    """Test rilevamento parole latine"""
    classifier = LanguageClassifier()
    
    test_cases = [
        ("populus", "legislator sive populus", Language.LATIN, 0.6),
        ("civium", "voluntatem civium generaliter", Language.LATIN, 0.6),
        ("cum", "dicimus igitur cum veritate", Language.LATIN, 0.6),
    ]
    
    print("\n🔍 Testing Latin Detection:")
    for word, context, expected_lang, min_conf in test_cases:
        lang, conf = classifier.classify_word(word, context)
        status = "✅" if lang == expected_lang and conf >= min_conf else "❌"
        print(f"  {status} '{word}' → {lang.value} (conf: {conf:.2f})")
        assert lang == expected_lang, f"Expected {expected_lang}, got {lang}"
        assert conf >= min_conf, f"Confidence too low: {conf} < {min_conf}"
    
    print("✅ Latin detection: PASS\n")


def test_english_detection():
    """Test rilevamento parole inglesi"""
    classifier = LanguageClassifier()
    
    test_cases = [
        ("checks", "sistema di checks and balances", Language.ENGLISH, 0.6),
        ("governance", "La governance multilivello", Language.ENGLISH, 0.4),
        ("should", "justice should lose their names", Language.ENGLISH, 0.6),
        ("balances", "checks and balances democratici", Language.ENGLISH, 0.6),
    ]
    
    print("🔍 Testing English Detection:")
    for word, context, expected_lang, min_conf in test_cases:
        lang, conf = classifier.classify_word(word, context)
        status = "✅" if lang == expected_lang and conf >= min_conf else "❌"
        print(f"  {status} '{word}' → {lang.value} (conf: {conf:.2f})")
        assert lang == expected_lang, f"Expected {expected_lang}, got {lang}"
        assert conf >= min_conf, f"Confidence too low: {conf} < {min_conf}"
    
    print("✅ English detection: PASS\n")


def test_proper_noun_filter():
    """Test filtraggio nomi propri"""
    filter_sys = ForeignWordFilter()
    
    test_cases = [
        ("Poddighe", "Marco Poddighe nato", True, "proper_noun"),
        ("Westfalia", "trattato di Westfalia", True, "proper_noun"),
        ("Weber", "come Weber sosteneva", True, "proper_noun"),
    ]
    
    print("🔍 Testing Proper Noun Filter:")
    for word, context, should_filter, expected_reason in test_cases:
        filtered, lang, reason = filter_sys.should_filter_error(word, context)
        status = "✅" if filtered == should_filter and reason == expected_reason else "❌"
        print(f"  {status} '{word}' → filtered={filtered}, reason={reason}")
        assert filtered == should_filter, f"Filter mismatch for {word}"
        assert reason == expected_reason, f"Wrong reason: {reason}"
    
    print("✅ Proper noun filter: PASS\n")


def test_technical_terms():
    """Test filtraggio termini tecnici"""
    filter_sys = ForeignWordFilter()
    
    technical = ["governance", "asset", "welfare", "blockchain", "smart"]
    
    print("🔍 Testing Technical Terms Filter:")
    for term in technical:
        filtered, lang, reason = filter_sys.should_filter_error(term, "")
        status = "✅" if filtered and reason == "technical_term" else "❌"
        print(f"  {status} '{term}' → filtered={filtered}, reason={reason}")
        assert filtered == True, f"{term} should be filtered"
        assert reason == "technical_term", f"Wrong reason for {term}"
    
    print("✅ Technical terms filter: PASS\n")


def test_italian_word_passthrough():
    """Test che parole italiane non vengano filtrate"""
    filter_sys = ForeignWordFilter()
    
    italian_words = [
        ("casa", "la casa è grande"),
        ("libro", "ho letto il libro"),
        ("governo", "il governo italiano"),
    ]
    
    print("🔍 Testing Italian Words Passthrough:")
    for word, context in italian_words:
        filtered, lang, reason = filter_sys.should_filter_error(word, context)
        status = "✅" if not filtered else "❌"
        print(f"  {status} '{word}' → filtered={filtered}")
        assert not filtered, f"Italian word '{word}' should not be filtered"
    
    print("✅ Italian passthrough: PASS\n")


if __name__ == "__main__":
    print("=" * 60)
    print("  LANGUAGE CLASSIFIER TEST SUITE")
    print("=" * 60)
    
    try:
        test_latin_detection()
        test_english_detection()
        test_proper_noun_filter()
        test_technical_terms()
        test_italian_word_passthrough()
        
        print("=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 60)
        
    except AssertionError as e:
        print("\n" + "=" * 60)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 60)
        raise
