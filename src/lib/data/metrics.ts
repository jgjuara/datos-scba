import type { CourtRecord } from './loader.svelte';

export interface CalculatedMetrics {
	ingresadas: number;
	resueltas: number;
	tasaResolucion: number;      // Resueltas / Ingresadas
	brechaAnual: number;         // Ingresadas - Resueltas
	tasaSentencia: number;        // Sentencia / Resueltas
	tasaConciliacion: number;     // Conciliación / Resueltas
	tasaTerminacionAlt: number;   // (Conciliación + Allanamiento + Transacción) / Resueltas
	indexResolucionSust: number;  // (Sentencia + Conciliación + Transacción) / Resueltas
	tasaCaducidad: number;        // Caducidad / Resueltas
	tasaDesistimiento: number;    // Desistimiento / Resueltas
	tasaIncompetencia: number;    // Incompetencia / Resueltas
	indexTerminacionProc: number; // (Caducidad + Desistimiento + Incompetencia) / Resueltas
	tasaSentenciaEfectiva: number; // Sentencia / (Resueltas - Caducidad)
}

/**
 * Calculates metrics for a single combined CourtRecord.
 * Safe division is implemented to prevent NaN and Infinity values.
 */
export function calculateMetrics(record: CourtRecord): CalculatedMetrics {
	const resueltas = record.totalResueltas;
	const ingresadas = record.ingresadas;

	const safeDiv = (num: number, den: number): number => {
		return den === 0 ? 0 : num / den;
	};

	const terminacionAltNum = record.conciliacion + record.allanamiento + record.transaccion;
	const resolucionSustNum = record.sentencia + record.conciliacion + record.transaccion;
	const terminacionProcNum = record.caducidad + record.desistimiento + record.incompetencia;
	const resueltasMenosCaducidad = resueltas - record.caducidad;

	return {
		ingresadas,
		resueltas,
		tasaResolucion: safeDiv(resueltas, ingresadas),
		brechaAnual: ingresadas - resueltas,
		tasaSentencia: safeDiv(record.sentencia, resueltas),
		tasaConciliacion: safeDiv(record.conciliacion, resueltas),
		tasaTerminacionAlt: safeDiv(terminacionAltNum, resueltas),
		indexResolucionSust: safeDiv(resolucionSustNum, resueltas),
		tasaCaducidad: safeDiv(record.caducidad, resueltas),
		tasaDesistimiento: safeDiv(record.desistimiento, resueltas),
		tasaIncompetencia: safeDiv(record.incompetencia, resueltas),
		indexTerminacionProc: safeDiv(terminacionProcNum, resueltas),
		tasaSentenciaEfectiva: safeDiv(record.sentencia, resueltasMenosCaducidad)
	};
}

/**
 * Aggregates a list of CourtRecord rows into a single virtual CourtRecord.
 */
export function aggregateRecords(records: CourtRecord[]): CourtRecord {
	const aggregate: CourtRecord = {
		anio: 0,
		sede: 'AGREGADO',
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

	for (const r of records) {
		aggregate.ingresadas += r.ingresadas;
		aggregate.sentencia += r.sentencia;
		aggregate.conciliacion += r.conciliacion;
		aggregate.allanamiento += r.allanamiento;
		aggregate.transaccion += r.transaccion;
		aggregate.caducidad += r.caducidad;
		aggregate.desistimiento += r.desistimiento;
		aggregate.interlocutorios += r.interlocutorios;
		aggregate.incompetencia += r.incompetencia;
		aggregate.totalResueltas += r.totalResueltas;
	}

	return aggregate;
}

/**
 * Calculates aggregated metrics directly from a list of records.
 */
export function calculateAggregatedMetrics(records: CourtRecord[]): CalculatedMetrics {
	const aggregatedRecord = aggregateRecords(records);
	return calculateMetrics(aggregatedRecord);
}
