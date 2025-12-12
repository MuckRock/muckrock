<script lang="ts">
	import type { ChatMessage } from '$lib/stores/chat.svelte';
	import { marked } from 'marked';

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

	// Parse markdown content into HTML
	function renderMarkdown(content: string): string {
		return marked.parse(content) as string;
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
		{@html renderMarkdown(message.content)}
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
		word-wrap: break-word;
		line-height: 1.6;
	}

	/* Markdown Typography */
	.message-content :global(h1),
	.message-content :global(h2),
	.message-content :global(h3),
	.message-content :global(h4),
	.message-content :global(h5),
	.message-content :global(h6) {
		margin: 1rem 0 0.5rem 0;
		font-weight: 600;
	}

	.message-content :global(h1) {
		font-size: 1.5rem;
	}
	.message-content :global(h2) {
		font-size: 1.3rem;
	}
	.message-content :global(h3) {
		font-size: 1.1rem;
	}

	.message-content :global(p) {
		margin: 0.5rem 0;
	}

	.message-content :global(p:first-child) {
		margin-top: 0;
	}

	.message-content :global(p:last-child) {
		margin-bottom: 0;
	}

	/* Lists */
	.message-content :global(ul),
	.message-content :global(ol) {
		margin: 0.5rem 0;
		padding-left: 1.5rem;
	}

	.message-content :global(li) {
		margin: 0.25rem 0;
	}

	/* Code blocks and inline code */
	.message-content :global(code) {
		background: rgba(0, 0, 0, 0.05);
		padding: 0.125rem 0.25rem;
		border-radius: 3px;
		font-family: 'Courier New', Courier, monospace;
		font-size: 0.9em;
	}

	.message-content :global(pre) {
		background: rgba(0, 0, 0, 0.05);
		padding: 0.75rem;
		border-radius: 4px;
		overflow-x: auto;
		margin: 0.5rem 0;
	}

	.message-content :global(pre code) {
		background: none;
		padding: 0;
	}

	/* Links */
	.message-content :global(a) {
		color: #2196f3;
		text-decoration: underline;
	}

	.message-content :global(a:hover) {
		color: #1976d2;
	}

	/* Blockquotes */
	.message-content :global(blockquote) {
		border-left: 3px solid #ddd;
		padding-left: 1rem;
		margin: 0.5rem 0;
		color: #666;
	}

	/* Tables */
	.message-content :global(table) {
		border-collapse: collapse;
		width: 100%;
		margin: 0.5rem 0;
	}

	.message-content :global(th),
	.message-content :global(td) {
		border: 1px solid #ddd;
		padding: 0.5rem;
		text-align: left;
	}

	.message-content :global(th) {
		background: rgba(0, 0, 0, 0.05);
		font-weight: 600;
	}

	/* Horizontal rule */
	.message-content :global(hr) {
		border: none;
		border-top: 1px solid #ddd;
		margin: 1rem 0;
	}

	/* Strong and emphasis */
	.message-content :global(strong) {
		font-weight: 600;
	}

	.message-content :global(em) {
		font-style: italic;
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
