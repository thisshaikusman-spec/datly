import { useState, useRef, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ArrowUp, Sparkles, Mic, Square, X, Plus, CheckSquare, Square as EmptySquare, Database, Volume2, VolumeX } from 'lucide-react';
import { DatlyLogo } from '../components/DatlyLogo';
import { WaveBackground } from '../components/WaveBackground';
import { AttachmentButton } from '../components/chat/AttachmentButton';
import { AttachmentPreview, validateFile } from '../components/chat/AttachmentPreview';
import type { Attachment } from '../components/chat/AttachmentPreview';
import { DatasetProcessing } from '../components/chat/DatasetProcessing';
import { DatasetUnderstanding } from '../components/chat/DatasetUnderstanding';
import type { Dataset } from '../lib/datasetParser';
import {
  uploadDataset,
  askQuestion,
  analyzeWorkspace,
  createWorkspace,
  listWorkspaceDatasets,
  deleteWorkspaceDataset,
  getStoredWorkspaceId,
  setStoredWorkspaceId,
  transcribeAudio,
  synthesizeSpeech
} from '../services/api';
import type { AnalysisResponse } from '../services/api';
import { AnswerCard } from '../components/chat/AnswerCard';
import { primeAudio } from '../services/audioPlayer';
import { InsightCard } from '../components/chat/InsightCard';
import { LoadingState } from '../components/chat/LoadingState';
import { ErrorState } from '../components/chat/ErrorState';

interface Message {
  id: number;
  role: 'user' | 'assistant';
  text?: string;
  attachment?: Attachment;
  dataset?: Dataset;
  isProcessing?: boolean;
  filename?: string;
  analysis?: AnalysisResponse;
  audioUrl?: string;          // TTS playback URL for this answer
  autoPlayAudio?: boolean;    // Auto-speak voice response flag
  insight?: string;
  error?: string;
  isLoading?: boolean;
}

// ─── Voice State ──────────────────────────────────────────────────────────────
type VoiceState = 'IDLE' | 'LISTENING' | 'ANALYZING' | 'ERROR';

interface VoiceError {
  kind: 'permission' | 'stt' | 'generic';
  message: string;
}

