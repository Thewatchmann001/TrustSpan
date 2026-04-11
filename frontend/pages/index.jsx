import { useState, useEffect } from "react";
import Link from "next/link";
import {
  Briefcase, Shield, Sparkles, Building2, Users, FileText,
  CheckCircle, Globe, ArrowRight, Menu, X, Star, Zap, Lock
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import Logo from "../components/Logo";
import { authAPI } from "../lib/api";

export default function Home() {
  const [stats, setStats] = useState(null);
  const [loadingStats, setLoadingStats] = useState(true);
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  useEffect(() => {
    async function fetchStats() {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/admin/public-stats`);
        if (response.ok) {
          const data = await response.json();
          setStats(data);
        }
      } catch (error) {
        console.error("Failed to fetch stats:", error);
      } finally {
        setLoadingStats(false);
      }
    }
    fetchStats();
  }, []);

  const navLinks = [
    { name: "Home", href: "#" },
    { name: "For Job Seekers", href: "/register" },
    { name: "For Employers", href: "/employer-register" },
    { name: "About", href: "#" },
  ];

  return (
    <div className="min-h-screen bg-[#0A1628] text-white font-['Inter'] selection:bg-[#1EB53A]/30">
      {/* Navbar */}
      <nav className="fixed top-0 w-full z-50 bg-[#0A1628]/95 backdrop-blur-md border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Logo size="default" showText={true} variant="light" />
          </div>

          <div className="hidden md:flex items-center gap-8">
            {navLinks.map((link) => (
              <a
                key={link.name}
                href={link.href}
                className="text-sm font-medium text-slate-300 hover:text-[#1EB53A] transition-colors"
              >
                {link.name}
              </a>
            ))}
          </div>

          <div className="hidden md:flex items-center gap-4">
            <Link href="/login" className="px-6 py-2 text-sm font-semibold text-white hover:text-[#1EB53A] transition-colors">
              Sign In
            </Link>
            <Link href="/register" className="px-6 py-2 text-sm font-bold bg-[#1EB53A] hover:bg-[#199a31] rounded-lg transition-all transform hover:scale-105 active:scale-95">
              Get Started
            </Link>
          </div>

          <button className="md:hidden text-white" onClick={() => setIsMenuOpen(!isMenuOpen)}>
            {isMenuOpen ? <X /> : <Menu />}
          </button>
        </div>

        {/* Mobile Menu */}
        <AnimatePresence>
          {isMenuOpen && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="md:hidden bg-[#0E2040] border-b border-white/10 overflow-hidden"
            >
              <div className="flex flex-col p-6 gap-4">
                {navLinks.map((link) => (
                  <a key={link.name} href={link.href} className="text-lg font-medium text-slate-300">{link.name}</a>
                ))}
                <div className="pt-4 flex flex-col gap-4 border-t border-white/10">
                  <Link href="/login" className="text-center font-semibold">Sign In</Link>
                  <Link href="/register" className="btn-cta text-center py-3 bg-[#1EB53A]">Get Started</Link>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </nav>

      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center pt-20 overflow-hidden">
        {/* Abstract Background */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-[#1EB53A]/5 rounded-full blur-[120px] pointer-events-none" />

        <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-2 gap-16 items-center w-full">
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8 }}
          >
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#1EB53A]/10 border border-[#1EB53A]/20 text-[#1EB53A] text-xs font-bold mb-8 uppercase tracking-wider">
              <span className="text-lg">🇸🇱</span> Sierra Leone's #1 Career Platform
            </div>

            <h1 className="text-6xl md:text-8xl font-[800] leading-[1.1] mb-8">
              Build a Career<br />
              <span className="text-[#1EB53A]">Worth Trusting</span>
            </h1>

            <p className="text-xl text-slate-400 mb-10 max-w-lg leading-relaxed font-normal">
              AI-powered CV builder, blockchain credentials, and direct employer connections — built for Sierra Leone's next generation.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 mb-12">
              <Link href="/cv-builder" className="px-8 py-4 bg-[#1EB53A] hover:bg-[#199a31] text-white rounded-lg font-bold flex items-center justify-center gap-2 transition-all transform hover:-translate-y-1">
                Build My CV <ArrowRight size={20} />
              </Link>
              <Link href="/employer-register" className="px-8 py-4 border border-white/10 hover:bg-white/5 text-white rounded-lg font-bold flex items-center justify-center transition-all">
                For Employers
              </Link>
            </div>

            <div className="flex flex-wrap gap-6">
              {[
                { icon: Lock, text: "Blockchain Verified" },
                { icon: Sparkles, text: "Mistral AI Powered" },
                { icon: Zap, text: "Solana Network" }
              ].map((badge, i) => (
                <div key={i} className="flex items-center gap-2 text-slate-500 text-sm font-medium">
                  <badge.icon size={16} className="text-[#1EB53A]" />
                  {badge.text}
                </div>
              ))}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="hidden lg:block relative"
          >
            <div className="relative z-10 bg-[#0E2040] border border-white/10 rounded-2xl p-8 shadow-2xl">
              <div className="flex items-center justify-between mb-8 pb-4 border-b border-white/5">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-full bg-slate-700 animate-pulse" />
                  <div>
                    <div className="w-32 h-4 bg-slate-700 rounded mb-2 animate-pulse" />
                    <div className="w-24 h-3 bg-slate-800 rounded animate-pulse" />
                  </div>
                </div>
                <div className="px-3 py-1 bg-[#1EB53A]/20 text-[#1EB53A] rounded-full text-xs font-bold">
                  ATS Score: 98
                </div>
              </div>

              <div className="space-y-6">
                <div>
                  <div className="w-full h-2 bg-white/5 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: "98%" }}
                      transition={{ duration: 1.5, delay: 1 }}
                      className="h-full bg-[#1EB53A]"
                    />
                  </div>
                  <div className="flex justify-between mt-2">
                    <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">AI Optimization Progress</span>
                    <span className="text-[10px] text-[#1EB53A] font-bold">Complete</span>
                  </div>
                </div>

                <div className="space-y-3">
                  <div className="h-4 bg-white/5 rounded w-3/4" />
                  <div className="h-4 bg-white/5 rounded w-full" />
                  <div className="h-4 bg-white/5 rounded w-1/2" />
                </div>

                <div className="grid grid-cols-2 gap-4 pt-4">
                  <div className="h-20 bg-white/5 rounded-xl border border-white/5 flex items-center justify-center">
                    <Sparkles className="text-violet-400" />
                  </div>
                  <div className="h-20 bg-white/5 rounded-xl border border-white/5 flex items-center justify-center">
                    <Shield className="text-[#1EB53A]" />
                  </div>
                </div>
              </div>
            </div>

            {/* Background Decor */}
            <div className="absolute -top-10 -right-10 w-40 h-40 bg-[#1EB53A]/10 rounded-full blur-3xl" />
            <div className="absolute -bottom-10 -left-10 w-40 h-40 bg-gold/5 rounded-full blur-3xl" />
          </motion.div>
        </div>
      </section>

      {/* Stats Bar */}
      <section className="py-12 bg-[#0E2040] border-y border-white/5">
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-2 lg:grid-cols-4 gap-8">
          {[
            { label: "Total Users", key: "total_users" },
            { label: "CVs Created", key: "total_cvs" },
            { label: "Employers", key: "total_employers" },
            { label: "Verified Credentials", key: "verified_credentials" }
          ].map((stat, i) => (
            <div key={i} className="text-center md:text-left">
              <p className="text-slate-500 text-sm font-semibold uppercase tracking-wider mb-2">{stat.label}</p>
              {loadingStats ? (
                <div className="h-10 w-24 bg-white/5 rounded animate-pulse" />
              ) : (
                <p className="text-4xl font-bold">{stats?.[stat.key]?.toLocaleString() || '0'}</p>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 bg-[#0A1628]">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <span className="text-[#1EB53A] text-xs font-bold uppercase tracking-[0.2em] mb-4 block">Platform Features</span>
            <h2 className="text-4xl md:text-5xl font-extrabold">One Platform. Every Career Tool.</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              {
                icon: FileText,
                title: "CV Builder",
                desc: "Build ATS-optimized CVs in minutes with AI assistance. Upload existing CV for instant parsing."
              },
              {
                icon: Sparkles,
                title: "AI Job Matching",
                desc: "AI matches your profile to verified employer openings across Sierra Leone and beyond."
              },
              {
                icon: Shield,
                title: "Blockchain Credentials",
                desc: "Every certificate and work history verified on Solana. Unforgeable. Portable. Trusted."
              }
            ].map((f, i) => (
              <div key={i} className="bg-[#0E2040] p-8 rounded-xl border border-white/5 border-l-4 border-l-[#1EB53A] group hover:bg-[#122850] transition-all">
                <div className="w-12 h-12 rounded-full bg-[#1EB53A]/10 flex items-center justify-center text-[#1EB53A] mb-6 group-hover:scale-110 transition-transform">
                  <f.icon size={24} />
                </div>
                <h3 className="text-xl font-bold mb-4">{f.title}</h3>
                <p className="text-slate-400 leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-24 bg-[#0E2040]">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-20">
            <h2 className="text-4xl md:text-5xl font-extrabold mb-4">How It Works</h2>
            <p className="text-slate-400">A simple process to elevate your career status.</p>
          </div>

          <div className="relative grid grid-cols-1 md:grid-cols-3 gap-12">
            {/* Desktop Connector Line */}
            <div className="hidden md:block absolute top-[60px] left-[15%] right-[15%] h-[2px] bg-white/5" />

            {[
              { step: "01", title: "Create Your Profile", desc: "Register and complete your professional profile" },
              { step: "02", title: "Build & Optimize", desc: "Use our AI CV builder or upload your existing CV" },
              { step: "03", title: "Get Matched", desc: "Employers find you. You find opportunities. Everyone wins." }
            ].map((s, i) => (
              <div key={i} className="relative text-center z-10">
                <div className="text-5xl font-black text-[#1EB53A] mb-8 drop-shadow-[0_0_15px_rgba(30,181,58,0.3)]">{s.step}</div>
                <h3 className="text-xl font-bold mb-4">{s.title}</h3>
                <p className="text-slate-400 max-w-[250px] mx-auto">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* For Employers Section */}
      <section className="py-24 bg-[#0A1628]">
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          <div>
            <span className="text-[#F4A31A] text-xs font-bold uppercase tracking-[0.2em] mb-4 block">For Hiring Managers</span>
            <h2 className="text-4xl md:text-6xl font-extrabold mb-8">Find Sierra Leone's<br />Best Talent</h2>
            <p className="text-lg text-slate-400 mb-10 leading-relaxed">
              Post your hiring criteria. Our AI searches thousands of verified CVs and ranks candidates by fit score. No more guesswork.
            </p>
            <Link href="/employer-register" className="px-8 py-4 bg-[#F4A31A] hover:bg-[#d98c0d] text-[#0A1628] rounded-lg font-bold flex items-center justify-center sm:inline-flex gap-2 transition-all transform hover:-translate-y-1">
              Register as Employer <ArrowRight size={20} />
            </Link>
          </div>

          <div className="bg-[#0E2040] rounded-2xl border border-white/10 p-6 shadow-2xl relative overflow-hidden">
            <div className="flex items-center justify-between mb-8">
              <div className="text-sm font-bold uppercase tracking-wider text-slate-500">Candidate Search Results</div>
              <div className="flex gap-1">
                <div className="w-2 h-2 rounded-full bg-red-500" />
                <div className="w-2 h-2 rounded-full bg-amber-500" />
                <div className="w-2 h-2 rounded-full bg-green-500" />
              </div>
            </div>

            <div className="space-y-4">
              {[
                { name: "Musa Kamara", role: "Sr. Software Engineer", score: 96 },
                { name: "Fatu Bangura", role: "Product Designer", score: 92 },
                { name: "Ibrahim Sesay", role: "Data Analyst", score: 89 }
              ].map((c, i) => (
                <div key={i} className="p-4 bg-white/5 rounded-xl border border-white/5 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-slate-700" />
                    <div>
                      <div className="text-sm font-bold">{c.name}</div>
                      <div className="text-[10px] text-slate-500">{c.role}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-bold text-[#1EB53A]">{c.score}%</div>
                    <div className="text-[10px] text-slate-500 uppercase font-bold tracking-tighter">Match Score</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="py-24 bg-[#0E2040]">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-extrabold mb-4">Success Stories</h2>
            <p className="text-slate-400">Trusted by professionals across Freetown and beyond.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              {
                name: "Alpha Jalloh",
                role: "Software Developer",
                company: "TechSalone",
                quote: "TrustBridge's AI CV builder helped me restructure my experience. I landed a senior role within two weeks of applying."
              },
              {
                name: "Zainab Conteh",
                role: "HR Manager",
                company: "Freetown Logistics",
                quote: "The candidate vetting is unmatched. We saved 40+ hours on our last hiring cycle thanks to the match scores."
              },
              {
                name: "Samuel Kargbo",
                role: "Operations Lead",
                company: "Sierra Mining",
                quote: "Blockchain verification gives me peace of mind. Knowing every degree is verified makes hiring a breeze."
              }
            ].map((t, i) => (
              <div key={i} className="bg-[#122850] p-8 rounded-xl border border-white/5 shadow-xl">
                <div className="flex gap-1 text-[#F4A31A] mb-6">
                  {[...Array(5)].map((_, i) => <Star key={i} size={16} fill="currentColor" />)}
                </div>
                <p className="text-slate-300 italic mb-8 leading-relaxed">"{t.quote}"</p>
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-full bg-slate-700" />
                  <div>
                    <div className="font-bold">{t.name}</div>
                    <div className="text-xs text-slate-500">{t.role} @ {t.company}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="py-24 px-6">
        <div className="max-w-5xl mx-auto rounded-3xl overflow-hidden relative">
          <div className="absolute inset-0 bg-gradient-to-br from-[#0D7C6E] to-[#0A1628]" />
          <div className="relative z-10 p-12 md:p-24 text-center">
            <h2 className="text-4xl md:text-6xl font-black mb-8 leading-tight">Ready to Build<br />Your Future?</h2>
            <p className="text-xl text-white/70 mb-12 max-w-lg mx-auto leading-relaxed">
              Join Sierra Leone's fastest growing career platform. Free to start.
            </p>
            <Link href="/register" className="px-10 py-5 bg-[#1EB53A] hover:bg-[#199a31] text-white rounded-xl font-[800] text-xl transition-all transform hover:-translate-y-1 shadow-2xl">
              Get Started Free <ArrowRight className="inline-block ml-2" />
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="pt-24 pb-12 bg-[#060D1A] border-t border-white/5">
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-2 lg:grid-cols-4 gap-12 mb-20">
          <div className="col-span-2 lg:col-span-1">
            <Logo size="default" showText={true} variant="light" className="mb-6" />
            <p className="text-slate-500 text-sm mb-8 leading-relaxed">
              Elevating Sierra Leone's professional landscape through AI and blockchain technology.
            </p>
            <div className="flex gap-4">
              {['twitter', 'linkedin', 'facebook'].map(s => (
                <div key={s} className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center hover:bg-[#1EB53A] transition-colors cursor-pointer">
                  <Globe size={16} />
                </div>
              ))}
            </div>
          </div>

          <div>
            <h4 className="font-bold mb-6">Job Seekers</h4>
            <ul className="space-y-4 text-sm text-slate-500">
              <li><Link href="/cv-builder" className="hover:text-[#1EB53A]">AI CV Builder</Link></li>
              <li><Link href="/register" className="hover:text-[#1EB53A]">Find Jobs</Link></li>
              <li><Link href="#" className="hover:text-[#1EB53A]">Career Advice</Link></li>
              <li><Link href="#" className="hover:text-[#1EB53A]">ATS Scoring</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="font-bold mb-6">Employers</h4>
            <ul className="space-y-4 text-sm text-slate-500">
              <li><Link href="/employer-register" className="hover:text-[#1EB53A]">Post a Job</Link></li>
              <li><Link href="/employer-register" className="hover:text-[#1EB53A]">Browse Talent</Link></li>
              <li><Link href="#" className="hover:text-[#1EB53A]">AI Ranking</Link></li>
              <li><Link href="#" className="hover:text-[#1EB53A]">Enterprise</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="font-bold mb-6">Company</h4>
            <ul className="space-y-4 text-sm text-slate-500">
              <li><Link href="#" className="hover:text-[#1EB53A]">About Us</Link></li>
              <li><Link href="#" className="hover:text-[#1EB53A]">Contact</Link></li>
              <li><Link href="#" className="hover:text-[#1EB53A]">Privacy Policy</Link></li>
              <li><Link href="#" className="hover:text-[#1EB53A]">Terms of Service</Link></li>
            </ul>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-6 pt-8 border-t border-white/5 flex flex-col md:row items-center justify-between gap-4">
          <p className="text-xs text-slate-500">© 2026 TrustBridge Sierra Leone. Built with ❤️ in Freetown.</p>
          <div className="flex gap-6 text-xs text-slate-500">
            <span>#1 in Career Trust</span>
            <span>Solana Native</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
