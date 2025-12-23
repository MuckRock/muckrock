<script lang="ts">
	import { settingsStore } from '$lib/stores/settings.svelte';
	import { apiClient } from '$lib/api/client';
	import { goto } from '$app/navigation';

	let testing = $state(false);
	let testResult = $state<string | null>(null);

	async function testConnection() {
		testing = true;
		testResult = null;

		try {
			const success = await apiClient.testConnection();
			testResult = success ? 'Connection successful!' : 'Connection failed';
		} catch (e) {
			testResult = `Error: ${e.message}`;
		} finally {
			testing = false;
		}
	}

	function handleSubmit(event: Event) {
		event.preventDefault();
		settingsStore.save();
		goto('/');
	}

	function handleReset() {
		if (confirm('Reset to default settings?')) {
			settingsStore.reset();
		}
	}
</script>

<form onsubmit={handleSubmit}>
	<div class="field">
		<label for="apiUrl">FOIA Coach API URL</label>
		<input
			id="apiUrl"
			type="text"
			bind:value={settingsStore.settings.apiUrl}
			placeholder="http://localhost:8001"
			required
		/>
		<small>Base URL for the FOIA Coach API service</small>
	</div>

	<div class="field">
		<label for="apiToken">API Token (optional)</label>
		<input
			id="apiToken"
			type="password"
			bind:value={settingsStore.settings.apiToken}
			placeholder="Leave blank for local development"
		/>
		<small>Optional token for remote deployments (not needed for local development)</small>
	</div>

	<div class="field">
		<label for="provider">AI Provider</label>
		<select
			id="provider"
			bind:value={settingsStore.settings.provider}
			required
		>
			<option value="openai">OpenAI</option>
			<option value="gemini">Google Gemini</option>
			<option value="mock">Mock (Testing)</option>
		</select>
		<small>Select which AI provider to use for queries</small>
	</div>

	<div class="field">
		<label for="model">Model</label>
		<input
			id="model"
			type="text"
			bind:value={settingsStore.settings.model}
			placeholder={settingsStore.settings.provider === 'openai' ? 'gpt-4o' : 'gemini-2.0-flash-001'}
			required
		/>
		<small>
			{#if settingsStore.settings.provider === 'openai'}
				OpenAI model (e.g., gpt-4o, gpt-4o-mini)
			{:else if settingsStore.settings.provider === 'gemini'}
				Gemini model (e.g., gemini-2.0-flash-001, gemini-1.5-pro)
			{:else}
				Model identifier
			{/if}
		</small>
	</div>

	<div class="field">
		<label for="systemPrompt">System Prompt</label>
		<textarea
			id="systemPrompt"
			bind:value={settingsStore.settings.systemPrompt}
			rows={10}
			placeholder="System instruction for the AI coach..."
			required
		></textarea>
		<small>
			The system instruction that defines the AI's behavior and response style.
			This applies to all providers (OpenAI, Gemini, Mock).
		</small>
	</div>

	<div class="actions">
		<button type="submit">Save Settings</button>
		<button type="button" onclick={handleReset}>Reset to Defaults</button>
		<button type="button" onclick={testConnection} disabled={testing}>
			{testing ? 'Testing...' : 'Test Connection'}
		</button>
	</div>

	{#if testResult}
		<div class="test-result" class:success={testResult.includes('successful')}>
			{testResult}
		</div>
	{/if}
</form>

<style>
	form {
		max-width: 600px;
	}

	.field {
		margin-bottom: 1.5rem;
	}

	label {
		display: block;
		font-weight: 600;
		margin-bottom: 0.5rem;
	}

	input,
	select {
		width: 100%;
		padding: 0.5rem;
		border: 1px solid #ccc;
		border-radius: 4px;
		font-size: 1rem;
	}

	textarea {
		width: 100%;
		padding: 0.5rem;
		border: 1px solid #ccc;
		border-radius: 4px;
		font-size: 0.95rem;
		font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
		line-height: 1.5;
		resize: vertical;
		min-height: 200px;
	}

	small {
		display: block;
		color: #666;
		margin-top: 0.25rem;
	}

	.actions {
		display: flex;
		gap: 0.5rem;
		flex-wrap: wrap;
	}

	button {
		padding: 0.5rem 1rem;
		border: none;
		border-radius: 4px;
		cursor: pointer;
		font-size: 1rem;
	}

	button[type='submit'] {
		background: #0066cc;
		color: white;
	}

	button[type='button'] {
		background: #f0f0f0;
		color: #333;
	}

	button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.test-result {
		margin-top: 1rem;
		padding: 0.75rem;
		border-radius: 4px;
		background: #ffebee;
		color: #c62828;
	}

	.test-result.success {
		background: #e8f5e9;
		color: #2e7d32;
	}
</style>
