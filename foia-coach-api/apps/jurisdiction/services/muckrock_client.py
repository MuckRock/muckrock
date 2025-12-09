"""Client for fetching jurisdiction data from main MuckRock API"""
import requests
from django.conf import settings
from typing import List, Dict, Optional


class MuckRockAPIClient:
    """
    Client for accessing MuckRock API to fetch jurisdiction data.
    Supports both local Docker and remote API endpoints.
    """

    def __init__(self):
        self.base_url = settings.MUCKROCK_API_URL
        self.token = settings.MUCKROCK_API_TOKEN
        self.session = requests.Session()
        if self.token:
            self.session.headers['Authorization'] = f'Token {self.token}'

    def get_jurisdictions(self, level: str = 's') -> List[Dict]:
        """Fetch state jurisdictions from MuckRock API"""
        response = self.session.get(
            f'{self.base_url}/api_v1/jurisdiction/',
            params={'level': level}
        )
        response.raise_for_status()
        return response.json()['results']

    def get_jurisdiction(self, abbrev: str) -> Optional[Dict]:
        """Fetch single jurisdiction by abbreviation"""
        response = self.session.get(
            f'{self.base_url}/api_v1/jurisdiction/',
            params={'abbrev': abbrev}
        )
        response.raise_for_status()
        data = response.json()
        results = data.get('results', [])
        return results[0] if results else None

    def get_jurisdiction_by_id(self, jurisdiction_id: int) -> Optional[Dict]:
        """Fetch single jurisdiction by ID"""
        response = self.session.get(
            f'{self.base_url}/api_v1/jurisdiction/{jurisdiction_id}/'
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()
