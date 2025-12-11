import { browser } from '$app/environment';

export interface ConversationContext {
	messages: Array<{
		role: 'user' | 'assistant';
		content: string;
	}>;
	currentState?: string;
}

function loadContext(): ConversationContext {
	if (browser) {
		const stored = localStorage.getItem('foia-coach-context');
		if (stored) {
			try {
				return JSON.parse(stored);
			} catch (e) {
				console.error('Failed to parse stored context:', e);
			}
		}
	}
	return { messages: [] };
}

class ContextStore {
	context = $state<ConversationContext>(loadContext());

	addUserMessage(content: string, state?: string) {
		this.context.messages.push({
			role: 'user',
			content
		});
		if (state) {
			this.context.currentState = state;
		}
		this.save();
	}

	addAssistantMessage(content: string, state?: string) {
		this.context.messages.push({
			role: 'assistant',
			content
		});
		if (state) {
			this.context.currentState = state;
		}
		this.save();
	}

	clear() {
		this.context = { messages: [] };
		if (browser) {
			localStorage.removeItem('foia-coach-context');
		}
	}

	getContext() {
		return {
			messages: this.context.messages.slice(-10), // Keep last 10 messages for context
			currentState: this.context.currentState
		};
	}

	private save() {
		if (browser) {
			localStorage.setItem('foia-coach-context', JSON.stringify(this.context));
		}
	}
}

export const contextStore = new ContextStore();
