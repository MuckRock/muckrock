import { browser } from '$app/environment';

// Settings interface
export interface Settings {
	apiUrl: string;
	apiToken: string;
	geminiModel: string;
}

// Default settings
const defaultSettings: Settings = {
	apiUrl: 'http://localhost:8001',
	apiToken: '',
	geminiModel: 'gemini-2.0-flash-001'
};

// Load from localStorage or use defaults
function loadSettings(): Settings {
	if (!browser) return defaultSettings;

	const stored = localStorage.getItem('foia-coach-settings');
	if (stored) {
		try {
			return { ...defaultSettings, ...JSON.parse(stored) };
		} catch (e) {
			console.error('Failed to parse settings:', e);
		}
	}
	return defaultSettings;
}

// Create reactive state using Svelte 5 runes
class SettingsStore {
	settings = $state(loadSettings());

	update(newSettings: Partial<Settings>) {
		this.settings = { ...this.settings, ...newSettings };
		this.save();
	}

	save() {
		if (browser) {
			localStorage.setItem('foia-coach-settings', JSON.stringify(this.settings));
		}
	}

	reset() {
		this.settings = defaultSettings;
		if (browser) {
			localStorage.removeItem('foia-coach-settings');
		}
	}
}

export const settingsStore = new SettingsStore();
