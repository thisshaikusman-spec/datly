import type { Dataset, ColumnSchema, DatasetProfile } from '../lib/datasetParser';

export interface JoinSpec {
  left: string;
  right: string;
  left_on: string;
  right_on: string;
  how?: string;
}

export interface VerificationDetails {
  operation?: string;
  dataset?: string;
  datasets_used?: string[];
  joins?: JoinSpec[];
  filters_applied?: any[];
  group_column?: string;
  metric_column?: string;
  aggregation?: string;
  sort?: string;
  limit?: number;
  row_count_before?: number;
  row_count_after?: number;
}

export interface VisualizationSpec {
  type: 'bar' | 'line' | 'scatter' | 'pie' | 'histogram' | 'area' | 'box' | 'table' | 'kpi' | 'none';
  title?: string;
  x?: string;
  y?: string;
  data?: any[];
  // Pie chart
  labels?: string[];
  values?: number[];
  // Histogram
  bins?: number[];
  frequencies?: number[];
  // Box plot
  stats?: {
    min: number;
    q1: number;
    median: number;
    q3: number;
    max: number;
  };
}

export interface ClarificationOption {
  label: string;
  value: string;
}

export interface AnalysisResponse {
  success: boolean;
  answer: string;
  result?: any;
  visualization?: VisualizationSpec;
  visualizations?: VisualizationSpec[];
  verification?: VerificationDetails;
  error?: string;
  language_code?: string;
  clarificationRequired?: boolean;
  clarificationPrompt?: string;
  clarificationOptions?: ClarificationOption[];
}

function resolveApiBase(): string {
  const envUrl = (
    import.meta.env.VITE_API_URL ||
    import.meta.env.VITE_API_BASE_URL ||
    (import.meta.env as any).NEXT_PUBLIC_API_URL ||
    ''
  ).trim();

  if (envUrl) {
    let normalized = envUrl.replace(/\/+$/, '');
    // Upgrade http: to https: when running over https to prevent browser Mixed Content errors
    if (typeof window !== 'undefined' && window.location.protocol === 'https:' && normalized.startsWith('http://')) {
      normalized = normalized.replace(/^http:\/\//i, 'https://');
    }
    if (!normalized.endsWith('/api/v1')) {
      if (normalized.endsWith('/api')) {
        normalized = `${normalized}/v1`;
      } else {
        normalized = `${normalized}/api/v1`;
      }
    }
    return normalized;
  }

  // In production (Vercel) or non-localhost environments, always default to the live Render backend URL
  const isLocalhost = typeof window !== 'undefined' && (
    window.location.hostname === 'localhost' ||
    window.location.hostname === '127.0.0.1' ||
    window.location.hostname === '[::1]'
  );

  if (import.meta.env.PROD || !isLocalhost) {
    return 'https://datly-2v3a.onrender.com/api/v1';
  }

  // In local development, use relative '/api/v1' which is proxied by Vite to localhost:8000
  return '/api/v1';
}

const API_BASE = resolveApiBase();

/**
 * Fetch wrapper with dual-route fallback and retry logic to withstand
 * Render free-tier cold-starts, CORS/firewall restrictions, and momentary connection pauses.
 */
async function fetchWithRetry(url: string, options: RequestInit = {}, retries = 3, delayMs = 1500): Promise<Response> {
  try {
    const res = await fetch(url, options);
    return res;
  } catch (err) {
    // If direct cross-origin request failed and running on Vercel,
    // seamlessly attempt the same-origin reverse-proxy route /api/...
    if (typeof window !== 'undefined' && !url.startsWith('/') && window.location.hostname.endsWith('vercel.app')) {
      try {
        const relativeUrl = url.replace(/^https?:\/\/[^\/]+/, '');
        const proxyRes = await fetch(relativeUrl, options);
        return proxyRes;
      } catch {
        // Fall back to retry loop below
      }
    }
    if (retries > 0) {
      await new Promise(r => setTimeout(r, delayMs));
      return fetchWithRetry(url, options, retries - 1, delayMs * 1.5);
    }
    throw err;
  }
}

export function getStoredWorkspaceId(): string | null {
  try {
    return sessionStorage.getItem('datly_workspace_id') || null;
  } catch {
    return null;
  }
}

export function setStoredWorkspaceId(workspaceId: string): void {
  try {
    sessionStorage.setItem('datly_workspace_id', workspaceId);
  } catch {}
}

export function clearStoredWorkspaceId(): void {
  try {
    sessionStorage.removeItem('datly_workspace_id');
  } catch {}
}

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetchWithRetry(`${API_BASE}/health`, {}, 1, 800);
    return res.ok;
  } catch {
    return false;
  }
}

