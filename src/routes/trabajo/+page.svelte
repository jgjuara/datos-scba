<script lang="ts">
	import { db } from "$lib/data/loader.svelte";
	import { calculateAggregatedMetrics } from "$lib/data/metrics";
	import type { CalculatedMetrics } from "$lib/data/metrics";
	import KPI from "$lib/components/KPI.svelte";
	import Filters from "$lib/components/Filters.svelte";
	import LineChart from "$lib/charts/LineChart.svelte";
	import AreaChart from "$lib/charts/AreaChart.svelte";
	import {
		Scale,
		FileText,
		CheckCircle2,
		TrendingUp,
		XSquare,
		Handshake,
	} from "@lucide/svelte";

	// Year filter range bound to Filters
	let selectedRange = $state<[number, number]>([2017, 2025]);
	let initialized = false;
	$effect(() => {
		if (!initialized && db.anios.length > 0) {
			selectedRange = [db.anios[0], db.anios[db.anios.length - 1]];
			initialized = true;
		}
	});

	// 1. Data filtered by selected year range (for KPIs)
	const filteredRecords = $derived.by(() => {
		return db.records.filter(
			(r) => r.anio >= selectedRange[0] && r.anio <= selectedRange[1],
		);
	});

	// Calculated metrics for KPIs
	const kpis = $derived(calculateAggregatedMetrics(filteredRecords));

	// Last year of the selected range
	const lastYear = $derived(selectedRange[1]);

	// Data for the last year of the selected range
	const lastYearRecords = $derived.by(() => {
		return db.records.filter((r) => r.anio === lastYear);
	});

	// Metrics for the last year
	const lastYearKpis = $derived(calculateAggregatedMetrics(lastYearRecords));

	// 2. Data grouped by year for temporal charts
	const yearlyAggr = $derived.by(() => {
		const result: Array<{ anio: number; [key: string]: any }> = [];

		for (const anio of db.anios) {
			if (anio < selectedRange[0] || anio > selectedRange[1]) continue;
			const yearRecords = db.records.filter((r) => r.anio === anio);
			if (yearRecords.length === 0) continue;

			let ingresadas = 0;
			let sentencia = 0;
			let conciliacion = 0;
			let allanamiento = 0;
			let transaccion = 0;
			let caducidad = 0;
			let desistimiento = 0;
			let interlocutorios = 0;
			let incompetencia = 0;
			let totalResueltas = 0;

			for (const r of yearRecords) {
				ingresadas += r.ingresadas;
				sentencia += r.sentencia;
				conciliacion += r.conciliacion;
				allanamiento += r.allanamiento;
				transaccion += r.transaccion;
				caducidad += r.caducidad;
				desistimiento += r.desistimiento;
				interlocutorios += r.interlocutorios;
				incompetencia += r.incompetencia;
				totalResueltas += r.totalResueltas;
			}

			const safeDiv = (num: number, den: number): number =>
				den === 0 ? 0 : num / den;

			result.push({
				anio,
				ingresadas,
				resueltas: totalResueltas,
				tasaResolucion: safeDiv(totalResueltas, ingresadas),
				brechaAnual: ingresadas - totalResueltas,
				// Breakdown fields
				Sentencia: sentencia,
				Conciliación: conciliacion,
				Allanamiento: allanamiento,
				Transacción: transaccion,
				Caducidad: caducidad,
				Desistimiento: desistimiento,
				Interlocutorios: interlocutorios,
				Incompetencia: incompetencia,
			});
		}

		return result;
	});

	// Data mapped specifically for charts
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

	const lineSeriesTasaResolucion = $derived([
		{
			name: "Tasa de Resolución",
			data: yearlyAggr.map((y) => ({ x: y.anio, y: y.tasaResolucion })),
			color: "var(--color-brand-indigo)",
		},
	]);

	// Breakdown config
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
		Sentencia: "#4f46e5", // Indigo oscuro
		Conciliación: "#10b981", // Verde
		Allanamiento: "#8b5cf6", // Violeta
		Transacción: "#06b6d4", // Cian
		Caducidad: "#f43f5e", // Rojo
		Desistimiento: "#e2e8f0", // Gris claro
		Interlocutorios: "#f59e0b", // Ámbar
		Incompetencia: "#64748b", // Gris oscuro
	};

	// Formatters
	const formatInt = (v: number) => v.toLocaleString("es-AR");
	const formatPercent = (v: number) => (v * 100).toFixed(1) + "%";

	// Inline BarChart sizing for Gap
	let barChartWidth = $state(600);
</script>

