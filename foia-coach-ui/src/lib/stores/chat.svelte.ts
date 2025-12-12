export interface Citation {
	display_name: string;
	source: string;
	jurisdiction_abbrev?: string;
	content?: string; // For backward compatibility
}

export interface ChatMessage {
	id: string;
	role: 'user' | 'assistant';
	content: string;
	timestamp: Date;
	citations?: Citation[];
	state?: string;
	provider?: string;
	model?: string;
}

class ChatStore {
	messages = $state<ChatMessage[]>([]);
	isLoading = $state(false);

	addMessage(message: Omit<ChatMessage, 'id' | 'timestamp'>) {
		this.messages.push({
			...message,
			id: crypto.randomUUID(),
			timestamp: new Date()
		});
	}

	clear() {
		this.messages = [];
	}

	setLoading(loading: boolean) {
		this.isLoading = loading;
	}
}

export const chatStore = new ChatStore();
