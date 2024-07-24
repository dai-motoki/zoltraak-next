import subprocess
import tempfile
import os

def create_diff(original_content, modified_content):
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False) as original_file, \
         tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False) as modified_file:
        original_file.write(original_content)
        modified_file.write(modified_content)
        original_file.flush()
        modified_file.flush()

        diff_command = f"diff -u {original_file.name} {modified_file.name}"
        result = subprocess.run(diff_command, shell=True, capture_output=True, text=True, encoding='utf-8')

    os.unlink(original_file.name)
    os.unlink(modified_file.name)

    return result.stdout

def apply_patch(original_content, diff_content):
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False) as original_file, \
         tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False) as patch_file:
        original_file.write(original_content)
        patch_file.write(diff_content)
        original_file.flush()
        patch_file.flush()

        patch_command = f"patch {original_file.name} {patch_file.name}"
        result = subprocess.run(patch_command, shell=True, capture_output=True, text=True, encoding='utf-8')

        with open(original_file.name, 'r', encoding='utf-8') as patched_file:
            patched_content = patched_file.read()

    os.unlink(original_file.name)
    os.unlink(patch_file.name)

    return patched_content

# 拡張されたテストコード（日本語テスト含む）
import unittest

class TestDiffPatch(unittest.TestCase):
    def test_diff_and_patch_basic(self):
        original_content = """
This is the original content.
It has multiple lines.
Some lines will be changed."""
        modified_content = """
This is the modified content.
It has multiple lines.
Some lines have been changed."""

        diff = create_diff(original_content, modified_content)
        patched_content = apply_patch(original_content, diff)

        self.assertEqual(patched_content, modified_content)

    def test_empty_diff(self):
        content = """
This content will not change."""

        diff = create_diff(content, content)
        patched_content = apply_patch(content, diff)

        self.assertEqual(patched_content, content)

    def test_add_line(self):
        original_content = """
Line 1
Line 2
Line 3"""
        modified_content = """
Line 1
Line 2
New Line
Line 3"""

        diff = create_diff(original_content, modified_content)
        patched_content = apply_patch(original_content, diff)

        self.assertEqual(patched_content, modified_content)

    def test_remove_line(self):
        original_content = """
Line 1
Line 2
Line 3
Line 4"""
        modified_content = """
Line 1
Line 3
Line 4"""

        diff = create_diff(original_content, modified_content)
        patched_content = apply_patch(original_content, diff)

        self.assertEqual(patched_content, modified_content)

    def test_modify_multiple_lines(self):
        original_content = """
Line 1
Line 2
Line 3
Line 4
Line 5"""
        modified_content = """
Line 1
Modified Line 2
Line 3
Modified Line 4
Line 5"""

        diff = create_diff(original_content, modified_content)
        patched_content = apply_patch(original_content, diff)

        self.assertEqual(patched_content, modified_content)

    def test_empty_original_content(self):
        original_content = """
"""
        modified_content = """
New content added to empty file."""

        diff = create_diff(original_content, modified_content)
        patched_content = apply_patch(original_content, diff)

        self.assertEqual(patched_content, modified_content)

    def test_completely_different_content(self):
        original_content = """
This is completely different."""
        modified_content = """
Nothing is the same as before."""

        diff = create_diff(original_content, modified_content)
        patched_content = apply_patch(original_content, diff)

        self.assertEqual(patched_content, modified_content)

    # 日本語テストケース
    def test_japanese_content(self):
        original_content = """
これは元のコンテンツです。
複数の行があります。
一部の行が変更されます。"""
        modified_content = """
これは変更されたコンテンツです。
複数の行があります。
一部の行が変更されました。"""

        diff = create_diff(original_content, modified_content)
        patched_content = apply_patch(original_content, diff)

        self.assertEqual(patched_content, modified_content)

    def test_japanese_add_line(self):
        original_content = """
1行目
2行目
3行目"""
        modified_content = """
1行目
2行目
新しい行
3行目"""

        diff = create_diff(original_content, modified_content)
        patched_content = apply_patch(original_content, diff)

        self.assertEqual(patched_content, modified_content)

    def test_japanese_remove_line(self):
        original_content = """
1行目
2行目
3行目
4行目"""
        modified_content = """
1行目
3行目
4行目"""

        diff = create_diff(original_content, modified_content)
        patched_content = apply_patch(original_content, diff)

        self.assertEqual(patched_content, modified_content)

    def test_japanese_mixed_content(self):
        original_content = """
これは日本語です。
This is English.
今日は晴れです。
The weather is nice."""
        modified_content = """
これは日本語です。
This is English.
今日は雨です。
The weather is rainy."""

        diff = create_diff(original_content, modified_content)
        patched_content = apply_patch(original_content, diff)

        self.assertEqual(patched_content, modified_content)

if __name__ == '__main__':
    unittest.main()