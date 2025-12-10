import { settingsStore } from '$lib/stores/settings.svelte';

export interface QueryRequest {
	question: string;
	state?: string;
	context?: any;
}

export interface QueryResponse {
	answer: string;
	citations: Array<{
		source: string;
		content: string;
	}>;
	state?: string;
}

export interface Jurisdiction {
	id: number;
	name: string;
	abbrev: string;
	level: string;
}

class APIClient {
	private getBaseUrl(): string {
		return settingsStore.settings.apiUrl;
	}

	private getHeaders(): HeadersInit {
		const headers: HeadersInit = {
			'Content-Type': 'application/json'
		};

		const token = settingsStore.settings.apiToken;
		if (token) {
			headers['Authorization'] = `Token ${token}`;
		}

		return headers;
	}

	async query(request: QueryRequest): Promise<QueryResponse> {
		const response = await fetch(`${this.getBaseUrl()}/api/v1/query/query/`, {
			method: 'POST',
			headers: this.getHeaders(),
			body: JSON.stringify(request)
		});

		if (!response.ok) {
			throw new Error(`API error: ${response.status} ${response.statusText}`);
		}

		return response.json();
	}

	async getJurisdictions(): Promise<Jurisdiction[]> {
		const response = await fetch(`${this.getBaseUrl()}/api/v1/jurisdictions/`, {
			headers: this.getHeaders()
		});

		if (!response.ok) {
			throw new Error(`API error: ${response.status}`);
		}

		const data = await response.json();
		return data.results || data;
	}

	async testConnection(): Promise<boolean> {
		try {
			await this.getJurisdictions();
			return true;
		} catch (e) {
			console.error('Connection test failed:', e);
			return false;
		}
	}
}

export const apiClient = new APIClient();
