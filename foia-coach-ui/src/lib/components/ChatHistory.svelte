<script lang="ts">
	import { chatStore } from '$lib/stores/chat.svelte';
	import ChatMessage from './ChatMessage.svelte';

	let chatContainer: HTMLDivElement;

	// Auto-scroll to bottom when new messages arrive
	$effect(() => {
		if (chatStore.messages.length > 0 && chatContainer) {
			chatContainer.scrollTop = chatContainer.scrollHeight;
		}
	});
</script>

<div class="chat-history" bind:this={chatContainer}>
	{#if chatStore.messages.length === 0}
		<div class="empty-state">
			<h2>Welcome to FOIA Coach</h2>
			<p>Ask a question about state public records laws to get started.</p>
		</div>
	{:else}
		{#each chatStore.messages as message (message.id)}
			<ChatMessage {message} />
		{/each}
	{/if}

	{#if chatStore.isLoading}
		<div class="loading">
			<span>FOIA Coach is thinking...</span>
		</div>
	{/if}
</div>

<style>
	.chat-history {
		height: calc(100vh - 300px);
		min-height: 400px;
		overflow-y: auto;
		padding: 1rem;
		border: 1px solid #ddd;
		border-radius: 8px;
		background: white;
	}

	.empty-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		height: 100%;
		text-align: center;
		color: #666;
	}

	.empty-state h2 {
		margin: 0 0 0.5rem 0;
	}

	.empty-state p {
		margin: 0;
	}

	.loading {
		text-align: center;
		padding: 1rem;
		color: #666;
		font-style: italic;
	}
</style>
