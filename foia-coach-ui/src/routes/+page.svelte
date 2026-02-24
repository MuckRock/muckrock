<script>
	import ChatHistory from '$lib/components/ChatHistory.svelte';
	import QueryForm from '$lib/components/QueryForm.svelte';
	import { chatStore } from '$lib/stores/chat.svelte';
	import { contextStore } from '$lib/stores/context.svelte';

	// Add some test messages for visualization
	function addTestMessages() {
		chatStore.addMessage({
			role: 'user',
			content: 'What is the response time for FOIA requests in Colorado?',
			state: 'CO'
		});

		chatStore.addMessage({
			role: 'assistant',
			content:
				'In Colorado, under the Colorado Open Records Act (CORA), public entities must respond to records requests within 3 business days. However, this response can be to acknowledge the request and provide a timeline for when the records will be available.',
			citations: [
				{
					source: 'Colorado CORA Guide',
					content: 'Response time: 3 business days to respond or acknowledge'
				}
			],
			state: 'CO'
		});
	}

	function clearChat() {
		chatStore.clear();
		contextStore.clear();
	}
</script>

<div class="page">
	<div class="header">
		<h1>Project Moss</h1>
		<div class="header-actions">
			<a href="/upload" class="link-button">Upload Resources</a>
			<button onclick={addTestMessages}>Add Test Messages</button>
			<button onclick={clearChat}>Clear Chat</button>
		</div>
	</div>

	<QueryForm />
	<ChatHistory />
</div>

<style>
	.page {
		max-width: 1000px;
		margin: 0 auto;
		padding: 2rem 1rem;
	}

	.header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 2rem;
		flex-wrap: wrap;
		gap: 1rem;
	}

	.header h1 {
		margin: 0;
		font-size: 2rem;
		color: #2196f3;
	}

	.header-actions {
		display: flex;
		gap: 0.5rem;
		flex-wrap: wrap;
	}

	.link-button {
		padding: 0.5rem 1rem;
		border-radius: 4px;
		background: #f0f0f0;
		cursor: pointer;
		font-size: 0.9rem;
		text-decoration: none;
		color: inherit;
		display: inline-block;
		transition: background-color 0.2s;
	}

	.link-button:hover {
		background: #e0e0e0;
	}

	button {
		padding: 0.5rem 1rem;
		border: none;
		border-radius: 4px;
		background: #f0f0f0;
		cursor: pointer;
		font-size: 0.9rem;
		transition: background-color 0.2s;
	}

	button:hover {
		background: #e0e0e0;
	}

	@media (max-width: 768px) {
		.page {
			padding: 1rem 0.5rem;
		}

		.header {
			flex-direction: column;
			align-items: flex-start;
		}

		.header h1 {
			font-size: 1.5rem;
		}
	}
</style>
