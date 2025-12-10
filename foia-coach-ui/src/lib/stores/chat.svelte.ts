export interface ChatMessage {
	id: string;
	role: 'user' | 'assistant';
	content: string;
	timestamp: Date;
	citations?: Array<{
		source: string;
		content: string;
	}>;
	state?: string;
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
