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
			// Try to parse error response body
			try {
				const errorData = await response.json();
				if (errorData.error) {
					// If it's a quota error, provide helpful message
					if (response.status === 429 && errorData.retry_after) {
						throw new Error(
							`${errorData.error} Please try again in ${errorData.retry_after} seconds.`
						);
					}
					throw new Error(errorData.error);
				}
			} catch (e) {
				// If JSON parsing fails, fall back to status text
				if (e instanceof Error && e.message.startsWith('API quota')) {
					throw e; // Re-throw our custom error
				}
			}
			throw new Error(`API error: ${response.status} ${response.statusText}`);
		}

		return response.json();
	}

	async getJurisdictions(): Promise<Jurisdiction[]> {
		const response = await fetch(`${this.getBaseUrl()}/api/v1/jurisdictions/`, {
			headers: this.getHeaders()
		});

		if (!response.ok) {
			// Try to parse error response body
			try {
				const errorData = await response.json();
				if (errorData.error) {
					throw new Error(errorData.error);
				}
			} catch (e) {
				// If JSON parsing fails, fall back to status text
				if (e instanceof Error && e.message !== `API error: ${response.status}`) {
					throw e; // Re-throw our custom error
				}
			}
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
