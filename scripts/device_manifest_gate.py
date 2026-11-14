"""Offline COMPAT-001 record checks; never hardware or release certification."""
import json
import re
import sys

GATES = frozenset('bootloader kernel vendor_blobs modem_ims gpu camera selinux avb ota accessibility recovery secure_keys'.split())
EDITIONS = {'aosp_rom', 'mobile_linux', 'android_app'}
APP_NA = {'bootloader', 'kernel', 'vendor_blobs', 'selinux', 'avb', 'ota', 'recovery'}
LINUX_NA = {'selinux', 'avb'}


def check(record):
    """Return review eligibility, not support. Invalid records raise ValueError."""
    def require(condition, message):
        if not condition:
            raise ValueError(message)
    require(type(record) is dict, 'record must be object')
    require(set(record) == {'schema', 'device', 'variant', 'edition', 'tier', 'baseline', 'hardware', 'gates'}, 'record fields')
    require(record['schema'] == 'mrnothing-device-v1', 'schema')
    for key in ('device', 'variant', 'baseline'):
        require(type(record[key]) is str and 0 < len(record[key]) <= 200 and record[key].strip() == record[key], key)
    edition = record['edition']
    require(type(edition) is str and edition in EDITIONS, 'edition')
    require(record['tier'] in ('research', 'candidate'), 'support promotion requires external acceptance')
    hardware = record['hardware']
    require(type(hardware) is dict and set(hardware) == {'arch', 'ram_gib', 'storage_gib', 'android_api'}, 'hardware fields')
    require(hardware['arch'] == 'arm64', 'initial hardware policy is arm64')
    for key, minimum in (('ram_gib', 4), ('storage_gib', 64)):
        require(type(hardware[key]) is int and hardware[key] >= minimum, key)
    api = hardware['android_api']
    require((edition == 'mobile_linux' and api is None) or
            (edition != 'mobile_linux' and type(api) is int and api >= 29), 'android_api')
    gates = record['gates']
    require(type(gates) is dict and set(gates) == GATES, 'all capability gates required')
    allowed_na = APP_NA if edition == 'android_app' else LINUX_NA if edition == 'mobile_linux' else set()
    blocked = []
    for name, gate in gates.items():
        require(type(gate) is dict and set(gate) == {'status', 'evidence', 'reason'}, name + ' fields')
        status, evidence, reason = gate['status'], gate['evidence'], gate['reason']
        require(type(status) is str and status in {'unknown', 'pass', 'fail', 'not_applicable'}, name + ' status')
        require(type(evidence) is list and len(evidence) <= 20, name + ' evidence')
        require(all(type(item) is str and re.fullmatch(r'evidence/[A-Za-z0-9_./-]+', item) and '..' not in item.split('/') for item in evidence), name + ' evidence paths')
        require(type(reason) is str and 0 < len(reason) <= 1000, name + ' reason')
        if status == 'not_applicable':
            require(name in allowed_na, name + ' cannot be waived')
        elif status == 'pass':
            require(bool(evidence), name + ' needs evidence references')
        else:
            blocked.append(name)
    return {'record_valid': True, 'review_ready': not blocked and record['tier'] == 'candidate',
            'blocked_gates': sorted(blocked), 'hardware_verified': False,
            'release_authorized': False, 'flash_authorized': False}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def main():
    try:
        with open(sys.argv[1], encoding='utf-8') as source:
            record = json.load(source, object_pairs_hook=unique_object)
        result = check(record)
        print(json.dumps(result, sort_keys=True))
        return 0 if result['review_ready'] else 1
    except (ValueError, TypeError, OSError, IndexError):
        print(json.dumps({'record_valid': False, 'release_authorized': False, 'flash_authorized': False}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