export async function createWorkspace(): Promise<string> {
  const res = await fetchWithRetry(`${API_BASE}/workspaces`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to create workspace');
  const data = await res.json();
  setStoredWorkspaceId(data.workspace_id);
  return data.workspace_id;
}

export async function listWorkspaceDatasets(workspaceId: string): Promise<Dataset[]> {
  const res = await fetchWithRetry(`${API_BASE}/workspaces/${workspaceId}/datasets`);
  if (!res.ok) throw new Error('Failed to list workspace datasets');
  const items = await res.json();
  return items.map((item: any) => ({
    id: item.id,
    name: item.name,
    alias: item.alias,
    fileType: item.file_type || 'csv',
    rows: item.rows || 0,
    columns: item.columns || 0,
    schema: [],
    profile: { rowCount: item.rows || 0, columnCount: item.columns || 0, missingPercentage: 0, duplicatePercentage: 0 },
    preview: []
  }));
}

export async function deleteWorkspaceDataset(workspaceId: string, datasetId: string): Promise<void> {
  const res = await fetchWithRetry(`${API_BASE}/workspaces/${workspaceId}/datasets/${datasetId}`, {
    method: 'DELETE'
  });
  if (!res.ok) throw new Error('Failed to delete dataset from workspace');
}

export async function uploadDataset(file: File, explicitWorkspaceId?: string): Promise<Dataset> {
  const formData = new FormData();
  formData.append('file', file);
  
  const currentWorkspaceId = explicitWorkspaceId || getStoredWorkspaceId();
  const headers: Record<string, string> = {};
  if (currentWorkspaceId) {
    headers['X-Workspace-Id'] = currentWorkspaceId;
  }

  const res = await fetchWithRetry(`${API_BASE}/datasets/upload`, {
    method: 'POST',
    headers,
    body: formData
  });
  if (!res.ok) throw new Error('Failed to upload dataset');
  const data = await res.json();
  
  // Persist workspace_id and dataset_id in sessionStorage
  if (data.workspace_id) {
    setStoredWorkspaceId(data.workspace_id);
  }
  try {
    sessionStorage.setItem('datly_active_dataset_id', data.dataset_id);
  } catch {}

  // Fetch full details gracefully
  let schema: ColumnSchema[] = [];
  let profile: DatasetProfile = { rowCount: data.rows, columnCount: data.columns, missingPercentage: 0, duplicatePercentage: 0 };
  try {
    schema = await getSchema(data.dataset_id);
  } catch (err) {
    console.warn('Could not fetch schema immediately:', err);
  }
  try {
    profile = await getProfile(data.dataset_id);
  } catch (err) {
    console.warn('Could not fetch profile immediately:', err);
  }
  
  const dataset: Dataset = {
    id: data.dataset_id,
    name: data.filename,
    alias: data.alias || data.filename.split('.')[0],
    fileType: data.file_type,
    rows: data.rows,
    columns: data.columns,
    schema,
    profile,
    preview: []
  };

  try {
    sessionStorage.setItem('datly_active_dataset_meta', JSON.stringify(dataset));
  } catch {}

  return dataset;
}

export async function getDataset(datasetId: string): Promise<Dataset> {
  const res = await fetchWithRetry(`${API_BASE}/datasets/${datasetId}`);
  if (!res.ok) throw new Error('Failed to get dataset');
  const data = await res.json();
  return {
    id: data.dataset_id,
    name: data.filename,
    fileType: data.file_type,
    rows: data.rows,
    columns: data.columns,
    schema: [],
    profile: { rowCount: data.rows, columnCount: data.columns, missingPercentage: 0, duplicatePercentage: 0 },
    preview: []
  };
}

export async function getSchema(datasetId: string): Promise<ColumnSchema[]> {
  const res = await fetchWithRetry(`${API_BASE}/datasets/${datasetId}/schema`);
  if (!res.ok) throw new Error('Failed to get schema');
  const data = await res.json();
  
  return data.column_details.map((col: any) => ({
    name: col.name,
    dataType: col.inferred_type || col.pandas_dtype,
    role: col.semantic_role === 'categorical' ? 'Category' : 
          col.semantic_role === 'numeric_metric' ? 'Numeric' : 
          col.semantic_role === 'numeric_measure' ? 'Numeric' : 
          col.semantic_role === 'datetime' ? 'Date' : 'Text',
    missingCount: col.missing_count
  }));
}

export async function getProfile(datasetId: string): Promise<DatasetProfile> {
  const res = await fetchWithRetry(`${API_BASE}/datasets/${datasetId}/profile`);
  if (!res.ok) throw new Error('Failed to get profile');
  const data = await res.json();
  
  // Calculate total missing percentage across all columns
  let totalMissing = 0;
  data.column_profiles.forEach((p: any) => {
    totalMissing += p.missing_count || 0;
  });
  const missingPercentage = data.rows > 0 ? (totalMissing / (data.rows * data.columns)) : 0;
  
  return {
    rowCount: data.rows,
    columnCount: data.columns,
    missingPercentage: missingPercentage,
    duplicatePercentage: 0 // backend doesn't provide this at dataset level easily
  };
}

// ─── Voice API ───────────────────────────────────────────────────────────────

export interface VoiceAnalysisResponse extends AnalysisResponse {
  transcript?: string;
  audio?: {
    available: boolean;
    audio_url: string | null;
    content_type: string;
  };
}

export interface TranscribeResponse {
  text: string;
  language_code: string;
  transcript?: string;
  success?: boolean;
}

/**
 * Send raw audio bytes to the backend for Speech-to-Text transcription.
 * Returns TranscribeResponse with text and language_code.
 */
export async function transcribeAudio(audioBlob: Blob): Promise<TranscribeResponse> {
  const mimeType = audioBlob.type || 'audio/webm';
  const ext = mimeType.includes('webm') ? 'webm' : mimeType.includes('ogg') ? 'ogg' : 'wav';
  const file = new File([audioBlob], `recording.${ext}`, { type: mimeType });

  const formData = new FormData();
  formData.append('file', file);

  let res: Response;
  try {
    res = await fetchWithRetry(`${API_BASE}/voice/transcribe`, {
      method: 'POST',
      body: formData
    }, 3, 1500);
  } catch {
    throw new Error('Backend unavailable. Could not connect to DATLY server.');
  }

  if (!res.ok) {
    let errData: any = null;
    let rawText = '';
    try {
      rawText = await res.text();
      errData = JSON.parse(rawText);
    } catch {
      // response wasn't JSON
    }
    const code = errData?.error?.code;
    const msg = errData?.error?.message || errData?.detail;

    if (code === 'SARVAM_NOT_CONFIGURED' || res.status === 503) {
      throw new Error(msg || 'Sarvam API key is missing on backend.');
    }
    if (code === 'EMPTY_AUDIO' || code === 'INVALID_FILE') {
      throw new Error(msg || 'Recorded audio is empty or too short. Please speak clearly.');
    }
    if (msg) {
      throw new Error(msg);
    }
    if (res.status === 502) {
      throw new Error('502 Bad Gateway: Upstream speech engine or backend service error.');
    }
    if (res.status === 504) {
      throw new Error('504 Gateway Timeout: Speech transcription timed out.');
    }
    throw new Error(`Speech transcription failed with status ${res.status}`);
  }

  let data: any;
  try {
    data = await res.json();
  } catch {
    throw new Error('Malformed backend response: Invalid JSON received.');
  }

  if (!data || (typeof data.text !== 'string' && typeof data.transcript !== 'string')) {
    throw new Error('Malformed backend response: Missing text in response.');
  }

  return {
    text: (data.text ?? data.transcript ?? '') as string,
    language_code: (data.language_code || 'en-IN') as string,
    transcript: (data.transcript ?? data.text ?? '') as string,
    success: data.success ?? true
  };
}

/**
 * Send a text answer to the backend for Text-to-Speech synthesis.
 * Returns the URL of an audio blob created from the returned wav bytes.
 */
export async function synthesizeSpeech(text: string, languageCode?: string): Promise<string> {
  const res = await fetchWithRetry(`${API_BASE}/voice/synthesize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, language_code: languageCode })
  });
  if (!res.ok) throw new Error('Speech synthesis failed.');
  const blob = await res.blob();
  return URL.createObjectURL(blob);
}

/**
 * Full voice-query endpoint: audio → STT → analysis → TTS (optional).
 * Supports both single dataset_id and workspace_id (+ optional dataset_ids).
 */
export async function analyzeVoice(
  target: { datasetId?: string; workspaceId?: string; datasetIds?: string[] } | string,
  audioBlob: Blob
): Promise<VoiceAnalysisResponse> {
  try {
    const formData = new FormData();
    const wsId = typeof target === 'object' ? (target.workspaceId || getStoredWorkspaceId()) : getStoredWorkspaceId();
    const dsId = typeof target === 'string' ? target : target.datasetId;
    const dsIds = typeof target === 'object' ? target.datasetIds : undefined;

    if (wsId) {
      formData.append('workspace_id', wsId);
    }
    if (dsId) {
      formData.append('dataset_id', dsId);
    }
    if (dsIds && dsIds.length > 0) {
      formData.append('dataset_ids', JSON.stringify(dsIds));
    }
    formData.append('file', audioBlob, 'recording.wav');

    const headers: Record<string, string> = {};
    if (wsId) {
      headers['X-Workspace-Id'] = wsId;
    }

    const res = await fetchWithRetry(`${API_BASE}/voice/analyze`, {
      method: 'POST',
      headers,
      body: formData
    });

    const data = await res.json();
    if (!res.ok) {
      return {
        success: false,
        answer: data.error?.message || data.detail || "Voice analysis failed.",
        error: data.error?.code || "VOICE_ERROR"
      };
    }

    let visData = [];
    if (data.result?.data) {
      visData = data.result.data;
    } else if (data.result?._external_result?.rows) {
      visData = data.result._external_result.rows;
    }

    const visualizations = (data.visualizations || (data.visualization ? [data.visualization] : [])).map((v: any) => ({
      ...v,
      data: v.data || visData
    }));
    const primaryVis = visualizations.length > 0 ? visualizations[0] : (data.visualization ? { ...data.visualization, data: visData } : undefined);

    return {
      success: true,
      transcript: data.transcript,
      language_code: data.language_code,
      answer: data.answer,
      result: data.result,
      visualization: primaryVis,
      visualizations: visualizations.length > 0 ? visualizations : undefined,
      verification: data.verification || data.analysis_plan,
      clarificationRequired: data.clarification_needed,
      clarificationPrompt: data.clarification_question,
      audio: data.audio
    };
  } catch (e: any) {
    return {
      success: false,
      answer: "DATLY couldn't connect to the voice engine.",
      error: e?.message || "Backend unavailable"
    };
  }
}

// ─── Text Analysis API ────────────────────────────────────────────────────────

export async function analyzeWorkspace(
  workspaceId: string,
  question: string,
  datasetIds?: string[]
): Promise<AnalysisResponse> {
  try {
    const res = await fetchWithRetry(`${API_BASE}/workspaces/${workspaceId}/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Workspace-Id': workspaceId
      },
      body: JSON.stringify({
        question,
        dataset_ids: datasetIds && datasetIds.length > 0 ? datasetIds : undefined
      })
    });

    const data = await res.json();
    if (!res.ok) {
      return {
        success: false,
        answer: data.error?.message || data.detail || "DATLY couldn't process your request.",
        error: data.error?.code || "INTERNAL_ERROR"
      };
    }

    let visData = [];
    if (data.result && data.result.data) {
      visData = data.result.data;
    } else if (data.result && data.result._external_result && data.result._external_result.rows) {
      visData = data.result._external_result.rows;
    }

    const visualizations = (data.visualizations || (data.visualization ? [data.visualization] : [])).map((v: any) => ({
      ...v,
      data: v.data || visData
    }));
    const primaryVis = visualizations.length > 0 ? visualizations[0] : (data.visualization ? { ...data.visualization, data: visData } : undefined);

    return {
      success: true,
      language_code: data.language_code,
      answer: data.answer,
      result: data.result,
      visualization: primaryVis,
      visualizations: visualizations.length > 0 ? visualizations : undefined,
      verification: data.verification || data.analysis_plan,
      clarificationRequired: data.clarification_needed,
      clarificationPrompt: data.clarification_question,
      clarificationOptions: data.clarification_question ? [
        { label: 'Clarify details', value: data.clarification_question }
      ] : undefined
    };
  } catch (e: any) {
    return {
      success: false,
      answer: "DATLY couldn't connect to the analytics engine.",
      error: e?.message || "Backend unavailable"
    };
  }
}

