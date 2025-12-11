<script>
	import Settings from '$lib/components/Settings.svelte';
</script>

<div class="page">
	<h1>Settings</h1>
	<p>Configure your FOIA Coach API connection</p>

	<Settings />
</div>

<style>
	.page {
		max-width: 1000px;
		margin: 0 auto;
		padding: 2rem 1rem;
	}

	h1 {
		margin: 0 0 0.5rem 0;
		font-size: 2rem;
		color: #2196f3;
	}

	p {
		margin: 0 0 2rem 0;
		color: #666;
	}

	@media (max-width: 768px) {
		.page {
			padding: 1rem 0.5rem;
		}

		h1 {
			font-size: 1.5rem;
		}
	}
</style>
