<script lang="ts">
	import { apiClient } from '$lib/api/client';
	import { jurisdictionsStore } from '$lib/stores/jurisdictions.svelte';
	import FileUploadItem from './FileUploadItem.svelte';

	interface UploadFile {
		file: File;
		status: 'pending' | 'uploading' | 'success' | 'error';
		progress: number;
		error?: string;
		resourceId?: number;
	}

	let selectedState = $state('');
	let files = $state<UploadFile[]>([]);
	let uploading = $state(false);
	let fileInput: HTMLInputElement;

	// Load jurisdictions
	$effect(() => {
		jurisdictionsStore.load();
	});

	function handleFileSelect(event: Event) {
		const input = event.target as HTMLInputElement;
		if (!input.files) return;

		const newFiles = Array.from(input.files).map((file) => ({
			file,
			status: 'pending' as const,
			progress: 0
		}));

		files = [...files, ...newFiles];

		// Reset input to allow selecting same files again
		input.value = '';
	}

	function removeFile(index: number) {
		files = files.filter((_, i) => i !== index);
	}

	async function uploadFiles() {
		if (!selectedState) {
			alert('Please select a state');
			return;
		}

		if (files.length === 0) {
			alert('Please select files to upload');
			return;
		}

		uploading = true;

		// Get jurisdiction ID from store
		const jurisdiction = jurisdictionsStore.jurisdictions.find((j) => j.abbrev === selectedState);

		if (!jurisdiction) {
			alert('Jurisdiction not found');
			uploading = false;
			return;
		}

		// Upload files sequentially
		for (let i = 0; i < files.length; i++) {
			const uploadFile = files[i];

			if (uploadFile.status === 'success') {
				continue; // Skip already uploaded files
			}

			uploadFile.status = 'uploading';
			uploadFile.progress = 0;

			try {
				const result = await apiClient.uploadResource({
					file: uploadFile.file,
					jurisdiction_abbrev: selectedState,
					jurisdiction_id: jurisdiction.id,
					provider: 'openai'
				});

				uploadFile.status = 'success';
				uploadFile.progress = 100;
				uploadFile.resourceId = result.id;
			} catch (error) {
				uploadFile.status = 'error';
				uploadFile.error = error instanceof Error ? error.message : 'Upload failed';
			}
		}

		uploading = false;
	}

	function clearCompleted() {
		files = files.filter((f) => f.status !== 'success');
	}

	function resetAll() {
		files = [];
		selectedState = '';
	}

	let successCount = $derived(files.filter((f) => f.status === 'success').length);
	let errorCount = $derived(files.filter((f) => f.status === 'error').length);
	let totalCount = $derived(files.length);
</script>

<div class="upload-container">
	<h2>Batch Upload Resources</h2>

	<div class="upload-form">
		<!-- State Selection -->
		<div class="form-group">
			<label for="state">Select State *</label>
			{#if jurisdictionsStore.loading}
				<select id="state" disabled>
					<option>Loading...</option>
				</select>
			{:else}
				<select id="state" bind:value={selectedState} disabled={uploading}>
					<option value="">-- Select State --</option>
					{#each jurisdictionsStore.jurisdictions as jurisdiction}
						<option value={jurisdiction.abbrev}>
							{jurisdiction.name} ({jurisdiction.abbrev})
						</option>
					{/each}
				</select>
			{/if}
		</div>

		<!-- File Selection -->
		<div class="form-group">
			<label>Select PDF Files *</label>
			<div class="file-input-wrapper">
				<input
					type="file"
					bind:this={fileInput}
					onchange={handleFileSelect}
					accept=".pdf"
					multiple
					disabled={uploading || !selectedState}
				/>
				<button
					type="button"
					onclick={() => fileInput?.click()}
					disabled={uploading || !selectedState}
					class="btn-secondary"
				>
					Choose Files
				</button>
			</div>
			<small>PDF files only, max 25MB each</small>
		</div>

		<!-- File List -->
		{#if files.length > 0}
			<div class="file-list">
				<div class="file-list-header">
					<h3>Files ({totalCount})</h3>
					<div class="status-summary">
						{#if successCount > 0}
							<span class="success-badge">{successCount} uploaded</span>
						{/if}
						{#if errorCount > 0}
							<span class="error-badge">{errorCount} failed</span>
						{/if}
					</div>
				</div>

				{#each files as uploadFile, index}
					<FileUploadItem
						{uploadFile}
						onRemove={() => removeFile(index)}
						disabled={uploading}
					/>
				{/each}
			</div>
		{/if}

		<!-- Actions -->
		<div class="actions">
			<button
				type="button"
				onclick={uploadFiles}
				disabled={uploading || !selectedState || files.length === 0}
				class="btn-primary"
			>
				{uploading
					? 'Uploading...'
					: `Upload ${files.length} File${files.length !== 1 ? 's' : ''}`}
			</button>

			{#if successCount > 0 && !uploading}
				<button type="button" onclick={clearCompleted} class="btn-secondary">
					Clear Completed
				</button>
			{/if}

			{#if files.length > 0 && !uploading}
				<button type="button" onclick={resetAll} class="btn-secondary">Reset All</button>
			{/if}
		</div>
	</div>
</div>

<style>
	.upload-container {
		border: 1px solid #ddd;
		border-radius: 8px;
		padding: 1.5rem;
		background: white;
		margin-bottom: 1.5rem;
	}

	.form-group {
		margin-bottom: 1.5rem;
	}

	label {
		display: block;
		font-weight: 500;
		margin-bottom: 0.5rem;
	}

	select {
		width: 100%;
		padding: 0.5rem;
		border: 1px solid #ddd;
		border-radius: 4px;
		font-size: 1rem;
	}

	.file-input-wrapper input[type='file'] {
		display: none;
	}

	.file-list {
		margin-top: 1.5rem;
		padding: 1rem;
		background: #f9f9f9;
		border-radius: 4px;
	}

	.file-list-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
	}

	.file-list-header h3 {
		margin: 0;
		font-size: 1rem;
	}

	.status-summary {
		display: flex;
		gap: 0.5rem;
	}

	.success-badge {
		padding: 0.25rem 0.75rem;
		background: #e8f5e9;
		color: #2e7d32;
		border-radius: 12px;
		font-size: 0.875rem;
	}

	.error-badge {
		padding: 0.25rem 0.75rem;
		background: #ffebee;
		color: #c62828;
		border-radius: 12px;
		font-size: 0.875rem;
	}

	.actions {
		display: flex;
		gap: 0.5rem;
		margin-top: 1.5rem;
	}

	.btn-primary {
		padding: 0.75rem 1.5rem;
		background: #2196f3;
		color: white;
		border: none;
		border-radius: 4px;
		font-weight: 500;
		cursor: pointer;
	}

	.btn-primary:hover:not(:disabled) {
		background: #1976d2;
	}

	.btn-primary:disabled {
		background: #ccc;
		cursor: not-allowed;
	}

	.btn-secondary {
		padding: 0.75rem 1.5rem;
		background: #f0f0f0;
		color: #333;
		border: none;
		border-radius: 4px;
		cursor: pointer;
	}

	.btn-secondary:hover:not(:disabled) {
		background: #e0e0e0;
	}

	.btn-secondary:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	small {
		display: block;
		color: #666;
		margin-top: 0.25rem;
		font-size: 0.875rem;
	}
</style>
