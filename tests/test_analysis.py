"""
Tests für analysis.py – fokussiert auf:
  slugify: Text-zu-URL-Slug-Konvertierung (Jinja2-Filter)
"""

import pytest
import re


# ---------------------------------------------------------------------------
# slugify – lokal repliziert für isolierte Unit-Tests
# ---------------------------------------------------------------------------

def slugify(s):
    s = s.lower().strip()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s_-]+', '-', s)
    s = re.sub(r'^-+|-+$', '', s)
    return s


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSlugifyBasic:
    def test_lowercase(self):
        assert slugify("Hello World") == "hello-world"

    def test_spaces_become_hyphens(self):
        assert slugify("foo bar baz") == "foo-bar-baz"

    def test_already_lowercase_unchanged(self):
        assert slugify("hello") == "hello"

    def test_single_word(self):
        assert slugify("Test") == "test"


class TestSlugifySpecialChars:
    def test_exclamation_mark_removed(self):
        assert slugify("Hello!") == "hello"

    def test_dot_removed(self):
        assert slugify("v1.0.0") == "v100"

    def test_parentheses_removed(self):
        assert slugify("foo (bar)") == "foo-bar"

    def test_slash_removed(self):
        assert slugify("foo/bar") == "foobar"

    def test_ampersand_removed(self):
        assert slugify("Cats & Dogs") == "cats-dogs"

    def test_unicode_letters_kept(self):
        # \w includes unicode letters
        assert "ber" in slugify("über")


class TestSlugifyHyphens:
    def test_existing_hyphen_preserved(self):
        assert slugify("foo-bar") == "foo-bar"

    def test_multiple_spaces_become_single_hyphen(self):
        assert slugify("foo   bar") == "foo-bar"

    def test_underscore_becomes_hyphen(self):
        assert slugify("foo_bar") == "foo-bar"

    def test_mixed_space_hyphen_becomes_single(self):
        assert slugify("foo - bar") == "foo-bar"

    def test_leading_hyphen_stripped(self):
        assert not slugify("-hello").startswith("-")

    def test_trailing_hyphen_stripped(self):
        assert not slugify("hello-").endswith("-")

    def test_leading_and_trailing_stripped(self):
        result = slugify("  ---hello---  ")
        assert result == "hello"


class TestSlugifyWhitespace:
    def test_leading_whitespace_stripped(self):
        assert slugify("  hello") == "hello"

    def test_trailing_whitespace_stripped(self):
        assert slugify("hello  ") == "hello"

    def test_tabs_become_hyphen(self):
        assert slugify("foo\tbar") == "foo-bar"


class TestSlugifyEdgeCases:
    def test_empty_string(self):
        assert slugify("") == ""

    def test_only_special_chars(self):
        assert slugify("!@#$%") == ""

    def test_numbers_preserved(self):
        assert slugify("study 42") == "study-42"

    def test_long_title(self):
        result = slugify("This Is A Very Long Study Title With Many Words")
        assert " " not in result
        assert result == result.lower()
