"""Owner-invoked text-only Sarvam smoke client; no phone tools or executor."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.sarvam_provider import SarvamError, generate_reply


def main():
    parser = argparse.ArgumentParser(description='Send stdin text to Sarvam; output untrusted reply only.')
    parser.add_argument('--allow-cloud', action='store_true', help='Explicitly allow sending this stdin prompt to Sarvam.')
    args = parser.parse_args()
    if not args.allow_cloud:
        print('Cloud opt-in required; no prompt read or sent.', file=sys.stderr)
        return 2
    prompt = sys.stdin.read(8193)
    try:
        print(generate_reply(prompt, cloud_opt_in=True))
        return 0
    except SarvamError as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
