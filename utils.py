"""Shared utilities for NOMAD batch registration notebooks."""

import io
import json
import time
import zipfile
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import requests
from urllib3.exceptions import InsecureRequestWarning
import urllib3

urllib3.disable_warnings(InsecureRequestWarning)


class NOMADAPIClient:
    """Client for NOMAD API operations."""
    
    def __init__(self, url_base, headers):
        """Initialize the API client.
        
        Args:
            url_base: Base URL for NOMAD (e.g., 'http://localhost:8000')
            headers: Headers dict with Authorization bearer token
        """
        self.url_base = url_base
        self.url = f'{url_base}/nomad-oasis/api/v1'
        self.headers = headers
    
    def get(self, path, params=None):
        """Make a GET request to the API."""
        return requests.get(
            f'{self.url}{path}',
            headers=self.headers,
            params=params,
            verify=False
        )
    
    def post(self, path, json_body=None):
        """Make a POST request to the API."""
        return requests.post(
            f'{self.url}{path}',
            headers=self.headers,
            json=json_body,
            verify=False
        )
    
    def put(self, path, data=None, files=None, params=None):
        """Make a PUT request to the API."""
        return requests.put(
            f'{self.url}{path}',
            headers=self.headers,
            data=data,
            files=files,
            params=params,
            verify=False
        )
    
    def iter_archive_query(self, query, required=None, owner='visible', page_size=200):
        """Iterate through archive query results with pagination."""
        required = required or {'data': '*', 'metadata': '*'}
        page_after_value = None
        results = []

        while True:
            body = {
                'required': required,
                'owner': owner,
                'query': query,
                'pagination': {'page_size': page_size},
            }
            if page_after_value:
                body['pagination']['page_after_value'] = page_after_value

            response = self.post('/entries/archive/query', json_body=body)
            response.raise_for_status()
            payload = response.json()
            results.extend(payload.get('data', []))

            pagination = payload.get('pagination', {})
            page_after_value = pagination.get('next_page_after_value')
            if not page_after_value:
                break

        return results
    
    def iter_upload_entries(self, upload_id, page_size=200):
        """Iterate through upload entries with pagination."""
        page_after_value = None
        results = []

        while True:
            params = {'page_size': page_size}
            if page_after_value:
                params['page_after_value'] = page_after_value

            response = self.get(f'/uploads/{upload_id}/entries', params=params)
            response.raise_for_status()
            payload = response.json()
            results.extend(payload.get('data', []))

            pagination = payload.get('pagination', {})
            page_after_value = pagination.get('next_page_after_value')
            if not page_after_value:
                break

        return results
    
    def get_uploads(self):
        """Get list of all uploads."""
        response = self.get('/uploads', params={'page_size': 200})
        response.raise_for_status()
        return response.json().get('data', [])
    
    def get_upload_id(self, uploads_list, name):
        """Get upload ID by name."""
        for upload in uploads_list:
            if upload.get('upload_name') == name:
                return upload.get('upload_id')
        return None
    
    def matches_schema(self, entry, schema):
        """Check if entry matches the given schema."""
        archive = entry.get('archive', {})
        data = archive.get('data', {})
        metadata = archive.get('metadata', {})
        return (
            data.get('m_def') == schema['m_def']
            or metadata.get('entry_type') == schema['entry_type']
        )
    
    def get_existing_samples(self, upload_id, schema, sort_key='name'):
        """Get existing samples of a given schema from an upload."""
        if not upload_id:
            return []

        all_entries = self.iter_archive_query({'upload_id': upload_id})
        filtered = [entry for entry in all_entries if self.matches_schema(entry, schema)]
        filtered.sort(key=lambda item: item.get('archive', {}).get('data', {}).get(sort_key, ''))
        return filtered
    
    def get_raw_path_metadata(self, upload_id, raw_path):
        """Get metadata for a raw path in an upload."""
        encoded_path = quote(raw_path.strip('/'), safe='/')
        response = self.get(f'/uploads/{upload_id}/rawdir/{encoded_path}')
        if response.status_code == 404:
            return None
        response.raise_for_status()
        payload = response.json()
        return payload.get('data', payload)
    
    def build_archive_bundle(self, prepared_rows):
        """Build a zip archive from prepared rows."""
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, mode='w', compression=zipfile.ZIP_DEFLATED) as archive_zip:
            for item in prepared_rows:
                archive_zip.writestr(
                    item['raw_path'],
                    json.dumps(item['archive'], indent=2)
                )
        buffer.seek(0)
        return buffer.getvalue()
    
    def write_archive_bundle_via_api(self, upload_id, prepared_rows):
        """Upload an archive bundle to NOMAD."""
        conflicting_paths = []
        for item in prepared_rows:
            existing_target = self.get_raw_path_metadata(upload_id, item['raw_path'])
            if existing_target and existing_target.get('directory_metadata'):
                conflicting_paths.append(item['raw_path'])

        if conflicting_paths:
            return 409, (
                'These raw paths already exist as directories from an earlier malformed upload: '
                + ', '.join(conflicting_paths)
                + '. Delete those sample paths in NOMAD or use a fresh upload, then retry.'
            )

        bundle = self.build_archive_bundle(prepared_rows)
        response = self.put(
            f'/uploads/{upload_id}/raw/',
            files={
                'file': (
                    'batch_upload.zip',
                    bundle,
                    'application/zip',
                )
            },
            params={
                'overwrite_if_exists': 'true',
                'auto_decompress': 'true',
            }
        )
        detail = response.text
        try:
            detail = response.json()
        except ValueError:
            pass
        return response.status_code, detail
    
    def process_upload(self, upload_id, timeout=180):
        """Trigger processing of an upload."""
        response = self.post(f'/uploads/{upload_id}/action/process')
        last_payload = None

        if response.status_code not in (200, 202):
            detail = response.text
            try:
                detail = response.json()
            except ValueError:
                pass

            state_response = self.get(f'/uploads/{upload_id}')
            state_response.raise_for_status()
            last_payload = state_response.json().get('data', {})

            if not (response.status_code == 400 and last_payload.get('process_running')):
                raise requests.HTTPError(
                    f'Processing failed: {response.status_code} {detail}',
                    response=response,
                )

        deadline = time.time() + timeout
        while time.time() < deadline:
            time.sleep(1)
            state_response = self.get(f'/uploads/{upload_id}')
            state_response.raise_for_status()
            last_payload = state_response.json().get('data', {})
            if not last_payload.get('process_running'):
                return last_payload

        raise TimeoutError(f'Processing did not finish within {timeout} seconds.')
    
    def get_upload_processing_details(self, upload_id):
        """Get processing details for all entries in an upload."""
        details = {}
        for entry in self.iter_upload_entries(upload_id):
            mainfile = entry.get('mainfile', '')
            if mainfile:
                details[mainfile] = entry
                details[Path(mainfile).name] = entry
        return details


