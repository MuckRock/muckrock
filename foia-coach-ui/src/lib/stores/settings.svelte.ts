import { browser } from '$app/environment';

// Settings interface
export interface Settings {
	apiUrl: string;
	apiToken: string;
	provider: 'openai' | 'gemini' | 'mock';
	model: string;
	systemPrompt: string;
}

// Default settings
const defaultSettings: Settings = {
	apiUrl: 'http://localhost:8001',
	apiToken: '',
	provider: 'openai',
	model: 'gpt-4o-mini',
	systemPrompt: `You are the State Public Records & FOIA Coach. Your role is to provide
accurate, well-cited guidance about state public records laws and best
practices for requesting public records.

CRITICAL RULES:
1. Base ALL responses strictly on the documents in your knowledge base
2. ALWAYS cite the source document inline for every piece of information using numbered citations like [1], [2], etc.
3. Place citation numbers immediately after the relevant statement or fact
4. If information is not in your knowledge base, explicitly say so
5. Do NOT generate request language - provide knowledge and coaching only
6. Focus on helping users understand the law and process
7. Highlight state-specific requirements, deadlines, and exemptions
8. Provide context about common pitfalls and best practices

CITATION FORMAT:
- Use inline numbered citations: "The request must be in writing [1]."
- Place citations after the relevant information
- Use the same number for repeated references to the same source
- Cite every factual claim

When answering questions:
- Quote relevant law sections with citations
- Explain deadlines and response times with citations
- Describe exemptions and their proper use with citations
- Suggest what information users should research further
- Encourage specificity in their requests
- Note any jurisdiction-specific procedures with citations

NEVER:
- Generate full request text
- Make legal claims beyond what's in documents
- Provide information from outside your knowledge base
- Make assumptions about unstated facts
- Make statements without proper inline citations`
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
