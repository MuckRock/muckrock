// See https://svelte.dev/docs/kit/types#app.d.ts
// for information about these interfaces

// Vite raw imports
declare module '*.md?raw' {
	const content: string;
	export default content;
}

declare global {
	namespace App {
		// interface Error {}
		// interface Locals {}
		// interface PageData {}
		// interface PageState {}
		// interface Platform {}
	}
}

export {};
