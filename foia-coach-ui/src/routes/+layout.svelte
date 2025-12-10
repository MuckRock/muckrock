<script lang="ts">
	import '../app.css';

	let { children } = $props();
</script>

<div class="app">
	<nav>
		<a href="/">Chat</a>
		<a href="/settings">Settings</a>
	</nav>
	<main>
		{@render children()}
	</main>
</div>

<style>
	.app {
		max-width: 1200px;
		margin: 0 auto;
		padding: 1rem;
	}
	nav {
		display: flex;
		gap: 1rem;
		margin-bottom: 2rem;
		padding: 1rem;
		border-bottom: 1px solid #ccc;
	}
</style>
