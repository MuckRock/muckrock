import { apiClient, type Jurisdiction } from '$lib/api/client';

/**
 * Hardcoded list of available jurisdictions
 * Used as default to avoid API calls
 */
const HARDCODED_JURISDICTIONS: Jurisdiction[] = [
	{
		id: 1,
		name: 'Colorado',
		abbrev: 'CO',
		level: 'state'
	},
	{
		id: 2,
		name: 'Georgia',
		abbrev: 'GA',
		level: 'state'
	},
	{
		id: 3,
		name: 'Tennessee',
		abbrev: 'TN',
		level: 'state'
	}
];

/**
 * Jurisdictions store with hardcoded default and optional API fetch
 */
class JurisdictionsStore {
	jurisdictions = $state<Jurisdiction[]>(HARDCODED_JURISDICTIONS);
	loading = $state(false);
	error = $state<string | null>(null);
	useHardcoded = $state(true);
	private loadPromise: Promise<void> | null = null;

	/**
	 * Load jurisdictions from API
	 * By default uses hardcoded list, pass force=true to fetch from API
	 */
	async load(force = false): Promise<void> {
		// If using hardcoded and not forcing, return immediately
		if (this.useHardcoded && !force) {
			return;
		}

		// If already loading, return the existing promise
		if (this.loadPromise && !force) {
			return this.loadPromise;
		}

		// If already loaded from API and not forcing, return immediately
		if (!this.useHardcoded && this.jurisdictions.length > 0 && !force) {
			return;
		}

		// Fetch from API
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
			this.useHardcoded = false;
		} catch (e) {
			this.error = `Failed to load jurisdictions: ${e instanceof Error ? e.message : String(e)}`;
			console.error('Error loading jurisdictions:', e);
			// Fall back to hardcoded on error
			this.jurisdictions = HARDCODED_JURISDICTIONS;
			this.useHardcoded = true;
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
	 * Reset to hardcoded jurisdictions
	 */
	resetToHardcoded(): void {
		this.jurisdictions = HARDCODED_JURISDICTIONS;
		this.useHardcoded = true;
		this.error = null;
	}

	/**
	 * Clear and reset store
	 */
	clear(): void {
		this.resetToHardcoded();
	}
}

export const jurisdictionsStore = new JurisdictionsStore();
