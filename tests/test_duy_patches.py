"""Tests for patched helpers _normalize_language and _inject_tiktok_directive.

These two helpers were added by the duy-vi-tiktok patch to fix:
  - language="Vietnamese" silently falling back to English
  - orientation="portrait" being ignored for slide_deck
"""

from notebooklm_tools.mcp.tools.studio import (
    _inject_tiktok_directive,
    _normalize_language,
)


class TestNormalizeLanguage:
    """Verify friendly language names map to BCP-47 codes."""

    def test_empty_passes_through(self):
        assert _normalize_language("") == ""

    def test_already_bcp47_short(self):
        assert _normalize_language("vi") == "vi"
        assert _normalize_language("en") == "en"
        assert _normalize_language("ja") == "ja"

    def test_already_bcp47_with_region(self):
        assert _normalize_language("vi-VN") == "vi-VN"
        assert _normalize_language("en-US") == "en-US"
        assert _normalize_language("pt-BR") == "pt-BR"

    def test_vietnamese_friendly_name(self):
        assert _normalize_language("Vietnamese") == "vi"
        assert _normalize_language("vietnamese") == "vi"
        assert _normalize_language("VIETNAMESE") == "vi"

    def test_english_friendly_name(self):
        assert _normalize_language("English") == "en"
        assert _normalize_language("english") == "en"

    def test_french_friendly_name(self):
        assert _normalize_language("French") == "fr"
        assert _normalize_language("Français") == "fr"

    def test_japanese_friendly_name(self):
        assert _normalize_language("Japanese") == "ja"
        assert _normalize_language("日本語") == "ja"

    def test_strips_whitespace(self):
        assert _normalize_language("  Vietnamese  ") == "vi"
        assert _normalize_language("  vi  ") == "vi"

    def test_unknown_long_string_passthrough(self):
        # Unknown friendly name passes through unchanged so NotebookLM can
        # validate and surface a clear error to the user.
        assert _normalize_language("Klingon") == "Klingon"


class TestInjectTiktokDirective:
    """Verify the 9:16 directive injection logic."""

    def test_empty_prompt_gets_directive_only(self):
        result = _inject_tiktok_directive("")
        assert "9:16" in result
        assert "Vietnamese" in result or "Vietnamese".lower() in result.lower()
        assert result.strip() == result

    def test_none_prompt_gets_directive_only(self):
        result = _inject_tiktok_directive(None)
        assert "9:16" in result

    def test_prompt_without_916_gets_directive_prepended(self):
        original = "Slide 1: Hook về deal sinh viên"
        result = _inject_tiktok_directive(original)
        assert result.startswith("Create a slide deck for TikTok")
        assert original in result
        assert result.count("9:16") == 1

    def test_prompt_already_has_916_not_duplicated(self):
        original = "Create a 5-slide deck (Vertical 9:16 ratio) for TikTok."
        result = _inject_tiktok_directive(original)
        assert result == original

    def test_prompt_already_has_vertical_not_duplicated(self):
        original = "Vertical orientation slide deck"
        result = _inject_tiktok_directive(original)
        assert result == original

    def test_bare_vietnamese_916_still_gets_directive(self):
        """Regression test: a Vietnamese prompt that only mentions '9:16'
        in passing (e.g. 'tỉ lệ 9:16') MUST still get the English directive,
        because NotebookLM only honors the exact English phrase."""
        original = "Tất cả slide phải có kích thước 9:16 (viết bằng tiếng Việt)"
        result = _inject_tiktok_directive(original)
        assert result.startswith("Create a slide deck for TikTok")
        assert original in result
        # Directive must appear exactly once (English + the Vietnamese mention)
        assert result.count("Vertical 9:16 ratio") == 1

    def test_bare_916_number_alone_still_gets_directive(self):
        """A bare '9:16' substring without English context must not trip
        the idempotence check."""
        original = "Làm slide 9:16 cho TikTok"
        result = _inject_tiktok_directive(original)
        assert result.startswith("Create a slide deck for TikTok")
        assert original in result

    def test_idempotent(self):
        """Calling twice must not duplicate the directive."""
        original = "My custom slide content"
        once = _inject_tiktok_directive(original)
        twice = _inject_tiktok_directive(once)
        assert once == twice

    def test_whitespace_preserved(self):
        original = "   "
        result = _inject_tiktok_directive(original)
        # Whitespace-only is treated as empty
        assert "9:16" in result
        assert result.strip() == result
