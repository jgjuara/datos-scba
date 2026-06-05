<script lang="ts">
	import { db } from '$lib/data/loader.svelte';
	import { calculateMetrics } from '$lib/data/metrics';
	import LineChart from '$lib/charts/LineChart.svelte';
	import { Scale, CheckCircle2, TrendingUp, FileText, XSquare, Plus, Check } from '@lucide/svelte';

	// Preselected seats to show on load
	let selectedSeats: string[] = $state(['LA PLATA', 'SAN ISIDRO']);

	// List of available colors for selected seats (up to 6 colors) with contrast >= 7:1 on #F8F6F1
	const colorPalette = ['#4338ca', '#0f5132', '#78350f', '#991b1b', '#9d174d', '#581c87'];

	function toggleSeat(name: string) {
		if (selectedSeats.includes(name)) {
			// Don't allow empty selection to avoid empty charts
			if (selectedSeats.length > 1) {
				selectedSeats = selectedSeats.filter((s) => s !== name);
			}
		} else {
			// Limit to maximum of 6 seats for readability
			if (selectedSeats.length < 6) {
				selectedSeats = [...selectedSeats, name];
			}
		}
	}

	// Dynamic color mapping for selected seats
	const seatColorMap = $derived.by(() => {
		const map = new Map<string, string>();
		selectedSeats.forEach((seat, index) => {
			map.set(seat, colorPalette[index % colorPalette.length]);
		});
		return map;
	});

	// Get data for selected seats grouped by year
	const performanceBySeatAndYear = $derived.by(() => {
		const map = new Map<string, Array<{ anio: number; ingresadas: number; resueltas: number; tasaResolucion: number; tasaSentencia: number; tasaCaducidad: number }>>();

		for (const seat of selectedSeats) {
			const seatRecs = db.records.filter((r) => r.sede === seat).sort((a, b) => a.anio - b.anio);
			const yearDetails = seatRecs.map((r) => {
				const metrics = calculateMetrics(r);
				return {
					anio: r.anio,
					ingresadas: r.ingresadas,
					resueltas: r.totalResueltas,
					tasaResolucion: metrics.tasaResolucion,
					tasaSentencia: metrics.tasaSentencia,
					tasaCaducidad: metrics.tasaCaducidad
				};
			});
			map.set(seat, yearDetails);
		}

		return map;
	});

	// Generate chart series for Ingresadas
	const seriesIngresadas = $derived(
		selectedSeats.map((seat) => ({
			name: seat,
			data: (performanceBySeatAndYear.get(seat) || []).map((p) => ({ x: p.anio, y: p.ingresadas })),
			color: seatColorMap.get(seat) || '#ccc'
		}))
	);

	// Generate chart series for Resueltas
	const seriesResueltas = $derived(
		selectedSeats.map((seat) => ({
			name: seat,
			data: (performanceBySeatAndYear.get(seat) || []).map((p) => ({ x: p.anio, y: p.resueltas })),
			color: seatColorMap.get(seat) || '#ccc'
		}))
	);

	// Generate chart series for Tasa de Resolución
	const seriesTasaResolucion = $derived(
		selectedSeats.map((seat) => ({
			name: seat,
			data: (performanceBySeatAndYear.get(seat) || []).map((p) => ({ x: p.anio, y: p.tasaResolucion })),
			color: seatColorMap.get(seat) || '#ccc'
		}))
	);

	// Generate chart series for Tasa de Sentencia
	const seriesTasaSentencia = $derived(
		selectedSeats.map((seat) => ({
			name: seat,
			data: (performanceBySeatAndYear.get(seat) || []).map((p) => ({ x: p.anio, y: p.tasaSentencia })),
			color: seatColorMap.get(seat) || '#ccc'
		}))
	);

	// Generate chart series for Tasa de Caducidad
	const seriesTasaCaducidad = $derived(
		selectedSeats.map((seat) => ({
			name: seat,
			data: (performanceBySeatAndYear.get(seat) || []).map((p) => ({ x: p.anio, y: p.tasaCaducidad })),
			color: seatColorMap.get(seat) || '#ccc'
		}))
	);

	const formatPercent = (v: number) => (v * 100).toFixed(1) + '%';
</script>

<div class="space-y-8">
	<!-- Top Bar -->
	<div>
		<h2 class="text-2xl font-bold text-brand-text tracking-tight">Comparador Simultáneo de Sedes</h2>
		<p class="text-xs text-brand-text-muted mt-1">Selecciona hasta 6 sedes en la grilla para superponer y contrastar sus indicadores históricos.</p>
	</div>

	<!-- Selector Panel -->
	<div class="glass-panel p-5 rounded-2xl border border-brand-border space-y-4">
		<div class="flex items-center justify-between">
			<h3 class="text-xs font-bold uppercase tracking-wider text-brand-text-muted">Sedes Seleccionadas ({selectedSeats.length}/6)</h3>
			{#if selectedSeats.length === 6}
				<span class="text-[10px] text-brand-warning font-bold uppercase">Límite máximo alcanzado</span>
			{/if}
		</div>

		<!-- Chips List grid -->
		<div class="flex flex-wrap gap-2">
			{#each db.sedes as name}
				{@const isSelected = selectedSeats.includes(name)}
				{@const color = seatColorMap.get(name)}
				<button
					onclick={() => toggleSeat(name)}
					class="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-semibold tracking-wide transition-all focus:outline-none {isSelected ? 'border-transparent text-white font-bold' : 'border-brand-border text-brand-text-muted hover:text-brand-text hover:border-brand-indigo/30 bg-white hover:bg-stone-50'}"
					style={isSelected ? `background-color: ${color}` : ''}
				>
					{#if isSelected}
						<Check class="w-3.5 h-3.5" />
					{:else}
						<Plus class="w-3.5 h-3.5" />
					{/if}
					{name}
				</button>
			{/each}
		</div>
	</div>

	<!-- Multi-Chart comparative Grid -->
	<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
		<!-- Chart 1: Ingresadas -->
		<div class="glass-panel p-6 rounded-3xl border border-brand-border h-[380px] flex flex-col justify-between">
			<LineChart
				series={seriesIngresadas}
				title="Comparativa: Causas Ingresadas"
			/>
		</div>

		<!-- Chart 2: Resueltas -->
		<div class="glass-panel p-6 rounded-3xl border border-brand-border h-[380px] flex flex-col justify-between">
			<LineChart
				series={seriesResueltas}
				title="Comparativa: Causas Resueltas"
			/>
		</div>

		<!-- Chart 3: Tasa de Resolución -->
		<div class="glass-panel p-6 rounded-3xl border border-brand-border h-[380px] flex flex-col justify-between">
			<LineChart
				series={seriesTasaResolucion}
				title="Comparativa: Tasa de Resolución"
				formatY={formatPercent}
			/>
		</div>

		<!-- Chart 4: Tasa de Sentencia -->
		<div class="glass-panel p-6 rounded-3xl border border-brand-border h-[380px] flex flex-col justify-between">
			<LineChart
				series={seriesTasaSentencia}
				title="Comparativa: Tasa de Sentencia"
				formatY={formatPercent}
			/>
		</div>

		<!-- Chart 5: Tasa de Caducidad -->
		<div class="glass-panel p-6 rounded-3xl border border-brand-border h-[380px] flex flex-col justify-between lg:col-span-2">
			<LineChart
				series={seriesTasaCaducidad}
				title="Comparativa: Tasa de Caducidad"
				formatY={formatPercent}
			/>
		</div>
	</div>
</div>
