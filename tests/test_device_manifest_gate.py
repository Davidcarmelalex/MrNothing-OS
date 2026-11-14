import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('compat_gate', ROOT / 'scripts/device_manifest_gate.py')
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class DeviceManifestTests(unittest.TestCase):
    def setUp(self):
        self.record = json.loads((ROOT / 'devices/caiman.aosp_rom.json').read_text())

    def test_reference_is_blocked(self):
        result = gate.check(self.record)
        self.assertEqual(set(result['blocked_gates']), gate.GATES)
        self.assertFalse(result['review_ready'])
        self.assertFalse(result['flash_authorized'])

    def test_missing_gates(self):
        for name in gate.GATES:
            record = copy.deepcopy(self.record)
            del record['gates'][name]
            with self.subTest(name=name), self.assertRaises(ValueError):
                gate.check(record)

    def test_no_blanket_waivers(self):
        for name in gate.GATES:
            record = copy.deepcopy(self.record)
            record['gates'][name]['status'] = 'not_applicable'
            with self.subTest(name=name), self.assertRaises(ValueError):
                gate.check(record)

    def test_pass_needs_evidence(self):
        self.record['gates']['kernel']['status'] = 'pass'
        with self.assertRaises(ValueError):
            gate.check(self.record)

    def test_references_are_not_certification(self):
        self.record['tier'] = 'candidate'
        for item in self.record['gates'].values():
            item.update(status='pass', evidence=['evidence/synthetic.json'])
        result = gate.check(self.record)
        self.assertTrue(result['review_ready'])
        self.assertFalse(result['hardware_verified'])
        self.assertFalse(result['release_authorized'])
        self.assertFalse(result['flash_authorized'])

    def test_minimums_and_boolean_confusion(self):
        for key, values in {'ram_gib': [True, 3, '8'], 'storage_gib': [False, 63], 'android_api': [True, 28, None]}.items():
            for value in values:
                record = copy.deepcopy(self.record)
                record['hardware'][key] = value
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    gate.check(record)

    def test_linux_does_not_inherit_android(self):
        self.record['edition'] = 'mobile_linux'
        with self.assertRaises(ValueError):
            gate.check(self.record)
        self.record['hardware']['android_api'] = None
        self.assertFalse(gate.check(self.record)['review_ready'])
        self.record['gates']['kernel']['status'] = 'not_applicable'
        with self.assertRaises(ValueError):
            gate.check(self.record)

    def test_app_waives_firmware_only(self):
        self.record['edition'] = 'android_app'
        for name in gate.APP_NA:
            self.record['gates'][name]['status'] = 'not_applicable'
        self.assertFalse(gate.check(self.record)['review_ready'])
        self.record['gates']['secure_keys']['status'] = 'not_applicable'
        with self.assertRaises(ValueError):
            gate.check(self.record)

    def test_no_support_promotion(self):
        self.record['tier'] = 'supported'
        with self.assertRaises(ValueError):
            gate.check(self.record)

    def test_duplicate_keys(self):
        with self.assertRaises(ValueError):
            json.loads('{"edition":"android_app","edition":"aosp_rom"}', object_pairs_hook=gate.unique_object)

    def test_unknown_fields_and_status(self):
        self.record['gates']['kernel']['status'] = True
        with self.assertRaises(ValueError):
            gate.check(self.record)
        self.record['gates']['kernel']['status'] = 'unknown'
        self.record['flash_authorized'] = True
        with self.assertRaises(ValueError):
            gate.check(self.record)

    def test_evidence_path_traversal(self):
        self.record['gates']['kernel']['evidence'] = ['evidence/../secret']
        with self.assertRaises(ValueError):
            gate.check(self.record)
