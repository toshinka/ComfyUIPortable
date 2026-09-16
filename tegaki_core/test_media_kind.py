"""Unit tests for banked canonical media-kind extension classifier.

Verifies:
- exact classification of proven IMAGE extensions (.png, .jpg, .jpeg, .webp)
- exact classification of proven VIDEO extensions (.mp4, .webm, .mov, .mkv)
- case normalization (.PNG, .Mp4, etc.)
- UNKNOWN classification for unproven extensions, missing extensions, dotfiles, audio
- purely syntactic operation without filesystem access
- PathLike and string input support
- invalid argument type rejection
- production parity with H3 and Manga extension contracts
"""

from __future__ import annotations

from pathlib import Path, PurePosixPath, PureWindowsPath
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tegaki_core.media_kind import (
    IMAGE_EXTENSIONS,
    VIDEO_EXTENSIONS,
    MediaKind,
    classify_media_kind,
    extract_media_extension,
    is_image_extension,
    is_video_extension,
)


class MediaKindClassifierTests(unittest.TestCase):
    """Test suite for MediaKind extension classifier."""

    def test_proven_image_extensions(self):
        for ext in (".png", ".jpg", ".jpeg", ".webp"):
            with self.subTest(ext=ext):
                self.assertEqual(classify_media_kind(ext), MediaKind.IMAGE)
                self.assertTrue(is_image_extension(ext))
                self.assertFalse(is_video_extension(ext))

    def test_proven_video_extensions(self):
        for ext in (".mp4", ".webm", ".mov", ".mkv"):
            with self.subTest(ext=ext):
                self.assertEqual(classify_media_kind(ext), MediaKind.VIDEO)
                self.assertTrue(is_video_extension(ext))
                self.assertFalse(is_image_extension(ext))

    def test_case_normalization(self):
        cases = [
            (".PNG", MediaKind.IMAGE),
            (".JpG", MediaKind.IMAGE),
            (".JPEG", MediaKind.IMAGE),
            (".WebP", MediaKind.IMAGE),
            (".MP4", MediaKind.VIDEO),
            (".WebM", MediaKind.VIDEO),
            (".MoV", MediaKind.VIDEO),
            (".MKV", MediaKind.VIDEO),
        ]
        for token, expected in cases:
            with self.subTest(token=token):
                self.assertEqual(classify_media_kind(token), expected)

    def test_paths_and_pathlike(self):
        self.assertEqual(
            classify_media_kind("output/h3/still/robot.png"),
            MediaKind.IMAGE,
        )
        self.assertEqual(
            classify_media_kind(Path("output/h3/video/clip.mp4")),
            MediaKind.VIDEO,
        )
        self.assertEqual(
            classify_media_kind(PurePosixPath("manga/ref/face.webp")),
            MediaKind.IMAGE,
        )
        self.assertEqual(
            classify_media_kind(PureWindowsPath(r"C:\workspace\anim.webm")),
            MediaKind.VIDEO,
        )

    def test_bare_tokens(self):
        self.assertEqual(classify_media_kind("png"), MediaKind.IMAGE)
        self.assertEqual(classify_media_kind("mp4"), MediaKind.VIDEO)
        self.assertEqual(classify_media_kind("JPEG"), MediaKind.IMAGE)
        self.assertEqual(classify_media_kind("MOV"), MediaKind.VIDEO)

    def test_multidot_filenames(self):
        self.assertEqual(
            classify_media_kind("h1c-job-12345.0001.png"),
            MediaKind.IMAGE,
        )
        self.assertEqual(
            classify_media_kind("video.final.cut.mp4"),
            MediaKind.VIDEO,
        )
        self.assertEqual(
            classify_media_kind("backup.mp4.bak"),
            MediaKind.UNKNOWN,
        )

    def test_unproven_and_unsupported_extensions(self):
        # Audio is disabled/forbidden in current production
        for audio_ext in (".mp3", ".wav", ".flac", ".ogg", ".aac"):
            with self.subTest(ext=audio_ext):
                self.assertEqual(classify_media_kind(audio_ext), MediaKind.UNKNOWN)

        # Other formats not in proven contracts
        for other in (".gif", ".bmp", ".tiff", ".svg", ".avi", ".flv", ".pdf", ".exe"):
            with self.subTest(ext=other):
                self.assertEqual(classify_media_kind(other), MediaKind.UNKNOWN)

    def test_missing_and_edge_case_extensions(self):
        self.assertEqual(classify_media_kind(""), MediaKind.UNKNOWN)
        self.assertEqual(classify_media_kind("   "), MediaKind.UNKNOWN)
        self.assertEqual(classify_media_kind("filename_without_ext"), MediaKind.UNKNOWN)
        self.assertEqual(classify_media_kind("/path/to/folder/"), MediaKind.UNKNOWN)
        self.assertEqual(classify_media_kind("trailing_dot."), MediaKind.UNKNOWN)
        self.assertEqual(classify_media_kind(".gitignore"), MediaKind.UNKNOWN)
        self.assertEqual(classify_media_kind(".env"), MediaKind.UNKNOWN)

    def test_pure_syntactic_no_filesystem_access(self):
        # Even completely fictional non-existent paths are classified purely by syntax
        fictional_path = "Z:/definitely/nonexistent/disk/phantom_image_12345.png"
        self.assertFalse(Path(fictional_path).exists())
        self.assertEqual(classify_media_kind(fictional_path), MediaKind.IMAGE)

    def test_invalid_types_raise_type_error(self):
        for invalid in (None, 123, 45.6, True, False, [], {}):
            with self.subTest(val=invalid):
                with self.assertRaises(TypeError):
                    classify_media_kind(invalid)  # type: ignore

    def test_production_parity_contracts(self):
        # H3 contracts
        from h3.adapters.native_ref2va import (
            PICTURE_SUFFIXES as H3_REF2VA_PICTURE,
            VIDEO_SUFFIXES as H3_REF2VA_VIDEO,
        )
        from h3.app.server import (
            REFERENCE_SUFFIXES as H3_SERVER_REF,
            VIDEO_SUFFIXES as H3_SERVER_VIDEO,
        )

        self.assertEqual(IMAGE_EXTENSIONS, H3_REF2VA_PICTURE)
        self.assertEqual(IMAGE_EXTENSIONS, H3_SERVER_REF)
        self.assertEqual(VIDEO_EXTENSIONS, H3_REF2VA_VIDEO)
        self.assertEqual(VIDEO_EXTENSIONS, H3_SERVER_VIDEO)

        # Manga contract parity (matches JS SUPPORTED_REFERENCE_EXTENSIONS)
        manga_js_supported = {".png", ".jpg", ".jpeg", ".webp"}
        self.assertEqual(IMAGE_EXTENSIONS, manga_js_supported)


if __name__ == "__main__":
    unittest.main()
