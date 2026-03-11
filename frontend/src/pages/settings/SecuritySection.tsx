import { useState } from 'react';
import CollapsibleSection from '../../components/CollapsibleSection';
import { setPassword, removePassword } from '../../api/auth';

interface SecuritySectionProps {
  isPasswordSet: boolean;
  logout: () => Promise<void>;
  refreshStatus: () => Promise<void>;
}

function SecuritySection({ isPasswordSet, logout, refreshStatus }: SecuritySectionProps) {
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [passwordSuccess, setPasswordSuccess] = useState<string | null>(null);
  const [isChangingPassword, setIsChangingPassword] = useState(false);

  const handleLogout = async () => {
    await logout();
    window.location.href = '/ui/login';
  };

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordError(null);
    setPasswordSuccess(null);

    if (newPassword !== confirmPassword) {
      setPasswordError('Passwords do not match');
      return;
    }

    if (newPassword && newPassword.length < 8) {
      setPasswordError('Password must be at least 8 characters');
      return;
    }

    setIsChangingPassword(true);
    try {
      if (newPassword) {
        await setPassword(newPassword, currentPassword);
        setPasswordSuccess(isPasswordSet ? 'Password changed successfully' : 'Password set successfully');
      } else {
        await removePassword(currentPassword);
        setPasswordSuccess('Password protection removed');
      }
      await refreshStatus();
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (error) {
      setPasswordError((error as Error).message);
    } finally {
      setIsChangingPassword(false);
    }
  };

  return (
    <CollapsibleSection
      title="Security"
      subtitle={isPasswordSet ? 'Password protection is enabled' : 'No password set - app is publicly accessible'}
    >
      <div className="flex justify-end mb-4">
        {isPasswordSet && (
          <button
            onClick={handleLogout}
            className="px-3 py-1.5 text-sm rounded bg-secondary text-secondary-foreground hover:bg-secondary/80 transition-colors"
          >
            Logout
          </button>
        )}
      </div>

      {!isPasswordSet && (
        <div className="mb-4 p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
          <p className="text-sm text-yellow-600 dark:text-yellow-400">
            This application has no password protection. Anyone with network access can view and modify data.
          </p>
        </div>
      )}

      <form onSubmit={handlePasswordSubmit} className="space-y-4">
        {isPasswordSet && (
          <div>
            <label htmlFor="currentPassword" className="block text-sm font-medium text-foreground mb-2">
              Current Password
            </label>
            <input
              type="password"
              id="currentPassword"
              autoComplete="current-password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              required
              className="w-full px-4 py-2 rounded-lg border border-input bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
        )}

        <div>
          <label htmlFor="newPassword" className="block text-sm font-medium text-foreground mb-2">
            {isPasswordSet ? 'New Password' : 'Set Password'}
          </label>
          <input
            type="password"
            id="newPassword"
            autoComplete="new-password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            placeholder={isPasswordSet ? 'Leave empty to remove password' : 'Minimum 8 characters'}
            className="w-full px-4 py-2 rounded-lg border border-input bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>

        <div>
          <label htmlFor="confirmPassword" className="block text-sm font-medium text-foreground mb-2">
            Confirm Password
          </label>
          <input
            type="password"
            id="confirmPassword"
            autoComplete="new-password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            className="w-full px-4 py-2 rounded-lg border border-input bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>

        {passwordError && (
          <div className="p-3 rounded-lg bg-destructive/10 text-destructive text-sm">
            {passwordError}
          </div>
        )}

        {passwordSuccess && (
          <div className="p-3 rounded-lg bg-green-500/10 text-green-600 dark:text-green-400 text-sm">
            {passwordSuccess}
          </div>
        )}

        <button
          type="submit"
          disabled={isChangingPassword || (!isPasswordSet && !newPassword)}
          className="px-4 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
        >
          {isChangingPassword
            ? 'Saving...'
            : isPasswordSet
            ? newPassword
              ? 'Change Password'
              : 'Remove Password'
            : 'Set Password'}
        </button>
      </form>
    </CollapsibleSection>
  );
}

export default SecuritySection;
