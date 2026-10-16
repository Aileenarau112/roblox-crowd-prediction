"""Shared dataset rules and deterministic features; no fitted transforms here."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INPUTS = ['visits', 'favorites', 'age_days', 'max_players']
LABELS = ['sepi', 'sedang', 'ramai']
FEATURE_SETS = {
    'riwayat_kunjungan': ['visits', 'age_days'],
    'profil_lengkap': INPUTS + ['favorites_per_1000_visits'],
}

def crowd_label(players):
    """Fixed educational thresholds, chosen before fitting or inspecting test scores."""
    return 'sepi' if players < 100 else 'sedang' if players < 1000 else 'ramai'

def build_features(frame):
    missing = set(INPUTS) - set(frame.columns)
    if missing:
        raise ValueError(f'Kolom belum lengkap: {sorted(missing)}')
    clean = frame[INPUTS].apply(pd.to_numeric, errors='raise').astype(float)
    if not np.isfinite(clean.to_numpy()).all() or (clean < 0).any().any():
        raise ValueError('Semua input harus angka berhingga, tidak kosong, dan tidak negatif.')
    if (clean.max_players < 1).any():
        raise ValueError('Kapasitas server minimal 1.')
    counts = clean[['visits', 'favorites', 'max_players']].to_numpy()
    if not np.equal(counts, np.floor(counts)).all():
        raise ValueError('Kunjungan, favorit, dan kapasitas server harus bilangan bulat.')
    clean['favorites_per_1000_visits'] = 1000 * clean.favorites / clean.visits.clip(lower=1)
    return clean

def load_snapshot():
    manifest = json.loads((ROOT/'data/raw/manifest.json').read_text(encoding='utf-8'))
    rows, excluded = [], []
    for source in manifest['files']:
        if not Path(source['path']).name.startswith('roblox_batch_'):
            continue
        path = ROOT / source['path']
        if hashlib.sha256(path.read_bytes()).hexdigest() != source['sha256']:
            raise ValueError(f'Data berubah dari manifest: {path.name}')
        observed = pd.Timestamp(source['saved_at_utc'])
        payload = json.loads(path.read_text(encoding='utf-8-sig'))
        for game in payload['data']:
            try:
                if game.get('isContentRestricted'):
                    raise ValueError('content_restricted')
                created = pd.Timestamp(game['created'])
                if pd.isna(created):
                    raise ValueError('created_missing')
                age_days = (observed-created).total_seconds()/86400
                creator = game['creator']
                row = {
                    'universe_id': str(game['id']), 'root_place_id': str(game['rootPlaceId']),
                    'name': game['name'], 'creator_group': f"{creator['type']}:{creator['id']}",
                    'genre': game.get('genre_l1') or game.get('genre') or 'Unknown',
                    'visits': game['visits'], 'favorites': game['favoritedCount'],
                    'age_days': age_days, 'max_players': game['maxPlayers'],
                    'playing': game['playing'], 'observed_at_utc': observed.isoformat(),
                }
                build_features(pd.DataFrame([row]))
                if not np.isfinite(float(row['playing'])) or float(row['playing']) < 0:
                    raise ValueError('playing_invalid')
                row['crowd_level'] = crowd_label(float(row['playing']))
                rows.append(row)
            except (KeyError, ValueError, TypeError) as exc:
                excluded.append({'universe_id': str(game.get('id')), 'reason': str(exc)})
    frame = pd.DataFrame(rows)
    if frame.empty or frame.universe_id.duplicated().any():
        raise ValueError('Snapshot kosong atau universe ID ganda.')
    return frame, excluded, manifest
