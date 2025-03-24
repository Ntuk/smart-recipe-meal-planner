import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthContext } from '../context/AuthContext';
import { useTranslation } from 'react-i18next';
import FormInput from '../components/FormInput';

const RegisterPage = () => {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [formError, setFormError] = useState('');
  
  const { register, isLoading, error } = useAuthContext();
  const navigate = useNavigate();
  const { t } = useTranslation();
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError('');
    
    // Basic validation
    if (!username.trim()) {
      setFormError(t('auth.username') + ' ' + t('common.error'));
      return;
    }
    
    if (!email.trim()) {
      setFormError(t('auth.email') + ' ' + t('common.error'));
      return;
    }
    
    if (!password.trim()) {
      setFormError(t('auth.password') + ' ' + t('common.error'));
      return;
    }
    
    if (password !== confirmPassword) {
      setFormError(t('auth.passwordsDoNotMatch', 'Passwords do not match'));
      return;
    }
    
    // Submit registration
    register({ username, email, password });
    
    // Navigate to home page on successful registration
    // Note: This will happen after the registration mutation succeeds
    if (!error) {
      navigate('/');
    }
  };
  
  return (
    <div className="min-h-screen bg-gray-100 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
          {t('auth.registerTitle')}
        </h2>
        <p className="mt-2 text-center text-sm text-gray-600">
          {t('auth.or')}{' '}
          <Link to="/login" className="font-medium text-blue-600 hover:text-blue-500">
            {t('auth.alreadyHaveAccount')}
          </Link>
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <form className="space-y-6" onSubmit={handleSubmit}>
            {(formError || error) && (
              <div className="bg-red-50 border-l-4 border-red-400 p-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg
                      className="h-5 w-5 text-red-400"
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                      aria-hidden="true"
                    >
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm text-red-700">{formError || error}</p>
                  </div>
                </div>
              </div>
            )}

            <FormInput
              id="username"
              name="username"
              type="text"
              autoComplete="username"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              label={t('auth.username')}
              placeholder="johndoe"
            />

            <FormInput
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              label={t('auth.email')}
              placeholder="you@example.com"
            />

            <FormInput
              id="password"
              name="password"
              type="password"
              autoComplete="new-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              label={t('auth.password')}
              placeholder="••••••••"
            />

            <FormInput
              id="confirm-password"
              name="confirmPassword"
              type="password"
              autoComplete="new-password"
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              label={t('auth.confirmPassword', 'Confirm Password')}
              placeholder="••••••••"
              error={password !== confirmPassword && confirmPassword !== '' ? t('auth.passwordsDoNotMatch', 'Passwords do not match') : undefined}
            />

            <div>
              <button
                type="submit"
                disabled={isLoading}
                className="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? t('common.loading') : t('common.register')}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage; 