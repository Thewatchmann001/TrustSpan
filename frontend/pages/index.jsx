import Link from "next/link";
import Image from "next/image";
import {
  Award,
  Building2,
  TrendingUp,
  Shield,
  Users,
  Zap,
  ArrowRight,
  CheckCircle,
  Briefcase,
  Sparkles,
  FileText,
  Globe,
  BarChart3,
  Target,
} from "lucide-react";
import { motion } from "framer-motion";
import Logo from "../components/Logo";
import BackgroundImage from "../components/BackgroundImage";

export default function Home() {
  const features = [
    {
      icon: Briefcase,
      title: "Land Your Dream Job",
      description:
        "ATS-optimized CVs that pass through applicant tracking systems. AI-powered job matching connects you with global opportunities.",
      color: "from-sky-500 to-sky-600",
      gradient: "career-gradient",
    },
    {
      icon: TrendingUp,
      title: "Invest in Verified Startups",
      description:
        "Blockchain-verified startups. Zero remittance fees. Transparent credibility scoring. Direct diaspora investment.",
      color: "from-amber-500 to-amber-600",
      gradient: "investment-gradient",
    },
    {
      icon: Shield,
      title: "Trust Through Technology",
      description:
        "All credentials verified on Solana blockchain. Immutable trust signals. Transparent credibility.",
      color: "from-sky-500 to-sky-600",
      gradient: "trust-gradient",
    },
    {
      icon: Sparkles,
      title: "Smart Connections",
      description:
        "AI-powered matching for jobs and investments. Personalized recommendations. Data-driven decisions.",
      color: "from-violet-500 to-violet-600",
      gradient: "career-gradient",
    },
  ];

  const benefits = [
    "Zero remittance fees with USDC stablecoins",
    "Currency risk eliminated",
    "Transparent credibility scoring",
    "Blockchain-verified credentials",
    "AI-powered job matching",
    "Direct diaspora investment",
  ];

  const steps = [
    {
      step: 1,
      title: "Build & Optimize",
      description: "Upload CV → AI optimizes → ATS score improves",
      icon: FileText,
      image: "/images/backgrounds/how-it-works/step-1-build.jpg",
      color: "from-sky-500 to-sky-600",
    },
    {
      step: 2,
      title: "Match & Apply",
      description: "AI finds jobs → Apply with confidence → Track applications",
      icon: Target,
      image: "/images/backgrounds/how-it-works/step-2-match.jpg",
      color: "from-violet-500 to-violet-600",
    },
    {
      step: 3,
      title: "Invest & Grow",
      description: "Discover startups → Verify credibility → Invest with USDC",
      icon: TrendingUp,
      image: "/images/backgrounds/how-it-works/step-3-invest.jpg",
      color: "from-amber-500 to-sky-600",
    },
  ];

  const stats = [
    { value: "90%+", label: "ATS Score Improvement", icon: BarChart3 },
    { value: "Zero", label: "Remittance Fees", icon: Shield },
    { value: "100%", label: "Blockchain Verified", icon: CheckCircle },
    { value: "Global", label: "Job Opportunities", icon: Globe },
  ];

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Hero Section */}
      <BackgroundImage
        src="/images/backgrounds/hero/landing-hero.jpg"
        alt="Professional workspace - TrustBridge"
        overlay="default"
        className="min-h-screen"
        priority={true}
      >
        <div className="max-w-7xl mx-auto px-6 py-24 md:py-32">
          {/* Logo */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="mb-8"
          >
            <div className="flex justify-center">
              <Logo size="large" showText={true} variant="light" />
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="text-center max-w-4xl mx-auto"
          >
            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.2 }}
              className="text-5xl md:text-6xl lg:text-7xl font-bold mb-6 leading-tight text-white"
            >
              Bridge Your Career & Connect To Diaspora
            </motion.h1>
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.4 }}
              className="text-xl md:text-2xl mb-10 text-white font-semibold leading-relaxed"
            >
              The platform where career building meets diaspora investment. Optimize your CV with AI, land your dream job, then invest in verified startups all in one place.
            </motion.p>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.6 }}
              className="flex flex-col sm:flex-row gap-4 justify-center items-center"
            >
              <Link
                href="/cv-builder"
                className="btn-cta inline-flex items-center gap-2 group"
              >
                Start Building Your CV
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </Link>
              <Link
                href="/investor-platform"
                className="btn-emerald inline-flex items-center gap-2 group"
              >
                Explore Investments
                <TrendingUp className="w-5 h-5 group-hover:scale-110 transition-transform" />
              </Link>
            </motion.div>
          </motion.div>
        </div>
      </BackgroundImage>

      {/* Value Proposition Section */}
      <div className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-bold text-slate-900 mb-4">
              Two Platforms, One Mission: Your Success
            </h2>
            <p className="text-xl text-slate-600 max-w-3xl mx-auto">
              From CV optimization to startup investment—everything you need to build your career and grow your wealth.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.6, delay: index * 0.1 }}
                  className="card-feature group"
                >
                  <div
                    className={`w-20 h-20 rounded-2xl bg-gradient-to-br ${feature.color} flex items-center justify-center mx-auto mb-6 shadow-xl group-hover:scale-110 transition-transform duration-300`}
                  >
                    <Icon className="w-10 h-10 text-white" />
                  </div>
                  <h3 className="text-2xl font-bold text-slate-900 mb-3">
                    {feature.title}
                  </h3>
                  <p className="text-slate-600 leading-relaxed">
                    {feature.description}
                  </p>
                </motion.div>
              );
            })}
          </div>
        </div>
      </div>

      {/* How It Works Section */}
      <div className="py-24 bg-gradient-to-br from-slate-50 to-slate-100">
        <div className="max-w-7xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-bold text-slate-900 mb-4">
              From CV to Investment: Your Journey
            </h2>
            <p className="text-xl text-slate-600 max-w-3xl mx-auto">
              A simple three-step process to transform your career and start investing.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {steps.map((item, index) => {
              const Icon = item.icon;
              return (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.6, delay: index * 0.2 }}
                  className="relative"
                >
                  <div className="card text-center">
                    {/* Step Number */}
                    <div
                      className={`absolute -top-6 left-1/2 transform -translate-x-1/2 w-16 h-16 rounded-2xl bg-gradient-to-br ${item.color} text-white flex items-center justify-center text-3xl font-bold shadow-xl`}
                    >
                      {item.step}
                    </div>

                    {/* Illustration Image */}
                    <div className="relative w-full h-48 rounded-xl overflow-hidden mb-6 mt-8">
                      <Image
                        src={item.image}
                        alt={item.title}
                        fill
                        className="object-cover"
                        loading="lazy"
                      />
                    </div>

                    {/* Icon */}
                    <div
                      className={`w-16 h-16 rounded-xl bg-gradient-to-br ${item.color} flex items-center justify-center mx-auto mb-4 shadow-lg`}
                    >
                      <Icon className="w-8 h-8 text-white" />
                    </div>

                    <h3 className="text-2xl font-bold text-slate-900 mb-3">
                      {item.title}
                    </h3>
                    <p className="text-slate-600 leading-relaxed">
                      {item.description}
                    </p>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Stats Section */}
      <div className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-bold text-slate-900 mb-4">
              TrustBridge by the Numbers
            </h2>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {stats.map((stat, index) => {
              const Icon = stat.icon;
              return (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, scale: 0.9 }}
                  whileInView={{ opacity: 1, scale: 1 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                  className="text-center"
                >
                  <div className="card-premium">
                    <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-amber-500 to-sky-600 flex items-center justify-center mx-auto mb-4 shadow-lg">
                      <Icon className="w-8 h-8 text-white" />
                    </div>
                    <div className="text-5xl font-bold text-slate-900 mb-2">
                      {stat.value}
                    </div>
                    <div className="text-slate-600 font-medium">
                      {stat.label}
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Final CTA Section */}
      <div className="relative py-24 overflow-hidden">
        <div
          className="absolute inset-0 bg-cover bg-center"
          style={{
            backgroundImage: 'url(/images/backgrounds/features/investment-feature.jpg)',
          }}
        >
          <div className="absolute inset-0 bg-gradient-to-br from-slate-900/90 via-slate-800/85 to-amber-500/40" />
        </div>
        <div className="relative z-10 max-w-4xl mx-auto px-6 text-center">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
            className="text-4xl md:text-5xl font-bold mb-6 text-white"
          >
            Ready to Bridge Your Future?
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="text-xl mb-10 text-slate-200 leading-relaxed"
          >
            Join thousands building careers and investing in verified startups.
          </motion.p>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8, delay: 0.4 }}
          >
            <Link
              href="/register"
              className="btn-cta inline-flex items-center gap-2 group"
            >
              Get Started Free
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </Link>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
