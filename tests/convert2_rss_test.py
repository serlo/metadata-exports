import json
from datetime import datetime
from pathlib import PurePath
import unittest
from convert2rss import generate_rss

class TestGenerateRssFromMetadata(unittest.TestCase):
    def test_generate_rss_from_metadata(self):
        test_dir = str(PurePath(__file__).parent)
        with open("keywords.json", "r", encoding="utf-8") as input_file:
            keywords = json.load(input_file)

        with open(
            f"{test_dir}/metadata_sample.json", "r", encoding="utf-8"
        ) as metadata_sample_file:
            published_date = datetime.fromisoformat("2023-08-09T16:24:18.219695")
            metadata = json.load(metadata_sample_file)
            with open(
                f"{test_dir}/publisher_sample.json", "r", encoding="utf-8"
            ) as publisher_sample_file:
                publisher = json.load(publisher_sample_file)
                with open(
                    f"{test_dir}/export_sample.rss", "r", encoding="utf-8"
                ) as export_sample_file:
                    expected_rss_export = export_sample_file.read()
                    actual_rss_export = generate_rss(
                        metadata, publisher, lambda: published_date, keywords
                    )
                    self.assertEqual(actual_rss_export, expected_rss_export)
