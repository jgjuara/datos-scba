<script lang="ts">
	import { Scale, Building2 } from '@lucide/svelte';
	import { goto } from '$app/navigation';
	import { base } from '$app/paths';
	import { db } from '$lib/data/loader.svelte';
	import type { CourtRecord } from '$lib/data/loader.svelte';
	import LineChart from '$lib/charts/LineChart.svelte';
	import AreaChart from '$lib/charts/AreaChart.svelte';

	function selectFuero(fuero: 'civil' | 'trabajo') {
		goto(`${base}/${fuero}`);
	}

	// Reconstruct Svelte CourtRecord interface structure grouped by year
	const yearlyCourtRecords = $derived.by(() => {
		const groups: { [anio: number]: CourtRecord } = {};

		for (const r of db.consolidatedRecords) {
			const anio = r.anio;
			if (!groups[anio]) {
				groups[anio] = {
					anio,
					sede: 'PROVINCIA',
					ingresadas: 0,
					sentencia: 0,
					conciliacion: 0,
					allanamiento: 0,
					transaccion: 0,
					caducidad: 0,
					desistimiento: 0,
					interlocutorios: 0,
					incompetencia: 0,
					totalResueltas: 0
				};
			}

			const record = groups[anio];
			const valor = r.valor;

			switch (r.tipo) {
				case 'Ingresadas':
					record.ingresadas += valor;
					break;
				case 'Sentencia':
					record.sentencia += valor;
					break;
				case 'Conciliación':
					record.conciliacion += valor;
					break;
				case 'Allanamiento':
					record.allanamiento += valor;
					break;
				case 'Transacción':
					record.transaccion += valor;
					break;
				case 'Caducidad':
					record.caducidad += valor;
					break;
				case 'Desistimiento':
					record.desistimiento += valor;
					break;
				case 'Interlocutorios':
					record.interlocutorios += valor;
					break;
				case 'Incompetencia':
					record.incompetencia += valor;
					break;
				case 'Total Resueltas':
					record.totalResueltas += valor;
					break;
			}
		}

		return Object.values(groups).sort((a, b) => a.anio - b.anio);
	});

	// Data grouped by year for charts
	const yearlyAggr = $derived.by(() => {
		return yearlyCourtRecords.map((r) => ({
			anio: r.anio,
			ingresadas: r.ingresadas,
			resueltas: r.totalResueltas,
			Sentencia: r.sentencia,
			Conciliación: r.conciliacion,
			Allanamiento: r.allanamiento,
			Transacción: r.transaccion,
			Caducidad: r.caducidad,
			Desistimiento: r.desistimiento,
			Interlocutorios: r.interlocutorios,
			Incompetencia: r.incompetencia
		}));
	});

	// Chart Series
	const lineSeriesActivity = $derived([
		{
			name: "Ingresadas",
			data: yearlyAggr.map((y) => ({ x: y.anio, y: y.ingresadas })),
			color: "var(--color-brand-indigo)",
		},
		{
			name: "Resueltas",
			data: yearlyAggr.map((y) => ({ x: y.anio, y: y.resueltas })),
			color: "var(--color-brand-success)",
		},
	]);

	const breakdownKeys = [
		"Sentencia",
		"Conciliación",
		"Allanamiento",
		"Transacción",
		"Caducidad",
		"Desistimiento",
		"Interlocutorios",
		"Incompetencia",
	];
	const breakdownColors = {
		Sentencia: "#4f46e5",
		Conciliación: "#10b981",
		Allanamiento: "#8b5cf6",
		Transacción: "#06b6d4",
		Caducidad: "#f43f5e",
		Desistimiento: "#e2e8f0",
		Interlocutorios: "#f59e0b",
		Incompetencia: "#64748b",
	};

	// State for Composición Histórica chart variety in teaser
	let compositionFuero = $state<'ambos' | 'civil' | 'trabajo'>('ambos');

	// Filter records specifically for Composición Histórica based on selected variety
	const compositionRecords = $derived.by(() => {
		return db.consolidatedRecords.filter(
			(r) => compositionFuero === 'ambos' || r.fuero === compositionFuero
		);
	});

	// Group composition records by year
	const compositionYearlyRecords = $derived.by(() => {
		const groups: { [anio: number]: CourtRecord } = {};

		for (const r of compositionRecords) {
			const anio = r.anio;
			if (!groups[anio]) {
				groups[anio] = {
					anio,
					sede: 'PROVINCIA',
					ingresadas: 0,
					sentencia: 0,
					conciliacion: 0,
					allanamiento: 0,
					transaccion: 0,
					caducidad: 0,
					desistimiento: 0,
					interlocutorios: 0,
					incompetencia: 0,
					totalResueltas: 0
				};
			}

			const record = groups[anio];
			const valor = r.valor;

			switch (r.tipo) {
				case 'Ingresadas':
					record.ingresadas += valor;
					break;
				case 'Sentencia':
					record.sentencia += valor;
					break;
				case 'Conciliación':
					record.conciliacion += valor;
					break;
				case 'Allanamiento':
					record.allanamiento += valor;
					break;
				case 'Transacción':
					record.transaccion += valor;
					break;
				case 'Caducidad':
					record.caducidad += valor;
					break;
				case 'Desistimiento':
					record.desistimiento += valor;
					break;
				case 'Interlocutorios':
					record.interlocutorios += valor;
					break;
				case 'Incompetencia':
					record.incompetencia += valor;
					break;
				case 'Total Resueltas':
					record.totalResueltas += valor;
					break;
			}
		}

		return Object.values(groups).sort((a, b) => a.anio - b.anio);
	});

	// Transform data for Composición Histórica AreaChart
	const compositionYearlyAggr = $derived.by(() => {
		return compositionYearlyRecords.map((r) => ({
			anio: r.anio,
			Sentencia: r.sentencia,
			Conciliación: r.conciliacion,
			Allanamiento: r.allanamiento,
			Transacción: r.transaccion,
			Caducidad: r.caducidad,
			Desistimiento: r.desistimiento,
			Interlocutorios: r.interlocutorios,
			Incompetencia: r.incompetencia
		}));
	});
