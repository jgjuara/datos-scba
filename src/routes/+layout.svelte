<script lang="ts">
	import { onMount } from "svelte";
	import { page } from "$app/stores";
	import { base } from "$app/paths";
	import { loadDataset, db } from "$lib/data/loader.svelte";
	import {
		LayoutDashboard,
		Building2,
		Loader2,
		AlertCircle,
		FileText,
	} from "@lucide/svelte";
	import "./layout.css";

	let { children } = $props();

	onMount(() => {
		loadDataset();
	});

	// Helper to check active route
	const activePath = $derived($page.url.pathname);

	function isRouteActive(itemPath: string, currentPath: string): boolean {
		const target = itemPath === "/" ? base || "/" : base + itemPath;
		return currentPath === target || currentPath === target + "/";
	}

	const navItems = [
		{ path: "/", label: "Provincia", icon: LayoutDashboard },
		{ path: "/sedes", label: "Sedes", icon: Building2 },
		{ path: "/sede", label: "Detalle x Sede", icon: FileText },
	];
</script>

<div class="min-h-screen flex flex-col bg-brand-bg text-brand-text">
	<!-- Glass header -->
	<header
		class="sticky top-0 z-40 w-full border-b border-brand-border bg-brand-bg/75 backdrop-blur-md"
	>
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
			<div class="flex items-center justify-between h-16">
				<!-- Title logo -->
				<div class="flex items-center gap-3">
					<div
						class="w-8 h-8 rounded-lg bg-gradient-to-tr from-brand-indigo to-brand-indigo-hover flex items-center justify-center font-bold text-white text-lg tracking-wider shadow-[0_0_15px_rgba(67,56,202,0.3)]"
					>
						T
					</div>
					<div>
						<h1
							class="text-sm font-bold tracking-tight text-brand-text leading-none"
						>
							Estadísticas de los Tribunales de Trabajo - SCBA
						</h1>
					</div>
				</div>

				<!-- Navigation -->
				<nav class="hidden md:flex space-x-1">
					{#each navItems as item}
						{@const Icon = item.icon}
						<a
							href="{base}{item.path}"
							class="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold tracking-wide transition {isRouteActive(
								item.path,
								activePath,
							)
								? 'bg-brand-indigo/10 text-brand-indigo border border-brand-indigo/20'
								: 'text-brand-text-muted hover:text-brand-text border border-transparent'}"
						>
							<Icon class="w-4 h-4" />
							{item.label}
						</a>
					{/each}
				</nav>

				<!-- Small Badge -->
				<div
					class="hidden sm:block text-[10px] bg-white border border-brand-border px-3 py-1 rounded-full text-brand-text-muted font-mono uppercase tracking-wider"
				>
					Datos 2017-2025
				</div>
			</div>
		</div>
	</header>

	<!-- Main content area -->
	<main
		class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col"
	>
		{#if db.loading}
			<!-- Loading State -->
			<div
				class="flex-1 flex flex-col items-center justify-center min-h-[350px]"
			>
				<Loader2
					class="w-10 h-10 text-brand-indigo animate-spin mb-4"
				/>
				<h3 class="text-lg font-bold text-brand-text">
					Cargando base de datos
				</h3>
				<p class="text-xs text-brand-text-muted mt-1">
					Parseando registros históricos de tribunales de trabajo...
				</p>
			</div>
		{:else if db.error}
			<!-- Error State -->
			<div
				class="flex-1 flex flex-col items-center justify-center min-h-[350px] max-w-md mx-auto text-center px-4"
			>
				<div
					class="p-3 rounded-2xl bg-brand-danger/10 border border-brand-danger/20 text-brand-danger mb-4"
				>
					<AlertCircle class="w-8 h-8" />
				</div>
				<h3 class="text-lg font-bold text-brand-text">
					Error de Carga
				</h3>
				<p class="text-xs text-brand-text-muted mt-2 leading-relaxed">
					{db.error}
				</p>
				<button
					onclick={() => window.location.reload()}
					class="mt-6 px-4 py-2 bg-brand-indigo hover:bg-brand-indigo-hover text-white rounded-xl text-xs font-bold transition focus:outline-none"
				>
					Reintentar
				</button>
			</div>
		{:else}
			<!-- Render Pages -->
			{@render children()}
		{/if}
	</main>

	<!-- Footer -->
	<footer
		class="border-t border-brand-border py-6 bg-stone-200/20 text-center text-[10px] text-brand-text-muted font-sans"
	>
		<div class="max-w-7xl mx-auto px-4">
			<p>© 2026 - Juan Gabriel Juara en base a datos de la SCBA</p>
			<p class="mt-1">
				Herramienta descriptiva y exploratoria de flujos procesales.
				Fuente de datos: Parquet/CSV SCBA.
			</p>
		</div>
	</footer>

	<!-- Mobile bottom navbar -->
	<nav
		class="md:hidden sticky bottom-0 z-40 bg-brand-bg/90 backdrop-blur-lg border-t border-brand-border py-2 px-4 flex justify-around"
	>
		{#each navItems as item}
			{@const Icon = item.icon}
			<a
				href="{base}{item.path}"
				class="flex flex-col items-center gap-1 py-1 px-3 rounded-xl transition {isRouteActive(
					item.path,
					activePath,
				)
					? 'text-brand-indigo'
					: 'text-brand-text-muted'}"
			>
				<Icon class="w-5 h-5" />
				<span class="text-[9px] font-bold">{item.label}</span>
			</a>
		{/each}
	</nav>
</div>
