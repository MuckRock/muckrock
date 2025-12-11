import { browser } from '$app/environment';
import { apiClient, type Jurisdiction } from '$lib/api/client';

interface JurisdictionsCache {
	jurisdictions: Jurisdiction[];
	timestamp: number;
}

// Cache TTL: 24 hours (jurisdictions don't change often)
const CACHE_TTL_MS = 24 * 60 * 60 * 1000;
const STORAGE_KEY = 'foia-coach-jurisdictions';

/**
 * Load cached jurisdictions from localStorage if available and not stale
 */
function loadCachedJurisdictions(): Jurisdiction[] | null {
	if (!browser) return null;

	try {
		const cached = localStorage.getItem(STORAGE_KEY);
		if (!cached) return null;

		const data: JurisdictionsCache = JSON.parse(cached);
		const now = Date.now();

		// Check if cache is still valid
		if (now - data.timestamp < CACHE_TTL_MS) {
			console.log('Using cached jurisdictions');
			return data.jurisdictions;
		}

		// Cache is stale
		console.log('Jurisdictions cache is stale, will refetch');
		return null;
	} catch (e) {
		console.error('Failed to load cached jurisdictions:', e);
		return null;
	}
}

/**
 * Save jurisdictions to localStorage cache
 */
function saveCachedJurisdictions(jurisdictions: Jurisdiction[]): void {
	if (!browser) return;

	try {
		const cache: JurisdictionsCache = {
			jurisdictions,
			timestamp: Date.now()
		};
		localStorage.setItem(STORAGE_KEY, JSON.stringify(cache));
		console.log('Cached jurisdictions to localStorage');
	} catch (e) {
		console.error('Failed to cache jurisdictions:', e);
	}
}

/**
 * Jurisdictions store with automatic caching
 */
class JurisdictionsStore {
	jurisdictions = $state<Jurisdiction[]>([]);
	loading = $state(false);
	error = $state<string | null>(null);
	private loadPromise: Promise<void> | null = null;

	/**
	 * Load jurisdictions from cache or API
	 * Returns immediately if already loaded or loading
	 */
	async load(force = false): Promise<void> {
		// If already loading, return the existing promise
		if (this.loadPromise && !force) {
			return this.loadPromise;
		}

		// If already loaded and not forcing, return immediately
		if (this.jurisdictions.length > 0 && !force) {
			return;
		}

		// Check cache first (unless forcing reload)
		if (!force) {
			const cached = loadCachedJurisdictions();
			if (cached && cached.length > 0) {
				this.jurisdictions = cached;
				this.error = null;
				return;
			}
		}

		// Need to fetch from API
		this.loadPromise = this.fetchFromAPI();
		await this.loadPromise;
		this.loadPromise = null;
	}

	/**
	 * Fetch jurisdictions from API
	 */
	private async fetchFromAPI(): Promise<void> {
		this.loading = true;
		this.error = null;

		try {
			console.log('Fetching jurisdictions from API...');
			const jurisdictions = await apiClient.getJurisdictions();
			this.jurisdictions = jurisdictions;
			saveCachedJurisdictions(jurisdictions);
		} catch (e) {
			this.error = `Failed to load jurisdictions: ${e instanceof Error ? e.message : String(e)}`;
			console.error('Error loading jurisdictions:', e);
			throw e;
		} finally {
			this.loading = false;
		}
	}

	/**
	 * Force reload jurisdictions from API
	 */
	async reload(): Promise<void> {
		return this.load(true);
	}

	/**
	 * Clear cache and reset store
	 */
	clear(): void {
		this.jurisdictions = [];
		this.error = null;
		if (browser) {
			localStorage.removeItem(STORAGE_KEY);
		}
	}
}

export const jurisdictionsStore = new JurisdictionsStore();
