import {afterEach,describe,it,expect,vi} from 'vitest';
import {renderHook,act,waitFor,cleanup} from '@testing-library/react';
import {useQuickNsga} from './useQuickNsga';
import type {RunOptions} from './types';
import {api} from './api';
vi.mock('./api',()=>({api:vi.fn()}));
afterEach(()=>{cleanup();vi.clearAllMocks()});
describe('Explicit quick search lifecycle',()=>{
 it('never starts on render, and posts K and scenario values only when requested',async()=>{const options={method:'NSGA2',K:8,resource_factor:1.5,radius_m:1500,optimizer_seed:99} as RunOptions;vi.mocked(api).mockResolvedValue({job_id:'a',status:'completed',generations:5,max_simulations:96});const view=renderHook(()=>useQuickNsga());expect(api).not.toHaveBeenCalled();view.rerender();expect(api).not.toHaveBeenCalled();await act(()=>view.result.current.start(options));expect(api).toHaveBeenCalledWith('quick-nsga2',{...options,optimizer_seed:2026});expect(view.result.current.job?.status).toBe('completed')});
 it('polls a running job and does not start another search when selecting a solution',async()=>{vi.mocked(api).mockResolvedValueOnce({job_id:'a',status:'running',generations:5,max_simulations:96}).mockResolvedValueOnce({job_id:'a',status:'completed',generations:5,max_simulations:96,result:{solutions:[]}});const view=renderHook(()=>useQuickNsga());await act(()=>view.result.current.start({method:'NSGA2',K:3} as RunOptions));await waitFor(()=>expect(view.result.current.job?.status).toBe('completed'),{timeout:2500});act(()=>view.result.current.setSelected('quick_001'));expect(api).toHaveBeenCalledTimes(2);expect(api).toHaveBeenLastCalledWith('quick-nsga2/a');expect(view.result.current.selected).toBe('quick_001')});
});
