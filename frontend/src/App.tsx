import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'motion/react';
import {
  ArrowRight, Paperclip, Cloud, Sun, MapPin, Calendar,
  TrendingUp, Package, AlertTriangle, Wind, Eye, EyeOff, X,
  Radio,
} from 'lucide-react';
import { cn } from './lib/utils';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine, PieChart, Pie
} from 'recharts';
import ModeSelectPage from './pages/ModeSelect';
import { RiskHeatmap } from './components/ui/RiskHeatmap';
import { SignalBreakdown } from './components/ui/SignalBreakdown';
import { useWebSocket } from './hooks/useWebSocket';

// ─── Root Router ────────────────────────────────────────────────────────────

export default function App() {
  return (
    <BrowserRouter>
      <div className="font-sans bg-white relative">
        <div className="noise-overlay" />
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<AuthPage />} />
          <Route path="/onboarding" element={<OnboardingPage />} />
          <Route path="/mode-select" element={<ModeSelectPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

// ─── Preloader ───────────────────────────────────────────────────────────────

function Preloader({ onComplete }: { onComplete: () => void }) {
  const letters = 'XYRA'.split('');
  useEffect(() => {
    const t = setTimeout(onComplete, 2000);
    return () => clearTimeout(t);
  }, []);
  return (
    <motion.div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black"
      exit={{ opacity: 0, scale: 1.1, transition: { duration: 1.5, ease: [0.76, 0, 0.24, 1] as const } }}
    >
      <div className="flex gap-4">
        {letters.map((char, i) => (
          <motion.span
            key={i}
            initial={{ y: 0, opacity: 0, filter: 'blur(15px)' }}
            animate={{ y: [0, -25, 0], opacity: [0, 1, 1, 1], filter: 'blur(0px)', scale: [1, 1.15, 1] }}
            transition={{
              y: { duration: 3, repeat: Infinity, delay: i * 0.15, ease: 'easeInOut' },
              scale: { duration: 3, repeat: Infinity, delay: i * 0.15, ease: 'easeInOut' },
              opacity: { times: [0, 0.15, 0.5, 1], duration: 3.6, ease: 'easeInOut' },
              filter: { duration: 1.5, delay: i * 0.15 },
            }}
            className="text-white font-serif text-8xl md:text-[10rem] tracking-tighter inline-block"
          >
            {char}
          </motion.span>
        ))}
      </div>
    </motion.div>
  );
}

// ─── Word Reveal ─────────────────────────────────────────────────────────────

function WordReveal({ text, baseDelay = 0, italic = false }: { text: string; baseDelay?: number; italic?: boolean }) {
  const words = text.split(' ');
  return (
    <span className="inline-flex flex-wrap gap-x-[0.25em]">
      {words.map((word, i) => (
        <span key={i} className="inline-block">
          <motion.span
            className={cn('inline-block px-1 rounded-sm transition-colors duration-200 hover:bg-[#FFB38E]/20 cursor-default', italic && 'italic')}
            initial={{ y: 60, opacity: 0, filter: 'blur(4px)' }}
            animate={{ y: 0, opacity: 1, filter: 'blur(0px)' }}
            transition={{ duration: 0.9, delay: baseDelay + i * 0.12, ease: [0.16, 1, 0.3, 1] as const }}
          >
            {word}
          </motion.span>
        </span>
      ))}
    </span>
  );
}

// ─── Landing Page ─────────────────────────────────────────────────────────────

function LandingPage() {
  const [isLoaded, setIsLoaded] = useState(false);
  const navigate = useNavigate();

  return (
    <div className="h-[100dvh] overflow-hidden relative">
      <AnimatePresence mode="wait">
        {!isLoaded && <Preloader key="pre" onComplete={() => setIsLoaded(true)} />}
      </AnimatePresence>

      {isLoaded && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, ease: 'easeOut' }}
          className="h-full flex flex-col relative"
        >
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,_rgba(255,179,142,0.08)_0%,_transparent_70%)] pointer-events-none z-[50]" />

          <div className="h-full flex flex-col p-6 md:p-16 relative overflow-hidden">
            <header className="flex justify-between items-center shrink-0 relative z-10 w-full px-4 md:px-12">
              <div className="font-serif text-2xl tracking-tight font-medium">XYRA</div>
              <button
                onClick={() => navigate('/login')}
                className="text-xs font-medium uppercase tracking-widest hover:opacity-50 transition-opacity"
              >
                SIGN IN
              </button>
            </header>

            <div className="flex-1 flex flex-col md:flex-row items-center justify-between gap-0 md:gap-8 relative z-10 w-full px-4 md:px-12">
              {/* Left: text */}
              <div className="w-full md:w-7/12 flex flex-col items-start text-left justify-center min-w-0">
                <motion.div
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.7, delay: 0.1, ease: [0.16, 1, 0.3, 1] as const }}
                  className="text-[10px] font-medium uppercase tracking-[0.25em] text-gray-400 mb-6"
                >
                  AI-Powered Retail Intelligence
                </motion.div>

                <div className="mb-8">
                  <h1 className="text-[13vw] md:text-[8vw] leading-[0.88] tracking-tighter font-serif font-light block">
                    <WordReveal text="Demand," baseDelay={0.25} />
                  </h1>
                  <h1 className="text-[13vw] md:text-[8vw] leading-[0.88] tracking-tighter font-serif font-extralight block">
                    <WordReveal text="Decoded." baseDelay={0.4} italic />
                  </h1>
                </div>

                <motion.p
                  initial={{ opacity: 0, y: 30 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 1.2, duration: 1, ease: [0.16, 1, 0.3, 1] as const }}
                  className="max-w-md text-base md:text-lg text-gray-500 font-normal leading-relaxed mb-12 md:mb-14"
                >
                  The intelligence engine for modern retail. Upload your data, predict demand spikes, and automate supply decisions.
                </motion.p>

                <motion.button
                  onClick={() => navigate('/onboarding')}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  whileHover={{ scale: 1.05, backgroundColor: '#f97316', color: '#fff' }}
                  whileTap={{ scale: 0.95 }}
                  transition={{ delay: 1.8, duration: 0.5 }}
                  className="group flex items-center gap-3 px-8 py-4 bg-[#FFB38E] text-black rounded-full text-lg md:text-xl font-serif italic shadow-xl shadow-orange-200/50 transition-colors duration-300 w-fit"
                >
                  Begin Analysis
                  <ArrowRight className="w-5 h-5 group-hover:translate-x-2 transition-transform duration-300" />
                </motion.button>
              </div>

              {/* Right: image */}
              <motion.img
                src="/market-stand.jpg"
                alt="Market Stand"
                initial={{ opacity: 0, x: 50 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 1, delay: 0.5, ease: [0.16, 1, 0.3, 1] as const }}
                className="w-full md:w-5/12 h-auto rounded-3xl shrink-0"
              />
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
}

