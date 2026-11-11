import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Select } from '../components/ui/select';
import { ShieldCheck, Lock, Mail, Building, User, Phone, ArrowRight } from 'lucide-react';

interface AuthScreenProps {
  initialMode?: 'login' | 'register';
  onLoginSuccess: (userData: { email: string; role: string; name: string }) => void;
  onBackToLanding: () => void;
}

export const AuthScreen: React.FC<AuthScreenProps> = ({
  initialMode = 'login',
  onLoginSuccess,
  onBackToLanding,
}) => {
  const [mode, setMode] = useState<'login' | 'register'>(initialMode);
  const [email, setEmail] = useState('contractor@apexdemo.com');
  const [password, setPassword] = useState('demolition2026!');
  const [fullName, setFullName] = useState('Marcus Vance');
  const [companyName, setCompanyName] = useState('Apex Demolition Group');
  const [role, setRole] = useState('CONTRACTOR');
  const [phone, setPhone] = useState('+1 (312) 555-0199');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!email || !password) {
      setError('Please provide both email and password.');
      return;
    }

    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
      onLoginSuccess({
        email,
        role,
        name: fullName,
      });
    }, 700);
  };

  const handleQuickLogin = (demoRole: 'CONTRACTOR' | 'SURVEYOR' | 'BUYER') => {
    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
      if (demoRole === 'CONTRACTOR') {
        onLoginSuccess({
          email: 'contractor@apexdemo.com',
          role: 'CONTRACTOR',
          name: 'Marcus Vance',
        });
      } else if (demoRole === 'SURVEYOR') {
        onLoginSuccess({
          email: 'surveyor@certifiedaudit.com',
          role: 'SURVEYOR',
          name: 'Sarah Lindqvist',
        });
      } else {
        onLoginSuccess({
          email: 'd.chen@midweststeel.com',
          role: 'BUYER',
          name: 'David Chen',
        });
      }
    }, 400);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between p-4 sm:p-6 font-sans">
      <div className="flex items-center justify-between max-w-5xl mx-auto w-full py-2">
        <button
          onClick={onBackToLanding}
          className="flex items-center gap-2.5 text-xs text-slate-400 hover:text-white transition-colors"
        >
          <div className="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center text-slate-950 font-bold">
            <ShieldCheck className="w-4 h-4 text-white" />
          </div>
          <span className="font-bold text-white text-sm">Demolition Intelligence</span>
        </button>

        <button
          onClick={onBackToLanding}
          className="text-xs text-slate-400 hover:text-white underline underline-offset-4"
        >
          ← Return to Public Portal
        </button>
      </div>

      <div className="max-w-md mx-auto w-full py-8">
        <Card className="border-slate-800 bg-slate-900/90 shadow-2xl backdrop-blur-md">
          <CardHeader className="text-center pb-4">
            <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 mx-auto mb-2">
              <Lock className="w-6 h-6" />
            </div>
            <CardTitle className="text-xl">
              {mode === 'login' ? 'Sign In to Workspace' : 'Create Enterprise Account'}
            </CardTitle>
            <CardDescription className="text-xs">
              {mode === 'login'
                ? 'Enter your credentials to access demolition surveys & recovery audits'
                : 'Register as a demolition contractor, surveyor, or certified materials buyer'}
            </CardDescription>

            {/* Mode Switch Tabs */}
            <div className="grid grid-cols-2 p-1 bg-slate-950 rounded-lg mt-4 border border-slate-800">
              <button
                type="button"
                onClick={() => setMode('login')}
                className={`py-1.5 text-xs font-semibold rounded-md transition-all ${
                  mode === 'login' ? 'bg-slate-800 text-white shadow' : 'text-slate-400 hover:text-white'
                }`}
              >
                Sign In
              </button>
              <button
                type="button"
                onClick={() => setMode('register')}
                className={`py-1.5 text-xs font-semibold rounded-md transition-all ${
                  mode === 'register' ? 'bg-slate-800 text-white shadow' : 'text-slate-400 hover:text-white'
                }`}
              >
                Register
              </button>
            </div>
          </CardHeader>

          <CardContent>
            {error && (
              <div className="mb-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-3.5">
              {mode === 'register' && (
                <>
                  <Input
                    label="Full Name"
                    icon={<User className="w-4 h-4" />}
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    required
                  />

                  <div className="grid grid-cols-2 gap-3">
                    <Input
                      label="Company Name"
                      icon={<Building className="w-4 h-4" />}
                      value={companyName}
                      onChange={(e) => setCompanyName(e.target.value)}
                      required
                    />

                    <Select
                      label="Enterprise Role"
                      value={role}
                      onChange={(e) => setRole(e.target.value)}
                    >
                      <option value="CONTRACTOR">Demolition Contractor</option>
                      <option value="SURVEYOR">Site Surveyor</option>
                      <option value="BUYER">Material Buyer</option>
                      <option value="RECYCLER">Certified Recycler</option>
                    </Select>
                  </div>

                  <Input
                    label="Phone Number"
                    icon={<Phone className="w-4 h-4" />}
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                  />
                </>
              )}

              <Input
                label="Corporate Email"
                type="email"
                icon={<Mail className="w-4 h-4" />}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />

              <Input
                label="Password"
                type="password"
                icon={<Lock className="w-4 h-4" />}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />

              <Button type="submit" variant="primary" className="w-full mt-2" isLoading={isLoading}>
                {mode === 'login' ? 'Sign In to Dashboard' : 'Complete Registration'}
                <ArrowRight className="w-4 h-4 ml-1.5" />
              </Button>
            </form>

            {/* Quick Demo Access Bar */}
            <div className="mt-6 pt-5 border-t border-slate-800 text-center">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 block mb-2">
                Fast Evaluation (Pre-filled Demo Profiles)
              </span>
              <div className="grid grid-cols-3 gap-2">
                <button
                  type="button"
                  onClick={() => handleQuickLogin('CONTRACTOR')}
                  className="p-2 rounded-lg bg-slate-800/80 hover:bg-slate-800 border border-slate-700/60 text-[11px] font-medium text-slate-200 transition-colors"
                >
                  Contractor
                </button>
                <button
                  type="button"
                  onClick={() => handleQuickLogin('SURVEYOR')}
                  className="p-2 rounded-lg bg-slate-800/80 hover:bg-slate-800 border border-slate-700/60 text-[11px] font-medium text-slate-200 transition-colors"
                >
                  Surveyor
                </button>
                <button
                  type="button"
                  onClick={() => handleQuickLogin('BUYER')}
                  className="p-2 rounded-lg bg-slate-800/80 hover:bg-slate-800 border border-slate-700/60 text-[11px] font-medium text-slate-200 transition-colors"
                >
                  Steel Buyer
                </button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="text-center text-xs text-slate-500 py-2">
        Encrypted with bcrypt & JWT authentication standards • Role-Based Access Control
      </div>
    </div>
  );
};
