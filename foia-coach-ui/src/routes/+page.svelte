<script>
	import ChatHistory from '$lib/components/ChatHistory.svelte';
	import { chatStore } from '$lib/stores/chat.svelte';

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
</script>

<div class="page">
	<div class="header">
		<h1>FOIA Coach</h1>
		<button onclick={addTestMessages}>Add Test Messages</button>
		<button onclick={() => chatStore.clear()}>Clear Chat</button>
	</div>

	<ChatHistory />
</div>

<style>
	.page {
		max-width: 900px;
		margin: 0 auto;
	}

	.header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
	}

	button {
		padding: 0.5rem 1rem;
		border: none;
		border-radius: 4px;
		background: #f0f0f0;
		cursor: pointer;
	}

	button:hover {
		background: #e0e0e0;
	}
</style>