// ─── Auth Page (Login / Sign Up) ──────────────────────────────────────────────

function AuthPage() {
  const [mode, setMode] = useState<'signup' | 'signin'>('signup');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = (e: React.SyntheticEvent) => {
    e.preventDefault();
    if (mode === 'signup') {
      navigate('/onboarding');
    } else {
      navigate('/dashboard', { state: { name: 'My Store' } });
    }
  };

  return (
    <div className="min-h-screen bg-white flex items-center justify-center p-4 md:p-8">
      <motion.div
        initial={{ opacity: 0, y: 30, scale: 0.97 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] as const }}
        className="w-full max-w-3xl bg-white rounded-3xl overflow-hidden shadow-xl border border-black/8 flex flex-col"
        style={{ minHeight: 480 }}
      >
        {/* Top accent edge — spans full card width */}
        <div className="h-[3px] w-full flex-shrink-0" style={{
          background: 'linear-gradient(to right, #0A0A0A 0%, #0A0A0A 40%, #FFB38E 55%, #f97316 65%, #FFB38E 75%, #0A0A0A 100%)'
        }} />

        {/* Panels row */}
        <div className="flex flex-1">
        {/* Left dark panel with candle-pillar glow */}
        <div
          className="hidden md:flex w-2/5 relative flex-col justify-between p-8"
          style={{
            background: '#0A0A0A',
            backgroundImage: `
              radial-gradient(ellipse 22px 55% at 18% 100%, rgba(249,115,22,0.95) 0%, transparent 100%),
              radial-gradient(ellipse 32px 65% at 36% 100%, rgba(255,140,40,0.85) 0%, transparent 100%),
              radial-gradient(ellipse 18px 48% at 54% 100%, rgba(249,100,22,0.9) 0%, transparent 100%),
              radial-gradient(ellipse 28px 60% at 72% 100%, rgba(255,120,30,0.88) 0%, transparent 100%),
              radial-gradient(ellipse 20px 50% at 88% 100%, rgba(249,80,10,0.8) 0%, transparent 100%)
            `,
          }}
        >
          <div className="font-serif text-white text-2xl tracking-tight font-medium">XYRA</div>
          <p className="text-white text-2xl font-serif leading-snug font-light">
            Demand decoded.<br />Intelligence for the modern retailer.
          </p>
        </div>

        {/* Right form panel */}
        <form onSubmit={handleSubmit} className="flex-1 p-8 md:p-10 flex flex-col justify-center">
          {/* Brand icon */}
          <div className="w-10 h-10 rounded-full bg-orange-100 flex items-center justify-center mb-6">
            <Sun className="w-5 h-5 text-orange-500" />
          </div>

          <h2 className="text-3xl font-serif font-light mb-1">
            {mode === 'signup' ? 'Get Started' : 'Welcome back'}
          </h2>
          <p className="text-sm text-gray-400 mb-8">
            {mode === 'signup' ? 'Welcome to XYRA — Let\'s get started' : 'Sign in to your XYRA account'}
          </p>

          <div className="space-y-4 mb-6">
            <div>
              <label className="text-[10px] font-medium text-gray-500 uppercase tracking-widest block mb-2">
                Your email
              </label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="hi@yourstore.com"
                className="w-full px-4 py-3 border border-gray-200 rounded-xl text-sm focus:outline-none focus:border-[#FFB38E] transition-colors"
              />
            </div>
            <div>
              <label className="text-[10px] font-medium text-gray-500 uppercase tracking-widest block mb-2">
                {mode === 'signup' ? 'Create new password' : 'Password'}
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="••••••••••"
                  className="w-full px-4 py-3 border border-[#FFB38E]/60 rounded-xl text-sm focus:outline-none focus:border-[#FFB38E] transition-colors pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(v => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>
          </div>

          <motion.button
            type="submit"
            whileHover={{ backgroundColor: '#f97316', color: '#fff' }}
            whileTap={{ scale: 0.97 }}
            className="w-full py-3.5 bg-[#FFB38E] text-black font-serif italic text-lg rounded-xl transition-colors duration-200 mb-4"
          >
            {mode === 'signup' ? 'Create new account' : 'Sign in'}
          </motion.button>

          <p className="text-center text-sm text-gray-400">
            {mode === 'signup' ? (
              <>Already have an account?{' '}
                <button
                  type="button"
                  onClick={() => setMode('signin')}
                  className="text-black font-medium underline underline-offset-2 hover:text-orange-500 transition-colors"
                >
                  Login
                </button>
              </>
            ) : (
              <>Don&apos;t have an account?{' '}
                <button
                  type="button"
                  onClick={() => setMode('signup')}
                  className="text-black font-medium underline underline-offset-2 hover:text-orange-500 transition-colors"
                >
                  Sign up
                </button>
              </>
            )}
          </p>
        </form>
        </div>{/* end panels row */}
      </motion.div>
    </div>
  );
}

