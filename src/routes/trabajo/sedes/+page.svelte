<script lang="ts">
	import { resolve } from "$app/paths";
	import { db } from "$lib/data/loader.svelte";
	import { calculateMetrics, aggregateRecords } from "$lib/data/metrics";
	import Filters from "$lib/components/Filters.svelte";
	import DataTable from "$lib/components/DataTable.svelte";
	import type { TableRow } from "$lib/components/DataTable.svelte";
	import ScatterChart from "$lib/charts/ScatterChart.svelte";
	import type { ScatterPoint } from "$lib/charts/ScatterChart.svelte";
	import LineChart from "$lib/charts/LineChart.svelte";
	import AreaChart from "$lib/charts/AreaChart.svelte";
	import SearchableMultiSelect from "$lib/components/SearchableMultiSelect.svelte";
	import {
		TrendingUp,
		FileText,
		XSquare,
		AlertCircle,
		Plus,
		Check,
		X,
	} from "@lucide/svelte";

	// Year filter
	let selectedRange = $state<[number, number]>([2017, 2025]);
	let initialized = false;
	$effect(() => {
		if (!initialized && db.anios.length > 0) {
			selectedRange = [db.anios[0], db.anios[db.anios.length - 1]];
			initialized = true;
		}
	});

	// Aggregate data per seat for the selected year filter
	const seatRows = $derived.by(() => {
		const result: TableRow[] = [];

		for (const sede of db.sedes) {
			const seatRecords = db.records.filter((r) => {
				const matchesSede = r.sede === sede;
				const matchesYear =
					r.anio >= selectedRange[0] && r.anio <= selectedRange[1];
				return matchesSede && matchesYear;
			});

			if (seatRecords.length === 0) continue;

			// Aggregate records (if 'todos' we sum across years)
			const aggregated = aggregateRecords(seatRecords);
			const metrics = calculateMetrics(aggregated);

			result.push({
				id: sede,
				name: sede,
				ingresadas: aggregated.ingresadas,
				resueltas: aggregated.totalResueltas,
				tasaResolucion: metrics.tasaResolucion,
				tasaSentencia: metrics.tasaSentencia,
				tasaCaducidad: metrics.tasaCaducidad,
			});
		}

		return result;
	});

	// Map seat rows for scatter chart
	const scatterPoints = $derived(
		seatRows.map((row) => ({
			x: row.ingresadas,
			y: row.tasaResolucion,
			size: row.resueltas,
			label: row.name,
			color:
				row.tasaResolucion >= 1.0
					? "rgba(15, 81, 50, 0.7)"
					: "rgba(67, 56, 202, 0.7)",
		})),
	);

	// Helper to extract rankings
	function getRankings(
		rows: TableRow[],
		key: "tasaResolucion" | "tasaSentencia" | "tasaCaducidad",
		count = 5,
	) {
		const sorted = [...rows].sort((a, b) => b[key] - a[key]);

		const top = sorted.slice(0, count);
		// Filter out items with 0 resolves to avoid skewed bottom lists
		const validForBottom = sorted.filter((r) => r.resueltas > 0);
		const bottom = [...validForBottom].reverse().slice(0, count);

		return { top, bottom };
	}

	const rankResolucion = $derived(getRankings(seatRows, "tasaResolucion"));
	const rankSentencia = $derived(getRankings(seatRows, "tasaSentencia"));
	const rankCaducidad = $derived(getRankings(seatRows, "tasaCaducidad"));

	// Comparator state
	let selectedSeats = $state(["LA PLATA", "SAN ISIDRO"]);
	const colorPalette = [
		"#4338ca",
		"#0f5132",
		"#78350f",
		"#991b1b",
		"#9d174d",
		"#581c87",
	];

	const seatColorMap = $derived.by(() => {
		const map = new Map<string, string>();
		selectedSeats.forEach((seat, index) => {
			map.set(seat, colorPalette[index % colorPalette.length]);
		});
		return map;
	});

	// Get data for selected seats grouped by year, filtered by selectedRange
	const performanceBySeatAndYear = $derived.by(() => {
		const map = new Map<
			string,
			Array<{
				anio: number;
				ingresadas: number;
				resueltas: number;
				tasaResolucion: number;
				tasaSentencia: number;
				tasaCaducidad: number;
			}>
		>();

		for (const seat of selectedSeats) {
			const seatRecs = db.records
				.filter((r) => {
					const matchesSede = r.sede === seat;
					const matchesYear =
						r.anio >= selectedRange[0] &&
						r.anio <= selectedRange[1];
					return matchesSede && matchesYear;
				})
				.sort((a, b) => a.anio - b.anio);

			const yearDetails = seatRecs.map((r) => {
				const metrics = calculateMetrics(r);
				return {
					anio: r.anio,
					ingresadas: r.ingresadas,
					resueltas: r.totalResueltas,
					tasaResolucion: metrics.tasaResolucion,
					tasaSentencia: metrics.tasaSentencia,
					tasaCaducidad: metrics.tasaCaducidad,
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
			data: (performanceBySeatAndYear.get(seat) || []).map((p) => ({
				x: p.anio,
				y: p.ingresadas,
			})),
			color: seatColorMap.get(seat) || "#ccc",
		})),
	);

	// Generate chart series for Resueltas
	const seriesResueltas = $derived(
		selectedSeats.map((seat) => ({
			name: seat,
			data: (performanceBySeatAndYear.get(seat) || []).map((p) => ({
				x: p.anio,
				y: p.resueltas,
			})),
			color: seatColorMap.get(seat) || "#ccc",
		})),
	);

	// Generate chart series for Tasa de Resolución
	const seriesTasaResolucion = $derived(
		selectedSeats.map((seat) => ({
			name: seat,
			data: (performanceBySeatAndYear.get(seat) || []).map((p) => ({
				x: p.anio,
				y: p.tasaResolucion,
			})),
			color: seatColorMap.get(seat) || "#ccc",
		})),
	);

	// Generate chart series for Tasa de Sentencia
	const seriesTasaSentencia = $derived(
		selectedSeats.map((seat) => ({
			name: seat,
			data: (performanceBySeatAndYear.get(seat) || []).map((p) => ({
				x: p.anio,
				y: p.tasaSentencia,
			})),
			color: seatColorMap.get(seat) || "#ccc",
		})),
	);

	// Generate chart series for Tasa de Caducidad
	const seriesTasaCaducidad = $derived(
		selectedSeats.map((seat) => ({
			name: seat,
			data: (performanceBySeatAndYear.get(seat) || []).map((p) => ({
				x: p.anio,
				y: p.tasaCaducidad,
			})),
			color: seatColorMap.get(seat) || "#ccc",
		})),
	);

	const allSedesColorObject = $derived.by(() => {
		const obj: { [key: string]: string } = {};
		const palette = [
			"#4338ca",
			"#0f5132",
			"#78350f",
			"#991b1b",
			"#9d174d",
			"#581c87",
			"#2563eb",
			"#16a34a",
			"#ca8a04",
			"#dc2626",
			"#db2777",
			"#7c3aed",
			"#0284c7",
			"#0d9488",
			"#ea580c",
			"#e11d48",
			"#4b5563",
			"#0891b2",
		];
		db.sedes.forEach((seat, index) => {
			obj[seat] = palette[index % palette.length];
		});
		return obj;
	});

	// Generate data for AreaChart of all seats: Ingresadas
	const areaDataIngresadasAll = $derived.by(() => {
		const list: Array<{ anio: number; [key: string]: number }> = [];
		const minYear = selectedRange[0];
		const maxYear = selectedRange[1];

		for (let yr = minYear; yr <= maxYear; yr++) {
			const row: { anio: number; [key: string]: number } = { anio: yr };
			db.sedes.forEach((seat) => {
				row[seat] = 0;
			});
			const yearRecs = db.records.filter((r) => r.anio === yr);
			yearRecs.forEach((r) => {
				if (row[r.sede] !== undefined) {
					row[r.sede] += r.ingresadas;
				}
			});
			list.push(row);
		}
		return list;
	});

	// Generate data for AreaChart of all seats: Resueltas
	const areaDataResueltasAll = $derived.by(() => {
		const list: Array<{ anio: number; [key: string]: number }> = [];
		const minYear = selectedRange[0];
		const maxYear = selectedRange[1];

		for (let yr = minYear; yr <= maxYear; yr++) {
			const row: { anio: number; [key: string]: number } = { anio: yr };
			db.sedes.forEach((seat) => {
				row[seat] = 0;
			});
			const yearRecs = db.records.filter((r) => r.anio === yr);
			yearRecs.forEach((r) => {
				if (row[r.sede] !== undefined) {
					row[r.sede] += r.totalResueltas;
				}
			});
			list.push(row);
		}
		return list;
	});

	const formatPercent = (v: number) => (v * 100).toFixed(1) + "%";
	const formatInt = (v: number) => v.toLocaleString("es-AR");
</script>

<div class="space-y-8">
	<!-- Top Bar -->
	<div
		class="flex flex-col md:flex-row md:items-center justify-between gap-4"
	>
		<div>
			<h2 class="text-2xl font-bold text-brand-text tracking-tight">
				Sedes judiciales - Trabajo
			</h2>
			<p class="text-xs text-brand-text-muted mt-1">
				Compare volumen de causas, tasa de resolución y modos de cierre entre departamentos y sedes.
			</p>
		</div>

		<!-- Filters -->
		<Filters years={db.anios} bind:selectedRange />
	</div>

	<!-- Scatter plot section -->
	<div class="grid grid-cols-1 gap-6">
		<div
			class="glass-panel p-6 rounded-3xl border border-brand-border min-h-[430px] flex flex-col justify-between"
		>
			<ScatterChart
				data={scatterPoints}
				title="Relación entre causas ingresadas y tasa de resolución"
				xLabel="Causas Ingresadas"
				yLabel="Tasa de Resolución"
				formatY={formatPercent}
			/>
		</div>
	</div>

	<!-- Stacked Area Charts Section 
	<div class="space-y-4">
		<div>
			<h3 class="text-lg font-bold text-brand-text">Distribución Acumulada de Causas por Sede</h3>
			<p class="text-xs text-brand-text-muted mt-1">Evolución de la carga ingresada y resuelta acumulada para la totalidad de las sedes.</p>
		</div>

		<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
			<div class="glass-panel p-6 rounded-3xl border border-brand-border min-h-[380px] flex flex-col justify-between">
				<AreaChart
					data={areaDataIngresadasAll}
					keys={db.sedes}
					colors={allSedesColorObject}
					title="Causas Ingresadas por Sede (Acumulado)"
					formatY={formatInt}
				/>
			</div>

			<div class="glass-panel p-6 rounded-3xl border border-brand-border min-h-[380px] flex flex-col justify-between">
				<AreaChart
					data={areaDataResueltasAll}
					keys={db.sedes}
					colors={allSedesColorObject}
					title="Causas Resueltas por Sede (Acumulado)"
					formatY={formatInt}
				/>
			</div>
		</div>
	</div>
	-->

	<!-- Data Table Section -->
	<div class="space-y-4">
		<div>
			<h3 class="text-lg font-bold text-brand-text">
				Tabla Comparativa General
			</h3>
			<p class="text-xs text-brand-text-muted mt-1">
				Ordene por columna o busque una sede específica.
			</p>
		</div>

		<DataTable data={seatRows} />
	</div>

	<!-- Rankings Grid -->
	<div class="space-y-6 pt-4 border-t border-brand-border">
		<div>
			<h3 class="text-lg font-bold text-brand-text">
				Rankings de Desempeño y Caducidad
			</h3>
			<p class="text-xs text-brand-text-muted mt-1">
				Sedes con mayores y menores valores en cada indicador. La muestra presenta cinco casos por grupo.
			</p>
		</div>

		<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
			<!-- Tasa de Resolución Ranking -->
			<div
				class="glass-panel p-5 rounded-2xl border border-brand-border flex flex-col gap-4"
			>
				<div
					class="flex items-center gap-2 border-b border-brand-border pb-3"
				>
					<TrendingUp class="w-5 h-5 text-brand-indigo" />
					<h4 class="text-sm font-bold text-brand-text">
						Tasa de Resolución
					</h4>
				</div>

				<div class="space-y-4">
					<!-- Top 5 -->
					<div>
						<h5
							class="text-xs font-bold text-brand-success uppercase tracking-wider mb-2"
						>
							Top 5
						</h5>
						<div class="space-y-1.5">
							{#each rankResolucion.top as item, i (item.id)}
								<div
									class="flex items-center justify-between text-xs py-1 px-2 rounded-lg bg-white border border-brand-border"
								>
									<span
										class="truncate max-w-[130px] text-brand-text-muted"
									>
										<a
											href={resolve(`/trabajo/sede?id=${encodeURIComponent(item.id)}`)}
											class="hover:text-brand-indigo transition font-medium font-sans"
										>
											{i + 1}. {item.name}
										</a>
									</span>
									<span
										class="font-mono font-bold text-brand-success"
										>{formatPercent(
											item.tasaResolucion,
										)}</span
									>
								</div>
							{/each}
						</div>
					</div>

					<!-- Bottom 5 -->
					<div>
						<h5
							class="text-xs font-bold text-brand-danger uppercase tracking-wider mb-2 font-sans"
						>
							Bottom 5
						</h5>
						<div class="space-y-1.5">
							{#each rankResolucion.bottom as item, i (item.id)}
								<div
									class="flex items-center justify-between text-xs py-1 px-2 rounded-lg bg-white border border-brand-border"
								>
									<span
										class="truncate max-w-[130px] text-brand-text-muted"
									>
										<a
											href={resolve(`/trabajo/sede?id=${encodeURIComponent(item.id)}`)}
											class="hover:text-brand-indigo transition font-medium font-sans"
										>
											{i + 1}. {item.name}
										</a>
									</span>
									<span
										class="font-mono font-bold text-brand-danger"
										>{formatPercent(
											item.tasaResolucion,
										)}</span
									>
								</div>
							{/each}
						</div>
					</div>
				</div>
			</div>

			<!-- Tasa de Sentencia Ranking -->
			<div
				class="glass-panel p-5 rounded-2xl border border-brand-border flex flex-col gap-4"
			>
				<div
					class="flex items-center gap-2 border-b border-brand-border pb-3"
				>
					<FileText class="w-5 h-5 text-brand-success" />
					<h4 class="text-sm font-bold text-brand-text">
						Tasa de Sentencia
					</h4>
				</div>

				<div class="space-y-4">
					<!-- Top 5 -->
					<div>
						<h5
							class="text-xs font-bold text-brand-success uppercase tracking-wider mb-2"
						>
							Top 5
						</h5>
						<div class="space-y-1.5">
							{#each rankSentencia.top as item, i (item.id)}
								<div
									class="flex items-center justify-between text-xs py-1 px-2 rounded-lg bg-white border border-brand-border"
								>
									<span
										class="truncate max-w-[130px] text-brand-text-muted"
									>
										<a
											href={resolve(`/trabajo/sede?id=${encodeURIComponent(item.id)}`)}
											class="hover:text-brand-indigo transition font-medium font-sans"
										>
											{i + 1}. {item.name}
										</a>
									</span>
									<span
										class="font-mono font-bold text-brand-success"
										>{formatPercent(
											item.tasaSentencia,
										)}</span
									>
								</div>
							{/each}
						</div>
					</div>

					<!-- Bottom 5 -->
					<div>
						<h5
							class="text-xs font-bold text-brand-danger uppercase tracking-wider mb-2 font-sans"
						>
							Bottom 5
						</h5>
						<div class="space-y-1.5">
							{#each rankSentencia.bottom as item, i (item.id)}
								<div
									class="flex items-center justify-between text-xs py-1 px-2 rounded-lg bg-white border border-brand-border"
								>
									<span
										class="truncate max-w-[130px] text-brand-text-muted"
									>
										<a
											href={resolve(`/trabajo/sede?id=${encodeURIComponent(item.id)}`)}
											class="hover:text-brand-indigo transition font-medium font-sans"
										>
											{i + 1}. {item.name}
										</a>
									</span>
									<span
										class="font-mono font-bold text-brand-danger"
										>{formatPercent(
											item.tasaSentencia,
										)}</span
									>
								</div>
							{/each}
						</div>
					</div>
				</div>
			</div>

			<!-- Tasa de Caducidad Ranking -->
			<div
				class="glass-panel p-5 rounded-2xl border border-brand-border flex flex-col gap-4"
			>
				<div
					class="flex items-center gap-2 border-b border-brand-border pb-3"
				>
					<XSquare class="w-5 h-5 text-brand-danger" />
					<h4 class="text-sm font-bold text-brand-text">
						Tasa de Caducidad
					</h4>
				</div>

				<div class="space-y-4">
					<!-- Top 5 (Peor caducidad, es decir, mayor tasa) -->
					<div>
						<h5
							class="text-xs font-bold text-brand-danger uppercase tracking-wider mb-2"
						>
							Mayor Caducidad
						</h5>
						<div class="space-y-1.5">
							{#each rankCaducidad.top as item, i (item.id)}
								<div
									class="flex items-center justify-between text-xs py-1 px-2 rounded-lg bg-white border border-brand-danger/20 border-dashed"
								>
									<span
										class="truncate max-w-[130px] text-brand-text-muted"
									>
										<a
											href={resolve(`/trabajo/sede?id=${encodeURIComponent(item.id)}`)}
											class="hover:text-brand-indigo transition font-medium font-sans"
										>
											{i + 1}. {item.name}
										</a>
									</span>
									<span
										class="font-mono font-bold text-brand-danger"
										>{formatPercent(
											item.tasaCaducidad,
										)}</span
									>
								</div>
							{/each}
						</div>
					</div>

					<!-- Bottom 5 (Menor caducidad, menor tasa) -->
					<div>
						<h5
							class="text-xs font-bold text-brand-success uppercase tracking-wider mb-2 font-sans"
						>
							Menor Caducidad
						</h5>
						<div class="space-y-1.5">
							{#each rankCaducidad.bottom as item, i (item.id)}
								<div
									class="flex items-center justify-between text-xs py-1 px-2 rounded-lg bg-white border border-brand-success/20 border-dashed"
								>
									<span
										class="truncate max-w-[130px] text-brand-text-muted"
									>
										<a
											href={resolve(`/trabajo/sede?id=${encodeURIComponent(item.id)}`)}
											class="hover:text-brand-indigo transition font-medium font-sans"
										>
											{i + 1}. {item.name}
										</a>
									</span>
									<span
										class="font-mono font-bold text-brand-success"
										>{formatPercent(
											item.tasaCaducidad,
										)}</span
									>
								</div>
							{/each}
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>

	<!-- Comparator Section -->
	<div class="space-y-6 pt-6 border-t border-brand-border">
		<div>
			<h3 class="text-lg font-bold text-brand-text">
				Comparador Simultáneo de Sedes
			</h3>
			<p class="text-xs text-brand-text-muted mt-1">
				Seleccione hasta 6 sedes para superponer y contrastar sus
				indicadores históricos para el período seleccionado.
			</p>
		</div>

		<!-- Selector Panel -->
		<div
			class="glass-panel p-5 rounded-2xl border border-brand-border space-y-4"
		>
			<div class="flex flex-col gap-4">
				<div class="space-y-1">
					<h4
						class="text-xs font-bold text-brand-text uppercase tracking-wider"
					>
						Buscador de Sedes
					</h4>
					<p class="text-[11px] text-brand-text-muted">
						Elija las sedes que quiere incorporar a las comparativas.
					</p>
				</div>
				<div class="flex flex-wrap items-center gap-4">
					<SearchableMultiSelect
						options={db.sedes}
						bind:selected={selectedSeats}
						maxSelected={6}
						placeholder="Buscar y agregar sedes..."
					/>

					<!-- Selected Chips -->
					<div class="flex flex-wrap gap-2">
						{#each selectedSeats as name (name)}
							{@const color = seatColorMap.get(name)}
							<div
								class="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-transparent text-xs font-semibold tracking-wide text-white transition-all shadow-sm"
								style="background-color: {color}"
							>
								<span>{name}</span>
								{#if selectedSeats.length > 1}
									<button
										type="button"
										onclick={() => {
											selectedSeats =
												selectedSeats.filter(
													(s) => s !== name,
												);
										}}
										class="hover:bg-white/20 rounded-md p-0.5 transition focus:outline-none cursor-pointer"
										aria-label="Eliminar {name}"
									>
										<X class="w-3 h-3" />
									</button>
								{/if}
							</div>
						{/each}
					</div>
				</div>
			</div>
		</div>

		<!-- Multi-Chart comparative Grid -->
		<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
			<!-- Chart 1: Ingresadas -->
			<div
				class="glass-panel p-6 rounded-3xl border border-brand-border min-h-[380px] flex flex-col justify-between"
			>
				<LineChart
					series={seriesIngresadas}
					title="Comparativa: Causas Ingresadas"
				/>
			</div>

			<!-- Chart 2: Resueltas -->
			<div
				class="glass-panel p-6 rounded-3xl border border-brand-border min-h-[380px] flex flex-col justify-between"
			>
				<LineChart
					series={seriesResueltas}
					title="Comparativa: Causas Resueltas"
				/>
			</div>

			<!-- Chart 3: Tasa de Resolución -->
			<div
				class="glass-panel p-6 rounded-3xl border border-brand-border min-h-[380px] flex flex-col justify-between"
			>
				<LineChart
					series={seriesTasaResolucion}
					title="Comparativa: Tasa de Resolución"
					formatY={formatPercent}
				/>
			</div>

			<!-- Chart 4: Tasa de Sentencia -->
			<div
				class="glass-panel p-6 rounded-3xl border border-brand-border min-h-[380px] flex flex-col justify-between"
			>
				<LineChart
					series={seriesTasaSentencia}
					title="Comparativa: Tasa de Sentencia"
					formatY={formatPercent}
				/>
			</div>

			<!-- Chart 5: Tasa de Caducidad -->
			<div
				class="glass-panel p-6 rounded-3xl border border-brand-border min-h-[380px] flex flex-col justify-between lg:col-span-2"
			>
				<LineChart
					series={seriesTasaCaducidad}
					title="Comparativa: Tasa de Caducidad"
					formatY={formatPercent}
				/>
			</div>
		</div>
	</div>
</div>
