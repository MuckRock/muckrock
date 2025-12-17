<script>
	import ResourceUpload from '$lib/components/ResourceUpload.svelte';
</script>

<div class="page">
	<div class="header">
		<h1>Upload Resources</h1>
		<a href="/" class="back-link">← Back to Chat</a>
	</div>

	<ResourceUpload />
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
	}

	.header h1 {
		margin: 0;
		font-size: 2rem;
		color: #2196f3;
	}

	.back-link {
		color: #2196f3;
		text-decoration: none;
	}

	.back-link:hover {
		text-decoration: underline;
	}
</style>