// ─── Onboarding Page ─────────────────────────────────────────────────────────

function OnboardingPage() {
  const [step, setStep] = useState(1);
  const [profileType, setProfileType] = useState('');
  const [name, setName] = useState('');
  const [storeLocation, setStoreLocation] = useState('');
  const [categories, setCategories] = useState<string[]>([]);
  const navigate = useNavigate();

  const nextStep = () => {
    if (step === 4) {
      navigate('/mode-select', { state: { name, profileType, location: storeLocation, categories } });
      return;
    }
    setStep(s => s + 1);
  };
  const prevStep = () => setStep(s => Math.max(1, s - 1));

  return (
    <div className="h-[100dvh] flex flex-col md:flex-row">
      {/* Left panel — light orange */}
      <div className="w-full md:w-5/12 p-6 md:p-8 flex flex-col justify-between border-b md:border-b-0 md:border-r border-black/10 bg-[#FFE5D0] shrink-0">
        <div className="font-serif text-2xl tracking-tight font-medium">XYRA</div>
        <div className="py-8 md:py-0">
          <motion.div
            key={step}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-7xl md:text-8xl font-serif text-black/10 mb-4"
          >
            0{step}
          </motion.div>
          <h2 className="text-3xl md:text-4xl font-serif leading-tight">
            {step === 1 && 'What type of store do you operate?'}
            {step === 2 && 'What is the name of your store?'}
            {step === 3 && 'Where are you located?'}
            {step === 4 && 'What categories do you sell?'}
          </h2>
        </div>
        <div className="text-xs font-medium text-gray-500 uppercase tracking-widest hidden md:block">
          Step {step} of 4
        </div>
      </div>

      {/* Right panel */}
      <div className="w-full md:w-7/12 p-6 md:p-12 flex flex-col justify-center flex-1 min-h-0">
        <AnimatePresence mode="wait">
          {step === 1 && (
            <ProfileSelection key="1" selected={profileType} onSelect={(t: string) => { setProfileType(t); nextStep(); }} />
          )}
          {step === 2 && (
            <NameInput key="2" name={name} onChange={setName} onNext={nextStep} onBack={prevStep} />
          )}
          {step === 3 && (
            <LocationInput key="3" location={storeLocation} onChange={setStoreLocation} onNext={nextStep} onBack={prevStep} />
          )}
          {step === 4 && (
            <CategorySelection
              key="4"
              selected={categories}
              onSelect={(c: string) => setCategories(prev => prev.includes(c) ? prev.filter(x => x !== c) : [...prev, c])}
              onNext={nextStep}
              onBack={prevStep}
            />
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

// ─── Step sub-components ──────────────────────────────────────────────────────

const fadeUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -20 },
  transition: { duration: 0.5, ease: [0.16, 1, 0.3, 1] as const },
};

function ProfileSelection({ selected, onSelect }: any) {
  return (
    <motion.div {...fadeUp} className="w-full max-w-xl mx-auto">
      <div className="flex flex-col">
        {['Grocery', 'Retail', 'Pharmacy', 'Other'].map(opt => (
          <button
            key={opt}
            onClick={() => onSelect(opt)}
            className="text-left text-2xl md:text-4xl font-serif py-5 md:py-6 border-b border-black/10 hover:pl-6 transition-all duration-500 group flex justify-between items-center"
          >
            <span className={selected === opt ? 'italic' : ''}>{opt}</span>
            <ArrowRight className={cn('w-6 h-6 md:w-8 md:h-8 transition-all duration-500', selected === opt ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-6 group-hover:opacity-100 group-hover:translate-x-0')} />
          </button>
        ))}
      </div>
    </motion.div>
  );
}

function NameInput({ name, onChange, onNext, onBack }: any) {
  return (
    <motion.div {...fadeUp} className="w-full max-w-xl mx-auto">
      <input
        type="text" value={name} onChange={e => onChange(e.target.value)}
        placeholder="Type here..." autoFocus
        onKeyDown={e => e.key === 'Enter' && name && onNext()}
        className="w-full bg-transparent text-3xl md:text-5xl font-serif border-b border-black/20 pb-3 focus:outline-none focus:border-black transition-colors placeholder:text-black/10"
      />
      <div className="flex items-center justify-between mt-10">
        <button onClick={onBack} className="text-xs font-medium uppercase tracking-widest text-gray-400 hover:text-black transition-colors">Back</button>
        <button onClick={onNext} disabled={!name} className="text-lg font-medium flex items-center gap-2 hover:opacity-60 transition-opacity disabled:opacity-20">
          Continue <ArrowRight className="w-5 h-5" />
        </button>
      </div>
    </motion.div>
  );
}

function LocationInput({ location, onChange, onNext, onBack }: any) {
  return (
    <motion.div {...fadeUp} className="w-full max-w-xl mx-auto">
      <input
        type="text" value={location} onChange={e => onChange(e.target.value)}
        placeholder="City or Pincode" autoFocus
        onKeyDown={e => e.key === 'Enter' && location && onNext()}
        className="w-full bg-transparent text-3xl md:text-5xl font-serif border-b border-black/20 pb-3 focus:outline-none focus:border-black transition-colors placeholder:text-black/10"
      />
      <div className="flex items-center justify-between mt-10">
        <button onClick={onBack} className="text-xs font-medium uppercase tracking-widest text-gray-400 hover:text-black transition-colors">Back</button>
        <button onClick={onNext} disabled={!location} className="text-lg font-medium flex items-center gap-2 hover:opacity-60 transition-opacity disabled:opacity-20">
          Continue <ArrowRight className="w-5 h-5" />
        </button>
      </div>
    </motion.div>
  );
}

function CategorySelection({ selected, onSelect, onNext, onBack }: any) {
  const cats = ['Food & Groceries', 'Beverages', 'Essentials', 'Electronics'];
  return (
    <motion.div {...fadeUp} className="w-full max-w-xl mx-auto">
      <div className="flex flex-wrap gap-3 mb-10">
        {cats.map(cat => (
          <button
            key={cat} onClick={() => onSelect(cat)}
            className={cn(
              'px-5 py-3 rounded-full border border-black text-base transition-colors',
              selected.includes(cat) ? 'bg-black text-white' : 'hover:bg-black/5'
            )}
          >
            {cat}
          </button>
        ))}
      </div>
      <div className="flex items-center justify-between">
        <button onClick={onBack} className="text-xs font-medium uppercase tracking-widest text-gray-400 hover:text-black transition-colors">Back</button>
        <button onClick={onNext} disabled={!selected.length} className="text-lg font-medium flex items-center gap-2 hover:opacity-60 transition-opacity disabled:opacity-20">
          Continue <ArrowRight className="w-5 h-5" />
        </button>
      </div>
    </motion.div>
  );
}

function DataUpload({ onNext, onBack }: any) {
  return (
    <motion.div {...fadeUp} className="w-full max-w-xl mx-auto">
      <div
        onClick={onNext}
        className="border border-black/20 border-dashed p-10 flex flex-col items-center justify-center cursor-pointer hover:bg-black/5 transition-colors mb-10 rounded-2xl"
      >
        <Paperclip className="w-6 h-6 mb-4 opacity-50" />
        <span className="text-xl font-serif italic">Select CSV File</span>
      </div>
      <div className="flex items-center justify-between">
        <button onClick={onBack} className="text-xs font-medium uppercase tracking-widest text-gray-400 hover:text-black transition-colors">Back</button>
      </div>
    </motion.div>
  );
}

function LoadingScreen({ onComplete }: any) {
  useEffect(() => { setTimeout(onComplete, 3000); }, []);
  return (
    <motion.div {...fadeUp} className="w-full flex justify-center">
      <div className="w-12 h-12 border border-black/20 border-t-black rounded-full animate-spin" />
    </motion.div>
  );
}

// ─── Dashboard Page ───────────────────────────────────────────────────────────

function DashboardPage() {
  const { state } = useLocation() as { state: any };
  const navigate = useNavigate();
  const name = state?.name || 'Store';
  const mode: 'static' | 'dynamic' = state?.mode || 'static';
  const [showBanner, setShowBanner] = useState(!state?.loggedIn);

  // Dynamic mode: subscribe to live WebSocket feed
  const { connected, liveData } = useWebSocket(mode === 'dynamic');

  const data = [
    { name: 'Mon', sales: 400, forecast: 420 }, { name: 'Tue', sales: 300, forecast: 350 },
    { name: 'Wed', sales: 500, forecast: 550 }, { name: 'Thu', sales: 280, forecast: 300 },
    { name: 'Fri', sales: null, forecast: 850 }, { name: 'Sat', sales: null, forecast: 920 },
    { name: 'Sun', sales: null, forecast: 780 },
  ];
  const categoryData = [
    { name: 'Grocery', value: 400, fill: '#000000' },
    { name: 'Retail', value: 300, fill: '#333333' },
    { name: 'Pharmacy', value: 200, fill: '#666666' },
    { name: 'Other', value: 100, fill: '#999999' },
  ];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.8 }}
      className="min-h-screen flex flex-col bg-white"
    >
      {/* Free-preview login banner */}
      <AnimatePresence>
        {showBanner && (
          <motion.div
            initial={{ y: -60, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: -60, opacity: 0 }}
            transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] as const }}
            className="w-full bg-[#FFB38E]/20 border-b border-[#FFB38E]/40 px-6 py-3 flex items-center justify-between"
          >
            <p className="text-sm text-gray-700">
              You&apos;re viewing a <span className="font-medium">free preview</span> — create an account to save your insights and unlock all features.
            </p>
            <div className="flex items-center gap-4 shrink-0 ml-4">
              <button
                onClick={() => navigate('/login')}
                className="text-xs font-medium uppercase tracking-widest px-4 py-1.5 bg-black text-white rounded-full hover:bg-[#f97316] transition-colors"
              >
                Get Full Access
              </button>
              <button onClick={() => setShowBanner(false)} className="text-gray-400 hover:text-black transition-colors">
                <X className="w-4 h-4" />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="flex flex-col p-4 md:p-8">
        {/* Header */}
        <header className="flex justify-between items-end border-b border-black/10 pb-4 mb-8 shrink-0">
          <div>
            <h1 className="text-4xl md:text-5xl font-serif tracking-tight mb-1">{name}</h1>
            <p className="text-gray-500 uppercase tracking-widest text-[10px] font-medium">Intelligence Overview</p>
          </div>
          <div className="flex items-center gap-4 text-xs font-medium">
            {mode === 'dynamic' ? (
              <div className={cn(
                'flex items-center gap-2 px-3 py-1.5 rounded-full transition-colors',
                connected ? 'bg-black text-white' : 'bg-gray-100 text-gray-400'
              )}>
                <div className={cn('w-1.5 h-1.5 rounded-full', connected ? 'bg-white animate-pulse' : 'bg-gray-400')} />
                {connected ? 'Live' : 'Connecting…'}
                <Radio className="w-3 h-3 ml-0.5" />
              </div>
            ) : (
              <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-100 text-gray-600 rounded-full">
                <div className="w-1.5 h-1.5 bg-gray-400 rounded-full" /> Static
              </div>
            )}
            <div className="hidden md:flex items-center gap-2 text-gray-500">
              <Calendar className="w-3 h-3" /> {new Date().toLocaleDateString()}
            </div>
          </div>
        </header>

        {/* Summary + Weather */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mb-6">
          <div className="lg:col-span-8 bg-white/50 backdrop-blur-sm p-8 border border-black/5 rounded-3xl flex flex-col justify-center">
            <h3 className="text-[10px] uppercase tracking-widest text-gray-400 mb-6">Executive Summary</h3>
            <p className="text-3xl md:text-5xl font-serif leading-tight max-w-4xl text-balance">
              Demand will surge by <span className="italic text-orange-600">35%</span> due to a local event. Restock <span className="underline decoration-1 underline-offset-8">Beverages</span> by Friday.
            </p>
          </div>
          <div className="lg:col-span-4 bg-[#FFB38E]/10 p-8 border border-[#FFB38E]/20 rounded-3xl flex flex-col justify-between">
            <div className="flex justify-between items-start">
              <h3 className="text-[10px] uppercase tracking-widest text-gray-500">Weather Impact</h3>
              <Sun className="w-8 h-8 text-orange-500" />
            </div>
            <div>
              <div className="text-5xl font-serif mb-2">28°C</div>
              <p className="text-sm text-gray-600 font-medium">Sunny • High demand for cold beverages expected</p>
            </div>
            <div className="flex gap-4 mt-4 text-[10px] font-medium uppercase tracking-widest text-gray-400">
              <span className="flex items-center gap-1"><Wind className="w-3 h-3" /> 12km/h</span>
              <span className="flex items-center gap-1"><Cloud className="w-3 h-3" /> 5%</span>
            </div>
          </div>
        </div>

        {/* Chart + Stock Alerts */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mb-6">
          <div className="lg:col-span-8 bg-white p-8 border border-black/5 rounded-3xl min-h-[400px] flex flex-col">
            <div className="flex justify-between items-center mb-8">
              <h3 className="text-[10px] uppercase tracking-widest text-gray-500">Demand Forecast</h3>
              <div className="flex gap-6 text-[10px] font-medium text-gray-400 uppercase tracking-widest">
                <span className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-black" /> Actual</span>
                <span className="flex items-center gap-2"><div className="w-2 h-2 rounded-full border border-black" /> Predicted</span>
              </div>
            </div>
            <div className="flex-1">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data}>
                  <defs>
                    <linearGradient id="colorSales" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#000" stopOpacity={0.1} />
                      <stop offset="95%" stopColor="#000" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#00000008" />
                  <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#999', fontSize: 11 }} dy={10} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fill: '#999', fontSize: 11 }} />
                  <Tooltip contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 30px -10px rgba(0,0,0,0.1)', padding: '12px', backgroundColor: '#fff' }} />
                  <ReferenceLine x="Fri" stroke="#FFB38E" strokeDasharray="3 3" label={{ position: 'top', value: 'Event Start', fill: '#FFB38E', fontSize: 10, fontWeight: 'bold' }} />
                  <Area type="monotone" dataKey="forecast" stroke="#000" strokeDasharray="4 4" fill="transparent" strokeWidth={1} />
                  <Area type="monotone" dataKey="sales" stroke="#000" fill="url(#colorSales)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="lg:col-span-4 bg-white p-8 border border-black/5 rounded-3xl flex flex-col">
            <h3 className="text-[10px] uppercase tracking-widest text-gray-500 mb-8">Stock Alerts</h3>
            <div className="space-y-8 flex-1">
              {[
                { item: 'Beverages', stock: 12, status: 'Critical', color: 'text-red-500' },
                { item: 'Fresh Produce', stock: 45, status: 'Low', color: 'text-orange-500' },
                { item: 'Dairy', stock: 120, status: 'Healthy', color: 'text-green-500' },
                { item: 'Bakery', stock: 18, status: 'Critical', color: 'text-red-500' },
              ].map(r => (
                <div key={r.item}>
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <div className="font-serif text-xl">{r.item}</div>
                      <div className="text-[10px] uppercase tracking-widest text-gray-400">{r.stock} units remaining</div>
                    </div>
                    <div className={cn('text-[10px] font-bold uppercase tracking-widest', r.color)}>{r.status}</div>
                  </div>
                  <div className="w-full h-1 bg-gray-100 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${(r.stock / 150) * 100}%` }}
                      className={cn('h-full', r.status === 'Critical' ? 'bg-red-500' : r.status === 'Low' ? 'bg-orange-500' : 'bg-black')}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Map + Pie + Events */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mb-6">
          <div className="lg:col-span-4 bg-white p-8 border border-black/5 rounded-3xl min-h-[350px] flex flex-col">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-[10px] uppercase tracking-widest text-gray-500">Store Location</h3>
              <MapPin className="w-4 h-4 text-gray-400" />
            </div>
            <div className="flex-1 bg-gray-50 rounded-2xl relative overflow-hidden border border-black/5">
              <div className="absolute inset-0 opacity-20" style={{ backgroundImage: 'radial-gradient(#000 1px, transparent 1px)', backgroundSize: '20px 20px' }} />
              <div className="absolute inset-0 flex items-center justify-center">
                <motion.div animate={{ y: [0, -10, 0] }} transition={{ duration: 2, repeat: Infinity }} className="relative">
                  <MapPin className="w-10 h-10 text-black fill-black/10" />
                  <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-4 h-1 bg-black/20 rounded-full blur-[2px]" />
                </motion.div>
              </div>
              <div className="absolute bottom-4 left-4 right-4 bg-white/90 backdrop-blur p-4 rounded-xl border border-black/5 shadow-lg">
                <div className="font-serif text-lg">{name}</div>
                <div className="text-[10px] text-gray-500 uppercase tracking-widest">Downtown District, Sector 4</div>
              </div>
            </div>
          </div>

          <div className="lg:col-span-4 bg-white p-8 border border-black/5 rounded-3xl min-h-[350px] flex flex-col">
            <h3 className="text-[10px] uppercase tracking-widest text-gray-500 mb-6">Sales by Category</h3>
            <div className="flex-1">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={categoryData} cx="50%" cy="50%" innerRadius={60} outerRadius={80} paddingAngle={5} dataKey="value" />
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="grid grid-cols-2 gap-4 mt-4">
              {categoryData.map((cat) => (
                <div key={cat.name} className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full" style={{ backgroundColor: cat.fill }} />
                  <span className="text-[10px] uppercase tracking-widest text-gray-500">{cat.name}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="lg:col-span-4 bg-black text-white p-8 rounded-3xl min-h-[350px] flex flex-col">
            <div className="flex justify-between items-center mb-8">
              <h3 className="text-[10px] uppercase tracking-widest text-gray-400">In-House Events</h3>
              <Calendar className="w-4 h-4 text-gray-400" />
            </div>
            <div className="space-y-6 flex-1">
              {[
                { title: 'Weekend Flash Sale', date: 'Apr 15–17', impact: '+25% Demand' },
                { title: 'Local Marathon', date: 'Apr 18', impact: '+40% Beverages' },
                { title: 'Inventory Audit', date: 'Apr 20', impact: 'System Offline' },
              ].map((ev, i) => (
                <div key={i} className="border-l-2 border-white/20 pl-4 py-1">
                  <div className="text-xs text-gray-400 mb-1">{ev.date}</div>
                  <div className="font-serif text-xl mb-1">{ev.title}</div>
                  <div className="text-[10px] font-bold uppercase tracking-widest text-[#FFB38E]">{ev.impact}</div>
                </div>
              ))}
            </div>
            <button className="mt-8 w-full py-3 border border-white/20 rounded-xl text-[10px] uppercase tracking-widest hover:bg-white hover:text-black transition-colors">
              View All Events
            </button>
          </div>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <div className="bg-white p-8 border border-black/5 rounded-3xl">
            <TrendingUp className="w-6 h-6 mb-4 text-green-500" />
            <div className="text-3xl font-serif mb-1">84%</div>
            <div className="text-[10px] uppercase tracking-widest text-gray-400">Prediction Accuracy</div>
          </div>
          <div className="bg-white p-8 border border-black/5 rounded-3xl">
            <Package className="w-6 h-6 mb-4 text-blue-500" />
            <div className="text-3xl font-serif mb-1">1,240</div>
            <div className="text-[10px] uppercase tracking-widest text-gray-400">Items Tracked</div>
          </div>
          <div className="bg-white p-8 border border-black/5 rounded-3xl">
            <AlertTriangle className="w-6 h-6 mb-4 text-red-500" />
            <div className="text-3xl font-serif mb-1">4</div>
            <div className="text-[10px] uppercase tracking-widest text-gray-400">Supply Disruptions</div>
          </div>
        </div>

        {/* ── New Graph 1: SKU Risk Heatmap ─────────────────────────────── */}
        <div className="mb-6">
          <RiskHeatmap />
        </div>

        {/* ── New Graph 2: Demand Signal Breakdown ──────────────────────── */}
        <div className="mb-12">
          <SignalBreakdown />
        </div>
      </div>
    </motion.div>
  );
}
