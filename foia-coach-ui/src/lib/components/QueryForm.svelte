<script lang="ts">
	import { apiClient } from '$lib/api/client';
	import { chatStore } from '$lib/stores/chat.svelte';
	import { contextStore } from '$lib/stores/context.svelte';
	import { jurisdictionsStore } from '$lib/stores/jurisdictions.svelte';

	let question = $state('');
	let selectedState = $state('');
	let submitting = $state(false);
	let error = $state<string | null>(null);

	// Load jurisdictions on mount (uses cache if available)
	$effect(() => {
		jurisdictionsStore.load().catch((e) => {
			error = `Failed to load jurisdictions: ${e instanceof Error ? e.message : String(e)}`;
		});
	});

	async function handleSubmit(e: Event) {
		e.preventDefault();

		if (!question.trim()) {
			error = 'Please enter a question';
			return;
		}

		try {
			submitting = true;
			error = null;

			// Add user message
			chatStore.addMessage({
				role: 'user',
				content: question,
				state: selectedState || undefined
			});

			// Update context with user message
			contextStore.addUserMessage(question.trim(), selectedState || undefined);

			// Set loading state
			chatStore.setLoading(true);

			// Get conversation context
			const context = contextStore.getContext();

			// Call API with context
			const response = await apiClient.query({
				question: question.trim(),
				state: selectedState || context.currentState || undefined,
				context: context.messages.length > 0 ? context : undefined
			});

			// Add assistant response
			chatStore.addMessage({
				role: 'assistant',
				content: response.answer,
				citations: response.citations,
				state: response.state,
				provider: response.provider,
				model: response.model
			});

			// Update context with assistant message
			contextStore.addAssistantMessage(response.answer, response.state);

			// Clear form
			question = '';
		} catch (e) {
			error = `Failed to get response: ${e instanceof Error ? e.message : String(e)}`;
			console.error('Error querying API:', e);
		} finally {
			submitting = false;
			chatStore.setLoading(false);
		}
	}
</script>

<form class="query-form" onsubmit={handleSubmit}>
	{#if error}
		<div class="error">{error}</div>
	{/if}

	<div class="form-row">
		<div class="jurisdiction-selector">
			<label for="state">State (optional):</label>
			{#if jurisdictionsStore.loading}
				<select id="state" disabled>
					<option>Loading...</option>
				</select>
			{:else}
				<select id="state" bind:value={selectedState} disabled={submitting}>
					<option value="">All States</option>
					{#each jurisdictionsStore.jurisdictions as jurisdiction}
						<option value={jurisdiction.abbrev}>{jurisdiction.name}</option>
					{/each}
				</select>
			{/if}
		</div>
	</div>

	<div class="form-row">
		<textarea
			bind:value={question}
			placeholder="Ask a question about public records laws..."
			rows="3"
			disabled={submitting || jurisdictionsStore.loading}
		></textarea>
	</div>

	<div class="form-row">
		<button
			type="submit"
			disabled={submitting || jurisdictionsStore.loading || !question.trim()}
		>
			{submitting ? 'Sending...' : 'Ask Question'}
		</button>
	</div>
</form>

<style>
	.query-form {
		border: 1px solid #ddd;
		border-radius: 8px;
		padding: 1rem;
		background: white;
		margin-bottom: 1.5rem;
	}

	.form-row {
		margin-bottom: 1rem;
	}

	.form-row:last-child {
		margin-bottom: 0;
	}

	.error {
		padding: 0.75rem;
		background: #fee;
		border: 1px solid #fcc;
		border-radius: 4px;
		color: #c33;
		margin-bottom: 1rem;
	}

	.jurisdiction-selector label {
		display: block;
		margin-bottom: 0.5rem;
		font-weight: 500;
	}

	select {
		width: 100%;
		padding: 0.5rem;
		border: 1px solid #ddd;
		border-radius: 4px;
		font-size: 1rem;
	}

	textarea {
		width: 100%;
		padding: 0.75rem;
		border: 1px solid #ddd;
		border-radius: 4px;
		font-size: 1rem;
		font-family: inherit;
		resize: vertical;
	}

	textarea:focus {
		outline: none;
		border-color: #2196f3;
	}

	button {
		padding: 0.75rem 1.5rem;
		border: none;
		border-radius: 4px;
		background: #2196f3;
		color: white;
		font-size: 1rem;
		font-weight: 500;
		cursor: pointer;
	}

	button:hover:not(:disabled) {
		background: #1976d2;
	}

	button:disabled {
		background: #ccc;
		cursor: not-allowed;
	}
</style>
