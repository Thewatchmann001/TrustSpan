import Link from "next/link";
import { useRouter } from "next/router";
import { useAuth } from "../contexts/AuthContext";
import {
  LogOut,
  Building2,
  GraduationCap,
  Briefcase,
  RefreshCw,
} from "lucide-react";
import Logo from "./Logo";

const ROLE_LABELS = { student: "Job seeker", founder: "Founder", investor: "Investor", employer: "Employer", admin: "Admin" };

export default function Layout({ children }) {
  const { user, logout, isAuthenticated, activeRole, capabilities, switchRole } = useAuth();
  const router = useRouter();

  const role = activeRole || user?.role || "";
  const allowedRoles = capabilities?.allowed_roles || (role ? [role] : []);

  const getNavLinks = () => {
    if (!user) return [];

    const links = [];
    const canJobSeeker = capabilities?.job_seeker !== false || role === "student" || role === "job_seeker";
    // const canInvestor = capabilities?.investor !== false || role === "investor";
    // const canFounder = capabilities?.founder === true || role === "founder" || role === "startup";

    if (canJobSeeker) {
      links.push({ href: "/cv-builder", label: "CV Builder", icon: GraduationCap });
    }

    // Feature 2 & 3: Employer Links
    if (role === "employer") {
      links.push({ href: "/employer-dashboard", label: "Dashboard", icon: LayoutIcon });
    } else {
      links.push({ href: "/employer-register", label: "For Employers", icon: Building2 });
    }

    // Feature 4: Admin Dashboard
    const ADMIN_EMAILS = ["josephemsamah@gmail.com"];
    if (role === "admin" || (user?.email && ADMIN_EMAILS.includes(user.email))) {
      links.push({ href: "/admin-dashboard", label: "Admin", icon: Shield });
    }

    return links;
  };

  const navLinks = getNavLinks();
  const showRoleSwitcher = false; // Array.isArray(allowedRoles) && allowedRoles.length > 1;

  const handleRoleSwitch = async (newRole) => {
    const result = await switchRole(newRole);
    if (result.success && result.active_role) {
      router.push("/cv-builder");
    }
  };

  // Don't show nav on landing page
  const isLandingPage = router.pathname === '/';

  return (
    <div className="min-h-screen">
      {isAuthenticated && !isLandingPage && (
        <nav className="glass-premium border-b border-blue-200/50 sticky top-0 z-50 backdrop-blur-xl">
          <div className="max-w-7xl mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <Logo size="default" />

              <div className="flex items-center gap-4">
                {showRoleSwitcher && (
                  <div className="flex items-center gap-2 rounded-xl bg-blue-50/80 px-3 py-2 border border-blue-200/60">
                    <span className="text-xs font-medium text-blue-700 hidden sm:inline">View as</span>
                    <select
                      value={role === "startup" ? "founder" : role}
                      onChange={(e) => handleRoleSwitch(e.target.value)}
                      className="text-sm font-semibold text-blue-800 bg-transparent border-0 cursor-pointer focus:ring-0 focus:outline-none py-1 pr-6"
                    >
                      {allowedRoles.map((r) => (
                        <option key={r} value={r}>{ROLE_LABELS[r] || r}</option>
                      ))}
                    </select>
                    <RefreshCw className="w-3.5 h-3.5 text-blue-600" />
                  </div>
                )}
                {navLinks.map((link) => {
                  const Icon = link.icon;
                  const isActive = router.pathname === link.href;
                  return (
                    <Link
                      key={link.href}
                      href={link.href}
                      className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-semibold transition-all duration-300 ${
                        isActive
                          ? "bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg shadow-blue-500/30"
                          : "text-blue-700 hover:bg-blue-50 hover:text-blue-800"
                      }`}
                    >
                      <Icon className="w-4 h-4" />
                      <span className="hidden md:inline">{link.label}</span>
                    </Link>
                  );
                })}

                <div className="flex items-center gap-4 pl-4 border-l border-blue-200">
                  <span className="text-sm text-blue-700 font-medium hidden md:inline">
                    {user?.full_name || user?.email}
                  </span>
                  <button
                    onClick={logout}
                    className="flex items-center gap-2 text-blue-700 hover:text-red-600 transition-colors font-medium px-3 py-2 rounded-lg hover:bg-red-50"
                  >
                    <LogOut className="w-4 h-4" />
                    <span className="hidden md:inline">Logout</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </nav>
      )}

      <main>{children}</main>
    </div>
  );
}