# Data processing utilities
def clean_text(value):
    """Clean and normalize text values."""
    cleaned = str(value)
    cleaned = cleaned.replace('\r\n', ' ').replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
    cleaned = cleaned.replace('\xa0', ' ')
    for hidden in ('\u200b', '\u200c', '\u200d', '\ufeff'):
        cleaned = cleaned.replace(hidden, '')
    cleaned = ' '.join(cleaned.split())
    return cleaned or None


def normalize_value(value):
    """Normalize a value (handle None, NaN, strings)."""
    if value is None:
        return None
    if isinstance(value, str):
        return clean_text(value)
    if pd.isna(value):
        return None
    return value


def normalize_sample_id(value):
    """Normalize a sample ID."""
    normalized = normalize_value(value)
    return str(normalized) if normalized is not None else None


def coerce_value(value, dtype):
    """Coerce a value to the given datatype."""
    if value is None:
        return None
    if dtype == 'float':
        return float(value)
    if dtype == 'int':
        return int(float(value))
    return str(value)


def make_row_by_key(row, col_keys, col_labels):
    """Convert a DataFrame row to a dict using column keys."""
    row = row.replace(pd.NA, None)
    return {
        key: normalize_value(row.get(label))
        for key, label in zip(col_keys, col_labels)
        if label in row.index
    }


