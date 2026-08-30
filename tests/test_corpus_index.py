from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location("corpus_index", SCRIPTS / "corpus_index.py")
assert SPEC and SPEC.loader
INDEX = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INDEX)


class CorpusIndexTests(unittest.TestCase):
    def test_split_chunks_keeps_all_content_and_locators(self) -> None:
        text = "\n\n".join(("甲" * 120 + "。", "乙" * 130 + "。", "丙" * 110 + "。"))
        chunks = INDEX.split_chunks(text, target_chars=200)

        self.assertEqual("".join(chunk["text"].replace("\n", "") for chunk in chunks), text.replace("\n", ""))
        self.assertEqual(chunks[0]["paragraph_start"], 1)
        self.assertEqual(chunks[-1]["paragraph_end"], 3)
        self.assertEqual(chunks[-1]["content_char_end"], 360)

    def test_build_roundtrip_and_source_hash(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "novel.txt"
            source.write_text("第一段。\n\n第二段。", encoding="utf-8")
            records = INDEX.build_index([source], chunk_chars=200)
            output = root / "index.jsonl"
            INDEX.write_jsonl(records, output)
            loaded = INDEX.read_jsonl(output)

        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]["text"], "第一段。\n\n第二段。")
        self.assertEqual(len(loaded[0]["source_sha256"]), 64)
        self.assertIn("metrics", loaded[0])

    def test_search_by_keyword_and_style(self) -> None:
        quiet = INDEX.analyze_text("天黑了。\n\n门关了。")
        dialogue = INDEX.analyze_text("“你来？”\n\n“我不来！”\n\n“为什么？”")
        records = [
            {"source": "quiet.txt", "chunk_number": 1, "text": "天黑了。门关了。", "metrics": quiet},
            {"source": "talk.txt", "chunk_number": 1, "text": "“你来？”“我不来！”“为什么？”", "metrics": dialogue},
        ]

        matches = INDEX.search_records(records, query_text="“去吗？”“不去！”", top=1)
        keyword = INDEX.search_records(records, contains=["门关"], top=2)

        self.assertEqual(matches[0]["source"], "talk.txt")
        self.assertEqual(keyword[0]["source"], "quiet.txt")


if __name__ == "__main__":
    unittest.main()
