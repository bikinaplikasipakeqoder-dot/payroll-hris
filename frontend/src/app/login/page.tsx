'use client';

import { useState, useEffect, FormEvent, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { login, getUser } from '@/lib/auth';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';

export default function LoginPage() {
  return (
    <Suspense>
      <LoginContent />
    </Suspense>
  );
}

function LoginContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectTo = searchParams.get('redirect') || '/dashboard';
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [rememberMe, setRememberMe] = useState(false);

  useEffect(() => {
    const user = getUser();
    if (user) {
      router.push(redirectTo);
    }
  }, [router, redirectTo]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    await new Promise((resolve) => setTimeout(resolve, 300));

    const result = login(email, password);
    if (result.success) {
      const target = result.user?.role === 'employee' ? '/employee-portal' : redirectTo;
      router.push(target);
    } else {
      setError(result.error || 'Terjadi kesalahan, silakan coba lagi');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-row">
      {/* Left gradient panel - hidden on mobile */}
      <div className="hidden lg:flex lg:w-[45%] bg-gradient-to-br from-primary-600 to-primary-800 relative overflow-hidden items-center justify-center">
        {/* Decorative circles */}
        <div className="absolute top-10 left-10 w-64 h-64 rounded-full bg-white/5" />
        <div className="absolute bottom-20 right-10 w-80 h-80 rounded-full bg-white/5" />
        <div className="absolute top-1/2 left-1/4 w-40 h-40 rounded-full bg-white/10" />
        <div className="absolute bottom-10 left-20 w-24 h-24 rounded-full bg-white/10" />
        <div className="absolute top-20 right-1/4 w-32 h-32 rounded-full bg-white/5" />

        {/* Content */}
        <div className="relative z-10 text-center px-12">
          <div className="mb-8">
            <div className="inline-flex items-center justify-center w-20 h-20 bg-white/20 rounded-2xl backdrop-blur-sm mb-6">
              <span className="text-3xl font-bold text-white">PP</span>
            </div>
            <h1 className="text-4xl font-bold text-white mb-4">PayrollPro</h1>
            <p className="text-lg text-white/80 leading-relaxed">
              Sistem Payroll &amp; HRIS Indonesia yang Modern
            </p>
          </div>

          {/* Abstract decorative SVG */}
          <svg
            className="w-64 h-48 mx-auto opacity-30"
            viewBox="0 0 200 150"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <circle cx="30" cy="75" r="25" stroke="white" strokeWidth="1.5" />
            <circle cx="100" cy="50" r="35" stroke="white" strokeWidth="1.5" />
            <circle cx="160" cy="90" r="20" stroke="white" strokeWidth="1.5" />
            <circle cx="70" cy="120" r="15" stroke="white" strokeWidth="1.5" />
            <circle cx="140" cy="30" r="12" stroke="white" strokeWidth="1.5" />
            <line x1="55" y1="75" x2="65" y2="55" stroke="white" strokeWidth="1" opacity="0.5" />
            <line x1="135" y1="50" x2="145" y2="78" stroke="white" strokeWidth="1" opacity="0.5" />
            <line x1="85" y1="115" x2="100" y2="85" stroke="white" strokeWidth="1" opacity="0.5" />
          </svg>
        </div>
      </div>

      {/* Right side - login form */}
      <div className="w-full lg:w-[55%] bg-white flex items-center justify-center px-4 py-12">
        <div className="max-w-md w-full px-8">
          {/* Company logo */}
          <div className="flex justify-center mb-6">
            <div className="w-14 h-14 bg-primary-600 rounded-full flex items-center justify-center">
              <span className="text-xl font-bold text-white">PP</span>
            </div>
          </div>

          {/* Heading */}
          <h2 className="text-2xl font-bold text-slate-800 text-center">
            Selamat Datang
          </h2>
          <p className="text-sm text-slate-500 text-center mb-8">
            Masuk ke akun Anda
          </p>

          {/* Error message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          {/* Login form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            <Input
              type="email"
              label="Email"
              placeholder="admin@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={loading}
            />

            <Input
              type="password"
              label="Password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={loading}
            />

            {/* Remember me & Forgot password */}
            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="w-4 h-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="text-sm text-slate-600">Ingat saya</span>
              </label>
              <a
                href="#"
                className="text-sm text-primary-600 hover:text-primary-700 font-medium"
              >
                Lupa password?
              </a>
            </div>

            {/* Submit button */}
            <Button
              type="submit"
              variant="primary"
              size="lg"
              loading={loading}
              className="w-full"
            >
              {loading ? 'Memproses...' : 'Masuk'}
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}
