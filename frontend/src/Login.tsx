
import { useState, type FormEvent } from "react";
import { ShieldCheck, LogIn } from "lucide-react";

import {
  login,
  saveAccessToken,
  getCurrentUser,
  clearAccessToken,
} from "./api";

interface LoginProps {
onAuthenticated: (username: string) => void;
}

function Login({ onAuthenticated }: LoginProps) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setError(null);
    setLoading(true);

    try {
      const tokenResponse = await login(username.trim(), password);

      saveAccessToken(tokenResponse.access_token);

      // Verify that the newly issued token is valid.
      const user = await getCurrentUser();

      onAuthenticated(user.username);
    } catch (err) {
      clearAccessToken();

      setError(
        err instanceof Error
          ? err.message
          : "Unable to authenticate. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="login-screen">
      <section className="login-card">
        <div className="login-brand">
          <div className="login-brand-icon">
            <ShieldCheck size={27} />
          </div>

          <div>
            <h1>SHIP</h1>
            <span>Infrastructure Control</span>
          </div>
        </div>

        <div className="login-heading">
          <span className="login-eyebrow">SECURE ACCESS</span>
          <h2>Welcome back</h2>
          <p>Sign in to access your infrastructure dashboard.</p>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          <div className="login-field">
            <label htmlFor="username">Username</label>
            <input
              id="username"
              type="text"
              autoComplete="username"
              placeholder="Enter your username"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              required
              disabled={loading}
            />
          </div>

          <div className="login-field">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              placeholder="Enter your password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
              disabled={loading}
            />
          </div>

          {error && (
            <div className="login-error" role="alert">
              {error}
            </div>
          )}

          <button
            className="login-submit"
            type="submit"
            disabled={loading || !username.trim() || !password}
          >
            {loading ? (
              "Authenticating..."
            ) : (
              <>
                Sign in
                <LogIn size={17} />
              </>
            )}
          </button>
        </form>

        <div className="login-footer">
          <span className="status-dot" />
          SHIP Control Plane
          <span className="login-version">SECURE SESSION</span>
        </div>
      </section>

      <p className="login-copyright">
        Self-Healing Infrastructure Platform
      </p>
    </main>
  );
}

export default Login;