export async function askQuestion(
  datasetId: string,
  question: string,
  workspaceId?: string,
  datasetIds?: string[]
): Promise<AnalysisResponse> {
  const wsId = workspaceId || getStoredWorkspaceId();
  if (wsId) {
    return analyzeWorkspace(wsId, question, datasetIds && datasetIds.length > 0 ? datasetIds : (datasetId ? [datasetId] : undefined));
  }

  try {
    let res = await fetchWithRetry(`${API_BASE}/analysis/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, dataset_id: datasetId })
    });

    if (res.status === 404) {
      res = await fetchWithRetry(`${API_BASE}/datasets/${datasetId}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question })
      });
    }

    const data = await res.json();
    if (!res.ok) {
      return {
        success: false,
        answer: data.error?.message || "DATLY couldn't process your request.",
        error: data.error?.code || "INTERNAL_ERROR"
      };
    }
    
    let visData = [];
    if (data.result && data.result.data) {
      visData = data.result.data;
    } else if (data.result && data.result._external_result && data.result._external_result.rows) {
      visData = data.result._external_result.rows;
    }

    const visualizations = (data.visualizations || (data.visualization ? [data.visualization] : [])).map((v: any) => ({
      ...v,
      data: v.data || visData
    }));
    const primaryVis = visualizations.length > 0 ? visualizations[0] : (data.visualization ? { ...data.visualization, data: visData } : undefined);
    
    return {
      success: true,
      language_code: data.language_code,
      answer: data.answer,
      result: data.result,
      visualization: primaryVis,
      visualizations: visualizations.length > 0 ? visualizations : undefined,
      verification: data.verification || data.analysis_plan,
      clarificationRequired: data.clarification_needed,
      clarificationPrompt: data.clarification_question
    };
  } catch (e: any) {
    return {
      success: false,
      answer: "DATLY couldn't connect to the analytics engine.",
      error: e?.message || "Backend unavailable"
    };
  }
}


