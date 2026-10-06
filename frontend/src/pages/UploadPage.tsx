import { useCallback, useState } from 'react';
import { Link } from 'react-router-dom';
import { DatlyLogo } from '../components/DatlyLogo';
import { WaveBackground } from '../components/WaveBackground';
import { UploadZone } from '../components/upload/UploadZone';
import { FileCard } from '../components/upload/FileCard';
import { ProcessingState } from '../components/upload/ProcessingState';
import { DatasetPreview } from '../components/upload/DatasetPreview';
import type { DatasetMeta } from '../components/upload/DatasetPreview';
import { uploadDataset, getSchema } from '../services/api';

// ─── Flow stages ──────────────────────────────────────────────────────────────
type Stage = 'idle' | 'selected' | 'processing' | 'done';



// ─── Page ─────────────────────────────────────────────────────────────────────
export function UploadPage() {
  const [stage, setStage] = useState<Stage>('idle');
  const [file, setFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState<string | undefined>();
  const [meta, setMeta] = useState<DatasetMeta | null>(null);

  const handleFile = useCallback((f: File, err?: string) => {
    setFile(f);
    setFileError(err);
    setStage('selected');
  }, []);

  const handleRemove = useCallback(() => {
    setFile(null);
    setFileError(undefined);
    setStage('idle');
  }, []);

  const handleContinue = useCallback(() => {
    setStage('processing');
  }, []);

  const handleProcessingComplete = useCallback(async () => {
    if (!file) return;
    try {
      const dataset = await uploadDataset(file);
      const schema = await getSchema(dataset.id);
      
      setMeta({
        id: dataset.id,
        name: dataset.name,
        ext: dataset.fileType,
        rows: dataset.rows,
        cols: dataset.columns,
        columns: schema.map(c => c.name),
        preview: [],
      });
      setStage('done');
    } catch (err) {
      setFileError('Failed to process dataset on the server.');
      setStage('selected');
    }
  }, [file]);

  return (
    <div className="min-h-screen w-full flex flex-col bg-[#141414] text-white font-sans overflow-x-hidden relative selection:bg-[#8b5cf6]/30">
      <WaveBackground />

      {/* Navbar */}
      <nav className="w-full flex items-center justify-between py-6 px-6 md:px-12 max-w-7xl mx-auto z-10 relative shrink-0">
        <Link to="/" className="flex items-center scale-[0.35] origin-left -ml-4 md:ml-0 hover:opacity-80 transition-opacity">
          <DatlyLogo reducedMotion={true} />
        </Link>
        <div className="hidden md:flex items-center gap-8 text-sm text-white/60 font-medium absolute left-1/2 -translate-x-1/2">
          <Link to="/" className="hover:text-white transition-colors">Home</Link>
          <Link to="/upload" className="text-white/90">Upload</Link>
        </div>
      </nav>

      {/* Card */}
      <main className="flex-1 flex flex-col items-center justify-center z-10 relative px-4 py-12">
        <div className="w-full max-w-xl">
          {/* Header — hide on done */}
          {stage !== 'done' && (
            <div className="text-center mb-8">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-white/10 bg-white/5 text-white/60 text-xs font-mono tracking-wider mb-5">
                <span className="w-1.5 h-1.5 rounded-full bg-[#f97316]" />
                DATASET UPLOAD
              </div>
              <h1 className="text-3xl md:text-4xl font-semibold text-[#f3f2ee] mb-3 tracking-tight">
                {stage === 'processing' ? 'Processing your data' : 'Upload your data'}
              </h1>
              {stage !== 'processing' && (
                <p className="text-white/40 text-base font-light">
                  Bring your CSV, Excel or JSON file and start asking questions.
                </p>
              )}
            </div>
          )}

          {/* Glassmorphism card */}
          <div className="relative rounded-3xl border border-white/8 bg-white/[0.03] backdrop-blur-sm p-6 md:p-8 shadow-[0_8px_48px_rgba(0,0,0,0.5)]">
            {/* Gradient top edge */}
            <div className="absolute top-0 left-0 right-0 h-px rounded-t-3xl bg-gradient-to-r from-transparent via-[#8b5cf6]/30 to-transparent" />

            {stage === 'idle' && (
              <UploadZone onFile={handleFile} />
            )}

            {stage === 'selected' && file && (
              <FileCard
                file={file}
                error={fileError}
                onRemove={handleRemove}
                onContinue={handleContinue}
              />
            )}

            {stage === 'processing' && (
              <ProcessingState onComplete={handleProcessingComplete} />
            )}

            {stage === 'done' && meta && (
              <DatasetPreview meta={meta} />
            )}

            {/* Gradient bottom edge */}
            <div className="absolute bottom-0 left-0 right-0 h-px rounded-b-3xl bg-gradient-to-r from-transparent via-[#f97316]/20 to-transparent" />
          </div>

          {/* Back link */}
          {stage === 'idle' && (
            <p className="text-center text-white/20 text-sm mt-6">
              <Link to="/" className="hover:text-white/50 transition-colors">← Back to homepage</Link>
            </p>
          )}
        </div>
      </main>
    </div>
  );
}