export function ChatPage() {
  const location = useLocation();
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [autoSpeak, setAutoSpeak] = useState(true);
  const [_nextId, setNextId] = useState(1);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Multi-dataset & Workspace state
  const [workspaceId, setWorkspaceId] = useState<string | null>(() => getStoredWorkspaceId());
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDatasetIds, setSelectedDatasetIds] = useState<string[]>([]);

  // Pending attachments staged in the input area
  const [attachmentMenuOpen, setAttachmentMenuOpen] = useState(false);
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  // Refs mirror for async callbacks (voice, uploads) to avoid stale closures
  const workspaceIdRef = useRef<string | null>(workspaceId);
  const datasetsRef = useRef<Dataset[]>(datasets);
  const selectedDatasetIdsRef = useRef<string[]>(selectedDatasetIds);

  useEffect(() => {
    workspaceIdRef.current = workspaceId;
  }, [workspaceId]);

  useEffect(() => {
    datasetsRef.current = datasets;
  }, [datasets]);

  useEffect(() => {
    selectedDatasetIdsRef.current = selectedDatasetIds;
  }, [selectedDatasetIds]);

  // Voice state
  const [voiceState, setVoiceState] = useState<VoiceState>('IDLE');
  const [voiceError, setVoiceError] = useState<VoiceError | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);

  // Close attachment menu when clicking outside
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (!(e.target as Element).closest('#attachment-btn') && !(e.target as Element).closest('[role="menu"]')) {
        setAttachmentMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  // Initialize workspace and datasets on mount or when location.state arrives
  useEffect(() => {
    const initWorkspace = async () => {
      let currentWs = workspaceId || getStoredWorkspaceId();
      const navDs = location.state?.dataset;

      if (!currentWs) {
        try {
          currentWs = await createWorkspace();
          setWorkspaceId(currentWs);
          setStoredWorkspaceId(currentWs);
        } catch (err) {
          console.warn('Could not auto-create workspace on mount:', err);
        }
      }

      if (navDs && (navDs.id || navDs.dataset_id)) {
        const dsObj: Dataset = {
          ...navDs,
          id: navDs.id || navDs.dataset_id,
          alias: navDs.alias || (navDs.name ? navDs.name.split('.')[0] : 'dataset_1')
        };
        setDatasets([dsObj]);
        setSelectedDatasetIds([dsObj.id]);
        setMessages(prev => {
          if (prev.length > 0) return prev;
          return [{
            id: 1,
            role: 'assistant',
            dataset: dsObj,
            text: `Dataset received. DATLY is ready to answer questions about ${dsObj.name || 'your data'}.`
          }];
        });
        setNextId(2);
      } else if (currentWs) {
        try {
          const list = await listWorkspaceDatasets(currentWs);
          if (list.length > 0) {
            setDatasets(list);
            setSelectedDatasetIds(list.map(d => d.id));
            if (messages.length === 0) {
              setMessages([{
                id: 1,
                role: 'assistant',
                text: `Workspace restored with ${list.length} dataset${list.length > 1 ? 's' : ''}: ${list.map(d => d.alias || d.name).join(', ')}. Ask questions about any or all of them.`
              }]);
              setNextId(2);
            }
          }
        } catch (err) {
          console.warn('Could not list workspace datasets:', err);
        }
      }
    };

    initWorkspace();
  }, [location.state]);

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 180)}px`;
  }, [input, attachments]);

  // Scroll to bottom on new message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, attachments]);

  // Cleanup audio stream on unmount
  useEffect(() => {
    return () => {
      stopStream();
    };
  }, []);

  const stopStream = () => {
    streamRef.current?.getTracks().forEach(t => t.stop());
    streamRef.current = null;
  };

  // Add files to staged attachments
  const handleFiles = (files: File[]) => {
    const newAttachments: Attachment[] = files.map(file => {
      const error = validateFile(file);
      return { kind: 'file', file, error };
    });
    setAttachments(prev => [...prev, ...newAttachments]);
  };

  const removeAttachment = (index: number) => {
    setAttachments(prev => prev.filter((_, i) => i !== index));
  };

  // Toggle dataset selection
  const toggleDatasetSelection = (datasetId: string) => {
    setSelectedDatasetIds(prev => {
      if (prev.includes(datasetId)) {
        return prev.filter(id => id !== datasetId);
      } else {
        return [...prev, datasetId];
      }
    });
  };

  // Delete dataset from workspace
  const handleDeleteDataset = async (datasetId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const wsId = workspaceIdRef.current || getStoredWorkspaceId();
    if (wsId) {
      try {
        await deleteWorkspaceDataset(wsId, datasetId);
      } catch (err) {
        console.warn('Could not delete dataset from server:', err);
      }
    }
    setDatasets(prev => prev.filter(d => d.id !== datasetId));
    setSelectedDatasetIds(prev => prev.filter(id => id !== datasetId));
  };

  // ─── Text / Voice Submit ───────────────────────────────────────────────────
  const handleSubmit = async (overrideText?: string, isVoice: boolean = false) => {
    primeAudio(); // Prime browser audio context immediately on user action
    const questionText = typeof overrideText === 'string' ? overrideText : input;
    const trimmed = questionText.trim();
    if (!trimmed && attachments.length === 0) return;
    if (attachments.some(a => a.error)) return;

    const currentAttachments = [...attachments];
    const userMsgId = Date.now();
    const assistantMsgId = userMsgId + 1;

    setAttachments([]);
    setInput('');

    // Ensure workspace exists
    let wsId = workspaceIdRef.current || getStoredWorkspaceId();
    if (!wsId) {
      try {
        wsId = await createWorkspace();
        setWorkspaceId(wsId);
        setStoredWorkspaceId(wsId);
      } catch (err) {
        console.error('Failed to create workspace:', err);
      }
    }

    // CASE 1: Uploading files
    if (currentAttachments.length > 0) {
      setIsUploading(true);
      const userMessage: Message = {
        id: userMsgId,
        role: 'user',
        text: trimmed || `Uploaded ${currentAttachments.length} dataset${currentAttachments.length > 1 ? 's' : ''}`
      };

      setMessages(prev => [
        ...prev,
        userMessage,
        {
          id: assistantMsgId,
          role: 'assistant',
          isProcessing: true,
          filename: currentAttachments.map(a => a.file.name).join(', ')
        }
      ]);

      const newlyUploaded: Dataset[] = [];
      try {
        for (const att of currentAttachments) {
          const ds = await uploadDataset(att.file, wsId || undefined);
          newlyUploaded.push(ds);
        }

        setDatasets(prev => {
          const updated = [...prev];
          for (const ds of newlyUploaded) {
            if (!updated.some(x => x.id === ds.id)) updated.push(ds);
          }
          return updated;
        });

        setSelectedDatasetIds(prev => {
          const updated = [...prev];
          for (const ds of newlyUploaded) {
            if (!updated.includes(ds.id)) updated.push(ds.id);
          }
          return updated;
        });

        // Show understanding card for first dataset, text summary for others
        const firstDs = newlyUploaded[0];
        setMessages(prev => prev.map(m =>
          m.id === assistantMsgId ? {
            id: m.id,
            role: 'assistant',
            dataset: firstDs,
            text: newlyUploaded.length > 1
              ? `Successfully uploaded ${newlyUploaded.length} datasets: ${newlyUploaded.map(d => d.alias || d.name).join(', ')}. Ready to analyze.`
              : undefined
          } : m
        ));

        // If user also provided a question along with uploads, analyze it now!
        if (trimmed && wsId) {
          const qAssistantMsgId = assistantMsgId + 1;
          setMessages(prev => [
            ...prev,
            { id: qAssistantMsgId, role: 'assistant', isLoading: true }
          ]);

          try {
            const allTargetIds = Array.from(new Set([...selectedDatasetIdsRef.current, ...newlyUploaded.map(d => d.id)]));
            const response = await analyzeWorkspace(wsId, trimmed, allTargetIds);
            
            // Show answer immediately with autoPlayAudio enabled
            setMessages(prev => prev.map(m =>
              m.id === qAssistantMsgId ? {
                id: m.id,
                role: 'assistant',
                analysis: response,
                autoPlayAudio: isVoice || autoSpeak
              } : m
            ));

            // In background, fetch Sarvam TTS audio for replay/Listen pill
            if ((isVoice || autoSpeak) && response.success && response.answer) {
              synthesizeSpeech(response.answer, response.language_code).then(url => {
                setMessages(prev => prev.map(m => m.id === qAssistantMsgId ? { ...m, audioUrl: url } : m));
              }).catch(() => {});
            }
          } catch (err: any) {
            setMessages(prev => prev.map(m =>
              m.id === qAssistantMsgId ? { id: m.id, role: 'assistant', error: err?.message || 'DATLY could not connect to the analytics engine.' } : m
            ));
          }
        }
      } catch (err: any) {
        setMessages(prev => prev.map(m =>
          m.id === assistantMsgId ? { id: m.id, role: 'assistant', error: err?.message || 'Failed to upload datasets.' } : m
        ));
      } finally {
        setIsUploading(false);
      }
      return;
    }

    // CASE 2: Text question without file upload
    const userMessage: Message = { id: userMsgId, role: 'user', text: trimmed };
    setMessages(prev => [
      ...prev,
      userMessage,
      { id: assistantMsgId, role: 'assistant', isLoading: true }
    ]);

    if (datasetsRef.current.length === 0) {
      setMessages(prev => prev.map(m =>
        m.id === assistantMsgId ? { id: m.id, role: 'assistant', error: 'Please upload at least one dataset first.' } : m
      ));
      return;
    }

    try {
      const activeTargets = selectedDatasetIdsRef.current.length > 0 ? selectedDatasetIdsRef.current : datasetsRef.current.map(d => d.id);
      let response: AnalysisResponse;

      if (wsId) {
        response = await analyzeWorkspace(wsId, trimmed, activeTargets);
      } else {
        const fallbackDs = activeTargets[0];
        response = await askQuestion(fallbackDs, trimmed);
      }

      // Display the answer and trigger immediate speech playback
      setMessages(prev => prev.map(m =>
        m.id === assistantMsgId ? {
          id: m.id,
          role: 'assistant',
          analysis: response,
          autoPlayAudio: isVoice || autoSpeak
        } : m
      ));

      // Asynchronously fetch high-fidelity Sarvam audio in background without blocking speech
      if ((isVoice || autoSpeak) && response.success && response.answer) {
        synthesizeSpeech(response.answer, response.language_code).then(url => {
          setMessages(prev => prev.map(m => m.id === assistantMsgId ? { ...m, audioUrl: url } : m));
        }).catch(() => {});
      }
    } catch (err: any) {
      console.error('[ANALYSIS] Error:', err);
      setMessages(prev => prev.map(m =>
        m.id === assistantMsgId ? { id: m.id, role: 'assistant', error: err?.message || 'DATLY could not connect to the analytics engine.' } : m
      ));
    }
  };

  // ─── Voice Flow ────────────────────────────────────────────────────────────
  const handleVoiceMicClick = async () => {
    primeAudio();
    setVoiceError(null);

    if (voiceState === 'LISTENING') {
      mediaRecorderRef.current?.stop();
      return;
    }

    if (voiceState !== 'IDLE') return;

    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
    } catch (err: any) {
      console.error('[VOICE] Microphone permission denied:', err);
      setVoiceError({ kind: 'permission', message: 'Microphone permission denied. Please allow microphone access.' });
      return;
    }

    audioChunksRef.current = [];
    const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
      ? 'audio/webm;codecs=opus'
      : MediaRecorder.isTypeSupported('audio/webm')
        ? 'audio/webm'
        : 'audio/ogg';

    let recorder: MediaRecorder;
    try {
      recorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = recorder;
    } catch (err: any) {
      console.error('[VOICE] MediaRecorder initialization failed:', err);
      stopStream();
      setVoiceError({ kind: 'generic', message: 'Recording failed to initialize. Please try again.' });
      return;
    }

    recorder.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) audioChunksRef.current.push(e.data);
    };

    recorder.onerror = (e) => {
      console.error('[VOICE] Recording failed:', e);
      stopStream();
      setVoiceState('IDLE');
      setVoiceError({ kind: 'generic', message: 'Recording failed. Please try again.' });
    };

    recorder.onstop = async () => {
      stopStream();
      const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });
      audioChunksRef.current = [];

      if (!audioBlob || audioBlob.size === 0) {
        setVoiceState('IDLE');
        setVoiceError({ kind: 'generic', message: 'Empty audio recorded. Please try speaking again.' });
        return;
      }

      setVoiceState('ANALYZING');
      try {
        const response = await transcribeAudio(audioBlob);
        const transcript = response.text || response.transcript || '';

        if (!transcript || !transcript.trim()) {
          setVoiceState('IDLE');
          setVoiceError({ kind: 'stt', message: 'No speech could be recognized. Please try speaking clearly.' });
          return;
        }

        setInput(transcript);
        setVoiceState('IDLE');
        setVoiceError(null);

        // Submit transcript automatically
        await handleSubmit(transcript, true);
      } catch (err: any) {
        setVoiceState('IDLE');
        setVoiceError({ kind: 'stt', message: err?.message || 'Speech recognition failed.' });
      }
    };

    setVoiceState('LISTENING');
    recorder.start(250);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      primeAudio();
      handleSubmit();
    }
  };

  // Drag-and-drop file upload handlers
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const files = Array.from(e.dataTransfer.files || []);
    if (files.length > 0) {
      handleFiles(files);
    }
  };

  const isEmpty = !input.trim() && attachments.length === 0;
  const isDisabled = isEmpty || isUploading || attachments.some(a => !!a.error);

  const micButtonClass = (() => {
    const base = 'w-8 h-8 rounded-lg flex items-center justify-center transition-all duration-200';
    if (voiceState === 'LISTENING') return `${base} text-red-400 bg-red-400/15 animate-pulse ring-1 ring-red-400/40`;
    if (voiceState === 'ANALYZING') return `${base} text-[#a78bfa] bg-[#a78bfa]/10 animate-pulse`;
    return `${base} text-white/35 hover:text-white/70 hover:bg-white/6`;
  })();

  const micTitle = (() => {
    if (voiceState === 'LISTENING') return 'Stop recording';
    if (voiceState === 'ANALYZING') return 'Converting speech…';
    return 'Start voice input';
  })();

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className="min-h-screen w-full flex flex-col bg-[#141414] text-white font-sans overflow-x-hidden relative"
    >
      <WaveBackground />

      {/* Drag overlay indicator */}
      {isDragging && (
        <div className="fixed inset-0 z-50 bg-[#7c3aed]/20 border-2 border-dashed border-[#a78bfa] flex items-center justify-center backdrop-blur-sm pointer-events-none">
          <div className="bg-[#1c1c1c] p-6 rounded-2xl border border-[#a78bfa]/40 text-center shadow-2xl">
            <Database size={36} className="text-[#a78bfa] mx-auto mb-2 animate-bounce" />
            <p className="text-white text-base font-semibold">Drop datasets to attach</p>
            <p className="text-white/50 text-xs mt-1">Supports CSV, XLSX, and JSON</p>
          </div>
        </div>
      )}

      {/* Navbar */}
      <nav className="w-full flex items-center justify-between py-6 px-6 md:px-12 max-w-7xl mx-auto z-10 relative shrink-0">
        <Link to="/" className="flex items-center gap-2 scale-[0.35] origin-left -ml-4 md:ml-0 hover:opacity-80 transition-opacity">
          <DatlyLogo reducedMotion={true} />
        </Link>
        <div className="hidden md:flex items-center gap-8 text-sm text-white/70 font-medium absolute left-1/2 -translate-x-1/2">
          <Link to="/" className="hover:text-white transition-colors">Home</Link>
        </div>

        {/* Multi-Dataset Context summary in Header */}
        <div className="flex items-center justify-end flex-1 md:flex-none">
          {datasets.length > 0 ? (
            <div className="flex items-center gap-2 bg-white/5 border border-white/10 rounded-full px-3.5 py-1.5 shadow-sm">
              <Database size={13} className="text-[#a78bfa]" />
              <span className="text-xs text-white/90 font-medium truncate max-w-[200px]">
                {datasets.length === 1
                  ? datasets[0].alias || datasets[0].name
                  : `${datasets.length} Datasets Active`}
              </span>
              <span className="text-white/20 text-xs">•</span>
              <span className="text-white/40 text-xs font-mono">
                {selectedDatasetIds.length}/{datasets.length} selected
              </span>
            </div>
          ) : (
            <div className="flex items-center gap-2 bg-white/5 border border-white/10 rounded-full px-3 py-1.5 shadow-sm text-white/40 text-xs">
              <span>No datasets attached</span>
            </div>
          )}
        </div>
      </nav>

      {/* Main Content */}
      <main className="flex-1 flex flex-col relative z-10 w-full max-w-3xl mx-auto px-4 md:px-6 pb-8">

        {/* Welcome section when empty */}
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center flex-1 text-center py-16">
            <h1 className="text-3xl md:text-4xl font-semibold text-[#f3f2ee] mb-4 tracking-tight">
              What would you like to discover?
            </h1>
            <p className="text-white/50 text-base md:text-lg max-w-md leading-relaxed font-light mb-6">
              Upload multiple datasets to ask questions, join tables, and explore verified patterns with instant visual charts.
            </p>
            {datasets.length === 0 && (
              <label className="cursor-pointer inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-white/80 hover:text-white transition-colors text-sm">
                <Plus size={16} className="text-[#a78bfa]" />
                <span>Upload Sales & Customers datasets</span>
                <input
                  type="file"
                  multiple
                  accept=".csv,.xlsx,.json"
                  className="sr-only"
                  onChange={(e) => {
                    const files = Array.from(e.target.files || []);
                    if (files.length > 0) handleFiles(files);
                    e.target.value = '';
                  }}
                />
              </label>
            )}
          </div>
        )}

        {/* Message thread */}
        {messages.length > 0 && (
          <div className="flex-1 py-8 space-y-6 overflow-y-auto" style={{ scrollbarWidth: 'none' }}>
            {messages.map((msg) =>
              msg.role === 'user' ? (
                <div key={msg.id} className="flex justify-end">
                  <div className="max-w-[80%] flex flex-col items-end gap-2">
                    {msg.attachment && (
                      <div className="pointer-events-none">
                        <AttachmentPreview attachment={msg.attachment} onRemove={() => {}} />
                      </div>
                    )}
                    {msg.text && (
                      <div className="bg-white/8 border border-white/10 rounded-2xl rounded-br-sm px-5 py-3 text-sm text-white/90 leading-relaxed whitespace-pre-wrap">
                        {msg.text}
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div key={msg.id} className="flex items-start gap-3">
                  <div className="shrink-0 w-8 h-8 rounded-xl bg-gradient-to-br from-[#7c3aed] to-[#f97316] flex items-center justify-center mt-0.5">
                    <Sparkles size={14} className="text-white" strokeWidth={1.8} />
                  </div>
                  <div className="max-w-[82%] border border-white/10 bg-white/4 rounded-2xl rounded-tl-sm px-5 py-3 text-sm text-white/80 leading-relaxed whitespace-pre-wrap">
                    {msg.isProcessing ? (
                      <DatasetProcessing filename={msg.filename || 'dataset'} />
                    ) : msg.isLoading ? (
                      <LoadingState />
                    ) : msg.error ? (
                      <ErrorState message={msg.error} />
                    ) : msg.dataset ? (
                      <div>
                        <DatasetUnderstanding dataset={msg.dataset} />
                        {msg.insight && <InsightCard insight={msg.insight} />}
                      </div>
                    ) : msg.analysis ? (
                      <AnswerCard
                        analysis={msg.analysis}
                        audioUrl={msg.audioUrl}
                        autoPlay={msg.autoPlayAudio}
                        onClarify={(opt) => {
                          setInput(opt.value || opt.label);
                          setTimeout(() => document.getElementById('chat-send-btn')?.click(), 100);
                        }}
                      />
                    ) : (
                      msg.text
                    )}
                  </div>
                </div>
              )
            )}
            <div ref={bottomRef} />
          </div>
        )}

        {/* Input area */}
        <div className={messages.length > 0 ? 'mt-auto sticky bottom-6' : 'mt-auto'}>

          {/* Voice status / error banner */}
          {(voiceState !== 'IDLE' || voiceError) && (
            <div className={`mb-2 flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-medium border transition-all duration-300 ${
              voiceError
                ? 'bg-red-500/10 border-red-500/20 text-red-400'
                : voiceState === 'LISTENING'
                  ? 'bg-red-500/10 border-red-500/20 text-red-400'
                  : 'bg-[#a78bfa]/10 border-[#a78bfa]/20 text-[#a78bfa]'
            }`}>
              {voiceError ? (
                <>
                  <span>⚠️</span>
                  <span>{voiceError.message}</span>
                  <button
                    className="ml-auto text-white/30 hover:text-white/60"
                    onClick={() => setVoiceError(null)}
                  >✕</button>
                </>
              ) : voiceState === 'LISTENING' ? (
                <>
                  <span className="w-2 h-2 rounded-full bg-red-400 animate-pulse" />
                  <span>Listening… Click 🔴 to stop</span>
                </>
              ) : (
                <>
                  <span className="w-2 h-2 rounded-full bg-[#a78bfa] animate-pulse" />
                  <span>Converting speech to text…</span>
                </>
              )}
            </div>
          )}

          {/* Dataset Chip Row Above Chat Input */}
          {datasets.length > 0 && (
            <div className="mb-2 flex items-center gap-2 overflow-x-auto pb-1 px-1" style={{ scrollbarWidth: 'none' }}>
              <span className="text-[11px] text-white/40 uppercase tracking-wider font-semibold shrink-0 pl-1">
                Datasets:
              </span>
              {datasets.map((d) => {
                const isSelected = selectedDatasetIds.includes(d.id);
                return (
                  <div
                    key={d.id}
                    onClick={() => toggleDatasetSelection(d.id)}
                    className={`shrink-0 flex items-center gap-2 px-2.5 py-1.5 rounded-xl border text-xs cursor-pointer select-none transition-all duration-200 ${
                      isSelected
                        ? 'bg-[#a78bfa]/15 border-[#a78bfa]/40 text-white shadow-sm'
                        : 'bg-white/5 border-white/10 text-white/50 hover:border-white/20 hover:text-white/70'
                    }`}
                  >
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleDatasetSelection(d.id);
                      }}
                      className="text-[#a78bfa] hover:text-white"
                      title={isSelected ? 'Deselect from query' : 'Include in query'}
                    >
                      {isSelected ? <CheckSquare size={13} /> : <EmptySquare size={13} className="text-white/30" />}
                    </button>
                    <span className="font-medium text-xs font-mono">{d.alias || d.name}</span>
                    {d.rows > 0 && (
                      <span className="text-[10px] text-white/40 font-mono">
                        ({d.rows.toLocaleString()} × {d.columns})
                      </span>
                    )}
                    <button
                      type="button"
                      onClick={(e) => handleDeleteDataset(d.id, e)}
                      title="Remove dataset"
                      className="ml-1 text-white/30 hover:text-red-400 transition-colors p-0.5 rounded"
                    >
                      <X size={12} />
                    </button>
                  </div>
                );
              })}

              {/* Add dataset fast button */}
              <label
                className="shrink-0 flex items-center gap-1 px-2.5 py-1.5 rounded-xl border border-dashed border-white/15 hover:border-[#a78bfa]/50 text-white/40 hover:text-[#a78bfa] text-xs cursor-pointer transition-colors"
                title="Add another dataset to workspace"
              >
                <Plus size={12} />
                <span>Add</span>
                <input
                  type="file"
                  multiple
                  accept=".csv,.xlsx,.json"
                  className="sr-only"
                  onChange={(e) => {
                    const files = Array.from(e.target.files || []);
                    if (files.length > 0) handleFiles(files);
                    e.target.value = '';
                  }}
                />
              </label>
            </div>
          )}

          <div className="relative group">
            {/* Gradient border glow on focus */}
            <div
              className="absolute -inset-[1px] rounded-2xl opacity-0 group-focus-within:opacity-100 transition-opacity duration-300 pointer-events-none"
              style={{
                background: 'linear-gradient(135deg, #7c3aed, #8b5cf6, #f97316)',
                borderRadius: '1rem',
                zIndex: 0,
              }}
            />

            <div className="relative z-10 flex flex-col bg-[#1c1c1c] rounded-2xl border border-white/10 group-focus-within:border-transparent transition-colors shadow-lg">

              {/* Multi-Attachment Preview Area */}
              {attachments.length > 0 && (
                <div className="px-4 pt-3 pb-2 border-b border-white/5 flex flex-wrap gap-2">
                  {attachments.map((att, idx) => (
                    <AttachmentPreview
                      key={`${att.file.name}-${idx}`}
                      attachment={att}
                      onRemove={() => removeAttachment(idx)}
                    />
                  ))}
                </div>
              )}

              <div className="flex items-end gap-3 px-4 py-3">
                <AttachmentButton
                  open={attachmentMenuOpen}
                  onToggle={() => setAttachmentMenuOpen(!attachmentMenuOpen)}
                  onFiles={handleFiles}
                />

                <textarea
                  ref={textareaRef}
                  id="chat-input"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={
                    attachments.length > 0
                      ? "Add a message or hit send to upload..."
                      : datasets.length > 1
                        ? "Ask across datasets (e.g. 'Top 5 customers by revenue')..."
                        : datasets.length === 1
                          ? `Ask about ${datasets[0].alias || datasets[0].name}...`
                          : "Upload datasets or ask a question…"
                  }
                  rows={1}
                  className="flex-1 bg-transparent resize-none outline-none text-white/90 placeholder-white/30 text-sm leading-relaxed max-h-[180px] overflow-y-auto py-1.5"
                  style={{ scrollbarWidth: 'none' }}
                />

                <div className="flex items-center gap-2 pb-0.5">
                  {/* Microphone / Stop button */}
                  <button
                    id="voice-mic-btn"
                    onClick={handleVoiceMicClick}
                    disabled={voiceState === 'ANALYZING'}
                    className={micButtonClass}
                    title={micTitle}
                    aria-label={micTitle}
                  >
                    {voiceState === 'LISTENING'
                      ? <Square size={14} strokeWidth={2.5} className="fill-red-400 text-red-400" />
                      : <Mic size={16} strokeWidth={2} />
                    }
                  </button>

                  {/* Auto-Speak Answers Toggle button */}
                  <button
                    type="button"
                    onClick={() => setAutoSpeak(!autoSpeak)}
                    className={`w-8 h-8 rounded-lg flex items-center justify-center transition-all duration-200 ${
                      autoSpeak
                        ? 'text-[#a78bfa] bg-[#a78bfa]/15 ring-1 ring-[#a78bfa]/30 shadow-[0_0_8px_rgba(167,139,250,0.2)]'
                        : 'text-white/30 hover:text-white/60 hover:bg-white/5'
                    }`}
                    title={autoSpeak ? "Voice Auto-Reply: ON (answers spoken aloud)" : "Voice Auto-Reply: OFF (muted)"}
                    aria-label={autoSpeak ? "Voice Auto-Reply: ON" : "Voice Auto-Reply: OFF"}
                  >
                    {autoSpeak ? <Volume2 size={16} strokeWidth={2} /> : <VolumeX size={16} strokeWidth={2} />}
                  </button>

                  {/* Send button */}
                  <button
                    id="chat-send-btn"
                    onClick={() => handleSubmit()}
                    disabled={isDisabled}
                    className={`shrink-0 w-9 h-9 rounded-xl flex items-center justify-center transition-all duration-200
                      ${isDisabled
                        ? 'bg-white/5 text-white/20 cursor-not-allowed'
                        : 'bg-gradient-to-br from-[#7c3aed] to-[#f97316] text-white hover:scale-105 shadow-[0_0_14px_rgba(139,92,246,0.4)] hover:shadow-[0_0_20px_rgba(139,92,246,0.6)]'
                      }`}
                  >
                    <ArrowUp size={16} strokeWidth={2.5} />
                  </button>
                </div>
              </div>
            </div>
          </div>

          <p className="text-center text-white/20 text-xs mt-3">
            Press <kbd className="font-mono bg-white/5 border border-white/10 rounded px-1">Enter</kbd> to send · <kbd className="font-mono bg-white/5 border border-white/10 rounded px-1">Shift+Enter</kbd> for new line · 🎤 to speak
          </p>
        </div>
      </main>
    </div>
  );
}
