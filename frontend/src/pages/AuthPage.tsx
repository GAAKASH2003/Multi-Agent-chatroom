import { useState, type FormEvent } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Sparkles, MessageSquare, Users, Zap } from 'lucide-react';

interface AuthUserPayload {
  email: string;
  name: string;
  id?: string;
  token?: string;
}

interface AuthPageProps {
  onLogin: (user: AuthUserPayload) => void;
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function AuthPage({ onLogin }: AuthPageProps) {
  const [mode, setMode] = useState<'login' | 'signup'>('login');
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const getErrorMessage = async (response: Response) => {
    try {
      const data = await response.json();
      if (typeof data?.detail === 'string') return data.detail;
      if (Array.isArray(data?.detail)) return data.detail[0]?.msg || 'Validation failed.';
    } catch {
      // ignore
    }
    return 'Authentication failed.';
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError('');

    if (!email || !password || (mode === 'signup' && !name)) {
      setError('Please fill in all fields.');
      return;
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters long.');
      return;
    }

    setIsSubmitting(true);

    try {
      const endpoint = mode === 'signup' ? '/auth/signup' : '/auth/login';
      const payload = mode === 'signup' ? { name, email, password } : { email, password };

      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(await getErrorMessage(response));
      }

      const data = await response.json();
      const userName = mode === 'signup' ? data?.user?.name || name : data?.name || email.split('@')[0];
      const userId = mode === 'signup' ? data?.user?.id : data?.user_id;
      const token = mode === 'signup' ? data?.access_token : data?.token;

      onLogin({
        email,
        name: userName,
        id: userId,
        token,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to authenticate right now.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-5xl grid lg:grid-cols-2 gap-8 items-center">
        {/* Left: branding */}
        <div className="hidden lg:flex flex-col gap-8 p-8">
          <div className="flex items-center gap-3">
            <div className="h-12 w-12 rounded-xl bg-primary/15 border border-primary/40 flex items-center justify-center">
              <MessageSquare className="h-6 w-6 text-primary" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-primary">NeonChat</h1>
              <p className="text-sm text-muted-foreground">Multi-agent chatrooms</p>
            </div>
          </div>

          <div className="space-y-6">
            <h2 className="text-4xl font-bold leading-tight">
              Chat with a <span className="text-accent">collective</span> of AI minds.
            </h2>
            <p className="text-muted-foreground text-lg">
              Create groups of AI characters and watch them converse, debate, and build on each
              other's ideas in real time.
            </p>
          </div>

          <div className="grid grid-cols-3 gap-4">
            {[
              { icon: Users, label: 'Group chats', color: 'text-primary' },
              { icon: Sparkles, label: 'AI personas', color: 'text-accent' },
              { icon: Zap, label: 'Live streaming', color: 'text-teal-400' },
            ].map((f) => (
              <div key={f.label} className="glass rounded-xl p-4 flex flex-col gap-2 items-center text-center">
                <f.icon className={`h-6 w-6 ${f.color}`} />
                <span className="text-xs text-muted-foreground">{f.label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Right: form */}
        <div className="glass rounded-2xl p-8 border border-border">
          <div className="lg:hidden flex items-center gap-3 mb-8">
            <div className="h-10 w-10 rounded-lg bg-primary/15 border border-primary/40 flex items-center justify-center">
              <MessageSquare className="h-5 w-5 text-primary" />
            </div>
            <h1 className="text-xl font-bold text-primary">NeonChat</h1>
          </div>

          <h2 className="text-2xl font-bold mb-2">
            {mode === 'login' ? 'Welcome back' : 'Create your account'}
          </h2>
          <p className="text-muted-foreground text-sm mb-6">
            {mode === 'login' ? 'Sign in to continue chatting.' : 'Start building AI chatrooms in seconds.'}
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            {mode === 'signup' && (
              <div className="space-y-2">
                <Label htmlFor="name">Name</Label>
                <Input
                  id="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Your name"
                  className="bg-background/50"
                />
              </div>
            )}
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="bg-background/50"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="bg-background/50"
              />
            </div>

            {error && <p className="text-sm text-destructive">{error}</p>}

            <Button
              type="submit"
              disabled={isSubmitting}
              className="w-full bg-primary hover:bg-primary/90 text-primary-foreground font-semibold"
            >
              {isSubmitting ? 'Please wait...' : mode === 'login' ? 'Sign in' : 'Create account'}
            </Button>
          </form>

          <p className="text-center text-sm text-muted-foreground mt-6">
            {mode === 'login' ? "Don't have an account? " : 'Already have an account? '}
            <button
              onClick={() => {
                setMode(mode === 'login' ? 'signup' : 'login');
                setError('');
              }}
              className="text-primary hover:text-primary/80 font-medium"
            >
              {mode === 'login' ? 'Sign up' : 'Sign in'}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
