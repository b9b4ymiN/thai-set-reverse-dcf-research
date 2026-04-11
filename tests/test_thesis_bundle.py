import tempfile
import unittest
from pathlib import Path

from src.pipeline.thesis_bundle import ThesisBundleBuilder


class ThesisBundleBuilderTests(unittest.TestCase):
    def test_build_copies_existing_files_and_reports_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            source = tmp / "methodology.md"
            source.write_text("hello", encoding="utf-8")

            builder = ThesisBundleBuilder(files=[str(source), str(tmp / "missing.md")])
            outdir = tmp / "bundle"
            manifest = builder.build(output_dir=str(outdir))

            self.assertEqual(manifest["copied_count"], 1)
            self.assertEqual(manifest["missing_count"], 1)
            self.assertTrue((outdir / "methodology.md").exists())
            self.assertTrue((outdir / "README.md").exists())
            self.assertTrue((outdir / "manifest.json").exists())


if __name__ == "__main__":
    unittest.main()