<div class="space-y-6">
	<!-- Top Bar -->
	<div
		class="flex flex-col md:flex-row md:items-center justify-between gap-4"
	>
		<div>
			<h2 class="text-2xl font-bold text-brand-text tracking-tight">
				Dashboard Provincial - Trabajo
			</h2>
			<p class="text-xs text-brand-text-muted mt-1">
				Análisis descriptivo consolidado de la justicia laboral
				bonaerense.
			</p>
		</div>

		<!-- Filters Component -->
		<Filters years={db.anios} bind:selectedRange />
	</div>

	<!-- KPIs Grid -->
	<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
		<KPI
			title="Stock de causas"
			value={formatInt(kpis.ingresadas - kpis.resueltas)}
			icon={Scale}
			variant="indigo"
			subtitle="Ingresadas - resueltas en el período"
		/>

		<KPI
			title="Tasa de Resolución"
			value={formatPercent(lastYearKpis.tasaResolucion)}
			icon={TrendingUp}
			variant={lastYearKpis.tasaResolucion >= 1.0 ? "success" : "warning"}
			trend={{
				value: formatPercent(lastYearKpis.tasaResolucion),
				direction: lastYearKpis.tasaResolucion >= 1.0 ? "up" : "down",
				label: `Último año (${lastYear})`,
			}}
		/>

		<KPI
			title="Tasa de Sentencia"
			value={formatPercent(lastYearKpis.tasaSentencia)}
			icon={FileText}
			variant="default"
			subtitle={`Sentencias / Resueltas (Último año: ${lastYear})`}
		/>

		<KPI
			title="Tasa de Conciliación"
			value={formatPercent(lastYearKpis.tasaConciliacion)}
			icon={Handshake}
			variant="default"
			subtitle={`Conciliación / Resueltas (Último año: ${lastYear})`}
		/>

		<KPI
			title="Tasa de Caducidad"
			value={formatPercent(lastYearKpis.tasaCaducidad)}
			icon={XSquare}
			variant={lastYearKpis.tasaCaducidad > 0.1 ? "danger" : "default"}
			subtitle={`Caducidad / Resueltas (Último año: ${lastYear})`}
		/>
	</div>

	<!-- Row 1: Line Charts -->
	<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
		<div
			class="glass-panel p-6 rounded-3xl border border-brand-border min-h-[400px] flex flex-col justify-between"
		>
			<LineChart
				series={lineSeriesActivity}
				title="Evolución Temporal: Causas Ingresadas vs Resueltas"
			/>
		</div>

		<!-- Custom Yearly Gap Bar Chart -->
		<div
			class="glass-panel p-6 rounded-3xl border border-brand-border min-h-[400px] flex flex-col justify-between"
			bind:clientWidth={barChartWidth}
		>
			<div class="px-2">
				<h5 class="text-sm font-bold text-brand-text">
					Brecha Anual (Ingresadas - Resueltas)
				</h5>
				<p
					class="text-[10px] text-brand-text-muted mt-1 leading-normal"
				>
					Valores positivos (rojo) representan acumulación neta de
					expedientes. Valores negativos (verde) indican resolución
					mayor al ingreso.
				</p>
			</div>

			<div class="flex-1 mt-4 select-none relative">
				{#if yearlyAggr.length > 0}
					{@const vals = yearlyAggr.map((y) => y.brechaAnual)}
					{@const rawMax = Math.max(...vals, 0)}
					{@const rawMin = Math.min(...vals, 0)}
					{@const maxVal = rawMax === 0 && rawMin === 0 ? 1000 : rawMax}
					{@const minVal = rawMax === 0 && rawMin === 0 ? -1000 : rawMin}
					{@const height = 240}
					{@const paddingY = 20}
					{@const chartH = height - paddingY * 2}
					<!-- Scales -->
					{@const xScaleBar = (index: number) => {
						const step = (barChartWidth - 110) / yearlyAggr.length;
						return 70 + index * step;
					}}
					{@const gapToY = (val: number) =>
						paddingY + (1 - (val - minVal) / (maxVal - minVal)) * chartH}
					<!-- Zero Y line coordinate -->
					{@const zeroY = gapToY(0)}

					<svg
						width={barChartWidth - 30}
						{height}
						class="overflow-visible"
					>
						<!-- Horizontal line at zero -->
						<line
							x1="60"
							y1={zeroY}
							x2={barChartWidth - 50}
							y2={zeroY}
							stroke="var(--color-brand-border)"
							stroke-width="1.5"
						/>

						<!-- Render Bars -->
						{#each yearlyAggr as y, i}
							{@const barX = xScaleBar(i)}
							{@const barY = gapToY(y.brechaAnual)}
							{@const barH = Math.abs(barY - zeroY)}
							{@const isAccumulation = y.brechaAnual > 0}

							<!-- Rect bar -->
							<rect
								x={barX - 12}
								y={isAccumulation ? barY : zeroY}
								width="24"
								height={Math.max(2, barH)}
								rx="3"
								fill={isAccumulation
									? "var(--color-brand-danger)"
									: "var(--color-brand-success)"}
								opacity="0.7"
								class="hover:opacity-100 transition cursor-pointer"
							/>

							<!-- Year Label -->
							<text
								x={barX}
								y={height - 2}
								text-anchor="middle"
								class="text-[10px] fill-brand-text-muted font-mono"
							>
								{y.anio}
							</text>

							<!-- Value label on top/bottom of bar -->
							<text
								x={barX}
								y={isAccumulation ? barY - 6 : barY + 14}
								text-anchor="middle"
								class="text-[9px] font-mono font-bold {isAccumulation
									? 'fill-brand-danger'
									: 'fill-brand-success'}"
							>
								{y.brechaAnual > 0 ? "+" : ""}{formatInt(
									y.brechaAnual,
								)}
							</text>
						{/each}
					</svg>
				{/if}
			</div>
		</div>
	</div>

	<!-- Row 2: Composition & Gap -->
	<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
		<div
			class="glass-panel p-6 rounded-3xl border border-brand-border min-h-[400px] flex flex-col justify-between"
		>
			<AreaChart
				data={yearlyAggr}
				keys={breakdownKeys}
				colors={breakdownColors}
				title="Composición Histórica de Resoluciones (Modos de Cierre)"
			/>
		</div>

		<div
			class="glass-panel p-6 rounded-3xl border border-brand-border min-h-[400px] flex flex-col justify-between"
		>
			<LineChart
				series={lineSeriesTasaResolucion}
				title="Evolución de la Tasa de Resolución"
				formatY={formatPercent}
			/>
		</div>
	</div>
</div>
