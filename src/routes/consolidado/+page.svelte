<script lang="ts">
	import { db } from "$lib/data/loader.svelte";
	import { calculateAggregatedMetrics } from "$lib/data/metrics";
	import type { CourtRecord } from "$lib/data/loader.svelte";
	import KPI from "$lib/components/KPI.svelte";
	import Filters from "$lib/components/Filters.svelte";
	import LineChart from "$lib/charts/LineChart.svelte";
	import AreaChart from "$lib/charts/AreaChart.svelte";
	import {
		Scale,
		FileText,
		TrendingUp,
		XSquare,
		Handshake,
	} from "@lucide/svelte";

	// Filter state
	const selectedFueroFilter = 'ambos';
	let selectedRange = $state<[number, number]>([2017, 2025]);
	let initialized = false;

	$effect(() => {
		if (!initialized && db.consolidatedAnios.length > 0) {
			selectedRange = [db.consolidatedAnios[0], db.consolidatedAnios[db.consolidatedAnios.length - 1]];
			initialized = true;
		}
	});

	// Filter raw records based on selected range and fuero filter
	const filteredRecords = $derived.by(() => {
		return db.consolidatedRecords.filter(
			(r) =>
				r.anio >= selectedRange[0] &&
				r.anio <= selectedRange[1] &&
				(selectedFueroFilter === 'ambos' || r.fuero === selectedFueroFilter)
		);
	});

	// Reconstruct Svelte CourtRecord interface structure grouped by year
	const yearlyCourtRecords = $derived.by(() => {
		const groups: { [anio: number]: CourtRecord } = {};

		for (const r of filteredRecords) {
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

	// Calculated metrics for KPIs in the period
	const kpis = $derived(calculateAggregatedMetrics(yearlyCourtRecords));

	// Last year in range
	const lastYear = $derived(selectedRange[1]);
	const lastYearRecords = $derived.by(() => {
		return yearlyCourtRecords.filter((r) => r.anio === lastYear);
	});
	const lastYearKpis = $derived(calculateAggregatedMetrics(lastYearRecords));

	// Data grouped by year for charts
	const yearlyAggr = $derived.by(() => {
		const safeDiv = (num: number, den: number): number =>
			den === 0 ? 0 : num / den;

		return yearlyCourtRecords.map((r) => ({
			anio: r.anio,
			ingresadas: r.ingresadas,
			resueltas: r.totalResueltas,
			tasaResolucion: safeDiv(r.totalResueltas, r.ingresadas),
			brechaAnual: r.ingresadas - r.totalResueltas,
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

	// Data grouped by year and fuero for stacked charts
	const yearlyByFuero = $derived.by(() => {
		const groups: {
			[anio: number]: {
				anio: number;
				ingresadasCivil: number;
				resueltasCivil: number;
				brechaCivil: number;
				ingresadasTrabajo: number;
				resueltasTrabajo: number;
				brechaTrabajo: number;
			};
		} = {};

		const filtered = db.consolidatedRecords.filter(
			(r) => r.anio >= selectedRange[0] && r.anio <= selectedRange[1]
		);

		for (const r of filtered) {
			const anio = r.anio;
			if (!groups[anio]) {
				groups[anio] = {
					anio,
					ingresadasCivil: 0,
					resueltasCivil: 0,
					brechaCivil: 0,
					ingresadasTrabajo: 0,
					resueltasTrabajo: 0,
					brechaTrabajo: 0
				};
			}

			const group = groups[anio];
			const valor = r.valor;

			if (r.fuero === 'civil') {
				if (r.tipo === 'Ingresadas') {
					group.ingresadasCivil += valor;
				} else if (r.tipo === 'Total Resueltas') {
					group.resueltasCivil += valor;
				}
			} else if (r.fuero === 'trabajo') {
				if (r.tipo === 'Ingresadas') {
					group.ingresadasTrabajo += valor;
				} else if (r.tipo === 'Total Resueltas') {
					group.resueltasTrabajo += valor;
				}
			}
		}

		for (const anio in groups) {
			const g = groups[anio];
			g.brechaCivil = g.ingresadasCivil - g.resueltasCivil;
			g.brechaTrabajo = g.ingresadasTrabajo - g.resueltasTrabajo;
		}

		return Object.values(groups).sort((a, b) => a.anio - b.anio);
	});

	const lineSeriesTasaResolucion = $derived([
		{
			name: "Tasa de Resolución (Total)",
			data: yearlyAggr.map((y) => ({ x: y.anio, y: y.tasaResolucion })),
			color: "var(--color-brand-indigo)",
		},
		{
			name: "Tasa de Resolución Civil y Comercial",
			data: yearlyByFuero.map((y) => ({
				x: y.anio,
				y: y.ingresadasCivil === 0 ? 0 : y.resueltasCivil / y.ingresadasCivil
			})),
			color: "var(--color-brand-civil)",
		},
		{
			name: "Tasa de Resolución Trabajo",
			data: yearlyByFuero.map((y) => ({
				x: y.anio,
				y: y.ingresadasTrabajo === 0 ? 0 : y.resueltasTrabajo / y.ingresadasTrabajo
			})),
			color: "var(--color-brand-laboral)",
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

	// State for Composición Histórica chart variety
	let compositionFuero = $state<'ambos' | 'civil' | 'trabajo'>('ambos');

	// Filter records specifically for Composición Histórica based on year and selected variety
	const compositionRecords = $derived.by(() => {
		return db.consolidatedRecords.filter(
			(r) =>
				r.anio >= selectedRange[0] &&
				r.anio <= selectedRange[1] &&
				(compositionFuero === 'ambos' || r.fuero === compositionFuero)
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

	// Formatters
	const formatInt = (v: number) => v.toLocaleString("es-AR");
	const formatPercent = (v: number) => (v * 100).toFixed(1) + "%";

	const ingresadasByFueroData = $derived(
		yearlyByFuero.map((y) => ({
			anio: y.anio,
			"Civil y Comercial": y.ingresadasCivil,
			"Trabajo": y.ingresadasTrabajo
		}))
	);

	const resueltasByFueroData = $derived(
		yearlyByFuero.map((y) => ({
			anio: y.anio,
			"Civil y Comercial": y.resueltasCivil,
			"Trabajo": y.resueltasTrabajo
		}))
	);

	const fueroKeys = ["Civil y Comercial", "Trabajo"];
	const fueroColorsMap = {
		"Civil y Comercial": "var(--color-brand-civil)",
		"Trabajo": "var(--color-brand-laboral)"
	};

	let barChartWidth = $state(600);

	// Tooltip state for gap bar chart
	let activeBarIndex = $state<number | null>(null);
	let barTooltipData = $state<{
		anio: number;
		screenX: number;
		brechaCivil: number;
		brechaTrabajo: number;
		total: number;
	} | null>(null);

	function handleBarMouseMove(event: MouseEvent) {
		const svgElement = event.currentTarget as SVGSVGElement;
		const rect = svgElement.getBoundingClientRect();
		const mouseX = event.clientX - rect.left;

		if (yearlyByFuero.length === 0) return;

		const step = (barChartWidth - 110) / yearlyByFuero.length;
		
		let closestIdx = 0;
		let minDiff = Infinity;
		
		for (let i = 0; i < yearlyByFuero.length; i++) {
			const barX = 70 + i * step;
			const diff = Math.abs(barX - mouseX);
			if (diff < minDiff) {
				minDiff = diff;
				closestIdx = i;
			}
		}

		if (minDiff < step / 2 + 10) {
			activeBarIndex = closestIdx;
			const y = yearlyByFuero[closestIdx];
			barTooltipData = {
				anio: y.anio,
				screenX: 70 + closestIdx * step,
				brechaCivil: y.brechaCivil,
				brechaTrabajo: y.brechaTrabajo,
				total: y.brechaCivil + y.brechaTrabajo
			};
		} else {
			activeBarIndex = null;
			barTooltipData = null;
		}
	}

	function handleBarMouseLeave() {
		activeBarIndex = null;
		barTooltipData = null;
	}
</script>

<div class="space-y-6">
	<!-- Header Dashboard -->
	<div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
		<div>
			<h2 class="text-2xl font-bold text-brand-text tracking-tight">
				Actividad judicial provincial consolidada
			</h2>
			<p class="text-xs text-brand-text-muted mt-1">
				Lectura integrada de causas ingresadas, causas resueltas y modos de cierre para los fueros Civil y Comercial y Trabajo.
			</p>
		</div>

		<!-- Filtros -->
		<div class="flex flex-col sm:flex-row items-start sm:items-center gap-3">
			<Filters years={db.consolidatedAnios} bind:selectedRange />
		</div>
	</div>

	<!-- KPIs Grid -->
	<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
		<KPI
			title="Stock de causas"
			value={formatInt(kpis.ingresadas - kpis.resueltas)}
			icon={Scale}
			variant="indigo"
			subtitle="Ingresadas menos resueltas en el período"
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
		<div class="glass-panel p-6 rounded-3xl border border-brand-border min-h-[400px] flex flex-col justify-between">
			<LineChart
				series={lineSeriesActivity}
				title="Evolución Temporal: Causas Ingresadas vs Resueltas"
			/>
		</div>

		<!-- Custom Yearly Gap Bar Chart Stacked by Fuero -->
		<div
			class="glass-panel p-6 rounded-3xl border border-brand-border min-h-[400px] flex flex-col justify-between"
			bind:clientWidth={barChartWidth}
		>
			<div class="px-2">
				<h5 class="text-sm font-bold text-brand-text">
					Brecha anual por fuero
				</h5>
				<p class="text-[10px] text-brand-text-muted mt-1 leading-normal">
					Diferencia entre causas ingresadas y resueltas. Los valores positivos indican acumulación neta de expedientes.
				</p>
				<!-- Legend for Bar Chart -->
				<div class="flex gap-4 mt-2 text-[10px]">
					<div class="flex items-center gap-1.5">
						<span class="w-3 h-3 rounded bg-[var(--color-brand-civil)] opacity-85"></span>
						<span class="text-brand-text-muted">Civil y Comercial</span>
					</div>
					<div class="flex items-center gap-1.5">
						<span class="w-3 h-3 rounded bg-[var(--color-brand-laboral)] opacity-85"></span>
						<span class="text-brand-text-muted">Trabajo</span>
					</div>
				</div>
			</div>

			<div class="flex-1 mt-4 select-none relative">
				{#if yearlyByFuero.length > 0}
					{@const vals = yearlyByFuero.map((y) => y.brechaCivil + y.brechaTrabajo)}
					{@const rawMax = Math.max(...vals, 0)}
					{@const rawMin = 0}
					{@const maxVal = rawMax === 0 ? 1000 : rawMax}
					{@const minVal = 0}
					{@const height = 240}
					{@const paddingY = 20}
					{@const chartH = height - paddingY * 2}
					<!-- Scales -->
					{@const xScaleBar = (index: number) => {
						const step = (barChartWidth - 110) / yearlyByFuero.length;
						return 70 + index * step;
					}}
					{@const gapToY = (val: number) =>
						paddingY + (1 - (val - minVal) / (maxVal - minVal)) * chartH}
					{@const zeroY = gapToY(0)}

					<svg
						width={barChartWidth - 30}
						{height}
						role="img"
						aria-label="Brecha anual por fuero"
						class="overflow-visible cursor-crosshair"
						onmousemove={handleBarMouseMove}
						onmouseleave={handleBarMouseLeave}
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

						<!-- Hover interaction guideline -->
						{#if barTooltipData}
							<line
								x1={barTooltipData.screenX}
								y1={paddingY}
								x2={barTooltipData.screenX}
								y2={height - 20}
								stroke="var(--color-brand-border)"
								stroke-width="1.5"
								stroke-dasharray="2 2"
							/>
						{/if}

						<!-- Render Bars -->
						{#each yearlyByFuero as y, i (y.anio)}
							{@const barX = xScaleBar(i)}
							{@const civilH = (y.brechaCivil / (maxVal - minVal)) * chartH}
							{@const trabajoH = (y.brechaTrabajo / (maxVal - minVal)) * chartH}
							{@const totalH = civilH + trabajoH}
							{@const totalVal = y.brechaCivil + y.brechaTrabajo}

							<!-- Civil y Comercial -->
							<rect
								x={barX - 12}
								y={zeroY - civilH}
								width="24"
								height={Math.max(1, civilH)}
								rx="2"
								fill="var(--color-brand-civil)"
								opacity={activeBarIndex === null || activeBarIndex === i ? "0.85" : "0.35"}
								class="transition cursor-pointer"
							/>

							<!-- Trabajo -->
							<rect
								x={barX - 12}
								y={zeroY - civilH - trabajoH}
								width="24"
								height={Math.max(1, trabajoH)}
								rx="2"
								fill="var(--color-brand-laboral)"
								opacity={activeBarIndex === null || activeBarIndex === i ? "0.85" : "0.35"}
								class="transition cursor-pointer"
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

							<!-- Value label -->
							<text
								x={barX}
								y={zeroY - totalH - 6}
								text-anchor="middle"
								class="text-[9px] font-mono font-bold fill-brand-text"
							>
								+{formatInt(totalVal)}
							</text>
						{/each}
					</svg>

					<!-- HTML Hover Tooltip for Gap Chart -->
					{#if barTooltipData}
						<div
							class="absolute z-50 glass-panel px-3 py-3 rounded-2xl border border-brand-border pointer-events-none shadow-2xl flex flex-col gap-2 min-w-[180px]"
							style="left: {barTooltipData.screenX + 15}px; top: 120px; transform: translateY(-50%);"
						>
							<div class="flex justify-between items-center border-b border-brand-border pb-1.5">
								<span class="text-xs font-bold text-brand-text">Brecha {barTooltipData.anio}</span>
								<span class="text-[10px] font-mono text-brand-text-muted">Total: +{formatInt(barTooltipData.total)}</span>
							</div>
							<div class="flex flex-col gap-1.5">
								<div class="flex items-center justify-between text-xs">
									<div class="flex items-center gap-1.5">
										<span class="w-2.5 h-2.5 rounded-sm" style="background-color: var(--color-brand-civil)"></span>
										<span class="text-brand-text-muted">Civil y Comercial</span>
									</div>
									<span class="font-mono font-bold text-brand-text">+{formatInt(barTooltipData.brechaCivil)}</span>
								</div>
								<div class="flex items-center justify-between text-xs">
									<div class="flex items-center gap-1.5">
										<span class="w-2.5 h-2.5 rounded-sm" style="background-color: var(--color-brand-laboral)"></span>
										<span class="text-brand-text-muted">Trabajo</span>
									</div>
									<span class="font-mono font-bold text-brand-text">+{formatInt(barTooltipData.brechaTrabajo)}</span>
								</div>
							</div>
						</div>
					{/if}
				{/if}
			</div>
		</div>
	</div>

	<!-- Row 2: Composition & Gap -->
	<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
		<div class="glass-panel p-6 rounded-3xl border border-brand-border min-h-[400px] flex flex-col justify-between">
			<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 px-2 mb-3">
				<h5 class="text-sm font-bold text-brand-text">
					Composición histórica de resoluciones
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

		<div class="glass-panel p-6 rounded-3xl border border-brand-border min-h-[400px] flex flex-col justify-between">
			<LineChart
				series={lineSeriesTasaResolucion}
				title="Evolución de la Tasa de Resolución"
				formatY={formatPercent}
			/>
		</div>
	</div>

	<!-- Row 3: Stacked Areas by Fuero -->
	<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
		<div class="glass-panel p-6 rounded-3xl border border-brand-border min-h-[400px] flex flex-col justify-between">
			<AreaChart
				data={ingresadasByFueroData}
				keys={fueroKeys}
				colors={fueroColorsMap}
				title="Causas Ingresadas por Fuero"
			/>
		</div>

		<div class="glass-panel p-6 rounded-3xl border border-brand-border min-h-[400px] flex flex-col justify-between">
			<AreaChart
				data={resueltasByFueroData}
				keys={fueroKeys}
				colors={fueroColorsMap}
				title="Causas Resueltas por Fuero"
			/>
		</div>
	</div>
</div>
