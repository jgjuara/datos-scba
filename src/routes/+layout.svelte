<script lang="ts">
	import { untrack } from "svelte";
	import { page } from "$app/stores"; // SvelteKit store page
	import { base, resolve } from "$app/paths";
	import { goto } from "$app/navigation";
	import {
		loadDataset,
		loadConsolidatedDataset,
		db,
	} from "$lib/data/loader.svelte";
	import {
		LayoutDashboard,
		Building2,
		Loader2,
		AlertCircle,
		FileText,
		Home,
	} from "@lucide/svelte";
	import "./layout.css";

	let { children } = $props();

	// Reactive derivation of the active fuero from the pathname
	const currentFuero = $derived.by(() => {
		const pathname = $page.url.pathname;
		// Clean pathname comparisons accounting for potential trailing slashes and base path
		const relativePath = base ? pathname.substring(base.length) : pathname;
		if (relativePath.startsWith("/trabajo")) {
			return "trabajo";
		}
		if (relativePath.startsWith("/civil")) {
			return "civil";
		}
		return null;
	});

	const isConsolidado = $derived.by(() => {
		const pathname = $page.url.pathname;
		const relativePath = base ? pathname.substring(base.length) : pathname;
		return relativePath.startsWith("/consolidado");
	});

	const isHome = $derived.by(() => {
		const pathname = $page.url.pathname;
		const relativePath = base ? pathname.substring(base.length) : pathname;
		return relativePath === "/" || relativePath === "";
	});

	// Trigger dataset loading reactively when the fuero changes
	$effect(() => {
		if (currentFuero === "trabajo") {
			untrack(() => loadDataset("trabajo"));
		} else if (currentFuero === "civil") {
			untrack(() => loadDataset("civil"));
		} else if (isConsolidado || isHome) {
			untrack(() => loadConsolidatedDataset());
		} else {
			db.loading = false;
		}
	});

	// Helper to check active route
	const activePath = $derived($page.url.pathname);

	function isRouteActive(itemPath: string, currentPath: string): boolean {
		const target = base + itemPath;
		return currentPath === target || currentPath === target + "/";
	}

	type NavPath =
		| "/civil"
		| "/civil/sedes"
		| "/civil/sede"
		| "/trabajo"
		| "/trabajo/sedes"
		| "/trabajo/sede";

	type NavItem = {
		path: NavPath;
		label: string;
		icon: typeof LayoutDashboard;
	};

	const navItems = $derived(
		currentFuero === "civil"
			? [
					{
						path: "/civil",
						label: "Provincia",
						icon: LayoutDashboard,
					},
					{
						path: "/civil/sedes",
						label: "Sedes",
						icon: Building2,
					},
					{
						path: "/civil/sede",
						label: "Detalle por sede",
						icon: FileText,
					},
				] satisfies NavItem[]
			: currentFuero === "trabajo"
				? [
						{
							path: "/trabajo",
							label: "Provincia",
							icon: LayoutDashboard,
						},
						{
							path: "/trabajo/sedes",
							label: "Sedes",
							icon: Building2,
						},
						{
							path: "/trabajo/sede",
							label: "Detalle por sede",
							icon: FileText,
						},
					] satisfies NavItem[]
			: [],
	);

	function resetFuero() {
		db.selectedFuero = null;
		if (typeof window !== "undefined") {
			localStorage.removeItem("selectedFuero");
		}
		goto(resolve("/"));
	}
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
							{#if currentFuero === "civil"}
								Juzgados Civiles y Comerciales - SCBA
							{:else if currentFuero === "trabajo"}
								Tribunales de Trabajo - SCBA
							{:else if isConsolidado}
								Tablero Consolidado - SCBA
							{:else}
								Estadísticas Judiciales Bonaerenses
							{/if}
						</h1>
					</div>
				</div>

				<!-- Navigation -->
				{#if currentFuero}
					<nav class="hidden md:flex space-x-1">
						{#each navItems as item (item.path)}
							{@const Icon = item.icon}
							<a
								href={resolve(item.path)}
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
				{/if}

				<!-- Header Actions / Reset Button -->
				<div class="flex items-center gap-3">
					{#if currentFuero || isConsolidado}
						<button
							onclick={resetFuero}
							class="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-brand-danger bg-brand-danger/10 border border-brand-danger/20 hover:bg-brand-danger/20 transition cursor-pointer"
						>
							<Home class="w-3.5 h-3.5" />
							Volver al menú inicial
						</button>
					{/if}
					<div
						class="hidden sm:block text-[10px] bg-white border border-brand-border px-3 py-1 rounded-full text-brand-text-muted font-mono uppercase tracking-wider"
					>
						Datos 2017-2025
					</div>
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
					Cargando datos judiciales
				</h3>
				<p class="text-xs text-brand-text-muted mt-1">
					{#if currentFuero === "civil"}
						Preparando registros históricos de juzgados civiles y
						comerciales...
					{:else if currentFuero === "trabajo"}
						Preparando registros históricos de tribunales de
						trabajo...
					{:else}
						Preparando registros históricos a nivel consolidado
						provincial...
					{/if}
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
					No se pudieron cargar los datos
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
			<p>
				© 2026 - <a
					href="https://www.linkedin.com/in/jgjuara/"
					target="_blank"
					rel="noopener noreferrer"
					class="hover:underline text-brand-indigo font-medium"
					>Juan Gabriel Juara</a
				>
				en base a datos de la
				<a
					href="https://www.scba.gov.ar/estadisticas.asp"
					target="_blank"
					rel="noopener noreferrer"
					class="hover:underline text-brand-indigo font-medium"
					>SCBA</a
				>
			</p>
			<p class="mt-1">
				Tablero descriptivo de gestión judicial basado en datos públicos.
				Fuente de datos: <a
					href="https://github.com/jgjuara/scba-estadisticas/tree/main/static/data"
					target="_blank"
					rel="noopener noreferrer"
					class="hover:underline text-brand-indigo font-medium"
					>CSV procesados a partir de publicaciones estadísticas de la SCBA</a
				>.
			</p>
		</div>
	</footer>

	<!-- Mobile bottom navbar -->
	{#if currentFuero}
		<nav
			class="md:hidden sticky bottom-0 z-40 bg-brand-bg/90 backdrop-blur-lg border-t border-brand-border py-2 px-4 flex justify-around"
		>
			{#each navItems as item (item.path)}
				{@const Icon = item.icon}
				<a
					href={resolve(item.path)}
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
	{/if}
</div>
