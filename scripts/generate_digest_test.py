import unittest

from generate_digest import chunk_message, escape_markdown_v2, clamp_title, MESSAGE_SEPARATOR


class TestChunkMessage(unittest.TestCase):

    def test_returns_header_only_when_no_content(self):
        result = chunk_message("Header", [])
        self.assertEqual(result, ["*Header*"])

    def test_single_chunk_when_content_fits(self):
        sections = ["Section A", "Section B"]
        result = chunk_message("Report", sections, max_length=4000)
        self.assertEqual(len(result), 1)
        self.assertIn("Section A", result[0])
        self.assertIn("Section B", result[0])
        self.assertTrue(result[0].startswith("*Report*"))

    def test_splits_into_multiple_chunks_when_exceeding_limit(self):
        sections = ["A" * 50, "B" * 50, "C" * 50]
        result = chunk_message("H", sections, max_length=70)
        self.assertGreater(len(result), 1)
        self.assertTrue(all(len(chunk) <= 70 for chunk in result))

    def test_continuation_header_on_subsequent_chunks(self):
        sections = ["A" * 50, "B" * 50]
        result = chunk_message("H", sections, max_length=60)
        self.assertTrue(result[0].startswith("*H*"))
        self.assertIn("cont", result[1])

    def test_all_sections_present_across_chunks(self):
        sections = ["AAA", "BBB", "CCC"]
        result = chunk_message("H", sections, max_length=25)
        combined = MESSAGE_SEPARATOR.join(result)
        for section in sections:
            self.assertIn(section, combined)

    def test_single_oversized_section_still_included(self):
        sections = ["X" * 200]
        result = chunk_message("H", sections, max_length=100)
        self.assertEqual(len(result), 1)
        self.assertIn("X" * 200, result[0])

    def test_first_chunk_uses_original_header(self):
        header_text = "Weekend issues report — Sun, 2026\\-03\\-01"
        sections = ["sec1"]
        result = chunk_message(header_text, sections, max_length=4000)
        self.assertTrue(result[0].startswith(f"*{header_text}*"))

    def test_continuation_header_format(self):
        header_text = "Weekend issues report — Sun, 2026\\-03\\-01"
        sections = ["A" * 200, "B" * 200]
        result = chunk_message(header_text, sections, max_length=270)
        self.assertIn("\\(cont\\.\\)", result[1])
        self.assertTrue(result[1].startswith("*Weekend issues report"))
        self.assertTrue(result[1].split(MESSAGE_SEPARATOR)[0].endswith("*"))

    def test_wraps_header_in_bold(self):
        result = chunk_message("Report title", ["content"])
        self.assertTrue(result[0].startswith("*Report title*"))


class TestEscapeMarkdownV2(unittest.TestCase):

    def test_escapes_special_characters(self):
        self.assertEqual(escape_markdown_v2("a.b"), "a\\.b")
        self.assertEqual(escape_markdown_v2("(x)"), "\\(x\\)")
        self.assertEqual(escape_markdown_v2("#1"), "\\#1")

    def test_plain_text_unchanged(self):
        self.assertEqual(escape_markdown_v2("hello"), "hello")


class TestClampTitle(unittest.TestCase):

    def test_short_title_unchanged(self):
        self.assertEqual(clamp_title("short title"), "short title")

    def test_long_title_clamped(self):
        words = " ".join(f"w{i}" for i in range(25))
        result = clamp_title(words)
        self.assertTrue(result.endswith("…"))
        self.assertEqual(len(result.split()), 18)


if __name__ == "__main__":
    unittest.main()
