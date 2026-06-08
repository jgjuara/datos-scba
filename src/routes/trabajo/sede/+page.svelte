<script lang="ts">
	import { untrack } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { db } from '$lib/data/loader.svelte';
	import { calculateMetrics, calculateAggregatedMetrics } from '$lib/data/metrics';
	import KPI from '$lib/components/KPI.svelte';
	import Filters from '$lib/components/Filters.svelte';
	import LineChart from '$lib/charts/LineChart.svelte';
	import AreaChart from '$lib/charts/AreaChart.svelte';
	import SearchableSelect from '$lib/components/SearchableSelect.svelte';
	import {
		Building2,
		Scale,
		CheckCircle2,
		TrendingUp,
		FileText,
		XSquare,
		ArrowUpRight,
		ArrowDownRight,
		AlertCircle
	} from '@lucide/svelte';

	// Sede selection state synchronized with query param '?id='
	let selectedSede = $state($page.url.searchParams.get('id') || '');

	$effect(() => {
		const currentSede = selectedSede;
		untrack(() => {
			const currentId = $page.url.searchParams.get('id') || '';
			if (currentSede !== currentId) {
				const url = new URL($page.url);
				if (currentSede) {
					url.searchParams.set('id', currentSede);
				} else {
					url.searchParams.delete('id');
				}
				goto(url.pathname + url.search, {
					keepFocus: true,
					replaceState: true,
					noScroll: true
				});
			}
		});
	});

	// React to URL changes directly (e.g. back/forward browser navigation)
	$effect(() => {
		const idParam = $page.url.searchParams.get('id') || '';
		untrack(() => {
			if (selectedSede !== idParam) {
				selectedSede = idParam;
			}
		});
	});

	// Period filter
	let selectedRange = $state<[number, number]>([2017, 2025]);
	let initialized = false;
	$effect(() => {
		if (!initialized && db.anios.length > 0) {
			selectedRange = [db.anios[0], db.anios[db.anios.length - 1]];
			initialized = true;
		}
	});

	// Verification: check if the selected seat exists in dataset
	const seatExists = $derived(selectedSede ? db.sedes.includes(selectedSede) : false);

	// Filter data for the current seat and selected period range
	const seatRecords = $derived.by(() => {
		if (!selectedSede) return [];
		return db.records.filter((r) => {
			const matchesSede = r.sede === selectedSede;
			const matchesYear = r.anio >= selectedRange[0] && r.anio <= selectedRange[1];
			return matchesSede && matchesYear;
		});
	});

	// Aggregate metrics (cumulative for selected period)
	const seatMetricsAcc = $derived(calculateAggregatedMetrics(seatRecords));

	// Provincial averages for benchmarking (cumulative for selected period)
	const provincialMetricsAcc = $derived.by(() => {
		const yearRecords = db.records.filter(
			(r) => r.anio >= selectedRange[0] && r.anio <= selectedRange[1]
		);
		return calculateAggregatedMetrics(yearRecords);
	});

	// Performance over time (annual details for charts within selected range)
	const annualPerformance = $derived.by(() => {
		const result = [];
		for (const r of [...seatRecords].sort((a, b) => a.anio - b.anio)) {
			result.push({
				anio: r.anio,
				record: r,
				metrics: calculateMetrics(r)
			});
		}
		return result;
	});

	// Provincial annual stats for comparison charts (within selected range)
	const provincialAnnualPerformance = $derived.by(() => {
		const result = new Map<number, any>();
		for (const anio of db.anios) {
			if (anio < selectedRange[0] || anio > selectedRange[1]) continue;
			const yearRecs = db.records.filter((r) => r.anio === anio);
			const metrics = calculateAggregatedMetrics(yearRecs);
			result.set(anio, metrics);
		}
		return result;
	});

	// Chart Series definitions
	const lineSeriesActivity = $derived([
		{
			name: 'Ingresadas (Sede)',
			data: annualPerformance.map((a) => ({ x: a.anio, y: a.record.ingresadas })),
			color: 'var(--color-brand-laboral)'
		},
		{
			name: 'Resueltas (Sede)',
			data: annualPerformance.map((a) => ({ x: a.anio, y: a.record.totalResueltas })),
			color: 'var(--color-brand-laboral)'
		}
	]);

	const lineSeriesTasaResolucion = $derived([
		{
			name: 'Sede',
			data: annualPerformance.map((a) => ({ x: a.anio, y: a.metrics.tasaResolucion })),
			color: 'var(--color-brand-laboral)'
		},
		{
			name: 'Provincia',
			data: annualPerformance.map((a) => ({
				x: a.anio,
				y: provincialAnnualPerformance.get(a.anio)?.tasaResolucion ?? 0
			})),
			color: 'var(--color-brand-indigo)'
		}
	]);

	const lineSeriesTasaSentencia = $derived([
		{
			name: 'Sede',
			data: annualPerformance.map((a) => ({ x: a.anio, y: a.metrics.tasaSentencia })),
			color: 'var(--color-brand-laboral)'
		},
		{
			name: 'Provincia',
			data: annualPerformance.map((a) => ({
				x: a.anio,
				y: provincialAnnualPerformance.get(a.anio)?.tasaSentencia ?? 0
			})),
			color: 'var(--color-brand-indigo)'
		}
	]);

	const lineSeriesTasaCaducidad = $derived([
		{
			name: 'Sede',
			data: annualPerformance.map((a) => ({ x: a.anio, y: a.metrics.tasaCaducidad })),
			color: 'var(--color-brand-laboral)'
		},
		{
			name: 'Provincia',
			data: annualPerformance.map((a) => ({
				x: a.anio,
				y: provincialAnnualPerformance.get(a.anio)?.tasaCaducidad ?? 0
			})),
			color: 'var(--color-brand-indigo)'
		}
	]);

	// Breakdown config
	const breakdownKeys = [
		'Sentencia',
		'Conciliación',
		'Allanamiento',
		'Transacción',
		'Caducidad',
		'Desistimiento',
		'Interlocutorios',
		'Incompetencia'
	];
	const breakdownColors = {
		Sentencia: '#4f46e5',
		Conciliación: '#10b981',
		Allanamiento: '#8b5cf6',
		Transacción: '#06b6d4',
		Caducidad: '#f43f5e',
		Desistimiento: '#e2e8f0',
		Interlocutorios: '#f59e0b',
		Incompetencia: '#64748b'
	};

	const seatResolutionBreakdown = $derived(
		annualPerformance.map((a) => ({
			anio: a.anio,
			Sentencia: a.record.sentencia,
			Conciliación: a.record.conciliacion,
			Allanamiento: a.record.allanamiento,
			Transacción: a.record.transaccion,
			Caducidad: a.record.caducidad,
			Desistimiento: a.record.desistimiento,
			Interlocutorios: a.record.interlocutorios,
			Incompetencia: a.record.incompetencia
		}))
	);

	// Benchmarks
	const resDiff = $derived(seatMetricsAcc.tasaResolucion - provincialMetricsAcc.tasaResolucion);
	const sentDiff = $derived(seatMetricsAcc.tasaSentencia - provincialMetricsAcc.tasaSentencia);
	const cadDiff = $derived(seatMetricsAcc.tasaCaducidad - provincialMetricsAcc.tasaCaducidad);

	// Helpers
	const formatInt = (v: number) => v.toLocaleString('es-AR');
	const formatPercent = (v: number) => (v * 100).toFixed(1) + '%';