def wait_for_sample_ids(api_client, upload_id, schema, expected_ids, sort_key='name', timeout=60):
    """Wait for samples to appear in archive query results."""
    expected_ids = {normalize_sample_id(sample_id) for sample_id in expected_ids if sample_id}
    if not expected_ids:
        return api_client.get_existing_samples(upload_id, schema, sort_key=sort_key)

    deadline = time.time() + timeout
    latest_entries = []
    while time.time() < deadline:
        latest_entries = api_client.get_existing_samples(upload_id, schema, sort_key=sort_key)
        found_ids = {
            normalize_sample_id(entry.get('archive', {}).get('data', {}).get(sort_key))
            for entry in latest_entries
        }
        if expected_ids.issubset(found_ids):
            return latest_entries
        time.sleep(1)

    return latest_entries


def resolve_reference_to_name(api_client, reference_str):
    """
    Extract sample name from a NOMAD reference string.
    
    Input: ../uploads/{upload_id}/archive/{entry_id}#/data
    Returns: (entry_id, name) tuple or (None, None) if not found
    
    Args:
        api_client: NOMADAPIClient instance
        reference_str: Reference string from archive
    """
    if not reference_str:
        return None, None
    
    try:
        # Parse reference: ../uploads/{upload_id}/archive/{entry_id}#/data
        parts = str(reference_str).split('/archive/')
        if len(parts) < 2:
            return None, None
        
        entry_id = parts[1].split('#')[0]
        if not entry_id:
            return None, None
        
        # Query by entry_id to get the name
        entries = api_client.iter_archive_query({'entry_id': entry_id})
        if not entries:
            return entry_id, None
        
        entry = entries[0]
        name = entry.get('archive', {}).get('data', {}).get('name')
        return entry_id, name
    
    except Exception:
        return None, None


def resolve_name_to_reference(api_client, sample_name, schema_m_def, upload_id=None):
    """
    Find a sample entry by name and return its reference string.
    
    Returns reference in format: ../uploads/{upload_id}/archive/{entry_id}#/data
    Strategy: Search current upload first, then all uploads if not specified
    
    Args:
        api_client: NOMADAPIClient instance
        sample_name: Name of the sample to find
        schema_m_def: Full m_def path (e.g., 'nomad_battery_space.schema_packages.hzb_bs_assembly_package.SeparatorSample')
        upload_id: Optional upload_id to search in (searches all if not provided)
    
    Returns:
        Reference string or None if not found
    """
    if not sample_name:
        return None
    
    try:
        # Try specified upload first
        if upload_id:
            entries = api_client.iter_archive_query({'upload_id': upload_id})
            matching = [
                e for e in entries
                if (e.get('archive', {}).get('data', {}).get('m_def') == schema_m_def
                    and e.get('archive', {}).get('data', {}).get('name') == sample_name)
            ]
            if matching:
                entry_id = matching[0].get('entry_id')
                reference = f"../uploads/{upload_id}/archive/{entry_id}#/data"
                return reference
        
        # Search all uploads if not found or not specified
        all_entries = api_client.iter_archive_query({})
        matching = [
            e for e in all_entries
            if (e.get('archive', {}).get('data', {}).get('m_def') == schema_m_def
                and e.get('archive', {}).get('data', {}).get('name') == sample_name)
        ]
        
        if not matching:
            return None
        
        entry_id = matching[0].get('entry_id')
        entry_obj = matching[0]
        
        # Try to get upload_id from different possible locations
        upload_id = entry_obj.get('upload_id')
        if not upload_id:
            metadata = entry_obj.get('metadata', {})
            upload_id = metadata.get('upload_id')
        if not upload_id:
            metadata = entry_obj.get('metadata', {})
            mainfile = metadata.get('mainfile', '')
            if mainfile:
                # mainfile format: uploads/{upload_id}/{path...}
                parts = mainfile.split('/')
                if parts[0] == 'uploads' and len(parts) > 1:
                    upload_id = parts[1]
        
        if not upload_id:
            return None
        
        reference = f"../uploads/{upload_id}/archive/{entry_id}#/data"
        return reference
    
    except Exception:
        return None
