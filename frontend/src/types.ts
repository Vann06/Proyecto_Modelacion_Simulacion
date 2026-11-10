import type {FeatureCollection} from 'geojson';
export type Row = Record<string, any>;
export type Method = 'RANDOM'|'GREEDY'|'NSGA2'|'MANUAL';
export interface Candidate {site_id:string; patch_id:string; longitude:number; latitude:number; Navn:string;display_name?:string;x_m:number;y_m:number}
export interface Resource {patch_id:string; longitude:number; latitude:number; exclusive_area_m2:number;resource_x_m:number;resource_y_m:number}
export interface Landscape {parks:FeatureCollection;zones:FeatureCollection;resource_geometry:FeatureCollection;candidates:Candidate[];resources:Resource[]}
export interface Trip {date:string;hive_slot:number;site_id:string;patch_id:string;trip_slot:number;departure_min:number;arrival_min:number;foraging_start_min:number|null;foraging_end_min:number|null;return_min:number|null;other_colonies_active_at_foraging_start:number|null;resource_consumed:number;resource_delivered:number;returned:boolean;one_way_distance_m:number}
export interface Day {date:string;patch_ids:string[];initial:number[];final:number[];consumption:number;regeneration:number;stock:number}
export interface Run {kind:string;method:Method;sites:string[];metrics:Record<string,number|null>;per_hive:Row[];trips:Trip[];days:Day[];events:Row[];parameters:Record<string,number|string>;provenance:Row;interpretation:string}
export interface RunOptions {method:Method;K:number;resource_factor:number;alpha:number;beta:number;radius_m:number;regeneration:number;departures:number;demand_mean:number;speed_m_s:number;optimizer_seed:number;replication_id:number;solution_id:string;site_ids:string[]}
export interface QuickSolution {solution_id:string;site_ids:string[];K:number;search_means:{total_resource_obtained:number;mean_distance_m:number};search_metrics:Record<string,number|null>}
export interface QuickResult {job_id:string;label:string;K:number;request:RunOptions;parameters:Record<string,number|string>;solutions:QuickSolution[];engine_version:string;empty_reason:string|null}
export interface QuickJob {job_id:string;status:'starting'|'running'|'completed'|'failed'|'interrupted';generation?:number;generations:number;installations?:number;simulations?:number;max_simulations:number;elapsed_s?:number;front_size?:number;error?:string;result?:QuickResult}
export interface Comparison {summary:Row[];paired:Row[];audit:Row[];nsga_installations:Row[];metadata:Row;history:Row[];front:{solutions:Row[]};changes:Row[]}
export interface Validation {metadata:Row;errors:Row[];flowers:Row[];activity:Row[];dietz:Row[];nina:Row;correspondence:Row[];sources:Row}
export interface Sensitivity {metadata:Row;summary:Row[];paired:Row[];per_hive_summary:Row[]}
