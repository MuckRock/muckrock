<script lang="ts">
	import type { ChatMessage } from '$lib/stores/chat.svelte';

	interface Props {
		message: ChatMessage;
	}

	let { message }: Props = $props();

	function formatTime(date: Date): string {
		return date.toLocaleTimeString('en-US', {
			hour: 'numeric',
			minute: '2-digit'
		});
	}
</script>

<div
	class="message"
	class:user={message.role === 'user'}
	class:assistant={message.role === 'assistant'}
>
	<div class="message-header">
		<span class="role">{message.role === 'user' ? 'You' : 'FOIA Coach'}</span>
		<span class="timestamp">{formatTime(message.timestamp)}</span>
		{#if message.state}
			<span class="state-badge">{message.state}</span>
		{/if}
		{#if message.provider}
			<span class="provider-badge" title="{message.model || message.provider}">
				{message.provider}
			</span>
		{/if}
	</div>

	<div class="message-content">
		{message.content}
	</div>

	{#if message.citations && message.citations.length > 0}
		<div class="citations">
			<h4>Sources:</h4>
			<ul>
				{#each message.citations as citation}
					<li>
						<strong>{citation.display_name || citation.source}</strong>
						{#if citation.jurisdiction_abbrev}
							<span class="cite-state">{citation.jurisdiction_abbrev}</span>
						{/if}
						{#if citation.content}
							<p>{citation.content}</p>
						{:else}
							<p class="cite-source">{citation.source}</p>
						{/if}
					</li>
				{/each}
			</ul>
		</div>
	{/if}
</div>

<style>
	.message {
		margin-bottom: 1.5rem;
		padding: 1rem;
		border-radius: 8px;
		max-width: 80%;
	}

	.message.user {
		background: #e3f2fd;
		margin-left: auto;
	}

	.message.assistant {
		background: #f5f5f5;
		margin-right: auto;
	}

	.message-header {
		display: flex;
		gap: 0.5rem;
		align-items: center;
		margin-bottom: 0.5rem;
		font-size: 0.875rem;
	}

	.role {
		font-weight: 600;
	}

	.timestamp {
		color: #666;
	}

	.state-badge {
		padding: 0.125rem 0.5rem;
		background: #fff3cd;
		border-radius: 4px;
		font-size: 0.75rem;
	}

	.provider-badge {
		padding: 0.125rem 0.5rem;
		background: #e3f2fd;
		border-radius: 4px;
		font-size: 0.75rem;
		font-weight: 500;
		cursor: help;
	}

	.cite-state {
		display: inline-block;
		padding: 0.125rem 0.375rem;
		background: #2196f3;
		color: white;
		border-radius: 3px;
		font-size: 0.7rem;
		margin-left: 0.5rem;
	}

	.cite-source {
		font-style: italic;
	}

	.message-content {
		white-space: pre-wrap;
		word-wrap: break-word;
	}

	.citations {
		margin-top: 1rem;
		padding-top: 1rem;
		border-top: 1px solid #ddd;
	}

	.citations h4 {
		margin: 0 0 0.5rem 0;
		font-size: 0.875rem;
		color: #666;
	}

	.citations ul {
		margin: 0;
		padding-left: 1.5rem;
	}

	.citations li {
		margin-bottom: 0.5rem;
	}

	.citations p {
		margin: 0.25rem 0 0 0;
		font-size: 0.875rem;
		color: #666;
	}
</style>
