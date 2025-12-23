import { settingsStore } from '$lib/stores/settings.svelte';

export interface QueryRequest {
	question: string;
	state?: string;
	provider?: string;
	model?: string;
	context?: any;
	system_prompt?: string;
}

export interface Citation {
	// Core fields (source is optional for backward compatibility with old data)
	source?: string;
	file_id?: string;

	// Inline positioning fields
	text?: string;
	start_index?: number;
	end_index?: number;
	index?: number;

	// Quote/content fields
	quote?: string;
	content?: string;

	// Resource metadata
	display_name?: string;
	jurisdiction_abbrev?: string;
	file_url?: string;
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

export interface ResourceUploadRequest {
	file: File;
	jurisdiction_abbrev: string;
	jurisdiction_id: number;
	provider?: string;
	display_name?: string;
	description?: string;
	resource_type?: string;
}

export interface ResourceUploadResponse {
	id: number;
	jurisdiction_id: number;
	jurisdiction_abbrev: string;
	display_name: string;
	description: string;
	resource_type: string;
	file_url: string;
	is_active: boolean;
	created_at: string;
	upload_status: {
		[provider: string]: string;
	};
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
		// Add provider, model, and system_prompt from settings if not specified
		const requestWithProvider = {
			...request,
			provider: request.provider || settingsStore.settings.provider,
			model: request.model || settingsStore.settings.model,
			system_prompt: request.system_prompt || settingsStore.settings.systemPrompt
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

	async uploadResource(request: ResourceUploadRequest): Promise<ResourceUploadResponse> {
		const formData = new FormData();
		formData.append('file', request.file);
		formData.append('jurisdiction_abbrev', request.jurisdiction_abbrev);
		formData.append('jurisdiction_id', request.jurisdiction_id.toString());

		if (request.provider) formData.append('provider', request.provider);
		if (request.display_name) formData.append('display_name', request.display_name);
		if (request.description) formData.append('description', request.description);
		if (request.resource_type) formData.append('resource_type', request.resource_type);

		const response = await fetch(`${this.getBaseUrl()}/api/v1/resources/upload/`, {
			method: 'POST',
			headers: {
				// No Content-Type - browser sets it with boundary for FormData
				...(settingsStore.settings.apiToken && {
					Authorization: `Token ${settingsStore.settings.apiToken}`
				})
			},
			body: formData
		});

		if (!response.ok) {
			try {
				const errorData = await response.json();
				if (errorData.error) throw new Error(errorData.error);
				if (errorData.details) {
					const errors = Object.entries(errorData.details)
						.map(([field, msgs]) => `${field}: ${msgs}`)
						.join(', ');
					throw new Error(errors);
				}
			} catch (e) {
				if (e instanceof Error && e.message !== '') throw e;
			}
			throw new Error(`Upload failed: ${response.status} ${response.statusText}`);
		}

		return response.json();
	}
}

export const apiClient = new APIClient();
