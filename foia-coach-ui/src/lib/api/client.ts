import { settingsStore } from '$lib/stores/settings.svelte';

export interface QueryRequest {
	question: string;
	state?: string;
	provider?: string;
	model?: string;
	context?: any;
}

export interface Citation {
	display_name: string;
	source: string;
	jurisdiction_abbrev?: string;
}

export interface QueryResponse {
	answer: string;
	citations: Citation[];
	provider?: string;
	model?: string;
	state?: string;
}

export interface ProviderStatus {
	current_provider: string;
	available_providers: string[];
	api_status: {
		openai: 'enabled' | 'disabled';
		gemini: 'enabled' | 'disabled';
		mock: 'always_enabled';
	};
	status: string;
	message: string;
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
		// Add provider and model from settings if not specified
		const requestWithProvider = {
			...request,
			provider: request.provider || settingsStore.settings.provider,
			model: request.model || settingsStore.settings.model
		};

		const response = await fetch(`${this.getBaseUrl()}/api/v1/query/query/`, {
			method: 'POST',
			headers: this.getHeaders(),
			body: JSON.stringify(requestWithProvider)
		});

		if (!response.ok) {
			// Try to parse error response body
			try {
				const errorData = await response.json();
				if (errorData.error) {
					// If it's an API disabled error, provide detailed message
					if (errorData.error_type === 'api_disabled') {
						throw new Error(
							`${errorData.error}: ${errorData.details || ''}`
						);
					}
					// If it's a quota error, provide helpful message
					if (response.status === 429 && errorData.retry_after) {
						throw new Error(
							`${errorData.error} Please try again in ${errorData.retry_after} seconds.`
						);
					}
					// Include details if available
					const errorMessage = errorData.details
						? `${errorData.error}: ${errorData.details}`
						: errorData.error;
					throw new Error(errorMessage);
				}
			} catch (e) {
				// If JSON parsing fails, fall back to status text
				if (e instanceof Error && (e.message.includes('API') || e.message.includes('disabled'))) {
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

	async getProviderStatus(): Promise<ProviderStatus> {
		const response = await fetch(`${this.getBaseUrl()}/api/v1/query/status/`, {
			headers: this.getHeaders()
		});

		if (!response.ok) {
			throw new Error(`Failed to get provider status: ${response.status}`);
		}

		return response.json();
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
