import {describe,it,expect} from 'vitest';
import {tripPosition,stocks} from './visualization';
import {fmt} from './api';
import type {Trip,Run} from './types';
const trip={date:'2017-07-18',departure_min:10,arrival_min:20,foraging_start_min:22,foraging_end_min:25,return_min:35,patch_id:'p',resource_consumed:3} as Trip;
describe('Drawing logged trips without simulating new events',()=>{
 it('is absent before departure and at/after return',()=>{expect(tripPosition(trip,9,[0,0],[10,10])).toBeNull();expect(tripPosition(trip,35,[0,0],[10,10])).toBeNull()});
 it('interpolates outbound, search, foraging and inbound',()=>{expect(tripPosition(trip,15,[0,0],[10,10])?.position).toEqual([5,5]);expect(tripPosition(trip,21,[0,0],[10,10])?.phase).toBe('Búsqueda');expect(tripPosition(trip,23,[0,0],[10,10])?.phase).toBe('Forrajeo');expect(tripPosition(trip,30,[0,0],[10,10])).toEqual({position:[5,5],phase:'Regreso'})});
 it('does not invent a return if it is not in the log',()=>{expect(tripPosition({...trip,foraging_end_min:null,return_min:null},30,[0,0],[10,10])?.position).toEqual([10,10])});
 it('withdraws only at actual foraging start and regenerates at closing',()=>{const run={trips:[trip],days:[{date:trip.date,patch_ids:['p'],initial:[10],final:[9]}],parameters:{day_minutes:600}} as unknown as Run;expect(stocks(run,trip.date,21).p).toBe(10);expect(stocks(run,trip.date,22).p).toBe(7);expect(stocks(run,trip.date,600).p).toBe(9)});
 it('shows undefined metrics without coercing to zero',()=>{expect(fmt(null)).toBe('No definido');expect(fmt(Number.NaN)).toBe('No definido');expect(fmt(0)).toBe('0')});
});