</script>

<div class="flex-1 flex flex-col items-center justify-center py-12 px-4 font-serif w-full">
	<div class="max-w-7xl w-full text-center space-y-8">
		<!-- Main Titles -->
		<div class="space-y-4">
			<div class="inline-flex items-center justify-center p-2.5 rounded-2xl bg-brand-indigo/10 border border-brand-indigo/20 text-brand-indigo mb-2">
				<Scale class="w-8 h-8" />
			</div>
			<h2 class="text-3xl sm:text-4xl font-extrabold tracking-tight text-brand-text font-serif">
				Estadísticas Judiciales de la Provincia de Buenos Aires
			</h2>
			<p class="text-sm sm:text-base text-brand-text-muted max-w-2xl mx-auto font-sans leading-relaxed">
				Seleccione la jurisdicción o fuero que desea explorar. Esta herramienta permite visualizar de forma descriptiva el flujo de causas, resoluciones y tasas de desempeño histórico desde 2017 a 2025.
			</p>
		</div>

		<!-- Cards/Buttons Grid -->
		<div class="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
			<!-- Consolidado Provincial Card -->
			<button
				onclick={() => goto(`${base}/consolidado`)}
				class="glass-panel-interactive text-left p-8 rounded-3xl border border-brand-border flex flex-col justify-between h-[280px] cursor-pointer focus:outline-none focus:ring-2 focus:ring-brand-indigo group"
			>
				<div class="space-y-4">
					<div class="w-12 h-12 rounded-2xl bg-gradient-to-tr from-purple-600 to-brand-indigo flex items-center justify-center text-white shadow-md transition group-hover:scale-110 duration-300">
						<Scale class="w-6 h-6" />
					</div>
					<div>
						<h3 class="text-xl font-bold text-brand-text font-serif group-hover:text-brand-indigo transition">
							Consolidado Provincial
						</h3>
						<p class="text-xs text-brand-text-muted mt-2 font-sans leading-relaxed">
							Analice la activity consolidada a nivel provincial de forma integrada. Visualice y filtre la evolución temporal de causas, brechas y tasas de resolución para ambos fueros.
						</p>
					</div>
				</div>
				<div class="flex items-center text-xs font-semibold text-brand-indigo font-sans mt-4 group-hover:translate-x-1 transition-transform">
					Comenzar exploración &rarr;
				</div>
			</button>

			<!-- Tribunales de Trabajo Card -->
			<button
				onclick={() => selectFuero('trabajo')}
				class="glass-panel-interactive text-left p-8 rounded-3xl border border-brand-border flex flex-col justify-between h-[280px] cursor-pointer focus:outline-none focus:ring-2 focus:ring-brand-indigo group"
			>
				<div class="space-y-4">
					<div class="w-12 h-12 rounded-2xl bg-gradient-to-tr from-brand-success to-emerald-600 flex items-center justify-center text-white shadow-md transition group-hover:scale-110 duration-300">
						<Scale class="w-6 h-6" />
					</div>
					<div>
						<h3 class="text-xl font-bold text-brand-text font-serif group-hover:text-brand-success transition">
							Tribunales de Trabajo
						</h3>
						<p class="text-xs text-brand-text-muted mt-2 font-sans leading-relaxed">
							Explore los registros históricos y el flujo de litigios laborales. Analice sentencias, conciliaciones, caducidades y el stock provincial de expedientes acumulados.
						</p>
					</div>
				</div>
				<div class="flex items-center text-xs font-semibold text-brand-success font-sans mt-4 group-hover:translate-x-1 transition-transform">
					Comenzar exploración &rarr;
				</div>
			</button>

			<!-- Juzgados Civiles Card -->
			<button
				onclick={() => selectFuero('civil')}
				class="glass-panel-interactive text-left p-8 rounded-3xl border border-brand-border flex flex-col justify-between h-[280px] cursor-pointer focus:outline-none focus:ring-2 focus:ring-brand-indigo group"
			>
				<div class="space-y-4">
					<div class="w-12 h-12 rounded-2xl bg-gradient-to-tr from-brand-indigo to-indigo-500 flex items-center justify-center text-white shadow-md transition group-hover:scale-110 duration-300">
						<Building2 class="w-6 h-6" />
					</div>
					<div>
						<h3 class="text-xl font-bold text-brand-text font-serif group-hover:text-brand-indigo transition">
							Juzgados en lo Civil y Comercial
						</h3>
						<p class="text-xs text-brand-text-muted mt-2 font-sans leading-relaxed">
							Acceda al análisis estadístico consolidado de la actividad en juzgados civiles y comerciales bonaerenses. Compare sedes, explore tasas de resolución y modos de cierre.
						</p>
					</div>
				</div>
				<div class="flex items-center text-xs font-semibold text-brand-indigo font-sans mt-4 group-hover:translate-x-1 transition-transform">
					Comenzar exploración &rarr;
				</div>
			</button>
		</div>

		<!-- Teaser Section -->
		<div class="mt-16 text-left space-y-6 w-full">
			<div class="border-t border-brand-border pt-8">
				<h3 class="text-xl font-bold text-brand-text font-serif">
					Vista Rápida: Actividad Provincial Consolidada
				</h3>
				<p class="text-xs text-brand-text-muted mt-1 font-sans">
					Resumen de la evolución y resolución de expedientes a nivel provincial consolidando ambos fueros (Civil y Comercial y Trabajo).
				</p>
			</div>

			<div class="grid grid-cols-1 lg:grid-cols-2 gap-6 w-full">
				<!-- Chart 1: Evolución Temporal -->
				<div class="glass-panel p-6 rounded-3xl border border-brand-border min-h-[400px] flex flex-col justify-between">
					<LineChart
						series={lineSeriesActivity}
						title="Evolución Temporal: Causas Ingresadas vs Resueltas"
					/>
				</div>

				<!-- Chart 2: Composición Histórica -->
				<div class="glass-panel p-6 rounded-3xl border border-brand-border min-h-[400px] flex flex-col justify-between">
					<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 px-2 mb-3">
						<h5 class="text-sm font-bold text-brand-text">
							Composición Histórica de Resoluciones (Modos de Cierre)
						</h5>
						
						<!-- Fuero selector buttons for Composición Histórica -->
						<div class="flex bg-stone-100 p-0.5 rounded-xl border border-brand-border self-start sm:self-auto shadow-inner">
							<button
								type="button"
								onclick={() => compositionFuero = 'ambos'}
								class="px-2.5 py-1 text-xs font-semibold rounded-lg transition-all duration-200 cursor-pointer {compositionFuero === 'ambos' ? 'bg-white text-brand-text shadow-sm border border-brand-border/40 font-bold' : 'text-brand-text-muted hover:text-brand-text border border-transparent'}"
							>
								Todos
							</button>
							<button
								type="button"
								onclick={() => compositionFuero = 'civil'}
								class="px-2.5 py-1 text-xs font-semibold rounded-lg transition-all duration-200 cursor-pointer {compositionFuero === 'civil' ? 'bg-[var(--color-brand-civil)] text-white shadow-sm border border-[var(--color-brand-civil)] font-bold' : 'text-brand-text-muted hover:text-brand-text border border-transparent'}"
							>
								Civil
							</button>
							<button
								type="button"
								onclick={() => compositionFuero = 'trabajo'}
								class="px-2.5 py-1 text-xs font-semibold rounded-lg transition-all duration-200 cursor-pointer {compositionFuero === 'trabajo' ? 'bg-[var(--color-brand-laboral)] text-white shadow-sm border border-[var(--color-brand-laboral)] font-bold' : 'text-brand-text-muted hover:text-brand-text border border-transparent'}"
							>
								Trabajo
							</button>
						</div>
					</div>
					
					<AreaChart
						data={compositionYearlyAggr}
						keys={breakdownKeys}
						colors={breakdownColors}
						title=""
					/>
				</div>
			</div>
		</div>

		<!-- Footer Badge -->
		<div class="text-[10px] text-brand-text-muted font-mono uppercase tracking-wider pt-6">
			Fuente de datos: <a href="https://www.scba.gov.ar/estadisticas.asp" target="_blank" rel="noopener noreferrer" class="hover:underline text-brand-indigo font-medium">Suprema Corte de Justicia de la Provincia de Buenos Aires (SCBA)</a>
		</div>
	</div>
</div>