</script>

<div class="space-y-6">
	<!-- Top Bar -->
	<div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
		<div class="flex items-center gap-3">
			<div class="p-2.5 bg-brand-indigo/10 border border-brand-indigo/20 text-brand-indigo rounded-2xl">
				<Building2 class="w-6 h-6" />
			</div>
			<div>
				<h2 class="text-2xl font-bold text-brand-text tracking-tight">Detalle por Sede Judicial - Trabajo</h2>
				<p class="text-xs text-brand-text-muted mt-1">
					Historial y comparativa detallada de rendimiento procesal por sede.
				</p>
			</div>
		</div>

		<!-- Filters -->
		<Filters years={db.anios} bind:selectedRange />
	</div>

	<!-- Selector Section -->
	<div class="glass-panel p-5 rounded-2xl border border-brand-border flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
		<div class="space-y-1">
			<h4 class="text-xs font-bold text-brand-text uppercase tracking-wider">Selección de Sede</h4>
			<p class="text-[11px] text-brand-text-muted">Elige una sede para analizar sus indicadores.</p>
		</div>

		<!-- Custom Searchable Select -->
		<SearchableSelect options={db.sedes} bind:selected={selectedSede} placeholder="Buscar y seleccionar sede..." />
	</div>

	{#if !selectedSede}
		<!-- Empty State -->
		<div class="glass-panel p-12 rounded-3xl border border-brand-border text-center flex flex-col items-center justify-center min-h-[300px]">
			<div class="w-16 h-16 rounded-full bg-brand-indigo/5 border border-brand-border flex items-center justify-center mb-4">
				<Building2 class="w-8 h-8 text-brand-indigo/60" />
			</div>
			<h3 class="text-base font-bold text-brand-text">Ninguna sede seleccionada</h3>
			<p class="text-xs text-brand-text-muted mt-2 max-w-sm">
				Utiliza el buscador superior para seleccionar una sede judicial y visualizar sus estadísticas detalladas.
			</p>
		</div>
	{:else if !seatExists}
		<!-- Not Found State -->
		<div class="glass-panel p-12 rounded-3xl border border-brand-border text-center flex flex-col items-center justify-center min-h-[300px]">
			<div class="w-16 h-16 rounded-full bg-brand-danger/5 border border-brand-danger/20 flex items-center justify-center mb-4">
				<AlertCircle class="w-8 h-8 text-brand-danger" />
			</div>
			<h3 class="text-base font-bold text-brand-text">Sede no encontrada</h3>
			<p class="text-xs text-brand-text-muted mt-2 max-w-sm">
				La sede "{selectedSede}" no se encuentra en el registro actual de tribunales de trabajo.
			</p>
		</div>
	{:else}
		<!-- Warning about Zarate-Campana consolidation if applicable -->
		{#if selectedSede === 'ZARATE-CAMPANA'}
			<div class="p-3.5 bg-brand-warning/10 border border-brand-warning/20 text-brand-warning text-xs rounded-xl flex items-start gap-3">
				<AlertCircle class="w-4 h-4 mt-0.5 flex-shrink-0" />
				<div>
					<span class="font-bold">Aclaración Metodológica:</span> Para los años 2017 y 2018, los datos consolidados corresponden a la sumatoria de las antiguas clasificaciones independientes de <i>ZARATE-CAMPANA Sede CAMPANA</i> y <i>ZARATE-CAMPANA Sede ZARATE</i>, posibilitando el análisis temporal unificado.
				</div>
			</div>
		{/if}

		<!-- KPIs block -->
		<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
			<KPI
				title="Ingresadas Acumuladas"
				value={formatInt(seatMetricsAcc.ingresadas)}
				icon={Scale}
				variant="indigo"
				subtitle="Total de ingresos en el período"
			/>

			<KPI
				title="Resueltas Acumuladas"
				value={formatInt(seatMetricsAcc.resueltas)}
				icon={CheckCircle2}
				variant="success"
				subtitle="Total de resoluciones en el período"
			/>

			<KPI
				title="Tasa de Resol. Histórica"
				value={formatPercent(seatMetricsAcc.tasaResolucion)}
				icon={TrendingUp}
				variant={seatMetricsAcc.tasaResolucion >= 1.0 ? 'success' : 'warning'}
				subtitle="Ingresos vs Egresos del período"
			/>

			<KPI
				title="Tasa Sentencia Histórica"
				value={formatPercent(seatMetricsAcc.tasaSentencia)}
				icon={FileText}
				variant="default"
				subtitle="Proporción promedio de sentencias"
			/>

			<KPI
				title="Tasa Caducidad Histórica"
				value={formatPercent(seatMetricsAcc.tasaCaducidad)}
				icon={XSquare}
				variant={seatMetricsAcc.tasaCaducidad > 0.1 ? 'danger' : 'default'}
				subtitle="Proporción promedio de caducidades"
			/>
		</div>

		<!-- Benchmark vs Province Section -->
		<div class="glass-panel p-5 rounded-2xl border border-brand-border space-y-4">
			<h3 class="text-sm font-bold text-brand-text">Desviación frente al Promedio Provincial (Filtrado {selectedRange[0]} - {selectedRange[1]})</h3>

			<div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
				<!-- Tasa Resolución Benchmark -->
				<div class="p-4 bg-white rounded-xl border border-brand-border flex items-center justify-between">
					<div>
						<span class="text-[10px] text-brand-text-muted font-semibold uppercase tracking-wider block">Tasa de Resolución</span>
						<div class="flex items-baseline gap-2 mt-1">
							<span class="text-lg font-bold">{formatPercent(seatMetricsAcc.tasaResolucion)}</span>
							<span class="text-xs text-brand-text-muted">vs {formatPercent(provincialMetricsAcc.tasaResolucion)} (Prov)</span>
						</div>
					</div>
					<div class="flex flex-col items-center">
						<span class="text-xs font-bold font-mono {resDiff >= 0 ? 'text-brand-success' : 'text-brand-danger'} flex items-center gap-0.5">
							{#if resDiff >= 0}<ArrowUpRight class="w-4 h-4" />{:else}<ArrowDownRight class="w-4 h-4" />{/if}
							{resDiff >= 0 ? '+' : ''}{(resDiff * 100).toFixed(1)} pp
						</span>
						<span class="text-[9px] text-brand-text-muted">Desviación</span>
					</div>
				</div>

				<!-- Tasa Sentencia Benchmark -->
				<div class="p-4 bg-white rounded-xl border border-brand-border flex items-center justify-between">
					<div>
						<span class="text-[10px] text-brand-text-muted font-semibold uppercase tracking-wider block">Tasa de Sentencia</span>
						<div class="flex items-baseline gap-2 mt-1">
							<span class="text-lg font-bold">{formatPercent(seatMetricsAcc.tasaSentencia)}</span>
							<span class="text-xs text-brand-text-muted">vs {formatPercent(provincialMetricsAcc.tasaSentencia)} (Prov)</span>
						</div>
					</div>
					<div class="flex flex-col items-center">
						<span class="text-xs font-bold font-mono {sentDiff >= 0 ? 'text-brand-success' : 'text-brand-danger'} flex items-center gap-0.5">
							{#if sentDiff >= 0}<ArrowUpRight class="w-4 h-4" />{:else}<ArrowDownRight class="w-4 h-4" />{/if}
							{sentDiff >= 0 ? '+' : ''}{(sentDiff * 100).toFixed(1)} pp
						</span>
						<span class="text-[9px] text-brand-text-muted">Desviación</span>
					</div>
				</div>

				<!-- Tasa Caducidad Benchmark -->
				<div class="p-4 bg-white rounded-xl border border-brand-border flex items-center justify-between">
					<div>
						<span class="text-[10px] text-brand-text-muted font-semibold uppercase tracking-wider block">Tasa de Caducidad</span>
						<div class="flex items-baseline gap-2 mt-1">
							<span class="text-lg font-bold">{formatPercent(seatMetricsAcc.tasaCaducidad)}</span>
							<span class="text-xs text-brand-text-muted">vs {formatPercent(provincialMetricsAcc.tasaCaducidad)} (Prov)</span>
						</div>
					</div>
					<div class="flex flex-col items-center">
						<span class="text-xs font-bold font-mono {cadDiff <= 0 ? 'text-brand-success' : 'text-brand-danger'} flex items-center gap-0.5">
							{#if cadDiff >= 0}<ArrowUpRight class="w-4 h-4" />{:else}<ArrowDownRight class="w-4 h-4" />{/if}
							{cadDiff >= 0 ? '+' : ''}{(cadDiff * 100).toFixed(1)} pp
						</span>
						<span class="text-[9px] text-brand-text-muted">Desviación</span>
					</div>
				</div>
			</div>
		</div>

		<!-- Charts Grid -->
		<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
			<!-- Chart 1: Activity -->
			<div class="glass-panel p-6 rounded-3xl border border-brand-border min-h-[380px] flex flex-col justify-between">
				<LineChart
					series={lineSeriesActivity}
					title="Evolución Temporal de Carga de Trabajo (Ingresos vs Resueltas)"
				/>
			</div>

			<!-- Chart 2: Resolution Rate -->
			<div class="glass-panel p-6 rounded-3xl border border-brand-border min-h-[380px] flex flex-col justify-between">
				<LineChart
					series={lineSeriesTasaResolucion}
					title="Comparativa Temporal: Tasa de Resolución (Sede vs Provincia)"
					formatY={formatPercent}
				/>
			</div>

			<!-- Chart 3: Sentencia Rate -->
			<div class="glass-panel p-6 rounded-3xl border border-brand-border min-h-[380px] flex flex-col justify-between">
				<LineChart
					series={lineSeriesTasaSentencia}
					title="Comparativa Temporal: Tasa de Sentencia (Sede vs Provincia)"
					formatY={formatPercent}
				/>
			</div>

			<!-- Chart 4: Caducidad Rate -->
			<div class="glass-panel p-6 rounded-3xl border border-brand-border min-h-[380px] flex flex-col justify-between">
				<LineChart
					series={lineSeriesTasaCaducidad}
					title="Comparativa Temporal: Tasa de Caducidad (Sede vs Provincia)"
					formatY={formatPercent}
				/>
			</div>

			<!-- Chart 5: Resolution Type Composition -->
			<div class="glass-panel p-6 rounded-3xl border border-brand-border min-h-[400px] flex flex-col justify-between">
				<AreaChart
					data={seatResolutionBreakdown}
					keys={breakdownKeys}
					colors={breakdownColors}
					title="Composición Histórica de Resoluciones (Modos de Cierre)"
				/>
			</div>
		</div>
	{/if}
</div>
