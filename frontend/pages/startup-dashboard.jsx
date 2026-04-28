import { useEffect } from "react";
import { useRouter } from "next/router";

export default function StartupDashboard() {
  const router = useRouter();

  useEffect(() => {
    router.push("/cv-builder");
  }, [router]);

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-amber-600"></div>
    </div>
  );
}
