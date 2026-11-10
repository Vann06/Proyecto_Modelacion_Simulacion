import {describe,it,expect} from 'vitest';
import {render,screen} from '@testing-library/react';
import {Notice,DownloadCSV,DataTable} from './Common';
describe('Scientific UI',()=>{
 it('keeps limitations visible',()=>{render(<Notice>RU no equivale a néctar</Notice>);expect(screen.getByText('RU no equivale a néctar')).toBeInTheDocument()});
 it('downloads through the API allowlist',()=>{render(<DownloadCSV name="validation"/>);expect(screen.getByRole('link')).toHaveAttribute('href','/api/download/validation')});
 it('does not present missing values as observed zeros',()=>{render(<DataTable rows={[{x:null}]} columns={[{key:'x',label:'Métrica'}]}/>);expect(screen.getByText('No disponible')).toBeInTheDocument()});
});
