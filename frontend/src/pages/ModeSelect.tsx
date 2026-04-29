/**
 * XYRA — Mode Selection Page
 * User picks Static (historical CSV) or Dynamic (real-time POS) before the dashboard.
 * Sits between Onboarding and Dashboard in the routing flow.
 */

import React, { useRef, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'motion/react';
import {
  Upload, Zap, ArrowRight, CheckCircle, Loader2, AlertCircle, FileText,
} from 'lucide-react';
import { cn } from '../lib/utils';
import { api } from '../services/api';

type Mode = 'static' | 'dynamic' | null;

// ── Onboarding state passed from previous page ─────────────────────────────────
interface OnboardingState {
  name: string;
  profileType: string;
  location: string;
  categories: string[];
}

export default function ModeSelectPage() {
  const navigate = useNavigate();
  const { state } = useLocation() as { state: OnboardingState | null };

  const storeState = state ?? { name: 'My Store', profileType: 'Grocery', location: '600001', categories: [] };
  const pincode = storeState.location?.replace(/[^0-9]/g, '') || '600001';

  const [selected, setSelected] = useState<Mode>(null);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [connectingDynamic, setConnectingDynamic] = useState(false);

  const fileRef = useRef<HTMLInputElement>(null);

  // ── Static mode: upload CSV and run pipeline ──────────────────────────────
  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setUploadError(null);

    try {
      const res = await api.uploadCsv(file, storeState.name, pincode, 2);
      const sessionId = res.data.session_id;
      navigate('/dashboard', {
        state: {
          ...storeState,
          mode: 'static',
          sessionId,
          quickStats: res.data.quick_stats,
        },
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Upload failed. Check backend is running.';
      setUploadError(msg);
      setUploading(false);
    }
  };

  // ── Dynamic mode: demo connect + navigate ─────────────────────────────────
  const handleDynamicConnect = async () => {
    setConnectingDynamic(true);
    // Simulate POS handshake (replace with real init-twins call in production)
    await new Promise((r) => setTimeout(r, 1800));
    navigate('/dashboard', {
      state: { ...storeState, mode: 'dynamic', sessionId: null },
    });
  };

  return (
    <div className="min-h-screen bg-white flex flex-col">
      {/* Top bar */}
      <header className="px-8 py-6 flex items-center justify-between border-b border-black/5">
        <div className="font-serif text-2xl tracking-tight font-medium">XYRA</div>
        <div className="text-[10px] font-medium uppercase tracking-widest text-gray-400">
          {storeState.name}
        </div>
      </header>

      <div className="flex-1 flex flex-col items-center justify-center px-6 py-12">
        {/* Title */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
          className="text-center mb-12"
        >
          <p className="text-[10px] font-medium uppercase tracking-[0.25em] text-gray-400 mb-3">
            Step 5 — Data Mode
          </p>
          <h1 className="text-4xl md:text-5xl font-serif leading-tight mb-3">
            How should XYRA<br />
            <span className="italic">read your data?</span>
          </h1>
          <p className="text-gray-500 text-base max-w-sm mx-auto">
            Choose Static to analyse a historical CSV, or Dynamic to connect your live POS system.
          </p>
        </motion.div>

        {/* Mode cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-3xl">
          {/* ── Static Card ──────────────────────────────────────────────── */}
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.15, ease: [0.16, 1, 0.3, 1] }}
          >
            <button
              onClick={() => setSelected('static')}
              className={cn(
                'w-full text-left rounded-3xl border p-8 transition-all duration-300 group',
                selected === 'static'
                  ? 'border-black bg-black text-white shadow-xl'
                  : 'border-black/10 bg-white hover:border-black/30 hover:shadow-md',
              )}
            >
              <div className={cn(
                'w-12 h-12 rounded-2xl flex items-center justify-center mb-6 transition-colors',
                selected === 'static' ? 'bg-white/15' : 'bg-black/5',
              )}>
                <FileText className={cn('w-6 h-6', selected === 'static' ? 'text-white' : 'text-black')} />
              </div>

              <h2 className="font-serif text-2xl mb-2">Static</h2>
              <p className={cn(
                'text-sm leading-relaxed mb-6',
                selected === 'static' ? 'text-white/70' : 'text-gray-500',
              )}>
                Upload a historical CSV. XYRA runs the full 7-layer ML pipeline once and delivers a complete demand analysis report.
              </p>

              <div className="flex flex-wrap gap-2">
                {['7-layer pipeline', 'Demand forecast', 'Risk classification', 'Reorder plan'].map((t) => (
                  <span
                    key={t}
                    className={cn(
                      'text-[9px] font-medium uppercase tracking-widest px-3 py-1 rounded-full',
                      selected === 'static' ? 'bg-white/15 text-white' : 'bg-black/5 text-gray-600',
                    )}
                  >
                    {t}
                  </span>
                ))}
              </div>
            </button>
          </motion.div>

          {/* ── Dynamic Card ─────────────────────────────────────────────── */}
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.27, ease: [0.16, 1, 0.3, 1] }}
          >
            <button
              onClick={() => setSelected('dynamic')}
              className={cn(
                'w-full text-left rounded-3xl border p-8 transition-all duration-300 group',
                selected === 'dynamic'
                  ? 'border-[#FFB38E] bg-[#FFB38E] text-black shadow-xl shadow-orange-200/50'
                  : 'border-black/10 bg-white hover:border-[#FFB38E]/50 hover:shadow-md',
              )}
            >
              <div className={cn(
                'w-12 h-12 rounded-2xl flex items-center justify-center mb-6 transition-colors',
                selected === 'dynamic' ? 'bg-black/10' : 'bg-orange-50',
              )}>
                <Zap className={cn('w-6 h-6', selected === 'dynamic' ? 'text-black' : 'text-orange-500')} />
              </div>

              <h2 className="font-serif text-2xl mb-2">Dynamic</h2>
              <p className={cn(
                'text-sm leading-relaxed mb-6',
                selected === 'dynamic' ? 'text-black/70' : 'text-gray-500',
              )}>
                Connect your live POS system. XYRA maintains a digital twin of every SKU and streams updates via WebSocket.
              </p>

              <div className="flex flex-wrap gap-2">
                {['Real-time twins', 'POS webhook', 'Live alerts', 'WebSocket push'].map((t) => (
                  <span
                    key={t}
                    className={cn(
                      'text-[9px] font-medium uppercase tracking-widest px-3 py-1 rounded-full',
                      selected === 'dynamic' ? 'bg-black/10 text-black' : 'bg-black/5 text-gray-600',
                    )}
                  >
                    {t}
                  </span>
                ))}
              </div>
            </button>
          </motion.div>
        </div>

        {/* ── Action panel ──────────────────────────────────────────────────── */}
        <AnimatePresence mode="wait">
          {selected === 'static' && (
            <motion.div
              key="static-panel"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 8 }}
              transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
              className="mt-8 w-full max-w-3xl"
            >
              {/* Drop zone */}
              <div
                onClick={() => fileRef.current?.click()}
                className={cn(
                  'border border-dashed rounded-2xl p-10 flex flex-col items-center justify-center cursor-pointer transition-colors mb-4',
                  file ? 'border-black bg-black/3' : 'border-black/20 hover:border-black/40 hover:bg-black/2',
                )}
              >
                {file ? (
                  <>
                    <CheckCircle className="w-8 h-8 text-emerald-500 mb-3" />
                    <p className="font-serif text-xl mb-1">{file.name}</p>
                    <p className="text-xs text-gray-400">{(file.size / 1024).toFixed(1)} KB — click to replace</p>
                  </>
                ) : (
                  <>
                    <Upload className="w-8 h-8 text-gray-400 mb-3" />
                    <p className="font-serif text-xl italic mb-1">Select CSV file</p>
                    <p className="text-xs text-gray-400">retail_store_inventory.csv or any sales export</p>
                  </>
                )}
              </div>
              <input
                ref={fileRef}
                type="file"
                accept=".csv"
                className="hidden"
                onChange={(e) => {
                  setFile(e.target.files?.[0] ?? null);
                  setUploadError(null);
                }}
              />

              {/* Error */}
              {uploadError && (
                <div className="flex items-center gap-2 text-red-500 text-sm mb-4 bg-red-50 px-4 py-3 rounded-xl">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{uploadError}</span>
                </div>
              )}

              {/* Run button */}
              <motion.button
                onClick={handleUpload}
                disabled={!file || uploading}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.97 }}
                className="w-full py-4 bg-black text-white font-serif italic text-xl rounded-2xl flex items-center justify-center gap-3 disabled:opacity-30 transition-opacity"
              >
                {uploading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Running 7-layer pipeline…
                  </>
                ) : (
                  <>
                    Run Analysis
                    <ArrowRight className="w-5 h-5" />
                  </>
                )}
              </motion.button>
            </motion.div>
          )}

          {selected === 'dynamic' && (
            <motion.div
              key="dynamic-panel"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 8 }}
              transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
              className="mt-8 w-full max-w-3xl"
            >
              {/* Info */}
              <div className="bg-[#FFB38E]/10 border border-[#FFB38E]/20 rounded-2xl p-6 mb-4 text-sm text-gray-700 leading-relaxed">
                <strong className="font-medium">How it works:</strong> XYRA will open a WebSocket connection
                and update a live digital twin for every SKU as sales happen. Compatible with{' '}
                <span className="font-medium">Petpooja, Marg ERP, Vyapar</span>, or any POS that supports webhooks.
              </div>

              <motion.button
                onClick={handleDynamicConnect}
                disabled={connectingDynamic}
                whileHover={{ scale: 1.02, backgroundColor: '#f97316', color: '#fff' }}
                whileTap={{ scale: 0.97 }}
                className="w-full py-4 bg-[#FFB38E] text-black font-serif italic text-xl rounded-2xl flex items-center justify-center gap-3 disabled:opacity-50 transition-colors"
              >
                {connectingDynamic ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Connecting to live stream…
                  </>
                ) : (
                  <>
                    Connect & Go Live
                    <Zap className="w-5 h-5" />
                  </>
                )}
              </motion.button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
