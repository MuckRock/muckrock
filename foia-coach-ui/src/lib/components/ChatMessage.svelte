<script lang="ts">
	import type { ChatMessage } from '$lib/stores/chat.svelte';
	import type { Citation } from '$lib/api/client';
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

	function formatResponseTime(ms: number): string {
		if (ms < 1000) return `${ms}ms`;
		return `${(ms / 1000).toFixed(1)}s`;
	}

	// Parse markdown content into HTML
	function renderMarkdown(content: string): string {
		return marked.parse(content) as string;
	}

	/**
	 * Parse and link citation markers like [1], [2] in the text
	 * Used when OpenAI provides citation numbers in text but no positioning info
	 */
	function parseAndLinkCitationMarkers(content: string, citations: Citation[]): string {
		if (!content || !citations.length) return renderMarkdown(content);

		let processedContent = content;

		// Deduplicate consecutive identical citation markers like [1][1] or [1] [1]
		processedContent = processedContent.replace(/(\[(\d+)\])(\s*\[\2\])+/g, '$1');

		// Replace citation markers [1], [2], etc. with clickable links
		// Match patterns like [1], [2], [3], etc. but not markdown links
		const citationPattern = /\[(\d+)\](?!\()/g;

		processedContent = processedContent.replace(citationPattern, (match, number) => {
			const citationNum = parseInt(number, 10);
			// Citation numbers are 1-indexed, array is 0-indexed
			const citation = citations[citationNum - 1];

			if (!citation) return match; // Keep original if no matching citation

			// Build title for hover
			const titleParts = [];
			if (citation.display_name || citation.source) {
				titleParts.push(citation.display_name || citation.source);
			}
			if (citation.quote) {
				const truncatedQuote = citation.quote.substring(0, 100) + (citation.quote.length > 100 ? '...' : '');
				titleParts.push(`"${truncatedQuote}"`);
			}
			const title = titleParts.join(' - ') || 'Citation';

			// Create clickable link or span
			if (citation.file_url) {
				return `<a href="${citation.file_url}" target="_blank" class="citation-link" title="${title}" data-citation="${citationNum}">[${citationNum}]</a>`;
			} else {
				return `<span class="citation-marker" title="${title}" data-citation="${citationNum}">[${citationNum}]</span>`;
			}
		});

		return renderMarkdown(processedContent);
	}

	/**
	 * Process content with inline citations
	 * Replaces citation markers with clickable links
	 */
	function renderContentWithCitations(content: string, citations: Citation[] | undefined): string {
		if (!content) return '';
		if (!citations || !Array.isArray(citations) || citations.length === 0) {
			return renderMarkdown(content);
		}

		// Check if citations have positioning information
		const hasPositioning = citations.some(
			(c) => c && typeof c === 'object' && c.start_index !== undefined && c.end_index !== undefined
		);

		// Try to parse citation markers from text even without positioning
		if (!hasPositioning) {
			return parseAndLinkCitationMarkers(content, citations);
		}

		// Sort citations by start_index in reverse order to replace from end to start
		// This prevents index shifting issues when replacing text
		const sortedCitations = [...citations]
			.filter((c) => c && typeof c === 'object' && c.start_index !== undefined && c.end_index !== undefined)
			.sort((a, b) => (b.start_index || 0) - (a.start_index || 0));

		let processedContent = content;

		// Replace each citation marker with a link
		sortedCitations.forEach((citation, idx) => {
			if (!citation) return;

			const { start_index, end_index, text, display_name, file_url, quote, source } = citation;

			if (start_index === undefined || end_index === undefined) return;

			// Validate indices are within bounds
			if (start_index < 0 || end_index > processedContent.length || start_index >= end_index) {
				return;
			}

			// Get the citation text (the marker like "[1]" or "【4:0†source】")
			const citationText = text || processedContent.substring(start_index, end_index);

			// Create the citation number (use index from citations array)
			const citationNum = sortedCitations.length - idx;

			// Build the citation link with title attribute for hover
			const titleParts = [];
			if (display_name || source) {
				titleParts.push(display_name || source);
			}
			if (quote) {
				const truncatedQuote = quote.substring(0, 100) + (quote.length > 100 ? '...' : '');
				titleParts.push(`"${truncatedQuote}"`);
			}
			const title = titleParts.join(' - ') || 'Citation';

			const citationLink = file_url
				? `<a href="${file_url}" target="_blank" class="citation-link" title="${title}" data-citation="${citationNum}">[${citationNum}]</a>`
				: `<span class="citation-marker" title="${title}" data-citation="${citationNum}">[${citationNum}]</span>`;

			// Replace the citation marker in the content
			processedContent =
				processedContent.substring(0, start_index) +
				citationLink +
				processedContent.substring(end_index);
		});

		return renderMarkdown(processedContent);
	}

	// Deduplicate citations by file_id or source
	function getUniqueCitations(citations: Citation[] | undefined): Citation[] {
		if (!citations || !Array.isArray(citations)) return [];

		const seen = new Set<string>();
		return citations.filter((citation) => {
			// Handle both old and new citation formats
			if (!citation || typeof citation !== 'object') return false;

			const key = citation.file_id || citation.source || citation.display_name || '';
			if (!key || seen.has(key)) return false;

			seen.add(key);
			return true;
		});
	}

	let uniqueCitations = $derived(getUniqueCitations(message?.citations));
	let hasInlineCitations = $derived(
		uniqueCitations.length > 0 &&
		uniqueCitations.some((c) => c && c.start_index !== undefined && c.end_index !== undefined)
	);
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
		{#if message.responseTimeMs}
			<span class="response-time" title="{message.responseTimeMs}ms">
				{formatResponseTime(message.responseTimeMs)}
			</span>
		{/if}
	</div>

	<div class="message-content">
		{@html renderContentWithCitations(message.content, message.citations)}
	</div>

	{#if uniqueCitations.length > 0}
		<div class="citations">
			<h4>Sources:</h4>
			<ul>
				{#each uniqueCitations as citation, idx}
					{#if citation}
						<li>
							{#if citation.file_url}
								<a href={citation.file_url} target="_blank" class="citation-source-link">
									<strong>{citation.display_name || citation.source || 'Unknown Source'}</strong>
								</a>
							{:else}
								<strong>{citation.display_name || citation.source || 'Unknown Source'}</strong>
							{/if}

							{#if citation.jurisdiction_abbrev}
								<span class="cite-state">{citation.jurisdiction_abbrev}</span>
							{/if}

							{#if hasInlineCitations}
								<span class="citation-number">[{idx + 1}]</span>
							{/if}

							{#if citation.quote}
								<p class="citation-quote">"{citation.quote}"</p>
							{:else if citation.content}
								<p>{citation.content}</p>
							{:else if !citation.file_url && citation.source}
								<p class="cite-source">{citation.source}</p>
							{/if}
						</li>
					{/if}
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

	.response-time {
		padding: 0.125rem 0.5rem;
		background: #e8f5e9;
		border-radius: 4px;
		font-size: 0.75rem;
		color: #2e7d32;
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

	/* Inline citation links */
	.message-content :global(a.citation-link),
	.message-content :global(span.citation-marker) {
		display: inline-block;
		background: #e3f2fd;
		color: #1976d2;
		padding: 0 0.25rem;
		margin: 0 0.125rem;
		border-radius: 3px;
		font-size: 0.75em;
		font-weight: 600;
		text-decoration: none;
		vertical-align: super;
		line-height: 1;
		cursor: help;
	}

	.message-content :global(a.citation-link:hover) {
		background: #bbdefb;
		color: #0d47a1;
	}

	.message-content :global(span.citation-marker) {
		cursor: default;
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

	.citation-source-link {
		color: #2196f3;
		text-decoration: none;
	}

	.citation-source-link:hover {
		text-decoration: underline;
	}

	.citation-number {
		display: inline-block;
		background: #e3f2fd;
		color: #1976d2;
		padding: 0.125rem 0.375rem;
		border-radius: 3px;
		font-size: 0.7rem;
		font-weight: 600;
		margin-left: 0.5rem;
	}

	.citation-quote {
		font-style: italic;
		color: #555;
		background: #f9f9f9;
		padding: 0.5rem;
		border-left: 3px solid #ddd;
		margin-top: 0.5rem !important;
	}
</style>
