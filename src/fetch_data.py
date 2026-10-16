"""Fetch a cached catalog of IDs, then verify statistics with Roblox's public API.

Run explicitly: python src/fetch_data.py
Existing raw responses are reused. Use a new data/raw folder for a new experiment;
do not mix snapshots or overwrite the submitted snapshot after test inspection.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data/raw'
CATALOG = 'https://rodict.vercel.app/api/export/games?format=json'
DETAILS = 'https://games.roblox.com/v1/games'

def fetch(url, path):
    if path.exists():
        return json.loads(path.read_text(encoding='utf-8-sig'))
    for attempt in range(3):
        try:
            request = Request(url, headers={'User-Agent': 'RobloxCrowd-Education/1.0'})
            with urlopen(request, timeout=45) as response:
                body = response.read()
            payload = json.loads(body)
            path.write_bytes(body)
            return payload
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 ** (attempt + 1))

def main():
    RAW.mkdir(parents=True, exist_ok=True)
    manifest_path = RAW/'manifest.json'
    previous = {}
    if manifest_path.exists():
        previous = {item['path']:item for item in json.loads(manifest_path.read_text(encoding='utf-8'))['files']}
    catalog_path = RAW / 'rodict_games.json'
    catalog = fetch(CATALOG, catalog_path)
    ids = list(dict.fromkeys(str(row['universe_id']) for row in catalog['rows']))
    if len(ids) < 100 or not all(i.isdigit() for i in ids):
        raise ValueError('Catalog too small or invalid IDs; review source before training.')
    sources = [(catalog_path, CATALOG)]
    returned = []
    invalid_rows = 0
    for start in range(0, len(ids), 50):
        url = DETAILS + '?' + urlencode({'universeIds': ','.join(ids[start:start+50])})
        path = RAW / f'roblox_batch_{start//50+1:02}.json'
        payload = fetch(url, path)
        rows = payload.get('data', [])
        if not rows:
            raise ValueError(f'Empty Roblox response: {path.name}')
        returned.extend(str(row['id']) for row in rows if int(row.get('id', 0)) > 0)
        invalid_rows += sum(int(row.get('id', 0)) <= 0 for row in rows)
        sources.append((path, url))
        print(f'{path.name}: {len(rows)} response records', flush=True)
        time.sleep(1)
    records = []
    for path,url in sources:
        relative = path.relative_to(ROOT).as_posix()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        old = previous.get(relative, {})
        saved_at = old.get('saved_at_utc') if old.get('sha256') == digest else None
        records.append({'path':relative, 'url':url, 'sha256':digest,
                        'saved_at_utc':saved_at or datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()})
    manifest = {
        'assembled_at_utc': datetime.now(timezone.utc).isoformat(),
        'catalog_generated_at': catalog.get('generatedAt'),
        'requested_universes': len(ids),
        'returned_universes': len(set(returned)),
        'unavailable_placeholder_rows': invalid_rows,
        'unavailable_ids': sorted(set(ids)-set(returned)),
        'selection': 'Universe IDs from rodict games export, at most 1000 busiest tracked games; all training statistics from Roblox API.',
        'files': records,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(f'Collection complete: {len(set(returned))} games')

if __name__ == '__main__':
    main()
