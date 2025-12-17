<script lang="ts">
	interface UploadFile {
		file: File;
		status: 'pending' | 'uploading' | 'success' | 'error';
		progress: number;
		error?: string;
		resourceId?: number;
	}

	interface Props {
		uploadFile: UploadFile;
		onRemove: () => void;
		disabled: boolean;
	}

	let { uploadFile, onRemove, disabled }: Props = $props();

	function formatFileSize(bytes: number): string {
		if (bytes < 1024) return bytes + ' B';
		if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
		return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
	}
</script>

<div class="file-item" class:uploading={uploadFile.status === 'uploading'}>
	<div class="file-info">
		<div class="file-icon">
			{#if uploadFile.status === 'pending'}
				📄
			{:else if uploadFile.status === 'uploading'}
				⏳
			{:else if uploadFile.status === 'success'}
				✓
			{:else}
				✗
			{/if}
		</div>

		<div class="file-details">
			<div class="file-name">{uploadFile.file.name}</div>
			<div class="file-meta">
				{formatFileSize(uploadFile.file.size)}
				{#if uploadFile.status === 'success'}
					<span class="status-text success">• Uploaded</span>
				{:else if uploadFile.status === 'error'}
					<span class="status-text error">• {uploadFile.error || 'Failed'}</span>
				{:else if uploadFile.status === 'uploading'}
					<span class="status-text">• Uploading...</span>
				{/if}
			</div>
		</div>
	</div>

	{#if uploadFile.status === 'pending' || uploadFile.status === 'error'}
		<button
			type="button"
			onclick={onRemove}
			{disabled}
			class="remove-btn"
			aria-label="Remove file"
		>
			×
		</button>
	{/if}
</div>

<style>
	.file-item {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0.75rem;
		background: white;
		border: 1px solid #ddd;
		border-radius: 4px;
		margin-bottom: 0.5rem;
	}

	.file-item.uploading {
		background: #f5f5f5;
	}

	.file-info {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		flex: 1;
	}

	.file-icon {
		font-size: 1.5rem;
	}

	.file-details {
		flex: 1;
	}

	.file-name {
		font-weight: 500;
		word-break: break-all;
	}

	.file-meta {
		font-size: 0.875rem;
		color: #666;
		margin-top: 0.25rem;
	}

	.status-text {
		margin-left: 0.5rem;
	}

	.status-text.success {
		color: #2e7d32;
	}

	.status-text.error {
		color: #c62828;
	}

	.remove-btn {
		width: 2rem;
		height: 2rem;
		border: none;
		background: #f0f0f0;
		border-radius: 50%;
		cursor: pointer;
		font-size: 1.5rem;
		line-height: 1;
		color: #666;
	}

	.remove-btn:hover:not(:disabled) {
		background: #e0e0e0;
		color: #333;
	}

	.remove-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}
</style>
