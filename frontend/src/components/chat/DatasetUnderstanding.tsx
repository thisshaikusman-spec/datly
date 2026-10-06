import type { Dataset } from '../../lib/datasetParser';
import { DatasetSummary } from './DatasetSummary';
import { SchemaTable } from './SchemaTable';
import { DataQuality } from './DataQuality';
import { DatasetPreviewTable } from './DatasetPreviewTable';


export function DatasetUnderstanding({ dataset }: { dataset: Dataset }) {
  return (
    <div className="flex flex-col gap-4 font-sans max-w-full">
      <DatasetSummary dataset={dataset} />
      <SchemaTable schema={dataset.schema} />
      <DataQuality profile={dataset.profile} />
      <DatasetPreviewTable dataset={dataset} />
      
      <p className="text-white/60 text-sm mt-2">
        DATLY is ready to answer questions about this data.
      </p>
    </div>
  );
}
