"""A divisão por semestre deve preservar todos os campos e registros."""

from collections import Counter
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from services.data.loader import load_offers
from services.config import DEFAULT_DATA


SOURCE = DEFAULT_DATA
ORIGINAL_CANONICAL_SHA256 = 'f82db114a0319be61348cc6f43662e48d0c943b0affcdaa441ef114271a069d1'
COUNTS = {'2022.1': 165, '2023.1': 172, '2023.2': 176, '2024.1': 173, '2024.2': 179,
          '2025.1': 175, '2025.2': 170, '2026.1': 172, '2026.2': 173}


class SemesterLoaderTests(unittest.TestCase):
    def test_migrated_dataset_preserves_every_record_field_and_order(self):
        rows, source = load_offers(SOURCE)
        original = [row for row in rows if row['periodo'] != '2022.1']
        canonical = json.dumps(original, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
        self.assertEqual(hashlib.sha256(canonical).hexdigest(), ORIGINAL_CANONICAL_SHA256)
        self.assertEqual(len(rows), 1555)
        self.assertEqual(dict(Counter(row['periodo'] for row in rows)), COUNTS)
        self.assertEqual([file['period'] for file in source['files']], list(COUNTS))
        self.assertEqual(source['currentRows'], 173)
        for period, count in COUNTS.items():
            semester, single = load_offers(SOURCE / f'{period}.json')
            self.assertEqual(len(semester), count)
            self.assertTrue(all(row['periodo'] == period for row in semester))
            self.assertEqual(single['sha256'], hashlib.sha256((SOURCE / f'{period}.json').read_bytes()).hexdigest())

    def test_directory_order_and_legacy_file_have_identical_records(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as temporary:
            directory = Path(temporary)
            self.assertTrue(directory.resolve().is_relative_to(Path(__file__).resolve().parent))
            later = [{'periodo': '2026.2', 'codigo': 'MC0002'}, {'periodo': '2026.2', 'codigo': 'MC0001'}]
            earlier = [{'periodo': '2023.1', 'codigo': 'CC0001'}]
            (directory / '2026.2.json').write_text(json.dumps(later), encoding='utf-8')
            (directory / '2023.1.json').write_text(json.dumps(earlier), encoding='utf-8-sig')
            (directory / 'README.md').write_text('Notas da base', encoding='utf-8')
            rows, source = load_offers(directory)
            (directory / 'completa.json').write_text(json.dumps(earlier + later), encoding='utf-8')
            legacy, _ = load_offers(directory / 'completa.json')
            self.assertEqual(rows, legacy)
            self.assertEqual([f['name'] for f in source['files']], ['2023.1.json', '2026.2.json'])
            self.assertEqual(load_offers(directory)[1]['sha256'], source['sha256'])

    def test_content_change_changes_collection_fingerprint(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as temporary:
            self.assertTrue(Path(temporary).resolve().is_relative_to(Path(__file__).resolve().parent))
            path = Path(temporary) / '2026.2.json'
            path.write_text('[{"periodo":"2026.2","matriculas":1}]', encoding='utf-8')
            before = load_offers(path.parent)[1]
            path.write_text('[{"periodo":"2026.2","matriculas":2}]', encoding='utf-8')
            after = load_offers(path.parent)[1]
            self.assertNotEqual(before['sha256'], after['sha256'])
            self.assertNotEqual(before['files'][0]['sha256'], after['files'][0]['sha256'])

    def test_invalid_and_empty_sources_are_rejected(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as temporary:
            directory = Path(temporary)
            self.assertTrue(directory.resolve().is_relative_to(Path(__file__).resolve().parent))
            with self.assertRaises(ValueError):
                load_offers(directory)
            with self.assertRaises(FileNotFoundError):
                load_offers(directory / 'inexistente')
            path = directory / '2026.2.json'
            for content in ('{}', '[', '[{"periodo":"2026.1"}]', '[4]'):
                path.write_text(content, encoding='utf-8')
                with self.assertRaises(ValueError):
                    load_offers(directory)
            path.unlink()
            (directory / '2026.3.json').write_text('[]', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'Nome de semestre inválido'):
                load_offers(directory)


if __name__ == '__main__':
    unittest.main()
